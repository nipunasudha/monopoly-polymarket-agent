"""
Integration tests for FastAPI endpoints.
"""
import pytest
import json
from fastapi.testclient import TestClient
from scripts.python.server import app, db


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup and teardown test database for each test."""
    # Drop and recreate tables for each test
    db.drop_tables()
    db.create_tables()
    yield
    # Cleanup
    db.drop_tables()


@pytest.fixture
def sample_forecast_in_db():
    """Add a sample forecast to the database."""
    forecast_data = {
        "market_id": "12345",
        "market_question": "Will Bitcoin reach $100k by end of 2026?",
        "outcome": "Yes",
        "probability": 0.35,
        "confidence": 0.70,
        "base_rate": 0.30,
        "reasoning": "Based on historical trends...",
    }
    return db.save_forecast(forecast_data)


@pytest.fixture
def sample_trade_in_db():
    """Add a sample trade to the database."""
    trade_data = {
        "market_id": "12345",
        "market_question": "Will Bitcoin reach $100k by end of 2026?",
        "outcome": "Yes",
        "side": "BUY",
        "size": 250.0,
        "price": 0.45,
        "forecast_probability": 0.60,
        "edge": 0.15,
        "status": "pending",
    }
    return db.save_trade(trade_data)


@pytest.fixture
def sample_portfolio_in_db():
    """Add a sample portfolio snapshot to the database."""
    portfolio_data = {
        "balance": 1000.0,
        "total_value": 1250.0,
        "open_positions": 3,
        "total_pnl": 250.0,
        "win_rate": 0.65,
        "total_trades": 10,
    }
    return db.save_portfolio_snapshot(portfolio_data)


@pytest.mark.integration
class TestRootEndpoints:
    """Test root and health check endpoints."""

    def test_read_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
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

    def test_get_forecasts_empty(self, client):
        """Test getting forecasts from empty database."""
        response = client.get("/api/forecasts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_forecasts_with_data(self, client, sample_forecast_in_db):
        """Test getting forecasts with data in database."""
        response = client.get("/api/forecasts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["market_id"] == "12345"
        assert data[0]["probability"] == 0.35

    def test_get_forecasts_with_limit(self, client):
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

    def test_get_forecast_not_found(self, client):
        """Test getting a non-existent forecast returns 404."""
        response = client.get("/api/forecasts/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_market_forecasts(self, client, sample_forecast_in_db):
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

    def test_get_market_forecasts_empty(self, client):
        """Test getting forecasts for market with no forecasts."""
        response = client.get("/api/markets/nonexistent/forecasts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


@pytest.mark.integration
class TestTradeEndpoints:
    """Test trade API endpoints."""

    def test_get_trades_empty(self, client):
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

    def test_get_trades_with_limit(self, client):
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

    def test_get_trade_not_found(self, client):
        """Test getting a non-existent trade returns 404."""
        response = client.get("/api/trades/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.integration
class TestPortfolioEndpoints:
    """Test portfolio API endpoints."""

    def test_get_portfolio_empty(self, client):
        """Test getting portfolio with no data returns 404."""
        response = client.get("/api/portfolio")
        
        assert response.status_code == 404
        data = response.json()
        assert "portfolio" in data["detail"].lower()
        assert "available" in data["detail"].lower()

    def test_get_portfolio_with_data(self, client, sample_portfolio_in_db):
        """Test getting current portfolio state."""
        response = client.get("/api/portfolio")
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 1000.0
        assert data["total_value"] == 1250.0
        assert data["total_pnl"] == 250.0
        assert data["win_rate"] == 0.65

    def test_get_portfolio_returns_latest(self, client):
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

    def test_get_portfolio_history_empty(self, client):
        """Test getting portfolio history from empty database."""
        response = client.get("/api/portfolio/history")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_portfolio_history_with_data(self, client):
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

    def test_get_portfolio_history_with_limit(self, client):
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
class TestAgentControlEndpoints:
    """Test agent control API endpoints."""

    def test_get_agent_status(self, client):
        """Test getting agent status."""
        response = client.get("/api/agent/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "total_forecasts" in data
        assert "total_trades" in data

    def test_get_agent_status_with_data(self, client, sample_forecast_in_db, sample_trade_in_db):
        """Test agent status includes counts."""
        response = client.get("/api/agent/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_forecasts"] >= 1
        assert data["total_trades"] >= 1

    def test_start_agent(self, client):
        """Test starting the agent."""
        response = client.post("/api/agent/start")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_stop_agent(self, client):
        """Test stopping the agent."""
        response = client.post("/api/agent/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_analyze_market(self, client):
        """Test triggering market analysis."""
        response = client.post("/api/markets/12345/analyze")
        
        assert response.status_code == 200
        data = response.json()
        assert data["market_id"] == "12345"
        assert "status" in data


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
