"""
Unit tests for UI components.
Tests individual component rendering in isolation.
"""
import pytest
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment for component testing."""
    template_dir = Path(__file__).parent.parent.parent / "dashboard"
    env = Environment(loader=FileSystemLoader([
        str(template_dir / "components"),
        str(template_dir / "templates"),
    ]))
    return env


class TestStatCard:
    """Test stat_card component."""
    
    def test_stat_card_renders_with_data(self, jinja_env):
        """Test stat card renders correctly with data."""
        template = jinja_env.get_template("stat_card.html")
        html = template.render(
            title="Balance",
            value="$1,000.00",
            icon_path="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2",
        )
        
        assert "Balance" in html
        assert "$1,000.00" in html
        assert "bg-white" in html
        assert "shadow" in html
    
    def test_stat_card_handles_missing_color_class(self, jinja_env):
        """Test stat card uses default color when not provided."""
        template = jinja_env.get_template("stat_card.html")
        html = template.render(
            title="Test",
            value="100",
            icon_path="M12 8",
        )
        
        assert "text-gray-400" in html  # Default color
    
    def test_stat_card_with_custom_color(self, jinja_env):
        """Test stat card accepts custom color class."""
        template = jinja_env.get_template("stat_card.html")
        html = template.render(
            title="Test",
            value="100",
            icon_path="M12 8",
            color_class="text-green-400",
        )
        
        assert "text-green-400" in html
    
    def test_stat_card_with_custom_value_class(self, jinja_env):
        """Test stat card accepts custom value class."""
        template = jinja_env.get_template("stat_card.html")
        html = template.render(
            title="P&L",
            value="+$500",
            icon_path="M12 8",
            value_class="text-green-600",
        )
        
        assert "text-green-600" in html
        assert "+$500" in html


class TestStatusBadge:
    """Test status_badge component."""
    
    def test_status_badge_executed(self, jinja_env):
        """Test status badge for executed status."""
        template = jinja_env.get_template("status_badge.html")
        html = template.render(status="executed")
        
        assert "executed" in html
        assert "bg-green-100" in html
        assert "text-green-800" in html
    
    def test_status_badge_pending(self, jinja_env):
        """Test status badge for pending status."""
        template = jinja_env.get_template("status_badge.html")
        html = template.render(status="pending")
        
        assert "pending" in html
        assert "bg-yellow-100" in html
        assert "text-yellow-800" in html
    
    def test_status_badge_failed(self, jinja_env):
        """Test status badge for failed status."""
        template = jinja_env.get_template("status_badge.html")
        html = template.render(status="failed")
        
        assert "failed" in html
        assert "bg-red-100" in html
        assert "text-red-800" in html
    
    def test_status_badge_running(self, jinja_env):
        """Test status badge for running status."""
        template = jinja_env.get_template("status_badge.html")
        html = template.render(status="running")
        
        assert "running" in html
        assert "bg-green-100" in html
    
    def test_status_badge_stopped(self, jinja_env):
        """Test status badge for stopped status."""
        template = jinja_env.get_template("status_badge.html")
        html = template.render(status="stopped")
        
        assert "stopped" in html
        assert "bg-gray-100" in html


class TestTradeRow:
    """Test trade_row component."""
    
    def test_trade_row_renders_complete_data(self, jinja_env):
        """Test trade row renders all trade data."""
        template = jinja_env.get_template("trade_row.html")
        trade = {
            "market_question": "Will it rain tomorrow?",
            "market_id": "test-123",
            "outcome": "YES",
            "side": "BUY",
            "size": 100.0,
            "price": 0.65,
            "status": "executed",
            "created_at": "2024-01-01",
        }
        html = template.render(trade=trade)
        
        assert "Will it rain tomorrow?" in html
        assert "test-123" in html
        assert "YES" in html
        assert "BUY" in html
        assert "100.0" in html
        assert "0.65" in html
    
    def test_trade_row_handles_missing_price(self, jinja_env):
        """Test trade row handles None price."""
        template = jinja_env.get_template("trade_row.html")
        trade = {
            "market_question": "Test",
            "market_id": "123",
            "outcome": "YES",
            "side": "BUY",
            "size": 50.0,
            "price": None,
            "status": "pending",
            "created_at": "2024-01-01",
        }
        html = template.render(trade=trade)
        
        assert "-" in html  # Placeholder for missing price


class TestForecastCard:
    """Test forecast_card component."""
    
    def test_forecast_card_renders_data(self, jinja_env):
        """Test forecast card renders forecast data."""
        template = jinja_env.get_template("forecast_card.html")
        forecast = {
            "market_question": "Will it snow?",
            "market_id": "snow-123",
            "outcome": "YES",
            "probability": 0.75,
            "confidence": 0.85,
            "reasoning": "Historical data suggests high probability",
            "created_at": "2024-01-01",
        }
        html = template.render(forecast=forecast)
        
        assert "Will it snow?" in html
        assert "snow-123" in html
        assert "YES" in html
        assert "75.0%" in html  # Probability as percentage
        assert "85.0%" in html  # Confidence as percentage (with decimal)
        assert "Historical data" in html
    
    def test_forecast_card_without_reasoning(self, jinja_env):
        """Test forecast card when reasoning is missing."""
        template = jinja_env.get_template("forecast_card.html")
        forecast = {
            "market_question": "Test",
            "market_id": "123",
            "outcome": "NO",
            "probability": 0.3,
            "confidence": 0.6,
            "reasoning": None,
            "created_at": "2024-01-01",
        }
        html = template.render(forecast=forecast)
        
        assert "Test" in html
        assert "30.0%" in html
        # Should not have reasoning section
        assert "Reasoning" not in html


class TestChart:
    """Test chart component."""
    
    def test_chart_renders_with_id(self, jinja_env):
        """Test chart component renders with canvas ID."""
        template = jinja_env.get_template("chart.html")
        html = template.render(
            chart_id="equityChart",
            title="Portfolio Value Over Time"
        )
        
        assert 'id="equityChart"' in html
        assert "Portfolio Value Over Time" in html
        assert "<canvas" in html
    
    def test_chart_with_different_title(self, jinja_env):
        """Test chart component with custom title."""
        template = jinja_env.get_template("chart.html")
        html = template.render(
            chart_id="testChart",
            title="Test Chart Title"
        )
        
        assert "Test Chart Title" in html
        assert 'id="testChart"' in html
