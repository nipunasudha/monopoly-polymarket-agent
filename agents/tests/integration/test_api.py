"""
Integration tests for FastAPI endpoints.
"""
import pytest
import json
from unittest.mock import patch
from scripts.python.server import db

# All fixtures are now in conftest.py


@pytest.mark.integration
class TestRootEndpoints:
    """Test root and health check endpoints."""

    def test_read_root(self, client, setup_test_db):
        """Test root endpoint - now returns 404 since dashboard moved to Next.js."""
        response = client.get("/")
        
        # Root endpoint no longer exists - dashboard is served by Next.js frontend
        assert response.status_code == 404
    
    def test_api_root(self, client, setup_test_db):
        """Test API root endpoint returns JSON."""
        response = client.get("/api")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


@pytest.mark.integration
class TestForecastEndpoints:
    """Test forecast API endpoints."""

    def test_get_forecasts_empty(self, client, setup_test_db):
        """Test getting forecasts from empty database."""
        response = client.get("/api/forecasts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_forecasts_with_data(self, client, setup_test_db, sample_forecast_in_db):
        """Test getting forecasts with data in database."""
        response = client.get("/api/forecasts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["market_id"] == "12345"
        assert data[0]["probability"] == 0.35

    def test_get_forecasts_with_limit(self, client, setup_test_db):
        """Test getting forecasts with limit parameter."""
        # Add multiple forecasts
        for i in range(5):
            db.save_forecast({
                "market_id": f"market_{i}",
                "market_question": f"Question {i}?",
                "outcome": "Yes",
                "probability": 0.5,
                "confidence": 0.7,
            })
        
        response = client.get("/api/forecasts?limit=3")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_forecast_by_id(self, client, sample_forecast_in_db):
        """Test getting a specific forecast by ID."""
        forecast_id = sample_forecast_in_db.id
        
        response = client.get(f"/api/forecasts/{forecast_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == forecast_id
        assert data["market_id"] == "12345"

    def test_get_forecast_not_found(self, client, setup_test_db):
        """Test getting a non-existent forecast returns 404."""
        response = client.get("/api/forecasts/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_market_forecasts(self, client, setup_test_db, sample_forecast_in_db):
        """Test getting all forecasts for a specific market."""
        # Add another forecast for the same market
        db.save_forecast({
            "market_id": "12345",
            "market_question": "Will Bitcoin reach $100k by end of 2026?",
            "outcome": "No",
            "probability": 0.65,
            "confidence": 0.70,
        })
        
        response = client.get("/api/markets/12345/forecasts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(f["market_id"] == "12345" for f in data)

    def test_get_market_forecasts_empty(self, client, setup_test_db):
        """Test getting forecasts for market with no forecasts."""
        response = client.get("/api/markets/nonexistent/forecasts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


@pytest.mark.integration
class TestTradeEndpoints:
    """Test trade API endpoints."""

    def test_get_trades_empty(self, client, setup_test_db):
        """Test getting trades from empty database."""
        response = client.get("/api/trades")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_trades_with_data(self, client, sample_trade_in_db):
        """Test getting trades with data in database."""
        response = client.get("/api/trades")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["market_id"] == "12345"
        assert data[0]["side"] == "BUY"
        assert data[0]["size"] == 250.0

    def test_get_trades_with_limit(self, client, setup_test_db):
        """Test getting trades with limit parameter."""
        # Add multiple trades
        for i in range(5):
            db.save_trade({
                "market_id": f"market_{i}",
                "market_question": f"Question {i}?",
                "outcome": "Yes",
                "side": "BUY",
                "size": 100.0,
                "forecast_probability": 0.6,
            })
        
        response = client.get("/api/trades?limit=3")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_trade_by_id(self, client, sample_trade_in_db):
        """Test getting a specific trade by ID."""
        trade_id = sample_trade_in_db.id
        
        response = client.get(f"/api/trades/{trade_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == trade_id
        assert data["market_id"] == "12345"
        assert data["status"] == "pending"

    def test_get_trade_not_found(self, client, setup_test_db):
        """Test getting a non-existent trade returns 404."""
        response = client.get("/api/trades/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.integration
class TestPortfolioEndpoints:
    """Test portfolio API endpoints."""

    def test_get_portfolio_empty(self, client, setup_test_db):
        """Test getting portfolio with no data returns empty portfolio."""
        response = client.get("/api/portfolio")
        
        # Portfolio endpoint returns 200 with default values when empty
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "total_value" in data

    def test_get_portfolio_with_data(self, client, sample_portfolio_in_db):
        """Test getting current portfolio state."""
        response = client.get("/api/portfolio")
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 1000.0
        assert data["total_value"] == 1250.0
        assert data["total_pnl"] == 250.0
        assert data["win_rate"] == 0.65

    def test_get_portfolio_returns_latest(self, client, setup_test_db):
        """Test that portfolio endpoint returns the most recent snapshot."""
        # Add multiple snapshots
        db.save_portfolio_snapshot({
            "balance": 1000.0,
            "total_value": 1000.0,
            "open_positions": 0,
            "total_pnl": 0.0,
            "total_trades": 0,
        })
        db.save_portfolio_snapshot({
            "balance": 1500.0,
            "total_value": 1750.0,
            "open_positions": 2,
            "total_pnl": 250.0,
            "total_trades": 5,
        })
        
        response = client.get("/api/portfolio")
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 1500.0  # Should be the latest

    def test_get_portfolio_history_empty(self, client, setup_test_db):
        """Test getting portfolio history from empty database."""
        response = client.get("/api/portfolio/history")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_portfolio_history_with_data(self, client, setup_test_db):
        """Test getting portfolio history."""
        # Add multiple snapshots
        for i in range(5):
            db.save_portfolio_snapshot({
                "balance": 1000.0 + (i * 100),
                "total_value": 1000.0 + (i * 100),
                "open_positions": i,
                "total_pnl": i * 50.0,
                "total_trades": i,
            })
        
        response = client.get("/api/portfolio/history")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_portfolio_history_with_limit(self, client, setup_test_db):
        """Test getting portfolio history with limit."""
        # Add multiple snapshots
        for i in range(10):
            db.save_portfolio_snapshot({
                "balance": 1000.0,
                "total_value": 1000.0,
                "open_positions": 0,
                "total_pnl": 0.0,
                "total_trades": 0,
            })
        
        response = client.get("/api/portfolio/history?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


@pytest.mark.integration
class TestAPIResponseFormats:
    """Test API response formats and validation."""

    def test_forecast_response_format(self, client, sample_forecast_in_db):
        """Test forecast response has correct format."""
        response = client.get(f"/api/forecasts/{sample_forecast_in_db.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "id" in data
        assert "market_id" in data
        assert "market_question" in data
        assert "outcome" in data
        assert "probability" in data
        assert "confidence" in data
        assert "created_at" in data
        
        # Check types
        assert isinstance(data["id"], int)
        assert isinstance(data["probability"], float)
        assert isinstance(data["confidence"], float)

    def test_trade_response_format(self, client, sample_trade_in_db):
        """Test trade response has correct format."""
        response = client.get(f"/api/trades/{sample_trade_in_db.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "id" in data
        assert "market_id" in data
        assert "side" in data
        assert "size" in data
        assert "status" in data
        assert "created_at" in data
        
        # Check types
        assert isinstance(data["id"], int)
        assert isinstance(data["size"], float)
        assert data["side"] in ["BUY", "SELL"]

    def test_portfolio_response_format(self, client, sample_portfolio_in_db):
        """Test portfolio response has correct format."""
        response = client.get("/api/portfolio")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "balance" in data
        assert "total_value" in data
        assert "open_positions" in data
        assert "total_pnl" in data
        assert "total_trades" in data
        assert "created_at" in data
        
        # Check types
        assert isinstance(data["balance"], float)
        assert isinstance(data["total_value"], float)
        assert isinstance(data["open_positions"], int)


@pytest.mark.integration
class TestAgentControlEndpoints:
    """Test agent control API endpoints.
    
    Note: Comprehensive integration tests for agent runner are in test_api_runner_integration.py
    """

    def test_agent_status_endpoint(self, client, setup_test_db):
        """Test GET /api/agent/status."""
        response = client.get("/api/agent/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert "state" in data
        assert "running" in data
        assert "last_run" in data
        assert "next_run" in data
        assert "interval_minutes" in data
        assert "run_count" in data
        assert "error_count" in data
        assert "last_error" in data
        assert "total_forecasts" in data
        assert "total_trades" in data
        
        # Check types and values
        assert isinstance(data["state"], str)
        assert data["state"] in ["stopped", "running", "paused", "error"]
        assert isinstance(data["running"], bool)
        assert isinstance(data["interval_minutes"], int)
        assert isinstance(data["run_count"], int)
        assert isinstance(data["error_count"], int)

    def test_start_agent_endpoint_response_format(self, client, setup_test_db):
        """Test POST /api/agent/start response format."""
        # Mock the agent runner to avoid actually starting it
        with patch("scripts.python.server.agent_runner") as mock_runner:
            mock_runner.state.value = "stopped"
            mock_runner.interval_minutes = 60
            mock_runner.next_run = None
            
            # Mock the start method
            async def mock_start():
                mock_runner.state.value = "running"
            mock_runner.start = mock_start
            
            response = client.post("/api/agent/start")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert "message" in data

    def test_start_agent_already_running_error(self, client, setup_test_db):
        """Test starting agent when already running returns error."""
        with patch("scripts.python.server.agent_runner") as mock_runner:
            mock_runner.state.value = "running"
            
            response = client.post("/api/agent/start")
            
            assert response.status_code == 400
            assert "detail" in response.json()

    def test_stop_agent_endpoint_response_format(self, client, setup_test_db):
        """Test POST /api/agent/stop response format."""
        with patch("scripts.python.server.agent_runner") as mock_runner:
            mock_runner.state.value = "running"
            
            async def mock_stop():
                mock_runner.state.value = "stopped"
            mock_runner.stop = mock_stop
            
            response = client.post("/api/agent/stop")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert "message" in data

    def test_stop_agent_not_running_error(self, client, setup_test_db):
        """Test stopping agent when not running returns error."""
        with patch("scripts.python.server.agent_runner") as mock_runner:
            mock_runner.state.value = "stopped"
            
            response = client.post("/api/agent/stop")
            
            assert response.status_code == 400
            assert "detail" in response.json()

    def test_pause_agent_endpoint_response_format(self, client, setup_test_db):
        """Test POST /api/agent/pause response format."""
        with patch("scripts.python.server.agent_runner") as mock_runner:
            async def mock_pause():
                pass
            mock_runner.pause = mock_pause
            
            response = client.post("/api/agent/pause")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert data["status"] == "paused"

    def test_resume_agent_endpoint_response_format(self, client, setup_test_db):
        """Test POST /api/agent/resume response format."""
        with patch("scripts.python.server.agent_runner") as mock_runner:
            async def mock_resume():
                pass
            mock_runner.resume = mock_resume
            
            response = client.post("/api/agent/resume")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert data["status"] == "resumed"

    def test_run_once_endpoint(self, client, setup_test_db):
        """Test POST /api/agent/run-once."""
        with patch("scripts.python.server.agent_runner") as mock_runner:
            # Mock the run_once method
            async def mock_run_once():
                return {
                    "success": True,
                    "started_at": "2026-02-07T00:00:00",
                    "completed_at": "2026-02-07T00:00:01",
                    "error": None
                }
            mock_runner.run_once = mock_run_once
            
            response = client.post("/api/agent/run-once")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "success" in data
            assert "started_at" in data
            assert "completed_at" in data
            assert "error" in data

    def test_update_interval_endpoint(self, client, setup_test_db):
        """Test PUT /api/agent/interval."""
        response = client.put(
            "/api/agent/interval",
            json={"interval_minutes": 120}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "updated"
        assert data["interval_minutes"] == 120

    def test_update_interval_invalid(self, client, setup_test_db):
        """Test updating interval with invalid value."""
        response = client.put(
            "/api/agent/interval",
            json={"interval_minutes": 0}
        )
        
        assert response.status_code == 400
        assert "at least 1 minute" in response.json()["detail"].lower()

    def test_agent_status_reflects_database_counts(self, client, setup_test_db, sample_forecast_in_db, sample_trade_in_db):
        """Test that agent status includes database counts."""
        response = client.get("/api/agent/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least the fixtures we created
        assert data["total_forecasts"] >= 1
        assert data["total_trades"] >= 1
