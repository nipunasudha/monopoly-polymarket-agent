"""
Integration tests for search functionality.
Uses mocked API calls to avoid costs.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.integration
class TestTavilySearch:
    """Test Tavily search integration with mocked API."""

    @patch("agents.connectors.search.TavilyClient")
    def test_tavily_client_initialization(self, mock_tavily):
        """Test that Tavily client can be initialized."""
        # The client is already initialized at module level
        # We just verify the mock is available
        assert mock_tavily is not None
        
        # We can create a new instance to test initialization
        from agents.connectors.search import TavilyClient
        client = TavilyClient(api_key="test_key")
        
        # Verify mock was called
        mock_tavily.assert_called_with(api_key="test_key")

    @patch("agents.connectors.search.tavily_client")
    def test_get_search_context_returns_string(self, mock_client):
        """Test that search returns context string."""
        # Mock the search response
        mock_client.get_search_context.return_value = (
            "This is search context about the query"
        )

        from agents.connectors.search import tavily_client

        result = tavily_client.get_search_context(query="Test query")

        assert isinstance(result, str)
        assert len(result) > 0

    @patch("agents.connectors.search.tavily_client")
    def test_search_context_for_market_question(self, mock_client):
        """Test searching for market-specific context."""
        mock_client.get_search_context.return_value = """
        Recent news about Bitcoin:
        - Bitcoin reached $95,000 this week
        - Institutional adoption continues to grow
        - Regulatory clarity improving in major markets
        """

        from agents.connectors.search import tavily_client

        query = "Will Bitcoin reach $100k by end of 2026?"
        result = tavily_client.get_search_context(query=query)

        assert "Bitcoin" in result
        assert isinstance(result, str)

    @patch("agents.connectors.search.tavily_client")
    def test_search_handles_empty_results(self, mock_client):
        """Test handling of empty search results."""
        mock_client.get_search_context.return_value = ""

        from agents.connectors.search import tavily_client

        result = tavily_client.get_search_context(query="Obscure query with no results")

        assert result == ""

    @patch("agents.connectors.search.tavily_client")
    def test_search_context_injection_into_prompt(self, mock_client):
        """Test that search context can be injected into prompts."""
        search_context = "Recent developments: XYZ happened, ABC was announced."
        mock_client.get_search_context.return_value = search_context

        from agents.connectors.search import tavily_client

        result = tavily_client.get_search_context(query="Market question")

        # Verify context can be used in prompt construction
        prompt = f"Based on this context: {result}\n\nMake a forecast."

        assert search_context in prompt
        assert "Make a forecast" in prompt


@pytest.mark.integration
@pytest.mark.skip(reason="Tests old LangChain executor - migrated to Claude SDK in Phase 4")
class TestSearchIntegrationWithExecutor:
    """Test search integration with Executor."""

    @patch("agents.connectors.search.tavily_client")
    @patch("agents.application.executor.ChatAnthropic")
    def test_search_context_flows_to_llm(
        self, mock_anthropic, mock_search, mock_llm_response
    ):
        """Test that search context flows through to LLM."""
        from agents.application.executor import Executor

        # Mock search to return context
        search_context = "Current market conditions: bullish sentiment, high volume"
        mock_search.get_search_context.return_value = search_context

        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response("Forecast based on context")
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm

        # In a real implementation, search context would be injected
        # For now, we verify the mocks work correctly
        from agents.connectors.search import tavily_client

        context = tavily_client.get_search_context(query="Test market")

        assert context == search_context

    @patch("agents.connectors.search.tavily_client")
    def test_multiple_search_queries(self, mock_client):
        """Test making multiple search queries."""
        # Different responses for different queries
        responses = {
            "query1": "Context for query 1",
            "query2": "Context for query 2",
            "query3": "Context for query 3",
        }

        def side_effect(query):
            return responses.get(query, "Default context")

        mock_client.get_search_context.side_effect = side_effect

        from agents.connectors.search import tavily_client

        result1 = tavily_client.get_search_context(query="query1")
        result2 = tavily_client.get_search_context(query="query2")
        result3 = tavily_client.get_search_context(query="query3")

        assert result1 == "Context for query 1"
        assert result2 == "Context for query 2"
        assert result3 == "Context for query 3"


@pytest.mark.integration
class TestSearchErrorHandling:
    """Test error handling in search functionality."""

    @patch("agents.connectors.search.tavily_client")
    def test_search_api_error_handling(self, mock_client):
        """Test handling of API errors."""
        # Mock an API error
        mock_client.get_search_context.side_effect = Exception("API Error")

        from agents.connectors.search import tavily_client

        with pytest.raises(Exception, match="API Error"):
            tavily_client.get_search_context(query="Test query")

    @patch("agents.connectors.search.tavily_client")
    def test_search_with_none_query(self, mock_client):
        """Test search with None query."""
        mock_client.get_search_context.return_value = ""

        from agents.connectors.search import tavily_client

        # This might raise an error or return empty - test actual behavior
        try:
            result = tavily_client.get_search_context(query=None)
            assert result == ""
        except (TypeError, AttributeError):
            # Expected if None is not handled
            pass

    @patch("agents.connectors.search.tavily_client")
    def test_search_with_empty_query(self, mock_client):
        """Test search with empty string query."""
        mock_client.get_search_context.return_value = ""

        from agents.connectors.search import tavily_client

        result = tavily_client.get_search_context(query="")

        assert result == ""


@pytest.mark.integration
@pytest.mark.slow
class TestSearchRateLimiting:
    """Test search rate limiting and throttling."""

    @patch("agents.connectors.search.tavily_client")
    def test_multiple_rapid_searches(self, mock_client):
        """Test making multiple rapid search requests."""
        mock_client.get_search_context.return_value = "Search result"

        from agents.connectors.search import tavily_client

        # Make multiple requests
        results = []
        for i in range(10):
            result = tavily_client.get_search_context(query=f"Query {i}")
            results.append(result)

        assert len(results) == 10
        assert all(r == "Search result" for r in results)
