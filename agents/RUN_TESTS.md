# How to Run Tests

## ⚠️ Important: Web3 Plugin Issue

Due to a conflict with the `web3` package's pytest plugin, you **must** use one of these methods:

## ✅ Recommended Methods

### Method 1: Use the test-agents command (EASIEST)
```bash
# From project root
uv run test-agents

# With options
uv run test-agents -v
uv run test-agents -m unit
uv run test-agents --cov=agents
```

### Method 2: Use the shell script
```bash
cd agents
./run_tests.sh
./run_tests.sh tests/unit -v
./run_tests.sh tests/integration
```

### Method 3: Set environment variable and flags
```bash
cd agents
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:web3 tests/
```

## ❌ This Will Fail

```bash
# DON'T DO THIS - will fail with web3 import error
uv run pytest tests/integration
uv run pytest tests/unit
```

## Quick Commands

```bash
# All tests
uv run test-agents

# Specific layers
uv run test-agents tests/unit
uv run test-agents tests/integration
uv run test-agents tests/e2e

# With markers
uv run test-agents -m unit
uv run test-agents -m integration
uv run test-agents -m "not slow"

# With coverage
uv run test-agents --cov=agents --cov-report=html

# Verbose
uv run test-agents -v -s
```

## Why This Happens

The `web3` package (required for Polymarket integration) includes a pytest plugin that has a broken import. The test runner and shell script automatically disable this plugin.

## Solution Summary

**Always use `uv run test-agents` instead of `uv run pytest` directly.**

This is configured in:
- `scripts/python/test_runner.py` - Handles the plugin disabling
- `run_tests.sh` - Shell wrapper with environment variables
- `pytest.ini` - Base configuration

## Test Results

When working correctly, you should see:

```
======================== 76 passed in 3.48s ========================
```

- 42 unit tests
- 23 integration tests  
- 8 E2E tests
- 3 legacy tests
