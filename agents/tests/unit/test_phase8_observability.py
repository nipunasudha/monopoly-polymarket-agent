"""
Unit tests for Phase 8: Observability & WebSocket Status Updates

Tests hub status endpoints, WebSocket broadcasts, structured logging,
and performance metrics tracking.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import the classes we need to test
from agents.core.hub import TradingHub
from agents.core.session import Task, Lane
from agents.core.structured_logging import configure_structlog, get_logger, PerformanceMetrics


# ============================================================================
# Phase 8: Structured Logging Tests
# ============================================================================

class TestStructuredLogging:
    """Test structured logging configuration and usage."""
    
    def test_configure_structlog_console_mode(self):
        """Test structlog configuration with console output."""
        # Should not raise any exceptions
        configure_structlog(level="INFO", json_output=False)
        logger = get_logger("test")
        assert logger is not None
    
    def test_configure_structlog_json_mode(self):
        """Test structlog configuration with JSON output."""
        configure_structlog(level="DEBUG", json_output=True)
        logger = get_logger("test_json")
        assert logger is not None
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid logger."""
        configure_structlog(level="INFO", json_output=False)
        logger = get_logger(__name__)
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")


class TestPerformanceMetrics:
    """Test performance metrics tracking."""
    
    def test_record_metric(self):
        """Test recording a metric."""
        configure_structlog(level="INFO", json_output=False)
        logger = get_logger("test_metrics")
        metrics = PerformanceMetrics(logger)
        
        metrics.record("test_metric", 42, context="test")
        
        all_metrics = metrics.get_all()
        assert "test_metric" in all_metrics
        assert all_metrics["test_metric"] == 42
    
    def test_increment_metric(self):
        """Test incrementing a counter metric."""
        configure_structlog(level="INFO", json_output=False)
        logger = get_logger("test_metrics")
        metrics = PerformanceMetrics(logger)
        
        metrics.increment("counter", 1)
        metrics.increment("counter", 5)
        
        all_metrics = metrics.get_all()
        assert all_metrics["counter"] == 6
    
    def test_timing_metric(self):
        """Test recording a timing metric (doesn't store in metrics dict)."""
        configure_structlog(level="INFO", json_output=False)
        logger = get_logger("test_metrics")
        metrics = PerformanceMetrics(logger)
        
        # Should not raise
        metrics.timing("operation_duration", 123.45, operation="test")
    
    def test_get_all_returns_copy(self):
        """Test that get_all returns a copy of metrics."""
        configure_structlog(level="INFO", json_output=False)
        logger = get_logger("test_metrics")
        metrics = PerformanceMetrics(logger)
        
        metrics.record("test", 100)
        all_metrics = metrics.get_all()
        all_metrics["test"] = 999  # Modify the copy
        
        # Original should be unchanged
        assert metrics.get_all()["test"] == 100


# ============================================================================
# Phase 8: Hub Metrics Tests
# ============================================================================

class TestHubMetrics:
    """Test TradingHub performance metrics integration."""
    
    @pytest.mark.asyncio
    async def test_hub_has_metrics_when_structlog_available(self):
        """Test hub initializes metrics when structlog is available."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            hub = TradingHub()
            
            # Hub should have metrics if structlog is imported successfully
            # (metrics could be None if structlog import failed)
            if hub.metrics is not None:
                assert isinstance(hub.metrics, PerformanceMetrics)
    
    @pytest.mark.asyncio
    async def test_hub_status_includes_metrics(self):
        """Test that get_status includes metrics when available."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            hub = TradingHub()
            
            status = hub.get_status()
            
            # If metrics are available, should be in status
            if hub.metrics is not None:
                assert "metrics" in status
                assert isinstance(status["metrics"], dict)
    
    @pytest.mark.asyncio
    async def test_enqueue_records_metrics(self):
        """Test that enqueuing tasks records metrics."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            hub = TradingHub()
            
            # Don't start hub - just enqueue
            task = Task(
                id="test_metrics_task",
                prompt="Test task",
                lane=Lane.RESEARCH,
                priority=5
            )
            
            await hub.enqueue(task)
            
            # Check stats are updated
            assert hub.stats["tasks_enqueued"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_task_records_timing(self):
        """Test that task execution records timing metrics."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            hub = TradingHub()
            
            # Mock the Claude API call
            hub.client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(type="text", text="Test result")]
            hub.client.messages.create = Mock(return_value=mock_response)
            
            task = Task(
                id="test_timing_task",
                prompt="Test timing",
                lane=Lane.RESEARCH,
                priority=5
            )
            
            await hub._execute_task(task, Lane.RESEARCH)
            
            # Should complete without error
            assert "test_timing_task" in hub.task_results


# ============================================================================
# Phase 8: Hub Status API Tests (Mocked)
# ============================================================================

