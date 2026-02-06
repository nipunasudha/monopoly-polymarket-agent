"""
Integration tests for background agent runner.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from agents.application.runner import AgentRunner, AgentState, get_agent_runner


@pytest.fixture
def mock_trader():
    """Mock Trader class."""
    with patch("agents.application.runner.Trader") as mock:
        trader_instance = Mock()
        trader_instance.one_best_trade = Mock()
        mock.return_value = trader_instance
        yield trader_instance


@pytest.fixture
def test_runner(mock_trader):
    """Create a test agent runner."""
    runner = AgentRunner(interval_minutes=1)
    return runner


@pytest.mark.integration
class TestAgentRunnerInitialization:
    """Test agent runner initialization."""

    def test_runner_initializes_with_defaults(self, mock_trader):
        """Test runner initializes with default values."""
        runner = AgentRunner()
        
        assert runner.interval_minutes == 60
        assert runner.state == AgentState.STOPPED
        assert runner.last_run is None
        assert runner.next_run is None
        assert runner.run_count == 0
        assert runner.error_count == 0

    def test_runner_initializes_with_custom_interval(self, mock_trader):
        """Test runner initializes with custom interval."""
        runner = AgentRunner(interval_minutes=30)
        
        assert runner.interval_minutes == 30

    def test_get_agent_runner_singleton(self):
        """Test that get_agent_runner returns singleton."""
        runner1 = get_agent_runner()
        runner2 = get_agent_runner()
        
        assert runner1 is runner2


@pytest.mark.integration
class TestAgentRunnerStatus:
    """Test agent runner status reporting."""

    def test_get_status_returns_dict(self, test_runner):
        """Test that get_status returns dictionary."""
        status = test_runner.get_status()
        
        assert isinstance(status, dict)
        assert "state" in status
        assert "running" in status
        assert "last_run" in status
        assert "next_run" in status
        assert "interval_minutes" in status
        assert "run_count" in status
        assert "error_count" in status

    def test_initial_status(self, test_runner):
        """Test initial status values."""
        status = test_runner.get_status()
        
        assert status["state"] == "stopped"
        assert status["running"] is False
        assert status["last_run"] is None
        assert status["next_run"] is None
        assert status["run_count"] == 0
        assert status["error_count"] == 0


@pytest.mark.integration
class TestAgentRunnerCycle:
    """Test single agent cycle execution."""

    @pytest.mark.asyncio
    async def test_run_agent_cycle_success(self, test_runner, mock_trader):
        """Test successful agent cycle."""
        result = await test_runner.run_agent_cycle()
        
        assert result["success"] is True
        assert result["error"] is None
        assert "started_at" in result
        assert "completed_at" in result
        assert test_runner.run_count == 1
        assert test_runner.last_run is not None

    @pytest.mark.asyncio
    async def test_run_agent_cycle_failure(self, test_runner, mock_trader):
        """Test agent cycle with error."""
        # Make trader raise an error
        mock_trader.one_best_trade.side_effect = Exception("Test error")
        
        result = await test_runner.run_agent_cycle()
        
        assert result["success"] is False
        assert result["error"] == "Test error"
        assert test_runner.error_count == 1
        assert test_runner.last_error == "Test error"

    @pytest.mark.asyncio
    async def test_run_once_manual_trigger(self, test_runner, mock_trader):
        """Test manual run_once trigger."""
        result = await test_runner.run_once()
        
        assert result["success"] is True
        assert test_runner.run_count == 1
        mock_trader.one_best_trade.assert_called_once()


@pytest.mark.integration
class TestAgentRunnerLifecycle:
    """Test agent runner start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_agent(self, test_runner):
        """Test starting the agent."""
        await test_runner.start()
        
        assert test_runner.state == AgentState.RUNNING
        assert test_runner.task is not None
        
        # Cleanup
        await test_runner.stop()

    @pytest.mark.asyncio
    async def test_stop_agent(self, test_runner):
        """Test stopping the agent."""
        await test_runner.start()
        await asyncio.sleep(0.1)  # Let it start
        
        await test_runner.stop()
        
        assert test_runner.state == AgentState.STOPPED
        assert test_runner.next_run is None

    @pytest.mark.asyncio
    async def test_start_already_running(self, test_runner):
        """Test starting agent when already running."""
        await test_runner.start()
        
        # Try to start again (should be no-op)
        await test_runner.start()
        
        assert test_runner.state == AgentState.RUNNING
        
        # Cleanup
        await test_runner.stop()

    @pytest.mark.asyncio
    async def test_stop_not_running(self, test_runner):
        """Test stopping agent when not running."""
        # Should be no-op
        await test_runner.stop()
        
        assert test_runner.state == AgentState.STOPPED


