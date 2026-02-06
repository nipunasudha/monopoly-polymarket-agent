# Test Commands Cheat Sheet

## ✅ Correct Commands (Use These)

```bash
# All tests (76 tests, ~3.5s)
uv run test-agents

# Specific test layers
uv run test-agents tests/unit          # 42 unit tests
uv run test-agents tests/integration   # 23 integration tests
uv run test-agents tests/e2e           # 8 E2E tests

# By marker
uv run test-agents -m unit             # Unit tests only
uv run test-agents -m integration      # Integration tests only
uv run test-agents -m "not slow"       # Skip slow tests

# Verbose output
uv run test-agents -v                  # Verbose
uv run test-agents -v -s               # Verbose + show print statements

# Coverage
uv run test-agents --cov=agents --cov-report=html
open htmlcov/index.html

# Specific test file
uv run test-agents tests/unit/test_utils.py
uv run test-agents tests/integration/test_executor.py

# Specific test function
uv run test-agents tests/unit/test_utils.py::TestParseCamelCase::test_simple_camel_case
```

## ❌ Wrong Commands (Don't Use)

```bash
# These will fail with web3 import error:
uv run pytest tests/integration        # ❌ WRONG
uv run pytest tests/unit               # ❌ WRONG
pytest tests/                          # ❌ WRONG
```

## Expected Output

```
======================== 76 passed in 3.48s ========================
```

Breakdown:
- 42 unit tests (utilities, models, parsers)
- 23 integration tests (LLM, search - mocked)
- 8 E2E tests (full workflows - mocked)
- 3 legacy tests

## Quick Reference

| Command | What It Does | Time |
|---------|--------------|------|
| `uv run test-agents` | Run all tests | ~3.5s |
| `uv run test-agents tests/unit` | Run unit tests only | ~2.4s |
| `uv run test-agents tests/integration` | Run integration tests | ~1.0s |
| `uv run test-agents tests/e2e` | Run E2E tests | ~0.3s |
| `uv run test-agents -m "not slow"` | Skip slow tests | ~3.2s |
| `uv run test-agents -v` | Verbose output | ~3.5s |

## Troubleshooting

**Problem**: `ImportError: cannot import name 'ContractName' from 'eth_typing'`

**Solution**: You used `uv run pytest` instead of `uv run test-agents`

**Fix**: Always use `uv run test-agents`

---

**Remember**: Always use `uv run test-agents`, never `uv run pytest` directly!
