# Monopoly: Polymarket Betting Agent Enhancement Plan

## Research Summary

Your codebase is a fork of the **official [Polymarket/agents](https://github.com/Polymarket/agents)** repo. It's a solid foundation — event discovery, RAG filtering, LLM superforecasting, and CLOB execution are all wired up. But the most successful agents in the wild go significantly further.

### What the Best Agents Do (and This One Doesn't Yet)

| Capability | Top Agents | Current Codebase |
| --- | --- | --- |
| **LLM** | Claude (29% returns in PredIQt Arena) | GPT-3.5-turbo-16k (2 generations behind) |
| **Architecture** | Multi-agent (researcher, analyst, risk mgr) | Single monolithic `Executor` |
| **Risk Management** | Kelly criterion, position limits | None — raw LLM % \* balance |
| **Data Sources** | News + web search + on-chain integrated | Tavily exists but never called in trading flow |
| **Persistence** | Trade history, calibration tracking, portfolio | None — every run starts fresh |
| **UI** | Dashboards (PredictOS, Polyseer, PredictEngine) | Placeholder FastAPI (hello world) |
| **Structured Output** | JSON responses for downstream processing | Free-text parsed with fragile regex |

### Notable Open-Source References

| Project | What to Learn From It | URL |
| --- | --- | --- |
| **PredictOS** | Next.js + Python full-stack agent with arbitrage, copy trading | `github.com/PredictionXBT/PredictOS` |
| **Polyseer** | Multi-agent Bayesian aggregation research platform | `github.com/yorkeccak/Polyseer` |
| **Gnosis agent** | API-first design with benchmarking/monitoring tooling | `github.com/gnosis/prediction-market-agent` |
| **Metaculus bot template** | Standardized forecasting framework, top-10 accuracy | `github.com/Metaculus/metac-bot-template` |
| **polymarket-mcp** | MCP interface for AI agent access to prediction markets | `github.com/berlinbra/polymarket-mcp` |
| **Awesome Prediction Market Tools** | Curated directory of 170+ tools | `github.com/aarora4/Awesome-Prediction-Market-Tools` |

---

## Implementation Plan

### Phase 1: Core Accuracy Upgrades (Highest Impact)

**1.1 — Upgrade LLM to Claude**

-   File: `agents/application/executor.py`
-   Replace `ChatOpenAI(model='gpt-3.5-turbo-16k')` with `ChatAnthropic(model='claude-sonnet-4-20250514')`
-   Add `langchain-anthropic` to `requirements.txt`
-   Keep OpenAI embeddings in `chroma.py` (cheaper, works fine for vector search)
-   Add `ANTHROPIC_API_KEY` to `.env.example`

**1.2 — Structured Superforecaster Output**

-   File: `agents/application/prompts.py`
-   Upgrade `superforecaster()` prompt to require JSON output: `{probability, confidence, base_rate, key_factors, evidence_for, evidence_against, reasoning}`
-   File: `agents/application/executor.py`
-   Replace fragile regex parsing in `format_trade_prompt_for_execution()` with JSON parsing
-   Extend `agents/utils/objects.py` with `ForecastResult` Pydantic model

**1.3 — Integrate Tavily Search into Trading Flow**

-   File: `agents/connectors/search.py`
-   Replace hardcoded Biden query with a proper `WebSearchClient` class
-   File: `agents/application/executor.py`
-   In `source_best_trade()`, call `WebSearchClient.get_context_for_forecast(market_question)` and inject the context into the superforecaster prompt so the LLM has current information

**1.4 — Risk Management**

-   New file: `agents/application/risk.py`
-   `RiskManager` class with Kelly criterion position sizing, max position %, max portfolio exposure, minimum edge threshold
-   File: `agents/application/trade.py`
-   Replace raw `float(size) * usdc_balance` with `RiskManager.calculate_position_size()`

### Phase 2: Persistence + Dashboard

**2.1 — SQLite Persistence Layer**

-   New file: `agents/connectors/database.py`
-   SQLAlchemy models: `TradeRecord`, `ForecastRecord`, `PortfolioSnapshot`
-   File: `agents/application/trade.py`
-   Save every forecast and trade decision to DB (even when execution is disabled)

**2.2 — FastAPI Backend**

-   File: `scripts/python/server.py` (overhaul the placeholder)
-   Key endpoints:
    -   `GET /api/markets` — active markets with agent scores
    -   `POST /api/markets/{id}/analyze` — trigger analysis for a specific market
    -   `GET /api/trades` — trade history
    -   `GET /api/portfolio` — balance, PnL, positions
    -   `GET /api/forecasts` — forecasts with calibration data
    -   `POST /api/agent/start` / `POST /api/agent/stop` — control the agent
    -   `GET /api/agent/status` — running state, last/next run
    -   `WS /ws/agent-log` — real-time log streaming

**2.3 — Dashboard UI**

-   New directory: `agents/dashboard/`
-   Tech: **Jinja2 templates + HTMX + Tailwind CSS (CDN)** — zero build step, pure Python
-   Pages:
    -   **Portfolio Overview**: balance, total PnL, win rate, equity curve chart
    -   **Market Scanner**: active markets with estimated edge, sort/filter
    -   **Market Detail**: full analysis view with evidence chain, probability vs market price
    -   **Trade History**: table with status, PnL
    -   **Forecast Calibration**: Brier score, calibration plot
    -   **Settings**: LLM model, risk params, scheduler frequency
-   Charts via Chart.js (CDN)

**2.4 — Background Agent Runner**

-   New file: `agents/application/runner.py`
-   Replace broken `cron.py` with async `AgentRunner` that integrates with FastAPI's event loop
-   Configurable interval (not just weekly Monday)

### Phase 3: Multi-Agent Architecture

**3.1 — Specialized Agent Roles**

-   New directory: `agents/application/multi_agent/`
-   `ResearchAgent` — gathers data from Tavily, NewsAPI, Gamma API for a given market
-   `AnalystAgent` — superforecaster probability estimation (use Claude Opus for this role)
-   `RiskManagerAgent` — go/no-go with position sizing
-   `AggregatorAgent` — runs multiple analyst instances, combines via Bayesian aggregation

**3.2 — Pipeline Orchestration**

-   Modify `Trader.one_best_trade()` to pipeline through: Research → Analysis (multiple) → Aggregate → Risk Check → Execute

### Phase 4: Advanced (Future)

-   Cross-market arbitrage detection
-   On-chain position tracking via Web3
-   Auto-resolution tracking for calibration scoring
-   React frontend upgrade (if HTMX proves limiting)
-   MCP server integration for Claude Desktop control

---

## Development

### Running Tests

```bash
uv run test-agents
```

This works from the project root. You can pass any pytest flags through, e.g. `uv run test-agents -v`.

---

## Testing Strategy

### Testing Architecture Overview

This system uses a **simplified testing pyramid** optimized for AI agent systems:

```
        /\
       /E2E\      ← Few (5-10 tests) - Full agent workflows
      /------\
     /  INT   \   ← Moderate (20-30 tests) - Component integration
    /----------\
   /    UNIT    \ ← Many (50+ tests) - Pure functions, utilities
  /--------------\
```

**Key Principle**: Over 70% of effort should test the **non-deterministic LLM components** (prompts, agent logic, decision-making), not just deterministic utilities. This inverts the common anti-pattern where only tools/utilities get tested.

### Test Organization

```
tests/
├── unit/              # Fast, isolated, deterministic
│   ├── test_risk.py           # Kelly criterion math
│   ├── test_parsers.py        # JSON/data parsing
│   ├── test_models.py         # Pydantic validation
│   └── test_utils.py          # Helper functions
│
├── integration/       # Component interactions
│   ├── test_database.py       # SQLite persistence
│   ├── test_search.py         # Tavily API calls (mocked)
│   ├── test_polymarket.py     # CLOB API (mocked)
│   ├── test_executor.py       # LLM prompt → structured output
│   └── test_multi_agent.py    # Agent coordination
│
├── e2e/              # Full workflows (slow)
│   ├── test_forecast_workflow.py    # Market → Forecast → Decision
│   ├── test_trade_workflow.py       # Full trading cycle
│   └── test_api_workflow.py         # Dashboard API endpoints
│
├── fixtures/         # Shared test data
│   ├── sample_markets.json
│   ├── sample_forecasts.json
│   └── mock_responses/
│
└── conftest.py       # pytest configuration & fixtures
```

### Phase-by-Phase Test Implementation

#### Phase 1: Foundation Tests (Start Here)

**1.1 Unit Tests for Risk Management**
```python
# tests/unit/test_risk.py
def test_kelly_criterion_calculation()
def test_position_size_limits()
def test_minimum_edge_threshold()
def test_max_portfolio_exposure()
```

**1.2 Integration Tests for LLM Structured Output**
```python
# tests/integration/test_executor.py
def test_superforecaster_returns_valid_json()
def test_forecast_includes_all_required_fields()
def test_confidence_score_in_valid_range()
def test_reasoning_chain_not_empty()
```

**1.3 Integration Tests for Web Search**
```python
# tests/integration/test_search.py
@pytest.mark.vcr  # Record/replay HTTP responses
def test_tavily_search_returns_context()
def test_search_context_injected_into_prompt()
```

**1.4 E2E Test for Basic Forecast**
```python
# tests/e2e/test_forecast_workflow.py
def test_end_to_end_forecast_generation():
    """Market question → Web search → LLM → Structured forecast"""
    market = load_fixture("sample_markets.json")[0]
    forecast = agent.generate_forecast(market)
    assert forecast.probability > 0
    assert forecast.reasoning is not None
```

#### Phase 2: Persistence & API Tests

**2.1 Database Integration Tests**
```python
# tests/integration/test_database.py
def test_save_and_retrieve_forecast()
def test_trade_history_query()
def test_portfolio_snapshot_calculation()
def test_database_migration_idempotent()
```

**2.2 API Integration Tests**
```python
# tests/integration/test_api.py
def test_get_markets_endpoint()
def test_trigger_analysis_endpoint()
def test_portfolio_endpoint_returns_valid_data()
def test_websocket_log_streaming()
```

**2.3 E2E Dashboard Test**
```python
# tests/e2e/test_api_workflow.py
def test_full_dashboard_workflow():
    """Start agent → Analyze market → View results in API"""
    client.post("/api/agent/start")
    client.post("/api/markets/123/analyze")
    response = client.get("/api/forecasts")
    assert len(response.json()) > 0
```

#### Phase 3: Multi-Agent Tests

**3.1 Multi-Agent Coordination Tests**
```python
# tests/integration/test_multi_agent.py
def test_research_agent_gathers_data()
def test_analyst_agent_produces_forecast()
def test_aggregator_combines_multiple_forecasts()
def test_risk_manager_rejects_low_edge_trades()
```

**3.2 E2E Multi-Agent Workflow**
```python
# tests/e2e/test_trade_workflow.py
def test_full_multi_agent_trading_cycle():
    """Research → Analyze → Aggregate → Risk Check → Execute"""
    market = load_fixture("sample_markets.json")[0]
    trade_decision = multi_agent_pipeline.execute(market)
    assert trade_decision.approved_by_risk_manager
    assert trade_decision.position_size > 0
```

### Testing Best Practices

**1. Mock External APIs (except in E2E)**
- Use `pytest-vcr` to record/replay HTTP responses
- Mock Polymarket CLOB API calls in integration tests
- Use real APIs only in E2E tests (with test accounts)

**2. Test LLM Outputs Structurally, Not Semantically**
```python
# ✅ Good - Test structure
assert isinstance(forecast.probability, float)
assert 0 <= forecast.probability <= 1
assert len(forecast.reasoning) > 50

# ❌ Bad - Test specific content (too brittle)
assert "Biden" in forecast.reasoning
```

**3. Use Fixtures for Consistent Test Data**
```python
# conftest.py
@pytest.fixture
def sample_market():
    return {
        "question": "Will Bitcoin reach $100k by end of 2026?",
        "current_price": 0.45,
        "liquidity": 50000
    }
```

**4. Separate Fast vs Slow Tests**
```bash
# Run only fast tests (unit + integration)
pytest -m "not slow"

# Run all tests including E2E
pytest
```

**5. Test Calibration Over Time**
```python
# tests/integration/test_calibration.py
def test_brier_score_calculation()
def test_calibration_plot_data_format()
def test_forecast_accuracy_tracking()
```

### Running Tests

```bash
# All tests
uv run test-agents

# Specific layer
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest tests/e2e

# With coverage
uv run pytest --cov=agents --cov-report=html

# Verbose with output
uv run test-agents -v -s

# Fast tests only (skip E2E)
uv run pytest -m "not slow"
```

### Test Metrics & Goals

| Metric | Target |
|--------|--------|
| **Unit test coverage** | >80% of `utils/`, `risk.py` |
| **Integration test coverage** | >60% of `executor.py`, `trade.py` |
| **E2E test coverage** | 5-10 critical workflows |
| **Test execution time** | <5s (unit), <30s (integration), <2min (E2E) |
| **CI/CD** | All tests pass before merge |

### Critical Testing Focus Areas

1. **LLM Prompt Testing** (often neglected, highest value)
   - Validate structured output format
   - Test edge cases (missing data, ambiguous questions)
   - Verify reasoning chain completeness

2. **Risk Management Logic** (highest financial impact)
   - Kelly criterion edge cases
   - Position limit enforcement
   - Portfolio exposure calculations

3. **Data Pipeline Integrity** (prevents silent failures)
   - Market data parsing
   - Search result integration
   - Database persistence

4. **Multi-Agent Coordination** (Phase 3 complexity)
   - Agent communication protocols
   - Aggregation logic
   - Failure handling (one agent fails)

---

## Verification Plan

1.  **Phase 1**: Run `python -m agents.application.trade` — should produce structured JSON forecasts with Claude, web search context, and Kelly-sized positions (no actual execution)
2.  **Phase 2**: Run `uvicorn scripts.python.server:app` — dashboard at localhost:8000 showing markets, past forecasts, and portfolio state
3.  **Phase 3**: Compare forecast accuracy (Brier score) of single-agent vs multi-agent on the same set of markets

## Critical Files

| File | Role |
| --- | --- |
| `agents/application/executor.py` | LLM coordination — most critical file |
| `agents/application/prompts.py` | All prompt templates |
| `agents/application/trade.py` | Trading orchestrator |
| `agents/connectors/search.py` | Tavily (currently disconnected) |
| `agents/utils/objects.py` | Pydantic models |
| `scripts/python/server.py` | FastAPI skeleton |
| `requirements.txt` | Dependencies |