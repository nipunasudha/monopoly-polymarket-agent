"""
End-to-end tests for forecast workflow.

NOTE: These tests reference the old LangChain-based executor (ChatAnthropic).
The executor was migrated to Claude SDK in Phase 4.
New end-to-end tests using OpenClaw architecture are in test_phase7_integration.py.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


@pytest.mark.skip(reason="Tests old LangChain executor - migrated to Claude SDK in Phase 4")
@pytest.mark.e2e
@pytest.mark.slow
class TestForecastWorkflow:
    """Test complete forecast generation workflow."""

    @patch("agents.application.executor.ChatAnthropic")
    @patch("agents.connectors.search.tavily_client")
    @patch("agents.application.executor.Gamma")
    def test_end_to_end_forecast_generation(
        self,
        mock_gamma,
        mock_search,
        mock_anthropic,
        sample_market,
        sample_forecast,
        mock_llm_response,
    ):
        """Test full workflow: market → search → LLM → forecast."""
        from agents.application.executor import Executor

        # Mock search context
        search_context = "Recent news: positive developments in the market"
        mock_search.get_search_context.return_value = search_context

        # Mock LLM to return structured forecast
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response(json.dumps(sample_forecast))
        mock_anthropic.return_value = mock_llm

        # Mock Gamma market data
        mock_gamma_instance = Mock()
        mock_gamma_instance.get_market.return_value = sample_market
        mock_gamma.return_value = mock_gamma_instance

        # Execute workflow
        executor = Executor()
        executor.llm = mock_llm

        result = executor.get_superforecast(
            event_title="Test Event",
            market_question=sample_market["question"],
            outcome="Yes",
        )

        # Verify result
        assert result is not None
        forecast_data = json.loads(result)
        assert "probability" in forecast_data
        assert "reasoning" in forecast_data
        assert 0 <= forecast_data["probability"] <= 1

    @patch("agents.application.executor.ChatAnthropic")
    @patch("agents.connectors.search.tavily_client")
    def test_forecast_with_search_context_integration(
        self, mock_search, mock_anthropic, sample_market, mock_llm_response
    ):
        """Test that search context is properly integrated into forecast."""
        from agents.application.executor import Executor

        # Mock search
        search_context = "Key information about the market question"
        mock_search.get_search_context.return_value = search_context

        # Mock LLM
        mock_llm = Mock()
        forecast_result = {
            "probability": 0.65,
            "confidence": 0.80,
            "reasoning": "Based on search context and analysis",
        }
        mock_llm.invoke.return_value = mock_llm_response(json.dumps(forecast_result))
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm

        # Get search context
        from agents.connectors.search import tavily_client

        context = tavily_client.get_search_context(
            query=sample_market["question"]
        )

        # Generate forecast (in real implementation, context would be injected)
        result = executor.get_superforecast(
            event_title="Test",
            market_question=sample_market["question"],
            outcome="Yes",
        )

        assert context == search_context
        assert result is not None

    @patch("agents.application.executor.ChatAnthropic")
    def test_forecast_validation(
        self, mock_anthropic, sample_market, sample_forecast, mock_llm_response
    ):
        """Test that forecast output is properly validated."""
        from agents.application.executor import Executor

        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response(json.dumps(sample_forecast))
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm

        result = executor.get_superforecast(
            event_title="Test Event",
            market_question=sample_market["question"],
            outcome="Yes",
        )

        # Parse and validate
        forecast_data = json.loads(result)

        # Validate structure
        assert isinstance(forecast_data["probability"], (int, float))
        assert isinstance(forecast_data["confidence"], (int, float))
        assert isinstance(forecast_data["reasoning"], str)

        # Validate ranges
        assert 0 <= forecast_data["probability"] <= 1
        assert 0 <= forecast_data["confidence"] <= 1

        # Validate content
        assert len(forecast_data["reasoning"]) > 0


@pytest.mark.e2e
@pytest.mark.skip(reason="Tests old LangChain executor - migrated to Claude SDK in Phase 4")
@pytest.mark.slow
class TestTradeDecisionWorkflow:
    """Test complete trade decision workflow."""

    @patch("agents.application.executor.ChatAnthropic")
    @patch("agents.application.executor.Polymarket")
    def test_forecast_to_trade_decision(
        self,
        mock_polymarket_class,
        mock_anthropic,
        sample_trade_response,
        mock_llm_response,
    ):
        """Test workflow from forecast to trade decision."""
        from agents.application.executor import Executor

        # Mock Polymarket balance
        mock_polymarket = Mock()
        mock_polymarket.get_usdc_balance.return_value = 1000.0
        mock_polymarket_class.return_value = mock_polymarket

        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response(sample_trade_response)
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm
        executor.polymarket = mock_polymarket

        # Execute trade decision workflow
        trade_size = executor.format_trade_prompt_for_execution(sample_trade_response)

        # Verify trade decision
        assert trade_size > 0
        assert trade_size <= 1000.0  # Should not exceed balance
        assert trade_size == 250.0  # 0.25 * 1000

    @patch("agents.application.executor.ChatAnthropic")
    @patch("agents.application.executor.Polymarket")
    def test_multiple_forecasts_workflow(
        self,
        mock_polymarket_class,
        mock_anthropic,
        sample_markets_list,
        sample_forecast,
        mock_llm_response,
    ):
        """Test generating forecasts for multiple markets."""
        from agents.application.executor import Executor

        # Mock Polymarket
        mock_polymarket = Mock()
        mock_polymarket_class.return_value = mock_polymarket

        # Mock LLM to return different forecasts
        mock_llm = Mock()
        forecasts = [
            {"probability": 0.35, "confidence": 0.70, "reasoning": "Forecast 1"},
            {"probability": 0.55, "confidence": 0.80, "reasoning": "Forecast 2"},
            {"probability": 0.45, "confidence": 0.75, "reasoning": "Forecast 3"},
        ]
        mock_llm.invoke.side_effect = [
            mock_llm_response(json.dumps(f)) for f in forecasts
        ]
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm

        # Generate forecasts for multiple markets
        results = []
        for market in sample_markets_list:
            result = executor.get_superforecast(
                event_title="Test Event",
                market_question=market["question"],
                outcome="Yes",
            )
            results.append(json.loads(result))

        # Verify all forecasts generated
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["probability"] == forecasts[i]["probability"]
            assert result["confidence"] == forecasts[i]["confidence"]


@pytest.mark.e2e
@pytest.mark.skip(reason="Tests old LangChain executor - migrated to Claude SDK in Phase 4")
@pytest.mark.slow
class TestErrorHandlingWorkflow:
    """Test error handling in complete workflows."""

    @patch("agents.application.executor.ChatAnthropic")
    def test_invalid_forecast_format_handling(
        self, mock_anthropic, mock_llm_response
    ):
        """Test handling of invalid forecast format from LLM."""
        from agents.application.executor import Executor

        # Mock LLM to return invalid JSON
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response("Invalid JSON response")
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm

        result = executor.get_superforecast(
            event_title="Test", market_question="Test?", outcome="Yes"
        )

        # Should return the raw response even if not valid JSON
        assert result == "Invalid JSON response"

    @patch("agents.application.executor.ChatAnthropic")
    def test_missing_trade_size_handling(self, mock_anthropic):
        """Test handling of missing trade size in response."""
        from agents.application.executor import Executor

        executor = Executor()

        invalid_response = "outcome: Yes\nconfidence: high"

        with pytest.raises(ValueError, match="Could not parse size"):
            executor.format_trade_prompt_for_execution(invalid_response)

    @patch("agents.application.executor.ChatAnthropic")
    @patch("agents.application.executor.Polymarket")
    def test_zero_balance_handling(
        self, mock_polymarket_class, mock_anthropic, sample_trade_response
    ):
        """Test handling of zero USDC balance."""
        from agents.application.executor import Executor

        # Mock zero balance
        mock_polymarket = Mock()
        mock_polymarket.get_usdc_balance.return_value = 0.0
        mock_polymarket_class.return_value = mock_polymarket

        executor = Executor()
        executor.polymarket = mock_polymarket

        trade_size = executor.format_trade_prompt_for_execution(sample_trade_response)

        # Should return 0 when balance is 0
        assert trade_size == 0.0
