"""
Integration tests for Phase 7: TradingHub integration into AgentRunner
Tests that runner properly initializes and switches between architectures.
"""
import pytest
import os
from unittest.mock import patch, Mock, AsyncMock
from agents.application.runner import AgentRunner


@pytest.mark.integration
class TestRunnerIntegration:
    """Test AgentRunner integration with TradingHub."""
    
    def test_runner_legacy_architecture(self):
        """Test runner initialization with legacy architecture."""
        with patch.dict(os.environ, {'USE_NEW_ARCHITECTURE': 'false'}):
            runner = AgentRunner(interval_minutes=60)
            
            assert runner.use_new_architecture == False
            assert runner.hub is None
            assert runner.research_agent is None
            assert runner.trading_agent is None
            assert runner.trader is not None
    
    def test_runner_new_architecture(self):
        """Test runner initialization with new architecture."""
        with patch.dict(os.environ, {
            'USE_NEW_ARCHITECTURE': 'true',
            'ANTHROPIC_API_KEY': 'test_key'
        }):
            runner = AgentRunner(interval_minutes=60)
            
            assert runner.use_new_architecture == True
            assert runner.hub is not None
            assert runner.research_agent is not None
            assert runner.trading_agent is not None
            assert runner.trader is not None
    
    def test_runner_status_includes_architecture(self):
        """Test that status includes architecture info."""
        with patch.dict(os.environ, {'USE_NEW_ARCHITECTURE': 'false'}):
            runner = AgentRunner()
            status = runner.get_status()
            
            assert "architecture" in status
            assert status["architecture"] == "legacy"
    
    def test_runner_status_includes_hub_status(self):
        """Test that status includes hub status when using new architecture."""
        with patch.dict(os.environ, {
            'USE_NEW_ARCHITECTURE': 'true',
            'ANTHROPIC_API_KEY': 'test_key'
        }):
            runner = AgentRunner()
            status = runner.get_status()
            
            assert "architecture" in status
            assert status["architecture"] == "new"
            assert "hub_status" in status
            assert "running" in status["hub_status"]
            assert "sessions" in status["hub_status"]
    
    @pytest.mark.asyncio
    async def test_runner_start_legacy(self):
        """Test starting runner with legacy architecture."""
        with patch.dict(os.environ, {'USE_NEW_ARCHITECTURE': 'false'}):
            runner = AgentRunner(interval_minutes=60)
            
            # Mock the event broadcaster
            runner._status_changed_callback = None
            
            await runner.start()
            assert runner.state.value == "running"
            
            await runner.stop()
            assert runner.state.value == "stopped"
    
    @pytest.mark.asyncio
    async def test_runner_start_new_architecture(self):
        """Test starting runner with new architecture."""
        with patch.dict(os.environ, {
            'USE_NEW_ARCHITECTURE': 'true',
            'ANTHROPIC_API_KEY': 'test_key'
        }):
            runner = AgentRunner(interval_minutes=60)
            runner._status_changed_callback = None
            
            await runner.start()
            assert runner.state.value == "running"
            assert runner.hub._running == True  # Hub should be running
            
            await runner.stop()
            assert runner.state.value == "stopped"
            assert runner.hub._running == False  # Hub should be stopped


@pytest.mark.integration
class TestTraderV2:
    """Test new one_best_trade_v2 method."""
    
    @pytest.mark.asyncio
    async def test_one_best_trade_v2_requires_hub(self):
        """Test that one_best_trade_v2 requires hub and agents."""
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
            await trader.one_best_trade_v2(hub, research_agent, trading_agent)
    
    @pytest.mark.asyncio
    async def test_one_best_trade_v2_skips_on_no_events(self):
        """Test that v2 skips when no events found."""
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
            await trader.one_best_trade_v2(hub, research_agent, trading_agent)
    
    def test_trader_has_both_methods(self):
        """Test that Trader has both old and new methods."""
        from agents.application.trade import Trader
        import inspect
        
        trader = Trader()
        
        # Both methods should exist
        assert hasattr(trader, 'one_best_trade')
        assert hasattr(trader, 'one_best_trade_v2')
        
        # Old method is sync
        assert not inspect.iscoroutinefunction(trader.one_best_trade)
        
        # New method is async
        assert inspect.iscoroutinefunction(trader.one_best_trade_v2)


@pytest.mark.integration
class TestEnvironmentFlag:
    """Test USE_NEW_ARCHITECTURE environment flag."""
    
    def test_env_flag_defaults_to_false(self):
        """Test that flag defaults to false when not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
                runner = AgentRunner()
                assert runner.use_new_architecture == False
    
    def test_env_flag_true_values(self):
        """Test various truthy values for flag."""
        for value in ['true', 'True', 'TRUE', 'yes', 'YES', '1']:
            with patch.dict(os.environ, {
                'USE_NEW_ARCHITECTURE': value,
                'ANTHROPIC_API_KEY': 'test_key'
            }):
                runner = AgentRunner()
                # Only 'true' (case-insensitive) should work
                expected = value.lower() == 'true'
                assert runner.use_new_architecture == expected
    
    def test_env_flag_false_values(self):
        """Test various falsy values for flag."""
        for value in ['false', 'False', 'FALSE', 'no', 'NO', '0', '']:
            with patch.dict(os.environ, {'USE_NEW_ARCHITECTURE': value}):
                runner = AgentRunner()
                assert runner.use_new_architecture == False