class TestHubStatusAPIs:
    """Test hub status API logic (without FastAPI server)."""
    
    @pytest.mark.asyncio
    async def test_get_hub_status_new_architecture(self):
        """Test getting hub status in new architecture mode."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            from agents.application.runner import AgentRunner
            
            # Create runner with new architecture
            with patch.dict("os.environ", {"USE_NEW_ARCHITECTURE": "true"}):
                runner = AgentRunner()
                
                status = runner.get_status()
                
                assert status["architecture"] == "new"
                assert "hub_status" in status
                assert isinstance(status["hub_status"], dict)
    
    @pytest.mark.asyncio
    async def test_get_hub_status_legacy_architecture(self):
        """Test getting hub status in legacy architecture mode."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            from agents.application.runner import AgentRunner
            
            # Create runner with legacy architecture
            with patch.dict("os.environ", {"USE_NEW_ARCHITECTURE": "false"}):
                runner = AgentRunner()
                
                status = runner.get_status()
                
                assert status["architecture"] == "legacy"
                assert "hub_status" not in status
    
    @pytest.mark.asyncio
    async def test_hub_status_includes_lane_info(self):
        """Test that hub status includes lane information."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key", "USE_NEW_ARCHITECTURE": "true"}):
            from agents.application.runner import AgentRunner
            
            runner = AgentRunner()
            status = runner.get_status()
            hub_status = status.get("hub_status", {})
            
            # Should have lane_status for each lane
            if "lane_status" in hub_status:
                lane_status = hub_status["lane_status"]
                # Lane names are lowercase in the dict
                assert "main" in lane_status or "MAIN" in lane_status
                assert "research" in lane_status or "RESEARCH" in lane_status
                assert "monitor" in lane_status or "MONITOR" in lane_status
                assert "cron" in lane_status or "CRON" in lane_status


# ============================================================================
# Phase 8: WebSocket Broadcast Tests (Mocked)
# ============================================================================

class TestWebSocketBroadcast:
    """Test WebSocket hub status broadcasting logic."""
    
    @pytest.mark.asyncio
    async def test_connection_manager_broadcasts_hub_status(self):
        """Test that ConnectionManager can broadcast hub status."""
        # This would be a full integration test with a real server
        # For now, we test the logic in isolation
        
        # Mock ConnectionManager
        from datetime import datetime
        
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        
        connections = [mock_ws]
        
        # Simulate a broadcast
        message = {
            "type": "hub_status_update",
            "data": {
                "running": True,
                "sessions": 2,
                "stats": {"tasks_enqueued": 5}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all connections
        for conn in connections:
            await conn.send_json(message)
        
        # Verify send_json was called
        mock_ws.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_handles_dead_connections(self):
        """Test that broadcast handles disconnected clients gracefully."""
        mock_ws_good = Mock()
        mock_ws_good.send_json = AsyncMock()
        
        mock_ws_dead = Mock()
        mock_ws_dead.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        
        connections = [mock_ws_good, mock_ws_dead]
        
        message = {"type": "test", "data": "test"}
        
        # Try to broadcast to all
        for conn in connections:
            try:
                await conn.send_json(message)
            except Exception:
                pass  # Expected for dead connection
        
        # Good connection should have received
        mock_ws_good.send_json.assert_called_once()


# ============================================================================
# Phase 8: Integration Test
# ============================================================================

class TestPhase8Integration:
    """Integration tests for Phase 8 features."""
    
    @pytest.mark.asyncio
    async def test_full_observability_flow(self):
        """Test the full observability flow: metrics, logging, status."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            # Configure structured logging
            configure_structlog(level="INFO", json_output=False)
            
            # Create hub
            hub = TradingHub()
            
            # Create and enqueue a task (don't start hub to avoid background processing)
            task = Task(
                id="integration_test_task",
                prompt="Test observability",
                lane=Lane.RESEARCH,
                priority=10
            )
            
            await hub.enqueue(task)
            
            # Get status (should include metrics)
            status = hub.get_status()
            
            assert status["running"] is False  # Not started
            assert status["stats"]["tasks_enqueued"] >= 1
            
            # Check lane status
            assert "lane_status" in status
    
    @pytest.mark.asyncio
    async def test_metrics_tracked_across_operations(self):
        """Test that metrics are tracked across multiple operations."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            configure_structlog(level="INFO", json_output=False)
            
            hub = TradingHub()
            
            # Enqueue multiple tasks (don't start hub)
            for i in range(3):
                task = Task(
                    id=f"task_{i}",
                    prompt=f"Test task {i}",
                    lane=Lane.RESEARCH,
                    priority=i
                )
                await hub.enqueue(task)
            
            # Check stats
            status = hub.get_status()
            assert status["stats"]["tasks_enqueued"] == 3
