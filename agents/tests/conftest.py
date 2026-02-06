"""
Pytest configuration and shared fixtures for the test suite.
"""
import pytest
import json
from typing import Dict, Any


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


# Pytest markers for test organization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (moderate speed)"
    )
    config.addinivalue_line("markers", "e2e: End-to-end tests (slow)")
    config.addinivalue_line("markers", "slow: Slow tests that can be skipped")
