"""
Integration tests for dashboard UI pages.
"""
import pytest
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
def sample_data_in_db():
    """Add sample data to database for testing."""
    # Add forecast
    forecast = db.save_forecast({
        "market_id": "12345",
        "market_question": "Will Bitcoin reach $100k by end of 2026?",
        "outcome": "Yes",
        "probability": 0.35,
        "confidence": 0.70,
        "reasoning": "Based on historical trends and current market conditions.",
    })
    
    # Add trade
    trade = db.save_trade({
        "market_id": "12345",
        "market_question": "Will Bitcoin reach $100k by end of 2026?",
        "outcome": "Yes",
        "side": "BUY",
        "size": 250.0,
        "price": 0.45,
        "forecast_probability": 0.60,
        "status": "executed",
    })
    
    # Add portfolio snapshot
    portfolio = db.save_portfolio_snapshot({
        "balance": 1000.0,
        "total_value": 1250.0,
        "open_positions": 3,
        "total_pnl": 250.0,
        "win_rate": 0.65,
        "total_trades": 10,
    })
    
    return {"forecast": forecast, "trade": trade, "portfolio": portfolio}


@pytest.mark.integration
class TestDashboardPages:
    """Test dashboard HTML pages."""

    def test_portfolio_page_loads(self, client):
        """Test portfolio dashboard page loads."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Portfolio Overview" in response.content

    def test_portfolio_page_with_data(self, client, sample_data_in_db):
        """Test portfolio page displays data."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert b"$1000" in response.content or b"1000.0" in response.content
        assert b"$250" in response.content or b"250.0" in response.content

    def test_markets_page_loads(self, client):
        """Test markets scanner page loads."""
        response = client.get("/markets")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Market Scanner" in response.content

    def test_trades_page_loads(self, client):
        """Test trades history page loads."""
        response = client.get("/trades")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Trade History" in response.content

    def test_trades_page_with_data(self, client, sample_data_in_db):
        """Test trades page displays trade data."""
        response = client.get("/trades")
        
        assert response.status_code == 200
        assert b"Bitcoin" in response.content
        assert b"BUY" in response.content
        assert b"executed" in response.content

    def test_forecasts_page_loads(self, client):
        """Test forecasts page loads."""
        response = client.get("/forecasts")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Forecasts" in response.content

    def test_forecasts_page_with_data(self, client, sample_data_in_db):
        """Test forecasts page displays forecast data."""
        response = client.get("/forecasts")
        
        assert response.status_code == 200
        assert b"Bitcoin" in response.content
        assert b"35" in response.content  # 35% probability


@pytest.mark.integration
class TestDashboardNavigation:
    """Test dashboard navigation."""

    def test_navigation_links_present(self, client):
        """Test that navigation links are present on all pages."""
        pages = ["/", "/markets", "/trades", "/forecasts"]
        
        for page in pages:
            response = client.get(page)
            assert response.status_code == 200
            # Check for navigation elements
            assert b"Portfolio" in response.content
            assert b"Markets" in response.content
            assert b"Trades" in response.content
            assert b"Forecasts" in response.content

    def test_page_titles(self, client):
        """Test that pages have correct titles."""
        test_cases = [
            ("/", b"Portfolio Overview"),
            ("/markets", b"Market Scanner"),
            ("/trades", b"Trade History"),
            ("/forecasts", b"Forecasts"),
        ]
        
        for url, expected_title in test_cases:
            response = client.get(url)
            assert response.status_code == 200
            assert expected_title in response.content


@pytest.mark.integration
class TestDashboardEmptyStates:
    """Test dashboard empty states."""

    def test_portfolio_empty_state(self, client):
        """Test portfolio page with no data."""
        response = client.get("/")
        
        assert response.status_code == 200
        # Should show zeros or empty state
        assert b"$0" in response.content or b"0.0" in response.content

    def test_trades_empty_state(self, client):
        """Test trades page with no data."""
        response = client.get("/trades")
        
        assert response.status_code == 200
        assert b"No trades yet" in response.content

    def test_forecasts_empty_state(self, client):
        """Test forecasts page with no data."""
        response = client.get("/forecasts")
        
        assert response.status_code == 200
        assert b"No forecasts yet" in response.content


@pytest.mark.integration
class TestDashboardAssets:
    """Test dashboard assets and dependencies."""

    def test_tailwind_css_loaded(self, client):
        """Test that Tailwind CSS is loaded."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert b"tailwindcss.com" in response.content

    def test_htmx_loaded(self, client):
        """Test that HTMX is loaded."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert b"htmx.org" in response.content

    def test_chartjs_loaded(self, client):
        """Test that Chart.js is loaded."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert b"chart.js" in response.content


@pytest.mark.integration
class TestDashboardDataRendering:
    """Test dashboard data rendering."""

    def test_portfolio_stats_displayed(self, client, sample_data_in_db):
        """Test that portfolio stats are displayed correctly."""
        response = client.get("/")
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Check for balance
        assert "1000" in content
        # Check for total value
        assert "1250" in content
        # Check for PnL
        assert "250" in content

    def test_trade_table_rendered(self, client, sample_data_in_db):
        """Test that trade table is rendered with data."""
        response = client.get("/trades")
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Check for table headers
        assert "Market" in content
        assert "Side" in content
        assert "Status" in content
        
        # Check for trade data
        assert "Bitcoin" in content
        assert "BUY" in content

    def test_forecast_cards_rendered(self, client, sample_data_in_db):
        """Test that forecast cards are rendered."""
        response = client.get("/forecasts")
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Check for forecast data
        assert "Bitcoin" in content
        assert "35" in content  # Probability percentage


@pytest.mark.integration
class TestDashboardResponsiveness:
    """Test dashboard responsive design."""

    def test_mobile_navigation_classes(self, client):
        """Test that mobile-responsive classes are present."""
        response = client.get("/")
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Check for responsive classes
        assert "sm:" in content  # Small screens
        assert "lg:" in content  # Large screens

    def test_grid_responsive_classes(self, client):
        """Test that grid layouts have responsive classes."""
        response = client.get("/")
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Check for grid responsive classes
        assert "grid-cols-1" in content
        assert "sm:grid-cols-2" in content or "lg:grid-cols-4" in content


@pytest.mark.integration
class TestDashboardCharts:
    """Test dashboard chart rendering."""

    def test_equity_chart_present(self, client, sample_data_in_db):
        """Test that equity chart canvas is present."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert b"equityChart" in response.content

    def test_chart_data_injection(self, client, sample_data_in_db):
        """Test that chart data is injected into page."""
        response = client.get("/")
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Check for Chart.js initialization
        assert "new Chart" in content
        assert "total_value" in content
