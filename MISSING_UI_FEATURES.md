# Missing UI Features from CLI

## CLI Commands vs UI Comparison

### ✅ Available in UI
1. **Agent Control** (`run_autonomous_trader`) - ✅ Available via Agent page (start/stop/pause/resume/run-once)
2. **Markets View** (`get_all_markets`) - ✅ Basic markets page exists
3. **Portfolio View** - ✅ Available
4. **Trades View** - ✅ Available
5. **Forecasts View** - ✅ Available

### ❌ Missing from UI

#### 1. **Market Filtering & Sorting** (`get_all_markets`)
- **CLI**: `get_all_markets(limit, sort_by="spread")`
- **Missing**: 
  - Sort by spread, volume, liquidity
  - Filter by trading criteria
  - Limit/pagination controls
- **Impact**: Users can't find best trading opportunities

#### 2. **Events Browsing** (`get_all_events`)
- **CLI**: `get_all_events(limit, sort_by="number_of_markets")`
- **Missing**: 
  - Events page/view
  - Browse events with multiple markets
  - Sort by number of markets
- **Impact**: Can't explore events that drive markets

#### 3. **News Search** (`get_relevant_news`)
- **CLI**: `get_relevant_news(keywords)`
- **Missing**: 
  - News search interface
  - Keyword-based news queries
  - News articles display
- **Impact**: Can't research market context

#### 4. **RAG Operations**
- **CLI**: 
  - `create_local_markets_rag(local_directory)`
  - `query_local_markets_rag(vector_db_directory, query)`
- **Missing**: 
  - RAG database creation UI
  - RAG query interface
  - Vector search functionality
- **Impact**: Can't use RAG features for market research

#### 5. **Superforecaster Query** (`ask_superforecaster`)
- **CLI**: `ask_superforecaster(event_title, market_question, outcome)`
- **Missing**: 
  - Manual superforecaster query form
  - Custom forecast generation
  - One-off analysis tool
- **Impact**: Can't manually query forecasts for specific markets

#### 6. **Market Creation** (`create_market`)
- **CLI**: `create_market()`
- **Missing**: 
  - Market creation form
  - Market proposal interface
  - Creator agent UI
- **Impact**: Can't propose new markets

#### 7. **LLM Chat** (`ask_llm`)
- **CLI**: `ask_llm(user_input)`
- **Missing**: 
  - General LLM chat interface
  - Free-form questions
  - LLM responses display
- **Impact**: Can't interact with LLM directly

#### 8. **Polymarket LLM** (`ask_polymarket_llm`)
- **CLI**: `ask_polymarket_llm(user_input)`
- **Missing**: 
  - Context-aware LLM chat (with markets & events)
  - Market-specific queries
  - Trading strategy questions
- **Impact**: Can't get market-aware LLM responses

#### 9. **Market Analysis** (`/api/markets/{market_id}/analyze`)
- **API**: Endpoint exists but returns "not yet implemented"
- **Missing**: 
  - Deep market analysis
  - Market detail page
  - Analysis results display
- **Impact**: Can't analyze individual markets

#### 10. **Market Detail View**
- **Missing**: 
  - Individual market page
  - Market history
  - Related forecasts/trades
  - Market metadata
- **Impact**: Can't drill into specific markets

## Priority Recommendations

### High Priority (Core Trading Features)
1. **Market Detail Page** - View individual markets with analysis
2. **Market Filtering/Sorting** - Find best opportunities
3. **Market Analysis** - Implement the analyze endpoint

### Medium Priority (Research Tools)
4. **Events Browser** - Explore events and their markets
5. **News Search** - Research market context
6. **Superforecaster Query** - Manual forecast generation

### Low Priority (Advanced Features)
7. **LLM Chat** - Direct LLM interaction
8. **RAG Operations** - Vector database management
9. **Market Creation** - Propose new markets
