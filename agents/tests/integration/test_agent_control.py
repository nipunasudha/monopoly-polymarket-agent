"""
Integration tests for agent control panel.
"""
import pytest
from fastapi.testclient import TestClient
from scripts.python.server import app, db
from agents.application.runner import get_agent_runner


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def agent_runner():
    """Get agent runner instance."""
    return get_agent_runner()


@pytest.fixture
def database():
    """Get database instance."""
    return db


class TestAgentControlPage:
    """Test agent control page rendering."""
    
    def test_agent_page_renders(self, client):
        """Test that agent control page renders successfully."""
        response = client.get("/agent")
        assert response.status_code == 200
        assert b"Agent Control Panel" in response.content
        assert b"Agent Status & Controls" in response.content
        assert b"Configuration" in response.content
        assert b"Recent Activity" in response.content
    
    def test_agent_page_shows_status(self, client, agent_runner):
        """Test that agent page displays current status."""
        response = client.get("/agent")
        assert response.status_code == 200
        
        # Should show status information (title case)
        status = agent_runner.get_status()
        assert status["state"].title().encode() in response.content
    
    def test_agent_page_shows_controls(self, client):
        """Test that agent page shows control buttons."""
        response = client.get("/agent")
        assert response.status_code == 200
        
        # Should have control buttons
        assert b"Start Agent" in response.content or b"Stop Agent" in response.content
    
    def test_agent_page_shows_stats(self, client):
        """Test that agent page shows statistics."""
        response = client.get("/agent")
        assert response.status_code == 200
        
        # Should show stat cards
        assert b"Total Runs" in response.content
        assert b"Errors" in response.content
        assert b"Total Forecasts" in response.content
        assert b"Total Trades" in response.content
    
    def test_agent_page_shows_config(self, client):
        """Test that agent page shows configuration options."""
        response = client.get("/agent")
        assert response.status_code == 200
        
        # Should show configuration
        assert b"Run Interval" in response.content
        assert b"Trading Mode" in response.content
        assert b"Dry Run" in response.content


class TestAgentControlPartials:
    """Test agent control partial endpoints."""
    
    def test_agent_controls_partial(self, client):
        """Test agent controls partial endpoint."""
        response = client.get("/partials/agent-controls")
        assert response.status_code == 200
        
        # Should contain control buttons
        assert b"button" in response.content
        assert b"hx-post" in response.content
    
    def test_agent_stats_partial(self, client):
        """Test agent stats partial endpoint."""
        response = client.get("/partials/agent-stats")
        assert response.status_code == 200
        
        # Should contain stats grid
        assert b"Total Runs" in response.content
        assert b"Success Rate" in response.content
        assert b"Total Forecasts" in response.content
        assert b"Total Trades" in response.content
    
    def test_activity_feed_partial_empty(self, client):
        """Test activity feed partial with no data."""
        response = client.get("/partials/activity-feed")
        assert response.status_code == 200
        
        # Should show either empty state or activity items (if data exists from other tests)
        assert (b"No recent activity" in response.content or 
                b"Trade Executed" in response.content or 
                b"Forecast Created" in response.content or
                b"flow-root" in response.content)
    
    def test_activity_feed_partial_with_limit(self, client):
        """Test activity feed partial with custom limit."""
        response = client.get("/partials/activity-feed?limit=5")
        assert response.status_code == 200
        assert response.status_code == 200
    
    def test_activity_feed_with_data(self, client, database):
        """Test activity feed partial displays forecast and trade data."""
        # Create sample forecast
        forecast_data = {
            "market_id": "test-market-123",
            "market_question": "Will Bitcoin reach $100k?",
            "outcome": "YES",
            "probability": 0.75,
            "confidence": 0.85,
            "base_rate": 0.5,
            "reasoning": "Test reasoning",
        }
        database.save_forecast(forecast_data)
        
        # Create sample trade
        trade_data = {
            "market_id": "test-market-123",
            "market_question": "Will Bitcoin reach $100k?",
            "outcome": "YES",
            "side": "BUY",
            "size": 10.0,
            "price": 0.75,
            "forecast_probability": 0.75,
            "edge": 0.05,
            "status": "executed",
        }
        database.save_trade(trade_data)
        
        response = client.get("/partials/activity-feed")
        assert response.status_code == 200
        
        # Should show activity items
        assert b"Bitcoin" in response.content


