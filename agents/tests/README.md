# Monopoly Agents Test Suite

This test suite implements a simplified testing pyramid optimized for AI agent systems, with a focus on testing non-deterministic LLM components without incurring API costs.

## Test Structure

```
tests/
├── unit/              # Fast, isolated, deterministic tests
│   ├── test_utils.py          # Utility function tests
│   ├── test_models.py         # Pydantic model validation
│   └── test_parsers.py        # Parsing logic tests
│
├── integration/       # Component interaction tests (mocked APIs)
│   ├── test_executor.py       # LLM executor with mocked calls
│   └── test_search.py         # Search integration with mocked API
│
├── e2e/              # End-to-end workflow tests
│   └── test_forecast_workflow.py    # Complete forecast workflows
│
├── fixtures/         # Shared test data
│   ├── sample_markets.json
│   └── sample_forecasts.json
│
├── conftest.py       # Pytest configuration and fixtures
└── README.md         # This file
```

## Running Tests

### All tests
```bash
uv run test-agents
```

### By test layer
```bash
# Unit tests only (fastest)
uv run pytest tests/unit

# Integration tests only
uv run pytest tests/integration

# E2E tests only (slowest)
uv run pytest tests/e2e
```

### By marker
```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run only e2e tests
uv run pytest -m e2e

# Skip slow tests
uv run pytest -m "not slow"
```

### With coverage
```bash
# Generate coverage report
uv run pytest --cov=agents --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Verbose output
```bash
# Show detailed output
uv run pytest -v -s

# Show only failed tests
uv run pytest --tb=short
```

## Test Philosophy

### 1. No LLM Costs
All tests use mocked LLM responses to avoid API costs. We test:
- **Structure** of LLM outputs (JSON format, required fields)
- **Logic** around LLM calls (prompt construction, response parsing)
- **Integration** between components

We do NOT test:
- Actual LLM response quality (that's for manual evaluation)
- Real API calls (except in optional E2E tests with real credentials)

### 2. Focus on Non-Deterministic Components
Unlike typical test suites that focus 70%+ on deterministic utilities, we invert this:
- **70% effort** on LLM components, agent logic, decision-making
- **30% effort** on utilities, parsers, models

This aligns with research showing that most agent testing neglects the core AI components.

### 3. Test Pyramid
```
     /\
    /E2E\      ← Few (5-10 tests) - Full workflows
   /------\
  /  INT   \   ← Moderate (20-30 tests) - Component integration  
 /----------\
/    UNIT    \ ← Many (50+ tests) - Pure functions
/--------------\
```

## Writing New Tests

### Unit Tests
Test pure functions and utilities:
```python
@pytest.mark.unit
def test_parse_camel_case():
    assert parse_camel_case("camelCase") == "camel case"
```

### Integration Tests
Test component interactions with mocked external services:
```python
@pytest.mark.integration
@patch("agents.application.executor.ChatAnthropic")
def test_executor_with_mocked_llm(mock_anthropic, mock_llm_response):
    mock_llm = Mock()
    mock_llm.invoke.return_value = mock_llm_response("Test response")
    mock_anthropic.return_value = mock_llm
    
    executor = Executor()
    executor.llm = mock_llm
    
    result = executor.get_llm_response("Test input")
    assert result == "Test response"
```

### E2E Tests
Test complete workflows:
```python
@pytest.mark.e2e
@pytest.mark.slow
def test_full_forecast_workflow(sample_market, mock_all_services):
    # Test complete workflow from market to forecast
    result = generate_forecast(sample_market)
    assert result["probability"] > 0
```

## Fixtures

Common fixtures are defined in `conftest.py`:
- `sample_market` - Sample market data
- `sample_event` - Sample event data
- `sample_forecast` - Sample forecast result
- `sample_trade_response` - Sample LLM trade response
- `mock_llm_response` - Factory for creating mock LLM responses
- `mock_usdc_balance` - Mock USDC balance

## Test Markers

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests with mocked services
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.slow` - Slow tests (can be skipped)

## Best Practices

### 1. Mock External APIs
```python
@patch("agents.connectors.search.tavily_client")
def test_search(mock_client):
    mock_client.get_search_context.return_value = "Context"
    # Test logic here
```

### 2. Test Structure, Not Content
```python
# ✅ Good - Test structure
assert isinstance(forecast["probability"], float)
assert 0 <= forecast["probability"] <= 1

# ❌ Bad - Test specific content (too brittle)
assert "Bitcoin" in forecast["reasoning"]
```

### 3. Use Fixtures for Consistency
```python
def test_with_fixture(sample_market):
    # Use consistent test data
    assert sample_market["id"] == 12345
```

### 4. Keep Tests Fast
- Unit tests: <5 seconds total
- Integration tests: <30 seconds total
- E2E tests: <2 minutes total

## Current Test Coverage

### Phase 1 (Implemented)
- ✅ Unit tests for utilities (`test_utils.py`)
- ✅ Unit tests for Pydantic models (`test_models.py`)
- ✅ Unit tests for parsing logic (`test_parsers.py`)
- ✅ Integration tests for Executor (`test_executor.py`)
- ✅ Integration tests for search (`test_search.py`)
- ✅ E2E tests for forecast workflow (`test_forecast_workflow.py`)

### Phase 2 (TODO)
- ⏳ Database integration tests
- ⏳ API endpoint tests
- ⏳ Dashboard workflow tests

### Phase 3 (TODO)
- ⏳ Multi-agent coordination tests
- ⏳ Full trading cycle tests

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running tests from the project root:
```bash
cd /path/to/monopoly/agents
uv run test-agents
```

### Mock Not Working
Ensure you're patching the right import path:
```python
# Patch where it's used, not where it's defined
@patch("agents.application.executor.ChatAnthropic")  # ✅
@patch("langchain_anthropic.ChatAnthropic")          # ❌
```

### Fixtures Not Found
Ensure `conftest.py` is in the tests directory and pytest can discover it.

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Add unit tests for new utilities
3. Add integration tests for new components
4. Add E2E tests for new workflows
5. Update this README if adding new test patterns

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing AI Agents (2026 Research)](https://arxiv.org/html/2509.19185v2)
- [Testing Pyramid Guide](https://semaphoreci.com/blog/testing-pyramid)
