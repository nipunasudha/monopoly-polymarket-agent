# Monopoly Trading Agent Architecture

**Version:** 2.0 (OpenClaw Architecture)  
**Last Updated:** 2026-02-08

---

## Table of Contents

1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Component Breakdown](#component-breakdown)
4. [Data Flow](#data-flow)
5. [Concurrency Model](#concurrency-model)
6. [Trading Flow](#trading-flow)
7. [Approval Workflow](#approval-workflow)
8. [Observability](#observability)
9. [Technology Stack](#technology-stack)

---

## Overview

The Monopoly Trading Agent is an autonomous prediction market trading system built on the **OpenClaw architecture**. It combines:

- **Lane-based concurrency** for parallel research and sequential decision-making
- **Specialized agents** (ResearchAgent, TradingAgent) for focused tasks
- **Human-in-the-loop** approval workflow for high-risk trades
- **Real-time observability** with WebSocket status updates and structured logging
- **Claude SDK** (Anthropic) for LLM-powered analysis
- **RAG-enhanced** market filtering with ChromaDB vector store

---

## Core Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        AgentRunner                            │
│  Manages lifecycle, scheduling, and background execution     │
└────────────┬─────────────────────────────────────┬───────────┘
             │                                     │
             ▼                                     ▼
    ┌────────────────┐                   ┌─────────────────┐
    │     Trader     │                   │   TradingHub    │
    │  Main logic    │                   │  Task manager   │
    └────────┬───────┘                   └────────┬────────┘
             │                                    │
             │         ┌──────────────────────────┘
             │         │                         │
             ▼         ▼                         ▼
    ┌────────────────────┐          ┌──────────────────────┐
    │  Research Agent    │          │   Trading Agent      │
    │  (RESEARCH lane)   │          │   (MAIN lane)        │
    └──────────┬─────────┘          └──────────┬───────────┘
               │                               │
               ▼                               ▼
    ┌────────────────────────────────────────────────────┐
    │             ToolRegistry                            │
    │  - exa_research (deep web search)                  │
    │  - tavily_search (general web search)              │
    │  - get_market_data (Polymarket API)                │
    │  - list_markets (Polymarket API)                   │
    │  - store_insight (memory management)               │
    └────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. TradingHub (Control Plane)

**Location:** `agents/core/hub.py`

The centralized control plane for task management and execution.

**Key Features:**
- **Lane-based queuing**: MAIN, RESEARCH, MONITOR, CRON
- **Concurrency limits**: 1 for MAIN, 3 for RESEARCH, 2 for MONITOR, 1 for CRON
- **Session management**: Multi-turn conversations with Claude
- **Claude SDK tool use loop**: Automatic tool calling and response handling
- **Memory cleanup**: TTL-based cleanup for sessions (1 hour) and task results (5 minutes)
- **Performance metrics**: Task execution timing, queue sizes, success/failure rates

**Methods:**
- `enqueue(task)` - Add task to lane queue
- `enqueue_and_wait(task, timeout)` - Synchronous task execution
- `start()` / `stop()` - Lifecycle management
- `get_status()` - Real-time status and metrics

### 2. Specialized Agents

#### ResearchAgent (`agents/core/agents.py`)

**Purpose:** Deep research on prediction markets

**Lane:** RESEARCH (parallel execution, concurrency: 3)

**Methods:**
- `research_market(question, description)` - Async research task
- `research_market_and_wait(question, description, timeout)` - Blocking research
- `quick_search(query)` - Fast search for context

**Tools Used:**
- `exa_research` - High-quality web search
- `tavily_search` - General web search
- `store_insight` - Memory management

#### TradingAgent (`agents/core/agents.py`)

**Purpose:** Trade evaluation and decision-making

**Lane:** MAIN (sequential execution, concurrency: 1)

**Methods:**
- `evaluate_trade(market_id, research)` - Async trade evaluation
- `evaluate_trade_and_wait(market_id, research, timeout)` - Blocking evaluation
- `batch_evaluate_markets(markets, research_results)` - Evaluate multiple markets

**Tools Used:**
- `get_market_data` - Fetch market prices and liquidity
- `list_markets` - List available markets

### 3. Tool Registry

**Location:** `agents/core/tools.py`

Centralizes tool definitions and execution logic.

**Tools:**
1. **exa_research** - Deep, high-quality web search (Exa API)
2. **tavily_search** - Fast general web search (Tavily API)
3. **get_market_data** - Fetch Polymarket market data
4. **list_markets** - List available Polymarket markets
5. **store_insight** - Store research insights in memory

**Execution:**
- Automatic sync/async detection
- Error handling with logging
- Tool input validation

### 4. Approval Manager

**Location:** `agents/core/approvals.py`

Human-in-the-loop workflow for high-risk trades.

**Features:**
- Auto-approve threshold (default: 5% of balance)
- Timeout handling (default: 5 minutes)
- WebSocket notifications
- Approval history tracking

**API Endpoints:**
- `POST /api/approvals/{trade_id}/approve`
- `POST /api/approvals/{trade_id}/reject`
- `GET /api/approvals/pending`
- `GET /api/approvals/stats`

### 5. Trader

**Location:** `agents/application/trade.py`

Main trading logic orchestrator.

**Method:** `async one_best_trade(hub, research_agent, trading_agent)`

**Flow:**
1. Pre-trade cleanup
2. Fetch all tradeable events
3. RAG-based event filtering
4. Map events to markets
5. **Parallel research** on top 3 markets
6. **Sequential trade evaluation** for each market
7. Parse LLM recommendations
8. **Approval workflow** (if needed)
9. Execute trade (if approved)

---

## Data Flow

```
1. Event Discovery
   ↓
2. RAG Filtering (ChromaDB + embeddings)
   ↓
3. Map to Markets
   ↓
4. Parallel Research (RESEARCH lane, 3 concurrent tasks)
   ├─ Market 1 → Exa + Tavily → Insights
   ├─ Market 2 → Exa + Tavily → Insights
   └─ Market 3 → Exa + Tavily → Insights
   ↓
5. Sequential Trade Evaluation (MAIN lane, 1 at a time)
   ├─ Market 1 + Research 1 → LLM → Decision
   ├─ Market 2 + Research 2 → LLM → Decision
   └─ Market 3 + Research 3 → LLM → Decision
   ↓
6. Approval (if trade size > threshold)
   ↓
7. Execution (Polymarket API)
   ↓
8. Persistence (SQLite database)
```

---

## Concurrency Model

### Lane-Based Queuing

Each lane has a concurrency limit enforced by TradingHub:

| Lane     | Concurrency | Purpose                     |
|----------|-------------|-----------------------------|
| MAIN     | 1           | Trading decisions (serial)  |
| RESEARCH | 3           | Background research (||)    |
| MONITOR  | 2           | Position monitoring (||)    |
| CRON     | 1           | Scheduled tasks (serial)    |

### Task Priority

Tasks within a lane are prioritized (higher number = higher priority):

```python
# High priority (execute first)
task = Task(id="critical", priority=10, lane=Lane.MAIN)

# Normal priority
task = Task(id="normal", priority=5, lane=Lane.RESEARCH)

# Low priority (execute last)
task = Task(id="background", priority=1, lane=Lane.CRON)
```

### Execution Model

- **MAIN lane**: Sequential execution ensures consistent decision-making
- **RESEARCH lane**: Parallel execution (3 concurrent) for fast market analysis
- **Background processor**: Continuously processes queued tasks
- **Automatic cleanup**: Expired sessions and results are removed periodically

---

## Trading Flow

### Phase 1: Event Discovery & Filtering

```python
# 1. Get all tradeable events from Polymarket
events = polymarket.get_all_tradeable_events()

# 2. Filter using RAG (ChromaDB vector similarity)
filtered_events = agent.filter_events_with_rag(events)

# 3. Map to markets
markets = agent.map_filtered_events_to_markets(filtered_events)
```

### Phase 2: Parallel Research

```python
# Research top 3 markets in parallel (RESEARCH lane)
top_markets = markets[:3]
research_results = []

for market in top_markets:
    result = await research_agent.research_market_and_wait(
        market_question=market["question"],
        market_description=market["description"],
        timeout=120.0
    )
    research_results.append(result)
```

### Phase 3: Sequential Trade Evaluation

```python
# Evaluate trades sequentially (MAIN lane)
for i, market in enumerate(top_markets):
    trade_eval = await trading_agent.evaluate_trade_and_wait(
        market_id=market["id"],
        research=research_results[i],
        timeout=120.0
    )
    
    # Parse LLM response
    probability = extract_probability(trade_eval)
    side = extract_side(trade_eval)  # BUY or SELL
    size = extract_size(trade_eval)
    
    # Calculate amount
    amount = size_fraction * usdc_balance
```

### Phase 4: Approval & Execution

```python
# Request approval if trade is large
if size_fraction > auto_approve_threshold:
    approved = await approval_manager.request_approval(
        trade_id=trade_id,
        trade_data=trade_data,
        timeout=300
    )
    
    if not approved:
        # Save as rejected
        continue

# Execute trade
trade = polymarket.execute_market_order(market, amount)

# Save to database
db.save_trade(trade_data)
```

---

## Approval Workflow

### Auto-Approval

Trades < 5% of balance are auto-approved.

### Manual Approval

1. **Notification**: WebSocket message sent to frontend
2. **User Action**: Approve or reject via API
3. **Timeout**: Auto-reject after 5 minutes
4. **Execution**: Trade executes if approved

### API Integration

```javascript
// Listen for approval requests
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'approval_request') {
    showApprovalUI(msg.data);
  }
};

// Approve
fetch(`/api/approvals/${trade_id}/approve`, { method: 'POST' });

// Reject
fetch(`/api/approvals/${trade_id}/reject`, { method: 'POST' });
```

---

## Observability

### Structured Logging

```python
from agents.core.structured_logging import configure_structlog, get_logger

configure_structlog(level="INFO", json_output=False)
logger = get_logger(__name__)

logger.info("task_enqueued", task_id="abc123", lane="research")
```

### Performance Metrics

```python
# Automatic tracking in TradingHub
metrics = hub.metrics.get_all()
# {
#   "tasks_enqueued": 5,
#   "queue_size": 2,
#   "task_execution_time_ms": [150, 200, 180]
# }
```

### WebSocket Status Updates

```javascript
// Subscribe to hub updates (broadcast every 2s)
ws.send(JSON.stringify({ action: 'get_hub_status' }));

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'hub_status_update') {
    updateDashboard(msg.data);
  }
};
```

### REST API Endpoints

- `GET /api/hub/status` - Current hub status
- `GET /api/hub/stats` - Detailed statistics
- `GET /api/agent/status` - Agent runner status

---

## Technology Stack

### Core Technologies

- **Python 3.9+**
- **FastAPI** - Web server and REST API
- **SQLAlchemy** - Database ORM
- **ChromaDB** - Vector store for RAG
- **SQLite** - Local database

### AI/ML

- **Anthropic Claude** (via Claude SDK) - Primary LLM
- **Sentence Transformers** - Text embeddings
- **Exa API** - High-quality web search
- **Tavily API** - General web search

### Infrastructure

- **asyncio** - Async I/O and concurrency
- **structlog** - Structured logging
- **WebSockets** - Real-time updates
- **pytest** - Testing framework

### External Services

- **Polymarket API** - Market data and trade execution
- **NewsAPI** - News aggregation
- **Polygon** - Blockchain integration (USDC)

---

## Migration History

### Version 1.0 (Legacy)
- LangChain-based LLM execution
- Sequential processing
- No parallel research
- No approval workflow

### Version 2.0 (OpenClaw)
- Claude SDK (direct Anthropic API)
- Lane-based concurrency
- Specialized agents (Research, Trading)
- Parallel market research
- Human-in-the-loop approvals
- Real-time observability
- Structured logging
- Performance metrics

**Migration Date:** 2026-02-08  
**Completed Phases:** 1-8  
**Status:** Production-ready

---

## Future Enhancements

1. **Rate Limiting** - Add tool execution rate limits
2. **Result Size Limits** - Prevent memory bloat from large responses
3. **Advanced Metrics** - Prometheus/Grafana integration
4. **Multi-Agent Coordination** - Cross-agent communication
5. **Adaptive Concurrency** - Dynamic lane limits based on load
6. **ML Model Integration** - Custom prediction models alongside LLM

---

**For detailed implementation examples, see:**
- Trading flow: `agents/application/trade.py`
- Hub implementation: `agents/core/hub.py`
- Agent definitions: `agents/core/agents.py`
- Tool registry: `agents/core/tools.py`
- API server: `scripts/python/server.py`
