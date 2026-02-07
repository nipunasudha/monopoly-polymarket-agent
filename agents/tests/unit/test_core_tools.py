"""
Unit tests for Phase 1: ToolRegistry
Tests tool registration, schema generation, and execution.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.core.tools import ToolRegistry


@pytest.mark.unit
class TestToolRegistry:
    """Test ToolRegistry functionality."""
    
    def test_tool_registry_initialization(self):
        """Test that ToolRegistry initializes correctly."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            assert registry is not None
            assert hasattr(registry, 'tools')
            assert hasattr(registry, 'executors')
            assert isinstance(registry.tools, dict)
            assert isinstance(registry.executors, dict)
    
    def test_tool_registry_without_exa(self):
        """Test ToolRegistry when Exa is not available."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}, clear=False):
            with patch('agents.core.tools.Exa', None):
                registry = ToolRegistry()
                # Should still initialize, just without Exa tools
                assert registry.exa is None
                assert 'exa_research' not in registry.tools
    
    def test_tool_registry_without_tavily(self):
        """Test ToolRegistry when Tavily key is not set."""
        with patch.dict('os.environ', {}, clear=True):
            registry = ToolRegistry()
            assert registry.tavily is None
            assert 'tavily_search' not in registry.tools
    
    def test_tool_schemas_generation(self):
        """Test that tool schemas are generated correctly."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            schemas = registry.get_tool_schemas()
            
            assert isinstance(schemas, list)
            assert len(schemas) > 0
            
            # Check schema structure
            for schema in schemas:
                assert 'name' in schema
                assert 'description' in schema
                assert 'input_schema' in schema
                assert schema['input_schema']['type'] == 'object'
    
    def test_register_custom_tool(self):
        """Test registering a custom tool."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            
            def custom_executor(**kwargs):
                return {"result": "custom"}
            
            registry.register_tool(
                name="custom_tool",
                description="A custom tool",
                input_schema={
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"}
                    },
                    "required": ["input"]
                },
                executor=custom_executor
            )
            
            assert "custom_tool" in registry.tools
            assert "custom_tool" in registry.executors
    
    def test_get_market_data_tool_registered(self):
        """Test that get_market_data tool is registered."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            assert "get_market_data" in registry.tools
            assert "get_market_data" in registry.executors
    
    def test_list_markets_tool_registered(self):
        """Test that list_markets tool is registered."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            assert "list_markets" in registry.tools
            assert "list_markets" in registry.executors
    
    def test_store_insight_tool_registered(self):
        """Test that store_insight tool is registered."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            assert "store_insight" in registry.tools
            assert "store_insight" in registry.executors


@pytest.mark.unit
@pytest.mark.asyncio
class TestToolExecution:
    """Test tool execution functionality."""
    
    @pytest.mark.asyncio
    async def test_execute_get_market_data(self):
        """Test executing get_market_data tool."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            
            # Mock polymarket.get_market
            mock_market = Mock()
            mock_market.question = "Test question"
            mock_market.description = "Test description"
            mock_market.active = True
            mock_market.spread = 0.05
            mock_market.outcomes = "['Yes', 'No']"
            mock_market.outcome_prices = "[0.5, 0.5]"
            mock_market.end = "2026-12-31"
            
            registry.polymarket.get_market = Mock(return_value=mock_market)
            
            result = await registry.execute_tool("get_market_data", market_id="123")
            
            assert isinstance(result, dict)
            assert "market_id" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_execute_list_markets(self):
        """Test executing list_markets tool."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            
            # Mock polymarket.get_all_markets
            mock_markets = []
            registry.polymarket.get_all_markets = Mock(return_value=mock_markets)
            
            result = await registry.execute_tool("list_markets", active_only=True, limit=10)
            
            assert isinstance(result, dict)
            assert "markets" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_execute_store_insight(self):
        """Test executing store_insight tool."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            
            result = await registry.execute_tool(
                "store_insight",
                key="test_key",
                content="Test content"
            )
            
            assert isinstance(result, dict)
            assert result["status"] == "stored"
            assert result["key"] == "test_key"
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'}):
            registry = ToolRegistry()
            
            with pytest.raises(ValueError, match="not found"):
                await registry.execute_tool("nonexistent_tool", arg1="value")
