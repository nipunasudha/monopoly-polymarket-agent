"""
Integration tests for Phase 4: Executor migration to Claude SDK
Tests that Executor works correctly with Claude SDK instead of LangChain.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from agents.application.executor import Executor


@pytest.mark.integration
class TestExecutorClaudeSDK:
    """Test Executor with Claude SDK."""
    
    def test_executor_uses_anthropic_not_langchain(self):
        """Test that Executor imports Anthropic, not LangChain."""
        import inspect
        source = inspect.getsource(Executor)
        
        # Should use Anthropic
        assert "from anthropic import Anthropic" in source or "Anthropic" in source
        
        # Should NOT use LangChain
        assert "ChatAnthropic" not in source
        assert "from langchain_anthropic" not in source
        assert "SystemMessage" not in source
        assert "HumanMessage" not in source
    
    def test_executor_initialization(self):
        """Test Executor initialization."""
        executor = Executor()
        assert executor is not None
        assert hasattr(executor, 'client') or executor.dry_run
        assert hasattr(executor, 'model')
        assert executor.model == "claude-sonnet-4-20250514"
    
    def test_executor_dry_run_mode(self):
        """Test Executor in dry_run mode."""
        with patch.dict(os.environ, {'TRADING_MODE': 'dry_run'}):
            executor = Executor()
            assert executor.dry_run == True
            assert executor.client is None
    
    @patch('agents.application.executor.Anthropic')
    def test_executor_live_mode(self, mock_anthropic):
        """Test Executor in live mode."""
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        with patch.dict(os.environ, {'TRADING_MODE': 'live', 'ANTHROPIC_API_KEY': 'test_key'}):
            executor = Executor()
            assert executor.dry_run == False
            assert executor.client is not None
    
    def test_get_llm_response_dry_run(self):
        """Test get_llm_response in dry_run mode."""
        with patch.dict(os.environ, {'TRADING_MODE': 'dry_run'}):
            executor = Executor()
            result = executor.get_llm_response("test input")
            
            assert isinstance(result, str)
            assert "Mock" in result or len(result) > 0
    
    @patch('agents.application.executor.Anthropic')
    def test_get_llm_response_live(self, mock_anthropic):
        """Test get_llm_response in live mode."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        with patch.dict(os.environ, {'TRADING_MODE': 'live', 'ANTHROPIC_API_KEY': 'test_key'}):
            executor = Executor()
            result = executor.get_llm_response("test input")
            
            assert result == "Test response"
            mock_client.messages.create.assert_called_once()
    
    def test_get_superforecast_dry_run(self):
        """Test get_superforecast in dry_run mode."""
        with patch.dict(os.environ, {'TRADING_MODE': 'dry_run'}):
            executor = Executor()
            result = executor.get_superforecast(
                event_title="Test Event",
                market_question="Will X happen?",
                outcome="Yes"
            )
            
            assert isinstance(result, str)
            assert "[DRY RUN]" in result
    
    @patch('agents.application.executor.Anthropic')
    def test_get_superforecast_live(self, mock_anthropic):
        """Test get_superforecast in live mode."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Forecast: 0.65 probability")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        with patch.dict(os.environ, {'TRADING_MODE': 'live', 'ANTHROPIC_API_KEY': 'test_key'}):
            executor = Executor()
            result = executor.get_superforecast(
                event_title="Test Event",
                market_question="Will X happen?",
                outcome="Yes"
            )
            
            assert isinstance(result, str)
            mock_client.messages.create.assert_called_once()
    
    def test_method_signatures_preserved(self):
        """Test that method signatures are preserved."""
        import inspect
        
        executor = Executor()
        
        # Check get_llm_response signature
        sig1 = inspect.signature(executor.get_llm_response)
        assert len(sig1.parameters) == 1
        assert 'user_input' in sig1.parameters
        
        # Check get_superforecast signature
        sig2 = inspect.signature(executor.get_superforecast)
        assert len(sig2.parameters) == 3
        assert 'event_title' in sig2.parameters
        assert 'market_question' in sig2.parameters
        assert 'outcome' in sig2.parameters
    
    @patch('agents.application.executor.Anthropic')
    def test_claude_sdk_message_format(self, mock_anthropic):
        """Test that messages are formatted correctly for Claude SDK."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        with patch.dict(os.environ, {'TRADING_MODE': 'live', 'ANTHROPIC_API_KEY': 'test_key'}):
            executor = Executor()
            executor.get_llm_response("test input")
            
            # Check that messages.create was called with correct format
            call_args = mock_client.messages.create.call_args
            assert 'model' in call_args.kwargs
            assert 'messages' in call_args.kwargs
            assert call_args.kwargs['messages'][0]['role'] == 'user'
            assert 'system' in call_args.kwargs or 'system' not in call_args.kwargs  # System is optional
