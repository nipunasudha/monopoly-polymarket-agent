"""
Integration tests for Executor class.
Tests LLM integration with mocked responses to avoid API costs.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.application.executor import Executor
import json


@pytest.mark.integration
class TestExecutorLLMIntegration:
    """Test Executor with mocked LLM calls."""

    @patch("agents.application.executor.ChatAnthropic")
    def test_executor_initialization(self, mock_anthropic):
        """Test that Executor initializes correctly."""
        executor = Executor()

        assert executor.token_limit == 180000
        assert executor.prompter is not None
        assert executor.gamma is not None
        assert executor.chroma is not None

    @patch("agents.application.executor.ChatAnthropic")
    def test_get_llm_response_returns_string(
        self, mock_anthropic, mock_llm_response
    ):
        """Test that get_llm_response returns string content."""
        # Setup mock
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response(
            "This is a test response from the LLM"
        )
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm

        result = executor.get_llm_response("Test input")

        assert isinstance(result, str)
        assert result == "This is a test response from the LLM"
        mock_llm.invoke.assert_called_once()

    @patch("agents.application.executor.ChatAnthropic")
    def test_get_superforecast_with_valid_inputs(
        self, mock_anthropic, mock_llm_response, sample_forecast
    ):
        """Test superforecast generation with valid inputs."""
        # Setup mock to return JSON forecast
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response(json.dumps(sample_forecast))
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm

        result = executor.get_superforecast(
            event_title="Test Event",
            market_question="Will X happen?",
            outcome="Yes",
        )

        assert isinstance(result, str)
        mock_llm.invoke.assert_called_once()

    @patch("agents.application.executor.ChatAnthropic")
    def test_format_trade_prompt_for_execution(
        self, mock_anthropic, sample_trade_response
    ):
        """Test formatting trade prompt for execution."""
        executor = Executor()

        # Mock the polymarket balance
        with patch.object(executor.polymarket, "get_usdc_balance", return_value=1000.0):
            result = executor.format_trade_prompt_for_execution(sample_trade_response)

            # size is 0.25, balance is 1000, so result should be 250
            assert result == 250.0

    @patch("agents.application.executor.ChatAnthropic")
    def test_format_trade_prompt_missing_size_raises_error(self, mock_anthropic):
        """Test that missing size in trade response raises ValueError."""
        executor = Executor()

        invalid_response = "outcome: Yes\nconfidence: high"

        with pytest.raises(ValueError, match="Could not parse size"):
            executor.format_trade_prompt_for_execution(invalid_response)

    @patch("agents.application.executor.ChatAnthropic")
    def test_estimate_tokens_accuracy(self, mock_anthropic):
        """Test token estimation is reasonable."""
        executor = Executor()

        # Test with known text
        text = "word " * 100  # 500 characters
        estimated = executor.estimate_tokens(text)

        # Should be around 125 tokens (500/4)
        assert estimated == 125

    @patch("agents.application.executor.ChatAnthropic")
    def test_divide_list_preserves_all_items(self, mock_anthropic):
        """Test that divide_list doesn't lose any items."""
        executor = Executor()

        original = list(range(100))
        divided = executor.divide_list(original, 7)

        # Flatten and check all items present
        flattened = [item for sublist in divided for item in sublist]
        assert len(flattened) == len(original)
        assert set(flattened) == set(original)


@pytest.mark.integration
class TestExecutorMarketFiltering:
    """Test market filtering with mocked components."""

    @patch("agents.application.executor.ChatAnthropic")
    def test_filter_events_prompt_generation(self, mock_anthropic):
        """Test that filter_events prompt is generated correctly."""
        executor = Executor()

        # filter_events() takes no arguments, just returns a prompt string
        prompt = executor.prompter.filter_events()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "filter" in prompt.lower() or "event" in prompt.lower()

    @patch("agents.application.executor.ChatAnthropic")
    @patch("agents.application.executor.Chroma")
    def test_filter_events_with_rag(
        self, mock_chroma_class, mock_anthropic, mock_llm_response
    ):
        """Test filtering events with RAG."""
        # Mock Chroma
        mock_chroma = Mock()
        mock_chroma.events.return_value = "RAG filtered events"
        mock_chroma_class.return_value = mock_chroma

        executor = Executor()
        executor.chroma = mock_chroma

        from agents.utils.objects import SimpleEvent

        events = [
            SimpleEvent(
                id=1,
                ticker="TEST",
                slug="test",
                title="Test Event",
                description="Test",
                end="2026-12-31",
                active=True,
                closed=False,
                archived=False,
                restricted=False,
                new=False,
                featured=False,
                markets="123",
            )
        ]

        result = executor.filter_events_with_rag(events)

        assert isinstance(result, str)
        mock_chroma.events.assert_called_once()


@pytest.mark.integration
class TestExecutorDataChunking:
    """Test data chunking for large datasets."""

    @patch("agents.application.executor.ChatAnthropic")
    def test_retain_keys_filters_correctly(self, mock_anthropic):
        """Test that retain_keys properly filters data."""
        from agents.application.executor import retain_keys

        data = [
            {
                "id": 1,
                "question": "Q1",
                "image": "img1.jpg",
                "description": "Desc1",
                "liquidity": 1000,
                "pagerDutyNotificationEnabled": True,
            },
            {
                "id": 2,
                "question": "Q2",
                "image": "img2.jpg",
                "description": "Desc2",
                "liquidity": 2000,
                "pagerDutyNotificationEnabled": False,
            },
        ]

        useful_keys = ["id", "question", "description", "liquidity"]
        result = retain_keys(data, useful_keys)

        assert len(result) == 2
        assert "image" not in result[0]
        assert "pagerDutyNotificationEnabled" not in result[0]
        assert "id" in result[0]
        assert "liquidity" in result[1]

    @patch("agents.application.executor.ChatAnthropic")
    def test_divide_list_creates_correct_chunks(self, mock_anthropic):
        """Test that divide_list creates correct number of chunks."""
        executor = Executor()

        data = list(range(100))
        chunks = executor.divide_list(data, 4)

        assert len(chunks) == 4
        # Each chunk should have 25 items
        for chunk in chunks:
            assert len(chunk) == 25


@pytest.mark.integration
class TestExecutorSourceBestTrade:
    """Test sourcing best trade with mocked components."""

    @patch("agents.application.executor.ChatAnthropic")
    def test_source_best_trade_calls_llm_twice(
        self, mock_anthropic, mock_llm_response, sample_forecast
    ):
        """Test that source_best_trade calls LLM for forecast and trade."""
        mock_llm = Mock()
        # First call returns forecast, second returns trade recommendation
        mock_llm.invoke.side_effect = [
            mock_llm_response(json.dumps(sample_forecast)),
            mock_llm_response("outcome: Yes\nsize: 0.25\nconfidence: high"),
        ]
        mock_anthropic.return_value = mock_llm

        executor = Executor()
        executor.llm = mock_llm

        # Create mock market object - source_best_trade expects a tuple (document, score)
        from langchain_core.documents import Document

        market_doc = Document(
            page_content="Market description here",
            metadata={
                "question": "Will X happen?",
                "outcome_prices": "[0.45, 0.55]",
                "outcomes": "['Yes', 'No']",
            },
        )

        result = executor.source_best_trade((market_doc, 0.95))

        assert isinstance(result, str)
        assert mock_llm.invoke.call_count == 2
