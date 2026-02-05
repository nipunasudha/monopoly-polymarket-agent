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