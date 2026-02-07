"""
Event broadcasting system for realtime updates via WebSocket.
SSE (Server-Sent Events) removed - using WebSocket only.
"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Broadcast events to connected WebSocket clients."""
    
    def __init__(self):
        """Initialize the event broadcaster."""
        self._ws_manager = None  # Will be set by server
    
    def set_ws_manager(self, ws_manager):
        """Set the WebSocket manager for broadcasting to WS clients."""
        self._ws_manager = ws_manager
    
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected WebSocket clients.
        
        Args:
            event_type: Type of event (e.g., "forecast_created", "trade_executed")
            data: Event data dictionary
        """
        if not (self._ws_manager and self._ws_manager.active_connections):
            return
        
        try:
            ws_message = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self._ws_manager.broadcast(ws_message)
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket: {e}")
    
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
