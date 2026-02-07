"""
Event broadcasting system for realtime updates via Server-Sent Events (SSE).
"""
import asyncio
import json
import logging
from typing import Dict, Any, AsyncGenerator, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Manage SSE connections and broadcast events to connected clients."""
    
    def __init__(self):
        """Initialize the event broadcaster."""
        self._connections: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()
        self._shutdown = False
    
    async def connect(self) -> AsyncGenerator[str, None]:
        """Create a new SSE connection.
        
        Yields:
            SSE-formatted event strings
        """
        queue: asyncio.Queue = asyncio.Queue()
        
        async with self._lock:
            self._connections.add(queue)
        
        try:
            # Send initial connection event
            yield self._format_sse_message("connected", {"timestamp": datetime.utcnow().isoformat()})
            
            # Stream events from queue
            while not self._shutdown:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message
                except asyncio.TimeoutError:
                    # Send keepalive ping every 30 seconds
                    yield self._format_sse_message("ping", {"timestamp": datetime.utcnow().isoformat()})
        except asyncio.CancelledError:
            logger.debug("SSE connection cancelled")
        except GeneratorExit:
            logger.debug("SSE connection closed by client")
        finally:
            async with self._lock:
                self._connections.discard(queue)
    
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients.
        
        Args:
            event_type: Type of event (e.g., "forecast_created", "trade_executed")
            data: Event data dictionary
        """
        if not self._connections:
            return
        
        message = self._format_sse_message(event_type, data)
        
        async with self._lock:
            # Send to all connected clients
            for queue in self._connections:
                try:
                    await queue.put(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
    
    def _format_sse_message(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as SSE message.
        
        Args:
            event_type: Event type
            data: Event data
            
        Returns:
            SSE-formatted message string
        """
        json_data = json.dumps(data)
        return f"event: {event_type}\ndata: {json_data}\n\n"
    
    async def emit_forecast_created(self, forecast: Dict[str, Any]):
        """Emit forecast created event.
        
        Args:
            forecast: Forecast data dictionary
        """
        await self.broadcast("forecast_created", {
            "id": forecast.get("id"),
            "market_id": forecast.get("market_id"),
            "market_question": forecast.get("market_question"),
            "probability": forecast.get("probability"),
            "confidence": forecast.get("confidence"),
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"Broadcast forecast_created event: {forecast.get('id')}")
    
    async def emit_trade_executed(self, trade: Dict[str, Any]):
        """Emit trade executed event.
        
        Args:
            trade: Trade data dictionary
        """
        await self.broadcast("trade_executed", {
            "id": trade.get("id"),
            "market_id": trade.get("market_id"),
            "market_question": trade.get("market_question"),
            "side": trade.get("side"),
            "size": trade.get("size"),
            "status": trade.get("status"),
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"Broadcast trade_executed event: {trade.get('id')}")
    
    async def emit_portfolio_updated(self, portfolio: Dict[str, Any]):
        """Emit portfolio updated event.
        
        Args:
            portfolio: Portfolio data dictionary
        """
        await self.broadcast("portfolio_updated", {
            "balance": portfolio.get("balance"),
            "total_value": portfolio.get("total_value"),
            "total_pnl": portfolio.get("total_pnl"),
            "win_rate": portfolio.get("win_rate"),
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info("Broadcast portfolio_updated event")
    
    async def emit_agent_status_changed(self, status: Dict[str, Any]):
        """Emit agent status changed event.
        
        Args:
            status: Agent status dictionary
        """
        await self.broadcast("agent_status_changed", {
            "state": status.get("state"),
            "running": status.get("running"),
            "run_count": status.get("run_count"),
            "error_count": status.get("error_count"),
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"Broadcast agent_status_changed event: {status.get('state')}")
    
    def connection_count(self) -> int:
        """Get the number of active connections.
        
        Returns:
            Number of active SSE connections
        """
        return len(self._connections)
    
    async def close_all_connections(self):
        """Close all active SSE connections.
        
        Used during shutdown to ensure clean exit.
        """
        logger.info(f"Closing {len(self._connections)} SSE connections")
        
        # Set shutdown flag to stop all connection loops
        self._shutdown = True
        
        # Send a final message to all queues to wake them up
        async with self._lock:
            for queue in self._connections:
                try:
                    # Put a shutdown message to wake up any waiting connections
                    await asyncio.wait_for(
                        queue.put(self._format_sse_message("shutdown", {"reason": "Server shutting down"})),
                        timeout=0.1
                    )
                except (asyncio.TimeoutError, Exception):
                    pass
            
            # Clear all connections
            self._connections.clear()
        
        logger.info("All SSE connections closed")


# Global broadcaster instance
_broadcaster: EventBroadcaster = None


def get_broadcaster() -> EventBroadcaster:
    """Get or create the global event broadcaster.
    
    Returns:
        EventBroadcaster instance
    """
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = EventBroadcaster()
    return _broadcaster