@pytest.mark.integration
class TestAgentRunnerPauseResume:
    """Test agent runner pause/resume functionality."""

    @pytest.mark.asyncio
    async def test_pause_agent(self, test_runner):
        """Test pausing the agent."""
        await test_runner.start()
        await asyncio.sleep(0.1)
        
        await test_runner.pause()
        
        assert test_runner.state == AgentState.PAUSED
        
        # Cleanup
        test_runner.state = AgentState.STOPPED

    @pytest.mark.asyncio
    async def test_resume_agent(self, test_runner):
        """Test resuming the agent."""
        await test_runner.start()
        await test_runner.pause()
        
        await test_runner.resume()
        
        assert test_runner.state == AgentState.RUNNING
        
        # Cleanup
        await test_runner.stop()

    @pytest.mark.asyncio
    async def test_pause_not_running(self, test_runner):
        """Test pausing when not running."""
        # Should be no-op
        await test_runner.pause()
        
        # State might change but shouldn't crash
        assert test_runner.state in [AgentState.STOPPED, AgentState.PAUSED]


@pytest.mark.integration
class TestAgentRunnerConfiguration:
    """Test agent runner configuration."""

    def test_set_interval(self, test_runner):
        """Test updating run interval."""
        test_runner.set_interval(120)
        
        assert test_runner.interval_minutes == 120

    def test_set_interval_updates_status(self, test_runner):
        """Test that interval update reflects in status."""
        test_runner.set_interval(45)
        
        status = test_runner.get_status()
        assert status["interval_minutes"] == 45


@pytest.mark.integration
@pytest.mark.slow
class TestAgentRunnerLoop:
    """Test agent runner continuous loop."""

    @pytest.mark.asyncio
    async def test_runner_executes_multiple_cycles(self, mock_trader):
        """Test that runner executes multiple cycles."""
        # Use very short interval for testing
        runner = AgentRunner(interval_minutes=0.01)  # ~0.6 seconds
        
        await runner.start()
        
        # Wait for a couple cycles
        await asyncio.sleep(1.5)
        
        await runner.stop()
        
        # Should have run at least once
        assert runner.run_count >= 1
        mock_trader.one_best_trade.assert_called()

    @pytest.mark.asyncio
    async def test_runner_calculates_next_run(self, test_runner):
        """Test that runner calculates next run time."""
        await test_runner.start()
        await asyncio.sleep(0.1)
        
        # Next run should be set
        assert test_runner.next_run is not None
        
        await test_runner.stop()

    @pytest.mark.asyncio
    async def test_runner_handles_errors_gracefully(self, mock_trader):
        """Test that runner continues after errors."""
        # First call fails, second succeeds
        mock_trader.one_best_trade.side_effect = [
            Exception("First error"),
            None,  # Success
        ]
        
        runner = AgentRunner(interval_minutes=0.01)
        
        await runner.start()
        await asyncio.sleep(1.5)
        await runner.stop()
        
        # Should have attempted multiple runs
        assert runner.error_count >= 1


@pytest.mark.integration
class TestAgentRunnerErrorHandling:
    """Test agent runner error handling."""

    @pytest.mark.asyncio
    async def test_cycle_failure_increments_error_count(self, test_runner, mock_trader):
        """Test that cycle failures increment error count."""
        mock_trader.one_best_trade.side_effect = Exception("Test error")
        
        result = await test_runner.run_agent_cycle()
        
        assert result["success"] is False
        assert test_runner.error_count == 1
        assert test_runner.last_error == "Test error"

    @pytest.mark.asyncio
    async def test_multiple_failures_tracked(self, test_runner, mock_trader):
        """Test that multiple failures are tracked."""
        mock_trader.one_best_trade.side_effect = Exception("Test error")
        
        await test_runner.run_agent_cycle()
        await test_runner.run_agent_cycle()
        await test_runner.run_agent_cycle()
        
        assert test_runner.error_count == 3
