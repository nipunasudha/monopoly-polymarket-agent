"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import pytest
import json
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from scripts.python.server import app, db
from agents.application.runner import get_agent_runner, AgentState

# Disable web3 plugin autoloading to avoid import errors
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"


@pytest.fixture
def sample_market() -> Dict[str, Any]:
    """Sample market data for testing."""
    return {
        "id": 12345,
        "question": "Will Bitcoin reach $100k by end of 2026?",
        "description": "This market resolves to Yes if Bitcoin (BTC) reaches or exceeds $100,000 USD on any major exchange by December 31, 2026, 11:59 PM UTC.",
        "outcomes": ["Yes", "No"],
        "outcome_prices": [0.45, 0.55],
        "liquidity": 50000.0,
        "volume": 125000.0,
        "active": True,
        "closed": False,
        "endDate": "2026-12-31T23:59:59Z",
    }


@pytest.fixture
def sample_event() -> Dict[str, Any]:
    """Sample event data for testing."""
    return {
        "id": "67890",  # String ID as per model
        "title": "Cryptocurrency Markets 2026",
        "description": "Markets related to cryptocurrency price predictions for 2026",
        "markets": "12345,12346,12347",  # String format for SimpleEvent
        "active": True,
        "closed": False,
        "featured": True,
    }


@pytest.fixture
def sample_forecast() -> Dict[str, Any]:
    """Sample forecast result for testing."""
    return {
        "probability": 0.35,
        "confidence": 0.70,
        "base_rate": 0.30,
        "key_factors": [
            "Historical Bitcoin price volatility",
            "Current adoption trends",
            "Regulatory environment",
        ],
        "evidence_for": [
            "Increasing institutional adoption",
            "Bitcoin ETF approvals",
        ],
        "evidence_against": [
            "Regulatory uncertainty",
            "Market volatility",
        ],
        "reasoning": "Based on historical trends and current market conditions, there is a moderate probability of Bitcoin reaching $100k by end of 2026.",
    }


@pytest.fixture
def sample_trade_response() -> str:
    """Sample trade response from LLM."""
    return """
ANALYSIS:
Based on the market analysis, the current price of 0.45 for Yes appears undervalued.
My forecast suggests a probability of 0.60 for Yes.

RECOMMENDATION:
outcome: Yes
size: 0.25
edge: 0.15
confidence: high

REASONING:
The market is underpricing the likelihood based on current trends.
"""


@pytest.fixture
def mock_llm_response():
    """Factory fixture for creating mock LLM responses."""
    
    def _create_response(content: str):
        """Create a mock LLM response object."""
        
        class MockResponse:
            def __init__(self, content: str):
                self.content = content
        
        return MockResponse(content)
    
    return _create_response


@pytest.fixture
def sample_markets_list(sample_market) -> list:
    """List of sample markets for testing."""
    markets = []
    for i in range(3):
        market = sample_market.copy()
        market["id"] = 12345 + i
        market["question"] = f"Test market question {i + 1}"
        markets.append(market)
    return markets


@pytest.fixture
def mock_usdc_balance() -> float:
    """Mock USDC balance for testing."""
    return 1000.0


# ============================================================================
# Shared Fixtures for Integration Tests
# ============================================================================

@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_trader():
    """Mock Trader class to avoid LLM costs."""
    with patch("agents.application.runner.Trader") as mock:
        trader_instance = Mock()
        # Mock the async one_best_trade method
        trader_instance.one_best_trade = AsyncMock()
        mock.return_value = trader_instance
        yield trader_instance


@pytest.fixture(autouse=False)
def setup_test_db():
    """Setup and teardown test database for each test.
    
    Note: autouse=False - only use when explicitly needed.
    For tests that need database, add this fixture to their parameters.
    """
    # Drop and recreate tables for each test
    db.drop_tables()
    db.create_tables()
    
    yield
    
    # Cleanup: ensure agent is stopped after each test
    runner = get_agent_runner()
    if runner.state.value == "running":
        # Force stop synchronously
        runner.state = AgentState.STOPPED
        if runner.task:
            runner.task.cancel()
    
    # Reset runner state
    runner.run_count = 0
    runner.error_count = 0
    runner.last_error = None
    runner.last_run = None
    runner.next_run = None
    runner.task = None
    
    # Cleanup database
    db.drop_tables()


