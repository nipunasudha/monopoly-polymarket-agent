"""
Integration tests for API endpoints with real AgentRunner.
Tests the actual integration between FastAPI endpoints and AgentRunner,
verifying that API calls correctly invoke runner methods and propagate state.

NOTE: We use spies/mocks to verify method calls without running background tasks.
"""
import pytest
from unittest.mock import patch, AsyncMock
from scripts.python.server import db
from agents.application.runner import get_agent_runner, AgentState

# All fixtures are now in conftest.py


@pytest.mark.integration
class TestAPIRunnerIntegration:
    """Test actual integration between API and AgentRunner."""

    def test_api_status_returns_real_runner_state(self, client, setup_test_db, mock_trader):
        """Test that API status endpoint returns actual runner state."""
        runner = get_agent_runner()
        runner.state = AgentState.STOPPED
        runner.interval_minutes = 60
        runner.run_count = 5
        runner.error_count = 2
        
        response = client.get("/api/agent/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should reflect actual runner state
        assert data["state"] == "stopped"
        assert data["interval_minutes"] == 60
        assert data["run_count"] == 5
        assert data["error_count"] == 2

    def test_api_start_calls_runner_start_method(self, client, setup_test_db, mock_trader):
        """Test that POST /api/agent/start calls runner.start()."""
        runner = get_agent_runner()
        runner.state = AgentState.STOPPED
        
        with patch.object(runner, 'start', new_callable=AsyncMock) as mock_start:
            response = client.post("/api/agent/start")
            
            assert response.status_code == 200
            mock_start.assert_called_once()

    def test_api_stop_calls_runner_stop_method(self, client, setup_test_db, mock_trader):
        """Test that POST /api/agent/stop calls runner.stop()."""
        runner = get_agent_runner()
        runner.state = AgentState.RUNNING
        
        with patch.object(runner, 'stop', new_callable=AsyncMock) as mock_stop:
            response = client.post("/api/agent/stop")
            
            assert response.status_code == 200
            mock_stop.assert_called_once()

    def test_api_pause_calls_runner_pause_method(self, client, setup_test_db, mock_trader):
        """Test that POST /api/agent/pause calls runner.pause()."""
        runner = get_agent_runner()
        
        with patch.object(runner, 'pause', new_callable=AsyncMock) as mock_pause:
            response = client.post("/api/agent/pause")
            
            assert response.status_code == 200
            mock_pause.assert_called_once()

    def test_api_resume_calls_runner_resume_method(self, client, setup_test_db, mock_trader):
        """Test that POST /api/agent/resume calls runner.resume()."""
        runner = get_agent_runner()
        
        with patch.object(runner, 'resume', new_callable=AsyncMock) as mock_resume:
            response = client.post("/api/agent/resume")
            
            assert response.status_code == 200
            mock_resume.assert_called_once()

    def test_api_run_once_calls_runner_run_once_method(self, client, setup_test_db, mock_trader):
        """Test that POST /api/agent/run-once calls runner.run_once()."""
        runner = get_agent_runner()
        
        with patch.object(runner, 'run_once', new_callable=AsyncMock) as mock_run_once:
            mock_run_once.return_value = {
                "success": True,
                "started_at": "2026-02-07T00:00:00",
                "completed_at": "2026-02-07T00:00:01",
                "error": None
            }
            
            response = client.post("/api/agent/run-once")
            
            assert response.status_code == 200
            mock_run_once.assert_called_once()
            
            data = response.json()
            assert data["success"] is True

    def test_api_interval_update_calls_runner_set_interval(self, client, setup_test_db, mock_trader):
        """Test that PUT /api/agent/interval calls runner.set_interval()."""
        runner = get_agent_runner()
        
        with patch.object(runner, 'set_interval') as mock_set_interval:
            response = client.put(
                "/api/agent/interval",
                json={"interval_minutes": 45}
            )
            
            assert response.status_code == 200
            mock_set_interval.assert_called_once_with(45)

    def test_api_start_checks_runner_state_before_starting(self, client, setup_test_db, mock_trader):
        """Test that API checks runner state before starting."""
        runner = get_agent_runner()
        runner.state = AgentState.RUNNING
        
        response = client.post("/api/agent/start")
        
        assert response.status_code == 400
        assert "already running" in response.json()["detail"].lower()

    def test_api_stop_checks_runner_state_before_stopping(self, client, setup_test_db, mock_trader):
        """Test that API checks runner state before stopping."""
        runner = get_agent_runner()
        runner.state = AgentState.STOPPED
        
        response = client.post("/api/agent/stop")
        
        assert response.status_code == 400
        assert "not running" in response.json()["detail"].lower()

    def test_api_interval_validation(self, client, setup_test_db, mock_trader):
        """Test that API validates interval values."""
        response = client.put(
            "/api/agent/interval",
            json={"interval_minutes": 0}
        )
        
        assert response.status_code == 400
        assert "at least 1 minute" in response.json()["detail"].lower()

    def test_api_uses_same_runner_instance(self, client, setup_test_db, mock_trader):
        """Test that all API calls use the same runner instance."""
        runner = get_agent_runner()
        runner.interval_minutes = 60
        
        # Update interval via API
        client.put("/api/agent/interval", json={"interval_minutes": 30})
        
        # Verify the same runner instance was updated
        assert runner.interval_minutes == 30

    def test_api_run_once_returns_runner_result(self, client, setup_test_db, mock_trader):
        """Test that run-once returns the actual runner result."""
        runner = get_agent_runner()
        
        expected_result = {
            "success": False,
            "started_at": "2026-02-07T00:00:00",
            "completed_at": "2026-02-07T00:00:01",
            "error": "Test error"
        }
        
        with patch.object(runner, 'run_once', new_callable=AsyncMock) as mock_run_once:
            mock_run_once.return_value = expected_result
            
            response = client.post("/api/agent/run-once")
            
            assert response.status_code == 200
            assert response.json() == expected_result
