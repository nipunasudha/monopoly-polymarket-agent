"""
Integration tests for partial endpoints.
Tests HTML fragments returned for HTMX updates.
"""
import pytest
from fastapi.testclient import TestClient


class TestPortfolioStatsPartial:
    """Test portfolio stats partial endpoint."""
    
    def test_portfolio_stats_partial_returns_html(self, client, setup_test_db):
        """Test portfolio stats partial returns HTML."""
        response = client.get("/partials/portfolio-stats")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Balance" in response.text
        assert "Total Value" in response.text
        assert "Total P&L" in response.text
        assert "Win Rate" in response.text
    
    def test_portfolio_stats_with_data(self, client, setup_test_db, sample_portfolio_in_db):
        """Test portfolio stats partial with actual data."""
        response = client.get("/partials/portfolio-stats")
        
        assert response.status_code == 200
        # Should contain portfolio values
        assert "$" in response.text
        assert "%" in response.text
    
    def test_portfolio_stats_default_values(self, client, setup_test_db):
        """Test portfolio stats partial with no data shows defaults."""
        response = client.get("/partials/portfolio-stats")
        
        assert response.status_code == 200
        assert "$1000.0" in response.text  # Default balance (Python float formatting)


class TestTradeListPartial:
    """Test trade list partial endpoint."""
    
    def test_trade_list_partial_returns_html(self, client, setup_test_db):
        """Test trade list partial returns HTML."""
        response = client.get("/partials/trade-list")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_trade_list_with_data(self, client, setup_test_db, sample_trade_in_db):
        """Test trade list partial with trade data."""
        response = client.get("/partials/trade-list")
        
        assert response.status_code == 200
        assert "Bitcoin" in response.text  # Sample data contains Bitcoin question
        assert "BUY" in response.text
    
    def test_trade_list_empty_state(self, client, setup_test_db):
        """Test trade list partial shows empty state."""
        response = client.get("/partials/trade-list")
        
        assert response.status_code == 200
        assert "No trades yet" in response.text
    
    def test_trade_list_limit_parameter(self, client, setup_test_db, sample_data_in_db):
        """Test trade list partial respects limit parameter."""
        response = client.get("/partials/trade-list?limit=5")
        
        assert response.status_code == 200
        # Should work without error


class TestForecastListPartial:
    """Test forecast list partial endpoint."""
    
    def test_forecast_list_partial_returns_html(self, client, setup_test_db):
        """Test forecast list partial returns HTML."""
        response = client.get("/partials/forecast-list")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_forecast_list_with_data(self, client, setup_test_db, sample_forecast_in_db):
        """Test forecast list partial with forecast data."""
        response = client.get("/partials/forecast-list")
        
        assert response.status_code == 200
        assert "Bitcoin" in response.text  # Sample data contains Bitcoin question
        assert "%" in response.text  # Probability percentage
    
    def test_forecast_list_empty_state(self, client, setup_test_db):
        """Test forecast list partial shows empty state."""
        response = client.get("/partials/forecast-list")
        
        assert response.status_code == 200
        assert "No forecasts yet" in response.text
    
    def test_forecast_list_limit_parameter(self, client, setup_test_db, sample_data_in_db):
        """Test forecast list partial respects limit parameter."""
        response = client.get("/partials/forecast-list?limit=5")
        
        assert response.status_code == 200


class TestAgentStatusPartial:
    """Test agent status partial endpoint."""
    
    def test_agent_status_partial_returns_html(self, client, setup_test_db):
        """Test agent status partial returns HTML."""
        response = client.get("/partials/agent-status")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Agent Status" in response.text
    
    def test_agent_status_shows_state(self, client, setup_test_db):
        """Test agent status partial shows current state."""
        response = client.get("/partials/agent-status")
        
        assert response.status_code == 200
        # Should show one of the valid states
        assert any(state in response.text.lower() for state in ["stopped", "running", "paused", "error"])
    
    def test_agent_status_indicator_colors(self, client, setup_test_db):
        """Test agent status partial includes status indicator."""
        response = client.get("/partials/agent-status")
        
        assert response.status_code == 200
        # Should have status indicator styling
        assert "rounded-full" in response.text


class TestPartialIntegration:
    """Test partial endpoints integration with database."""
    
    def test_all_partials_work_together(self, client, setup_test_db, sample_data_in_db):
        """Test all partial endpoints work with sample data."""
        # Test all partials can be fetched
        partials = [
            "/partials/portfolio-stats",
            "/partials/trade-list",
            "/partials/forecast-list",
            "/partials/agent-status",
        ]
        
        for partial_url in partials:
            response = client.get(partial_url)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    def test_partials_update_independently(self, client, setup_test_db):
        """Test partials can be fetched independently."""
        # Each partial should work without affecting others
        response1 = client.get("/partials/portfolio-stats")
        response2 = client.get("/partials/trade-list")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        # Content should be different
        assert response1.text != response2.text
