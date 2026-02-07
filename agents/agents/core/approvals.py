"""ApprovalManager - Human-in-the-loop for high-risk operations."""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval status states."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class ApprovalRequest:
    """Represents a pending approval request."""
    trade_id: str
    trade_data: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_at: Optional[float] = None
    rejected_at: Optional[float] = None
    timeout: int = 300  # seconds


class ApprovalManager:
    """Human-in-the-loop for high-risk operations.
    
    Manages approval workflow for trades that exceed risk thresholds.
    Supports auto-approval for small trades and manual approval for large trades.
    """
    
    def __init__(
        self,
        auto_approve_threshold: float = 0.05,
        default_timeout: int = 300,
        websocket_broadcaster: Optional[Callable] = None
    ):
        """Initialize ApprovalManager.
        
        Args:
            auto_approve_threshold: Trade size threshold (as fraction of balance) for auto-approval
            default_timeout: Default timeout in seconds for approval requests
            websocket_broadcaster: Optional function to broadcast WebSocket events
        """
        self.auto_approve_threshold = auto_approve_threshold
        self.default_timeout = default_timeout
        self.websocket_broadcaster = websocket_broadcaster
        
        # Store pending approvals
        self.pending: Dict[str, ApprovalRequest] = {}
        
        # Event waiters (trade_id -> asyncio.Event)
        self.waiters: Dict[str, asyncio.Event] = {}
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "auto_approved": 0,
            "manually_approved": 0,
            "rejected": 0,
            "timeout": 0,
        }
    
    async def request_approval(
        self,
        trade_id: str,
        trade_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> bool:
        """Request approval for a trade (blocks until approved/rejected/timeout).
        
        Args:
            trade_id: Unique identifier for the trade
            trade_data: Dictionary containing trade details (size, market, etc.)
            timeout: Optional timeout in seconds (defaults to self.default_timeout)
            
        Returns:
            True if approved, False if rejected or timeout
        """
        timeout = timeout or self.default_timeout
        self.stats["total_requests"] += 1
        
        # Auto-approve if below risk threshold
        trade_size = trade_data.get("size", 0)
        if isinstance(trade_size, str):
            try:
                trade_size = float(trade_size)
            except (ValueError, TypeError):
                trade_size = 0
        
        if trade_size < self.auto_approve_threshold:
            self.stats["auto_approved"] += 1
            logger.info(f"[APPROVAL] Auto-approved trade {trade_id} (size: {trade_size:.4f} < {self.auto_approve_threshold})")
            return True
        
        # Create approval request
        request = ApprovalRequest(
            trade_id=trade_id,
            trade_data=trade_data,
            timeout=timeout
        )
        
        self.pending[trade_id] = request
        
        # Create event waiter
        event = asyncio.Event()
        self.waiters[trade_id] = event
        
        # Notify dashboard via WebSocket
        await self._notify_dashboard(trade_id, trade_data)
        
        # Wait for approval with timeout
        return await self._wait_for_approval(trade_id, timeout)
    
    async def _wait_for_approval(self, trade_id: str, timeout: int) -> bool:
        """Wait for approval decision with timeout.
        
        Args:
            trade_id: Trade ID to wait for
            timeout: Timeout in seconds
            
        Returns:
            True if approved, False otherwise
        """
        event = self.waiters.get(trade_id)
        if not event:
            logger.error(f"[APPROVAL] No waiter found for trade {trade_id}")
            return False
        
        try:
            # Wait for event with timeout
            await asyncio.wait_for(event.wait(), timeout=timeout)
            
            # Check status
            request = self.pending.get(trade_id)
            if request:
                if request.status == ApprovalStatus.APPROVED:
                    self.stats["manually_approved"] += 1
                    return True
                elif request.status == ApprovalStatus.REJECTED:
                    self.stats["rejected"] += 1
                    return False
            
            return False
            
        except asyncio.TimeoutError:
            # Timeout - mark as rejected
            request = self.pending.get(trade_id)
            if request:
                request.status = ApprovalStatus.TIMEOUT
                request.rejected_at = time.time()
            
            self.stats["timeout"] += 1
            logger.warning(f"[APPROVAL] Trade {trade_id} timed out after {timeout}s")
            
            # Cleanup
            self._cleanup(trade_id)
            
            return False
    
    async def _notify_dashboard(self, trade_id: str, trade_data: Dict[str, Any]):
        """Notify dashboard via WebSocket about pending approval.
        
        Args:
            trade_id: Trade ID
            trade_data: Trade data
        """
        if self.websocket_broadcaster:
            try:
                message = {
                    "type": "approval_request",
                    "trade_id": trade_id,
                    "trade_data": trade_data,
                    "timestamp": time.time()
                }
                await self.websocket_broadcaster(message)
            except Exception as e:
                logger.error(f"[APPROVAL] Failed to notify dashboard: {e}")
    
    def approve(self, trade_id: str) -> bool:
        """Approve a pending trade.
        
        Args:
            trade_id: Trade ID to approve
            
        Returns:
            True if approved successfully, False if trade not found
        """
        request = self.pending.get(trade_id)
        if not request:
            logger.warning(f"[APPROVAL] Trade {trade_id} not found for approval")
            return False
        
        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"[APPROVAL] Trade {trade_id} already processed (status: {request.status})")
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approved_at = time.time()
        
        # Wake up waiter
        event = self.waiters.get(trade_id)
        if event:
            event.set()
        
        logger.info(f"[APPROVAL] Trade {trade_id} approved")
        
        # Cleanup after a delay (allow caller to retrieve status)
        asyncio.create_task(self._cleanup_after_delay(trade_id, delay=5.0))
        
        return True
    
    def reject(self, trade_id: str) -> bool:
        """Reject a pending trade.
        
        Args:
            trade_id: Trade ID to reject
            
        Returns:
            True if rejected successfully, False if trade not found
        """
        request = self.pending.get(trade_id)
        if not request:
            logger.warning(f"[APPROVAL] Trade {trade_id} not found for rejection")
            return False
        
        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"[APPROVAL] Trade {trade_id} already processed (status: {request.status})")
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.rejected_at = time.time()
        
        # Wake up waiter
        event = self.waiters.get(trade_id)
        if event:
            event.set()
        
        logger.info(f"[APPROVAL] Trade {trade_id} rejected")
        
        # Cleanup after a delay
        asyncio.create_task(self._cleanup_after_delay(trade_id, delay=5.0))
        
        return True
    
    async def _cleanup_after_delay(self, trade_id: str, delay: float):
        """Cleanup approval request after a delay.
        
        Args:
            trade_id: Trade ID to cleanup
            delay: Delay in seconds
        """
        await asyncio.sleep(delay)
        self._cleanup(trade_id)
    
    def _cleanup(self, trade_id: str):
        """Cleanup approval request.
        
        Args:
            trade_id: Trade ID to cleanup
        """
        self.pending.pop(trade_id, None)
        self.waiters.pop(trade_id, None)
    
    def get_pending(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending approval requests.
        
        Returns:
            Dictionary of pending requests (trade_id -> request data)
        """
        return {
            trade_id: {
                "trade_id": req.trade_id,
                "trade_data": req.trade_data,
                "created_at": req.created_at,
                "status": req.status.value,
                "timeout": req.timeout,
                "time_remaining": max(0, req.timeout - (time.time() - req.created_at))
            }
            for trade_id, req in self.pending.items()
            if req.status == ApprovalStatus.PENDING
        }
    
    def get_status(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific approval request.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            Status dictionary or None if not found
        """
        request = self.pending.get(trade_id)
        if not request:
            return None
        
        return {
            "trade_id": request.trade_id,
            "status": request.status.value,
            "created_at": request.created_at,
            "approved_at": request.approved_at,
            "rejected_at": request.rejected_at,
            "timeout": request.timeout,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get approval statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            "pending_count": len([r for r in self.pending.values() if r.status == ApprovalStatus.PENDING])
        }