# ============================================================================
# Sample Data Fixtures (Dictionary format)
# ============================================================================

@pytest.fixture
def sample_forecast_data():
    """Sample forecast data dictionary for testing."""
    return {
        "market_id": "12345",
        "market_question": "Will Bitcoin reach $100k by end of 2026?",
        "outcome": "Yes",
        "probability": 0.35,
        "confidence": 0.70,
        "base_rate": 0.30,
        "reasoning": "Based on historical trends and current market conditions...",
        "evidence_for": json.dumps(["Institutional adoption", "ETF approvals"]),
        "evidence_against": json.dumps(["Regulatory uncertainty", "Market volatility"]),
        "key_factors": json.dumps(["Bitcoin price history", "Adoption trends"]),
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data dictionary for testing."""
    return {
        "market_id": "12345",
        "market_question": "Will Bitcoin reach $100k by end of 2026?",
        "outcome": "Yes",
        "side": "BUY",
        "size": 250.0,
        "price": 0.45,
        "forecast_probability": 0.60,
        "edge": 0.15,
        "status": "pending",
        "execution_enabled": False,
    }


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data dictionary for testing."""
    return {
        "balance": 1000.0,
        "total_value": 1250.0,
        "open_positions": 3,
        "total_pnl": 250.0,
        "win_rate": 0.65,
        "total_trades": 10,
        "extra_data": json.dumps({"last_updated": "2026-02-07"}),
    }


# ============================================================================
# Sample Data Fixtures (Saved to Database)
# ============================================================================

@pytest.fixture
def sample_forecast_in_db(setup_test_db, sample_forecast_data):
    """Add a sample forecast to the database."""
    # Use simplified version for API/dashboard tests
    forecast_data = {
        "market_id": sample_forecast_data["market_id"],
        "market_question": sample_forecast_data["market_question"],
        "outcome": sample_forecast_data["outcome"],
        "probability": sample_forecast_data["probability"],
        "confidence": sample_forecast_data["confidence"],
        "base_rate": sample_forecast_data["base_rate"],
        "reasoning": sample_forecast_data["reasoning"],
    }
    return db.save_forecast(forecast_data)


@pytest.fixture
def sample_trade_in_db(setup_test_db, sample_trade_data):
    """Add a sample trade to the database."""
    return db.save_trade(sample_trade_data)


@pytest.fixture
def sample_portfolio_in_db(setup_test_db, sample_portfolio_data):
    """Add a sample portfolio snapshot to the database."""
    # Use simplified version for API/dashboard tests
    portfolio_data = {
        "balance": sample_portfolio_data["balance"],
        "total_value": sample_portfolio_data["total_value"],
        "open_positions": sample_portfolio_data["open_positions"],
        "total_pnl": sample_portfolio_data["total_pnl"],
        "win_rate": sample_portfolio_data["win_rate"],
        "total_trades": sample_portfolio_data["total_trades"],
    }
    return db.save_portfolio_snapshot(portfolio_data)


@pytest.fixture
def sample_data_in_db(setup_test_db, sample_forecast_in_db, sample_trade_in_db, sample_portfolio_in_db):
    """Add sample forecast, trade, and portfolio to database for testing."""
    return {
        "forecast": sample_forecast_in_db,
        "trade": sample_trade_in_db,
        "portfolio": sample_portfolio_in_db,
    }


# Pytest markers for test organization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (moderate speed)"
    )
    config.addinivalue_line("markers", "e2e: End-to-end tests (slow)")
    config.addinivalue_line("markers", "slow: Slow tests that can be skipped")
