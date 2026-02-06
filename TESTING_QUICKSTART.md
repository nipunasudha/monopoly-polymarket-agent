# Testing Quick Start Guide

## ✅ 193 Tests Passing

All tests run in **~8 seconds** with **zero LLM API costs**.

## Running Tests

### ⚠️ Important: Always use `uv run test-agents`

Due to a web3 plugin conflict, **do NOT use `uv run pytest` directly**. Always use:

```bash
# ✅ CORRECT - Use test-agents command
uv run test-agents

# ❌ WRONG - Will fail with import error
uv run pytest tests/integration
```

### Quick Commands

```bash
# Run all tests (193 tests, ~8s)
uv run test-agents

# By test layer
uv run test-agents tests/unit          # 42 unit tests
uv run test-agents tests/integration  # 143 integration tests
uv run test-agents tests/e2e         # 8 E2E tests

# By marker
uv run test-agents -m unit           # Unit tests only
uv run test-agents -m integration   # Integration tests only
uv run test-agents -m "not slow"     # Skip slow tests

# Verbose output
uv run test-agents -v                 # Verbose
uv run test-agents -v -s              # Verbose + show prints

# Coverage
uv run test-agents --cov=agents --cov-report=html
open htmlcov/index.html

# Specific test file
uv run test-agents tests/unit/test_utils.py
uv run test-agents tests/integration/test_api.py

# Specific test function
uv run test-agents tests/unit/test_utils.py::TestParseCamelCase::test_simple_camel_case
```

## Test Structure

```
tests/
├── unit/              # 42 tests - Fast, isolated
│   ├── test_utils.py         # Utility functions
│   ├── test_models.py        # Pydantic models
│   └── test_parsers.py       # Parsing logic
│
├── integration/       # 143 tests - Mocked APIs
│   ├── test_executor.py      # LLM integration
│   ├── test_search.py        # Search integration
│   ├── test_database.py      # Database operations
│   ├── test_api.py           # API endpoints
│   ├── test_api_runner_integration.py  # API-Runner integration
│   ├── test_dashboard.py     # Dashboard UI
│   └── test_runner.py        # Background runner
│
├── e2e/              # 8 tests - Full workflows
│   └── test_forecast_workflow.py
│
└── fixtures/         # Test data
    ├── sample_markets.json
    └── sample_forecasts.json
```

## Test Coverage

| Layer | Tests | Coverage | Speed |
|-------|-------|----------|-------|
| Unit | 42 | Utilities, models, parsers | ~2.4s |
| Integration | 143 | LLM, search, database, API, dashboard, runner | ~5.0s |
| E2E | 8 | Full workflows (mocked) | ~0.3s |
| **Total** | **193** | **Phase 1 & 2 complete** | **~8s** |

## Key Features

✅ **Zero API Costs** - All LLM calls are mocked
✅ **Fast Execution** - Complete suite runs in ~8 seconds
✅ **100% Pass Rate** - All 193 tests passing
✅ **Easy to Run** - Single command: `uv run test-agents`

## What's Tested

### ✅ Phase 1 (Complete - 76 tests)
- Utility functions (parsing, preprocessing)
- Pydantic model validation
- LLM integration (mocked)
- Search integration (mocked)
- Trade decision logic
- Forecast generation workflow
- Error handling

### ✅ Phase 2 (Complete - 77 tests)
- **2.1 Database persistence** (26 tests)
  - Forecast CRUD operations
  - Trade CRUD operations
  - Portfolio snapshots
  - Database migrations
- **2.2 API endpoints** (29 tests)
  - Forecast endpoints
  - Trade endpoints
  - Portfolio endpoints
  - Agent control endpoints
- **2.3 Dashboard UI** (22 tests)
  - Portfolio overview page
  - Forecasts page
  - Trades page
  - Navigation and responsive design

### ✅ Phase 2.4: Background Agent Runner (COMPLETE)
- **22 tests** covering async agent runner
- State management (STOPPED, RUNNING, PAUSED, ERROR)
- Lifecycle control (start, stop, pause, resume)
- Configurable intervals
- Manual triggers
- Error tracking

### ⏳ Phase 3 (TODO)
- Multi-agent coordination
- Agent communication
- Aggregation logic
- Full trading cycles

## Documentation

- **Testing Strategy**: `UPGRADE.md` (Testing Strategy section)

## Common Issues

### Web3 Plugin Error
If you see `ImportError: cannot import name 'ContractName' from 'eth_typing'`:

**Cause**: You're running `uv run pytest` directly instead of using the test runner.

**Solution**: Always use `uv run test-agents`:
```bash
# ✅ CORRECT
uv run test-agents tests/integration

# ❌ WRONG - causes web3 error
uv run pytest tests/integration
```

### Alternative: Running Tests Manually
If you absolutely need to run pytest directly:
```bash
cd agents
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:web3 tests/

# Or use the shell script
./run_tests.sh tests/integration
```

## Example Output

```
======================== test session starts ==============================
platform darwin -- Python 3.9.21, pytest-8.4.2, pluggy-1.6.0
collected 76 items

tests/unit/test_utils.py ............. PASSED                      [ 17%]
tests/unit/test_models.py ............ PASSED                      [ 33%]
tests/unit/test_parsers.py ............... PASSED                  [ 55%]
tests/integration/test_executor.py ............ PASSED             [ 71%]
tests/integration/test_search.py ........... PASSED                [ 85%]
tests/e2e/test_forecast_workflow.py ........ PASSED                [100%]

======================== 76 passed in 3.48s ===========================
```

---

**Remember**: Always use `uv run test-agents`, never `uv run pytest` directly!
