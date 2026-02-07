"""
Integration tests for Phase 5: ApprovalManager
Tests approval workflow, auto-approval, manual approval, and timeouts.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from agents.core.approvals import ApprovalManager, ApprovalStatus, ApprovalRequest


@pytest.mark.integration
@pytest.mark.asyncio
class TestApprovalManager:
    """Test ApprovalManager functionality."""
    
    @pytest.mark.asyncio
    async def test_approval_manager_initialization(self):
        """Test ApprovalManager initialization."""
        manager = ApprovalManager()
        assert manager is not None
        assert manager.auto_approve_threshold == 0.05
        assert manager.default_timeout == 300
        assert isinstance(manager.pending, dict)
        assert isinstance(manager.waiters, dict)
    
    @pytest.mark.asyncio
    async def test_auto_approval_small_trade(self):
        """Test auto-approval for trades below threshold."""
        manager = ApprovalManager(auto_approve_threshold=0.05)
        
        result = await manager.request_approval(
            trade_id="small_trade",
            trade_data={"size": 0.01}  # 1% - below threshold
        )
        
        assert result == True
        assert manager.stats["auto_approved"] == 1
        assert manager.stats["total_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_manual_approval_flow(self):
        """Test manual approval workflow."""
        manager = ApprovalManager(auto_approve_threshold=0.05)
        
        trade_id = "large_trade"
        
        # Start approval request
        approval_task = asyncio.create_task(
            manager.request_approval(
                trade_id=trade_id,
                trade_data={"size": 0.10},  # 10% - above threshold
                timeout=5
            )
        )
        
        # Wait a bit
        await asyncio.sleep(0.1)
        
        # Check pending
        pending = manager.get_pending()
        assert trade_id in pending
        
        # Approve
        approved = manager.approve(trade_id)
        assert approved == True
        
        # Wait for result
        result = await approval_task
        assert result == True
        assert manager.stats["manually_approved"] == 1
    
    @pytest.mark.asyncio
    async def test_rejection_flow(self):
        """Test rejection workflow."""
        manager = ApprovalManager(auto_approve_threshold=0.05)
        
        trade_id = "rejected_trade"
        
        # Start approval request
        approval_task = asyncio.create_task(
            manager.request_approval(
                trade_id=trade_id,
                trade_data={"size": 0.10},
                timeout=5
            )
        )
        
        await asyncio.sleep(0.1)
        
        # Reject
        rejected = manager.reject(trade_id)
        assert rejected == True
        
        # Wait for result
        result = await approval_task
        assert result == False
        assert manager.stats["rejected"] == 1
    
    @pytest.mark.asyncio
    async def test_timeout_behavior(self):
        """Test timeout behavior."""
        manager = ApprovalManager(auto_approve_threshold=0.05, default_timeout=1)
        
        trade_id = "timeout_trade"
        
        # Start approval request with short timeout
        result = await manager.request_approval(
            trade_id=trade_id,
            trade_data={"size": 0.10},
            timeout=1  # 1 second timeout
        )
        
        # Should timeout and return False
        assert result == False
        assert manager.stats["timeout"] == 1
        
        # Check request status
        status = manager.get_status(trade_id)
        assert status is None or status["status"] == ApprovalStatus.TIMEOUT.value
    
    @pytest.mark.asyncio
    async def test_get_pending(self):
        """Test getting pending approvals."""
        manager = ApprovalManager(auto_approve_threshold=0.05)
        
        trade_id = "pending_trade"
        
        # Start approval request
        approval_task = asyncio.create_task(
            manager.request_approval(
                trade_id=trade_id,
                trade_data={"size": 0.10},
                timeout=5
            )
        )
        
        await asyncio.sleep(0.1)
        
        # Get pending
        pending = manager.get_pending()
        assert trade_id in pending
        assert pending[trade_id]["status"] == ApprovalStatus.PENDING.value
        
        # Cleanup
        manager.approve(trade_id)
        await approval_task
    
    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting approval status."""
        manager = ApprovalManager(auto_approve_threshold=0.05)
        
        trade_id = "status_trade"
        
        # Start approval request
        approval_task = asyncio.create_task(
            manager.request_approval(
                trade_id=trade_id,
                trade_data={"size": 0.10},
                timeout=5
            )
        )
        
        await asyncio.sleep(0.1)
        
        # Get status
        status = manager.get_status(trade_id)
        assert status is not None
        assert status["trade_id"] == trade_id
        assert status["status"] == ApprovalStatus.PENDING.value
        
        # Approve and check status
        manager.approve(trade_id)
        await asyncio.sleep(0.1)
        
        status = manager.get_status(trade_id)
        # Status might be cleaned up, or show approved
        assert status is None or status["status"] == ApprovalStatus.APPROVED.value
        
        await approval_task
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self):
        """Test statistics tracking."""
        manager = ApprovalManager(auto_approve_threshold=0.05)
        
        # Auto-approve
        await manager.request_approval("trade1", {"size": 0.01})
        
        # Manual approve
        task2 = asyncio.create_task(manager.request_approval("trade2", {"size": 0.10}, timeout=5))
        await asyncio.sleep(0.1)
        manager.approve("trade2")
        await task2
        
        # Reject
        task3 = asyncio.create_task(manager.request_approval("trade3", {"size": 0.10}, timeout=5))
        await asyncio.sleep(0.1)
        manager.reject("trade3")
        await task3
        
        # Check stats
        stats = manager.get_stats()
        assert stats["total_requests"] == 3
        assert stats["auto_approved"] == 1
        assert stats["manually_approved"] == 1
        assert stats["rejected"] == 1
    
    @pytest.mark.asyncio
    async def test_websocket_notification(self):
        """Test WebSocket notification."""
        mock_broadcaster = AsyncMock()
        manager = ApprovalManager(websocket_broadcaster=mock_broadcaster)
        
        trade_id = "notify_trade"
        
        # Start approval request
        approval_task = asyncio.create_task(
            manager.request_approval(
                trade_id=trade_id,
                trade_data={"size": 0.10},
                timeout=5
            )
        )
        
        await asyncio.sleep(0.1)
        
        # Check that broadcaster was called
        assert mock_broadcaster.called
        
        # Cleanup
        manager.approve(trade_id)
        await approval_task
    
    @pytest.mark.asyncio
    async def test_approve_nonexistent_trade(self):
        """Test approving a trade that doesn't exist."""
        manager = ApprovalManager()
        
        result = manager.approve("nonexistent")
        assert result == False
    
    @pytest.mark.asyncio
    async def test_reject_nonexistent_trade(self):
        """Test rejecting a trade that doesn't exist."""
        manager = ApprovalManager()
        
        result = manager.reject("nonexistent")
        assert result == False
    
    @pytest.mark.asyncio
    async def test_approve_already_processed(self):
        """Test approving a trade that's already processed."""
        manager = ApprovalManager(auto_approve_threshold=0.05)
        
        trade_id = "processed_trade"
        
        # Auto-approve (processes immediately)
        await manager.request_approval(trade_id, {"size": 0.01})
        
        # Try to approve again
        result = manager.approve(trade_id)
        assert result == False  # Should fail because not pending
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_approvals(self):
        """Test handling multiple concurrent approval requests."""
        manager = ApprovalManager(auto_approve_threshold=0.05)
        
        # Start multiple approval requests
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                manager.request_approval(
                    trade_id=f"trade_{i}",
                    trade_data={"size": 0.10},
                    timeout=5
                )
            )
            tasks.append(task)
        
        await asyncio.sleep(0.1)
        
        # Check all are pending
        pending = manager.get_pending()
        assert len(pending) == 5
        
        # Approve all
        for i in range(5):
            manager.approve(f"trade_{i}")
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        assert all(results) == True
        assert manager.stats["manually_approved"] == 5
