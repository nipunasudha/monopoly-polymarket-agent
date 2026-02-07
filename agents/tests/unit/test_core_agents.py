"""
Unit tests for Phase 3: ResearchAgent and TradingAgent
Tests agent initialization, task creation, and integration with TradingHub.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from agents.core.hub import TradingHub
from agents.core.agents import ResearchAgent, TradingAgent
from agents.core.session import Lane


@pytest.mark.unit
@pytest.mark.asyncio
class TestResearchAgent:
    """Test ResearchAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_research_agent_initialization(self):
        """Test ResearchAgent initialization."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = ResearchAgent(hub)
            
            assert agent.hub == hub
            assert len(agent.system_prompt) > 0
            assert "research" in agent.system_prompt.lower()
    
    @pytest.mark.asyncio
    async def test_research_market_creates_task(self):
        """Test that research_market creates a task."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = ResearchAgent(hub)
            
            task_id = await agent.research_market(
                market_question="Will X happen?",
                market_description="Test market"
            )
            
            assert task_id is not None
            assert isinstance(task_id, str)
            assert task_id.startswith("research_")
            
            # Check task was enqueued
            status = hub.get_status()
            assert status['lane_status']['research']['queued'] == 1
    
    @pytest.mark.asyncio
    async def test_research_market_uses_correct_lane(self):
        """Test that research tasks use RESEARCH lane."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = ResearchAgent(hub)
            
            await agent.research_market("Test question")
            
            # Check task is in RESEARCH lane
            assert len(hub.lanes[Lane.RESEARCH]) == 1
            task = hub.lanes[Lane.RESEARCH][0]
            assert task.lane == Lane.RESEARCH
    
    @pytest.mark.asyncio
    async def test_research_market_includes_tools(self):
        """Test that research tasks include correct tools."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = ResearchAgent(hub)
            
            await agent.research_market("Test question")
            
            task = hub.lanes[Lane.RESEARCH][0]
            assert "exa_research" in task.tools or "tavily_search" in task.tools
            assert "store_insight" in task.tools
    
    @pytest.mark.asyncio
    async def test_quick_search(self):
        """Test quick_search method."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = ResearchAgent(hub)
            
            task_id = await agent.quick_search("test query")
            
            assert task_id is not None
            task = hub.lanes[Lane.RESEARCH][0]
            assert "tavily_search" in task.tools


@pytest.mark.unit
@pytest.mark.asyncio
class TestTradingAgent:
    """Test TradingAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_trading_agent_initialization(self):
        """Test TradingAgent initialization."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = TradingAgent(hub)
            
            assert agent.hub == hub
            assert len(agent.system_prompt) > 0
            assert "trading" in agent.system_prompt.lower() or "quantitative" in agent.system_prompt.lower()
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_creates_task(self):
        """Test that evaluate_trade creates a task."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = TradingAgent(hub)
            
            task_id = await agent.evaluate_trade(
                market_id="market_123",
                research={"response": "Test research"}
            )
            
            assert task_id is not None
            assert task_id.startswith("trade_")
            
            # Check task was enqueued
            status = hub.get_status()
            assert status['lane_status']['main']['queued'] == 1
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_uses_main_lane(self):
        """Test that trading tasks use MAIN lane."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = TradingAgent(hub)
            
            await agent.evaluate_trade("market_123")
            
            # Check task is in MAIN lane
            assert len(hub.lanes[Lane.MAIN]) == 1
            task = hub.lanes[Lane.MAIN][0]
            assert task.lane == Lane.MAIN
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_includes_tools(self):
        """Test that trading tasks include correct tools."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = TradingAgent(hub)
            
            await agent.evaluate_trade("market_123")
            
            task = hub.lanes[Lane.MAIN][0]
            assert "get_market_data" in task.tools
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_high_priority(self):
        """Test that trading tasks have high priority."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = TradingAgent(hub)
            
            await agent.evaluate_trade("market_123")
            
            task = hub.lanes[Lane.MAIN][0]
            assert task.priority == 10  # High priority for trading
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_markets(self):
        """Test batch evaluation of multiple markets."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = TradingAgent(hub)
            
            market_ids = ["market_1", "market_2", "market_3"]
            task_ids = await agent.batch_evaluate_markets(market_ids)
            
            assert len(task_ids) == 3
            assert all(tid.startswith("trade_") for tid in task_ids)
            
            # Check all tasks enqueued
            status = hub.get_status()
            assert status['lane_status']['main']['queued'] == 3
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_with_research(self):
        """Test batch evaluation with research results."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            hub = TradingHub()
            agent = TradingAgent(hub)
            
            market_ids = ["market_1", "market_2"]
            research_results = [
                {"response": "Research 1"},
                {"response": "Research 2"}
            ]
            
            task_ids = await agent.batch_evaluate_markets(
                market_ids,
                research_results=research_results
            )
            
            assert len(task_ids) == 2
            
            # Check tasks have research context
            tasks = list(hub.lanes[Lane.MAIN])
            assert len(tasks) == 2