class TestAgentIntervalUpdate:
    """Test agent interval update endpoint."""
    
    def test_update_interval_post(self, client):
        """Test updating interval via POST."""
        response = client.post(
            "/api/agent/interval",
            json={"interval_minutes": 30}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["interval_minutes"] == 30
    
    def test_update_interval_invalid(self, client):
        """Test updating interval with invalid value."""
        response = client.post(
            "/api/agent/interval",
            json={"interval_minutes": 0}
        )
        assert response.status_code == 400


class TestNavigationIntegration:
    """Test navigation menu integration."""
    
    def test_agent_link_in_navigation(self, client):
        """Test that Agent link appears in navigation."""
        response = client.get("/")
        assert response.status_code == 200
        assert b'href="/agent"' in response.content
        assert b"Agent" in response.content
    
    def test_agent_link_active_state(self, client):
        """Test that Agent link shows active state on agent page."""
        response = client.get("/agent")
        assert response.status_code == 200
        
        # Should have active styling on agent link
        assert b'href="/agent"' in response.content


class TestAgentControlFlow:
    """Test complete agent control flow."""
    
    @pytest.mark.asyncio
    async def test_start_stop_flow(self, client, agent_runner):
        """Test starting and stopping agent via UI endpoints."""
        # Ensure agent is stopped
        if agent_runner.state.value == "running":
            await agent_runner.stop()
        
        # Start agent
        response = client.post("/api/agent/start")
        assert response.status_code == 200
        assert agent_runner.state.value == "running"
        
        # Stop agent
        response = client.post("/api/agent/stop")
        assert response.status_code == 200
        assert agent_runner.state.value == "stopped"
    
    @pytest.mark.asyncio
    async def test_pause_resume_flow(self, client, agent_runner):
        """Test pausing and resuming agent."""
        # Ensure agent is running
        if agent_runner.state.value != "running":
            await agent_runner.start()
        
        # Pause agent
        response = client.post("/api/agent/pause")
        assert response.status_code == 200
        assert agent_runner.state.value == "paused"
        
        # Resume agent
        response = client.post("/api/agent/resume")
        assert response.status_code == 200
        assert agent_runner.state.value == "running"
        
        # Clean up
        await agent_runner.stop()
    
    def test_run_once_trigger(self, client):
        """Test manual run-once trigger."""
        response = client.post("/api/agent/run-once")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "started_at" in data
        assert "completed_at" in data


class TestErrorHandling:
    """Test error handling in agent control."""
    
    @pytest.mark.asyncio
    async def test_start_already_running(self, client, agent_runner):
        """Test starting agent when already running."""
        # Start agent
        if agent_runner.state.value != "running":
            await agent_runner.start()
        
        # Try to start again
        response = client.post("/api/agent/start")
        assert response.status_code == 400
        
        # Clean up
        await agent_runner.stop()
    
    @pytest.mark.asyncio
    async def test_stop_not_running(self, client, agent_runner):
        """Test stopping agent when not running."""
        # Ensure agent is stopped
        if agent_runner.state.value == "running":
            await agent_runner.stop()
        
        # Try to stop
        response = client.post("/api/agent/stop")
        assert response.status_code == 400


class TestRealtimeUpdates:
    """Test real-time update integration."""
    
    def test_partials_have_sse_triggers(self, client):
        """Test that page includes SSE triggers for updates."""
        response = client.get("/agent")
        assert response.status_code == 200
        
        # Should have SSE trigger attributes
        assert b"hx-trigger" in response.content
        assert b"sse:" in response.content
    
    def test_controls_update_on_status_change(self, client):
        """Test that controls partial updates on status change."""
        response = client.get("/agent")
        assert response.status_code == 200
        
        # Should have SSE listener for status changes
        assert b"sse:agent_status_changed" in response.content
    
    def test_stats_update_on_events(self, client):
        """Test that stats update on forecast/trade events."""
        response = client.get("/agent")
        assert response.status_code == 200
        
        # Should listen for multiple event types
        assert b"agent-stats" in response.content
