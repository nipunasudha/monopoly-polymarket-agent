"""
Integration test for Trader class to ensure forecasts and trades are saved.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import text
from agents.application.trade import Trader
from agents.connectors.database import Database


class TestTraderPersistence:
    """Test that Trader saves forecasts and trades to database."""
    
    @pytest.fixture
    def db(self):
        """Get database instance."""
        return Database()
    
    @pytest.fixture(autouse=True)
    def setup_db(self, db):
        """Setup database tables for each test."""
        # Ensure tables exist
        db.create_tables()
        yield
        # Cleanup
        db.drop_tables()
    
    @pytest.fixture
    def mock_trader_dependencies(self):
        """Mock external dependencies to avoid real API calls."""
        import os
        # Ensure dry_run mode for tests
        original_mode = os.environ.get("TRADING_MODE")
        if "TRADING_MODE" in os.environ:
            del os.environ["TRADING_MODE"]
        
        with patch('agents.application.trade.Polymarket') as mock_poly, \
             patch('agents.application.trade.Agent') as mock_agent, \
             patch('agents.application.trade.Gamma'):
            
            # Mock Polymarket to return sample events
            mock_poly_instance = mock_poly.return_value
            mock_poly_instance.get_all_tradeable_events.return_value = [
                MagicMock(id=1, question="Test event?")
            ]
            mock_poly_instance.get_usdc_balance.return_value = 1.0
            
            # Mock Agent to return sample data
            mock_agent_instance = mock_agent.return_value
            mock_agent_instance.filter_events_with_rag.return_value = [MagicMock()]
            
            # Mock market tuple structure (document, score)
            mock_doc = MagicMock()
            mock_doc.dict.return_value = {
                "metadata": {
                    "id": 12345,
                    "question": "Will Bitcoin reach $100k by end of 2026?",
                    "outcomes": "['Yes', 'No']",
                    "outcome_prices": "[0.45, 0.55]",
                    "clob_token_ids": '["token1", "token2"]',
                },
                "page_content": "Bitcoin price prediction market"
            }
            mock_agent_instance.map_filtered_events_to_markets.return_value = [MagicMock()]
            mock_agent_instance.filter_markets.return_value = [(mock_doc, 0.95)]
            
            # Mock LLM response as string (what source_best_trade returns)
            mock_agent_instance.source_best_trade.return_value = """
ANALYSIS:
The market is underpriced based on fundamental analysis.

RESPONSE:
outcome: YES
probability: 0.72
confidence: 0.85
reasoning: Strong fundamentals suggest Bitcoin will reach $100k
size: 0.15
side: BUY
"""
            
            mock_agent_instance.format_trade_prompt_for_execution.return_value = 0.15
            
            try:
                yield mock_poly, mock_agent
            finally:
                # Restore original TRADING_MODE
                if original_mode:
                    os.environ["TRADING_MODE"] = original_mode
    
    def test_trader_saves_forecast(self, db, setup_db, mock_trader_dependencies):
        """Test that Trader saves forecast to database."""
        # Clear database
        with db.get_session() as session:
            session.execute(text("DELETE FROM forecasts"))
            session.execute(text("DELETE FROM trades"))
            session.commit()
        
        # Run trader
        trader = Trader()
        trader.one_best_trade()
        
        # Verify forecast was saved
        forecasts = db.get_recent_forecasts(limit=10)
        assert len(forecasts) > 0, "Forecast should be saved to database"
        
        forecast = forecasts[0]
        assert forecast.market_id == "12345"
        assert forecast.market_question == "Will Bitcoin reach $100k by end of 2026?"
        assert forecast.outcome == "YES"
        assert forecast.probability == 0.72
        assert forecast.confidence == 0.85
        assert "Bitcoin" in forecast.reasoning or "fundamentals" in forecast.reasoning.lower()
    
    def test_trader_saves_trade(self, db, setup_db, mock_trader_dependencies):
        """Test that Trader saves trade to database."""
        # Clear database
        with db.get_session() as session:
            session.execute(text("DELETE FROM forecasts"))
            session.execute(text("DELETE FROM trades"))
            session.commit()
        
        # Run trader
        trader = Trader()
        trader.one_best_trade()
        
        # Verify trade was saved
        trades = db.get_recent_trades(limit=10)
        assert len(trades) > 0, "Trade should be saved to database"
        
        trade = trades[0]
        assert trade.market_id == "12345"
        assert trade.market_question == "Will Bitcoin reach $100k by end of 2026?"
        assert trade.outcome == "YES"
        assert trade.side == "BUY"
        assert trade.size == 0.15
        assert trade.status == "simulated"  # dry_run mode
    
    def test_trader_creates_both_forecast_and_trade(self, db, setup_db, mock_trader_dependencies):
        """Test that Trader creates both forecast and trade in one run."""
        # Clear database
        with db.get_session() as session:
            session.execute(text("DELETE FROM forecasts"))
            session.execute(text("DELETE FROM trades"))
            session.commit()
        
        # Run trader
        trader = Trader()
        trader.one_best_trade()
        
        # Verify both were created
        forecasts = db.get_recent_forecasts(limit=10)
        trades = db.get_recent_trades(limit=10)
        
        assert len(forecasts) == 1, "Should create exactly 1 forecast"
        assert len(trades) == 1, "Should create exactly 1 trade"
        
        # Verify they're for the same market
        assert forecasts[0].market_id == trades[0].market_id
