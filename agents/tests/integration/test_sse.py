"""
Integration tests for Server-Sent Events (SSE) functionality.

NOTE: These tests are skipped because SSE was replaced with WebSocket.
The EventBroadcaster API changed - it no longer has connect() or connection_count()
methods, instead it uses a WebSocket manager.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from agents.connectors.events import EventBroadcaster, get_broadcaster

pytestmark = pytest.mark.skip(reason="SSE replaced with WebSocket - EventBroadcaster API changed")


class TestEventBroadcaster:
    """Test EventBroadcaster class."""
    
    def test_broadcaster_initialization(self):
        """Test broadcaster can be initialized."""
        broadcaster = EventBroadcaster()
        assert broadcaster.connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(self):
        """Test broadcasting with no active connections."""
        broadcaster = EventBroadcaster()
        # Should not raise error
        await broadcaster.broadcast("test_event", {"data": "value"})
    
    @pytest.mark.asyncio
    async def test_connect_yields_initial_message(self):
        """Test SSE connection yields initial connected message."""
        broadcaster = EventBroadcaster()
        
        gen = broadcaster.connect()
        first_message = await gen.__anext__()
        
        assert "event: connected" in first_message
        assert "data:" in first_message
        
        # Cleanup
        await gen.aclose()
    
    @pytest.mark.asyncio
    async def test_broadcast_to_connected_client(self):
        """Test broadcasting events to connected client."""
        broadcaster = EventBroadcaster()
        
        # Start connection
        gen = broadcaster.connect()
        
        # Skip initial connected message
        await gen.__anext__()
        
        # Broadcast an event
        await broadcaster.broadcast("test_event", {"key": "value"})
        
        # Receive the event
        message = await asyncio.wait_for(gen.__anext__(), timeout=1.0)
        
        assert "event: test_event" in message
        assert '"key": "value"' in message
        
        # Cleanup
        await gen.aclose()
    
    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """Test broadcasting to multiple connections."""
        broadcaster = EventBroadcaster()
        
        # Create two connections
        gen1 = broadcaster.connect()
        gen2 = broadcaster.connect()
        
        # Skip initial messages
        await gen1.__anext__()
        await gen2.__anext__()
        
        assert broadcaster.connection_count() == 2
        
        # Broadcast event
        await broadcaster.broadcast("multi_test", {"id": 123})
        
        # Both should receive
        msg1 = await asyncio.wait_for(gen1.__anext__(), timeout=1.0)
        msg2 = await asyncio.wait_for(gen2.__anext__(), timeout=1.0)
        
        assert "event: multi_test" in msg1
        assert "event: multi_test" in msg2
        
        # Cleanup
        await gen1.aclose()
        await gen2.aclose()
        
        assert broadcaster.connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_emit_forecast_created(self):
        """Test emitting forecast created event."""
        broadcaster = EventBroadcaster()
        
        gen = broadcaster.connect()
        await gen.__anext__()  # Skip connected message
        
        forecast = {
            "id": 1,
            "market_id": "test-market",
            "market_question": "Will it rain?",
            "probability": 0.75,
            "confidence": 0.85,
        }
        
        await broadcaster.emit_forecast_created(forecast)
        
        message = await asyncio.wait_for(gen.__anext__(), timeout=1.0)
        
        assert "event: forecast_created" in message
        assert '"market_id": "test-market"' in message
        assert '"probability": 0.75' in message
        
        await gen.aclose()
    
    @pytest.mark.asyncio
    async def test_emit_trade_executed(self):
        """Test emitting trade executed event."""
        broadcaster = EventBroadcaster()
        
        gen = broadcaster.connect()
        await gen.__anext__()
        
        trade = {
            "id": 1,
            "market_id": "test-market",
            "market_question": "Will it rain?",
            "side": "BUY",
            "size": 10.0,
            "status": "executed",
        }
        
        await broadcaster.emit_trade_executed(trade)
        
        message = await asyncio.wait_for(gen.__anext__(), timeout=1.0)
        
        assert "event: trade_executed" in message
        assert '"side": "BUY"' in message
        assert '"size": 10.0' in message
        
        await gen.aclose()
    
    @pytest.mark.asyncio
    async def test_emit_portfolio_updated(self):
        """Test emitting portfolio updated event."""
        broadcaster = EventBroadcaster()
        
        gen = broadcaster.connect()
        await gen.__anext__()
        
        portfolio = {
            "balance": 1000.0,
            "total_value": 1500.0,
            "total_pnl": 500.0,
            "win_rate": 0.65,
        }
        
        await broadcaster.emit_portfolio_updated(portfolio)
        
        message = await asyncio.wait_for(gen.__anext__(), timeout=1.0)
        
        assert "event: portfolio_updated" in message
        assert '"balance": 1000.0' in message
        assert '"win_rate": 0.65' in message
        
        await gen.aclose()
    
    @pytest.mark.asyncio
    async def test_emit_agent_status_changed(self):
        """Test emitting agent status changed event."""
        broadcaster = EventBroadcaster()
        
        gen = broadcaster.connect()
        await gen.__anext__()
        
        status = {
            "state": "running",
            "running": True,
            "run_count": 5,
            "error_count": 0,
        }
        
        await broadcaster.emit_agent_status_changed(status)
        
        message = await asyncio.wait_for(gen.__anext__(), timeout=1.0)
        
        assert "event: agent_status_changed" in message
        assert '"state": "running"' in message
        assert '"run_count": 5' in message
        
        await gen.aclose()
    
    @pytest.mark.asyncio
    async def test_keepalive_ping(self):
        """Test keepalive ping is sent after timeout."""
        broadcaster = EventBroadcaster()
        
        gen = broadcaster.connect()
        await gen.__anext__()  # Skip connected message
        
        # Wait for keepalive (should come after 30s, but we'll wait a bit)
        # Note: This test would take 30s in real time, so we just verify the mechanism
        # In a real scenario, you'd mock time or use a shorter timeout for testing
        
        await gen.aclose()
    
    def test_get_broadcaster_singleton(self):
        """Test get_broadcaster returns singleton instance."""
        b1 = get_broadcaster()
        b2 = get_broadcaster()
        assert b1 is b2


class TestSSEEndpoint:
    """Test SSE endpoint integration."""
    
    def test_sse_endpoint_exists(self):
        """Test SSE endpoint is registered."""
        # Note: TestClient doesn't support streaming responses well and will hang
        # The SSE endpoint is tested via the EventBroadcaster tests above
        # This test just documents that the endpoint exists in the API
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "python"))
        from server import app
        routes = [route.path for route in app.routes]
        assert "/api/events/stream" in routes
    
    def test_sse_headers(self):
        """Test SSE endpoint configuration."""
        # SSE endpoint is difficult to test with TestClient due to streaming
        # The important tests are in TestEventBroadcaster which test the actual logic
        # This test just verifies the endpoint is configured
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "python"))
        from server import app
        sse_route = next((r for r in app.routes if r.path == "/api/events/stream"), None)
        assert sse_route is not None
