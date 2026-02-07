"""
Integration tests for Phase 7+: TradingHub integration into AgentRunner
Tests that runner properly initializes with OpenClaw architecture.
"""
import pytest
import os
from unittest.mock import patch, Mock, AsyncMock
from agents.application.runner import AgentRunner


@pytest.mark.integration
class TestRunnerIntegration:
    """Test AgentRunner integration with TradingHub."""
    
    def test_runner_initialization(self):
        """Test runner initialization with OpenClaw architecture."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            runner = AgentRunner(interval_minutes=60)
            
            assert runner.hub is not None
            assert runner.research_agent is not None
            assert runner.trading_agent is not None
            assert runner.trader is not None
    
    def test_runner_status_includes_hub_status(self, setup_test_db):
        """Test that status includes hub status."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            runner = AgentRunner()
            
            # Mock database calls to avoid table issues
            from unittest.mock import Mock
            runner.db.get_recent_forecasts = Mock(return_value=[])
            runner.db.get_recent_trades = Mock(return_value=[])
            
            status = runner.get_status()
            
            assert "hub_status" in status
            assert "running" in status["hub_status"]
            assert "sessions" in status["hub_status"]
    
    @pytest.mark.asyncio
    async def test_runner_start_and_stop(self):
        """Test starting and stopping runner."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            runner = AgentRunner(interval_minutes=60)
            runner._status_changed_callback = None
            
            await runner.start()
            assert runner.state.value == "running"
            assert runner.hub._running == True  # Hub should be running
            
            await runner.stop()
            assert runner.state.value == "stopped"
            assert runner.hub._running == False  # Hub should be stopped


@pytest.mark.integration
class TestTrader:
    """Test one_best_trade method."""
    
    @pytest.mark.asyncio
    async def test_one_best_trade_requires_hub(self):
        """Test that one_best_trade requires hub and agents."""
        from agents.application.trade import Trader
        from agents.core.hub import TradingHub
        from agents.core.agents import ResearchAgent, TradingAgent
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            trader = Trader()
            hub = TradingHub()
            research_agent = ResearchAgent(hub)
            trading_agent = TradingAgent(hub)
            
            # Mock Polymarket to return no events
            trader.polymarket.get_all_tradeable_events = Mock(return_value=[])
            
            # Should not crash
            await trader.one_best_trade(hub, research_agent, trading_agent)
    
    @pytest.mark.asyncio
    async def test_one_best_trade_skips_on_no_events(self):
        """Test that one_best_trade skips when no events found."""
        from agents.application.trade import Trader
        from agents.core.hub import TradingHub
        from agents.core.agents import ResearchAgent, TradingAgent
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            trader = Trader()
            hub = TradingHub()
            research_agent = ResearchAgent(hub)
            trading_agent = TradingAgent(hub)
            
            trader.polymarket.get_all_tradeable_events = Mock(return_value=[])
            
            # Should complete without errors
            await trader.one_best_trade(hub, research_agent, trading_agent)
    
    def test_trader_has_one_best_trade_method(self):
        """Test that Trader has one_best_trade method."""
        from agents.application.trade import Trader
        import inspect
        
        trader = Trader()
        
        # Method should exist and be async
        assert hasattr(trader, 'one_best_trade')
        assert inspect.iscoroutinefunction(trader.one_best_trade)

