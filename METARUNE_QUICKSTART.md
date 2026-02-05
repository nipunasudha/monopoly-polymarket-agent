# Polymarket Agents - Metarune Quickstart Guide

## Installation Summary

Your Polymarket agents repository has been successfully set up with Python 3.9 and all 174 dependencies installed.

### Environment Details
- **Python Version:** 3.9.25
- **Virtual Environment Location:** `.venv/`
- **Total Packages Installed:** 174
- **Key Dependencies:**
  - Web3 ecosystem (web3, eth-account, py_clob_client, py_order_utils)
  - LLM stack (openai, langchain, langgraph, langchain-chroma)
  - Server stack (fastapi, uvicorn, starlette)
  - CLI framework (typer, click)
  - Vector database (chromadb, chroma-hnswlib)
  - Data sources (newsapi-python, tavily-python)

### Activation Command
```bash
# Activate the virtual environment
source .venv/bin/activate

# Verify activation (should show .venv in shell prompt)
which python  # Should point to .venv/bin/python
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              USER INTERFACES                         │
├──────────────────────┬──────────────────────────────┤
│  CLI (Typer)         │  REST API (FastAPI)           │
│  9 Commands          │  Health checks, Market data   │
└──────────────────────┼──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│           AGENT EXECUTION LAYER (Executor)           │
├─────────────────────────────────────────────────────┤
│  - LLM Coordination (OpenAI)      - RAG (Chroma)    │
│  - Market Filtering                - Event Analysis │
│  - Trade Calculation                                 │
└──────────────────┬──────────────────────────────────┘
                   │
       ┌───────────┼───────────┐
       │           │           │
   ┌───▼──┐  ┌───▼────┐  ┌───▼────┐
   │Gamma │  │Data    │  │Trading │
   │API   │  │Sources │  │CLOB    │
   └──────┘  └────────┘  └────────┘
       │           │           │
   Markets,    News, Web    Polygon
   Events      Search        Network
```

---

## Key File Locations

| Purpose | File Path |
|---------|-----------|
| **CLI Entry Point** | `scripts/python/cli.py` |
| **REST API Server** | `scripts/python/server.py` |
| **Autonomous Trading** | `agents/application/trade.py` |
| **LLM Executor** | `agents/application/executor.py` |
| **Gamma API Client** | `agents/polymarket/gamma.py` |
| **Trading CLOB Client** | `agents/polymarket/polymarket.py` |
| **Vector RAG Database** | `agents/connectors/chroma.py` |
| **News Connector** | `agents/connectors/news.py` |
| **Web Search** | `agents/connectors/search.py` |
| **Data Models** | `agents/utils/objects.py` |
| **Configuration** | `.env` (placeholder ready) |
| **Tests** | `tests/test.py` |

---

## Configuration Guide

### Required Environment Variables

Edit `.env` file and populate these keys:

```bash
# REQUIRED: Polygon blockchain wallet
POLYGON_WALLET_PRIVATE_KEY="your_private_key_here"

# REQUIRED: OpenAI API key (for LLM features)
OPENAI_API_KEY="sk-..."

# OPTIONAL: Web search capability
TAVILY_API_KEY="your_tavily_key"

# OPTIONAL: News data source
NEWSAPI_API_KEY="your_newsapi_key"
```

**⚠️ Security Notes:**
- Never commit `.env` file (already in `.gitignore`)
- Keep private keys absolutely secret
- Treat API keys as sensitive credentials
- US persons may be restricted from trading per Polymarket ToS

---

## CLI Commands Overview

### 1. Market Discovery
```bash
# List all tradeable markets (limit 5, sorted by spread)
python scripts/python/cli.py get-all-markets --limit 5 --sort-by spread

# Query events
python scripts/python/cli.py get-all-events --limit 3
```

### 2. Data & Research
```bash
# Search news by keyword
python scripts/python/cli.py get-relevant-news "bitcoin" "ethereum"

# Query local markets RAG
python scripts/python/cli.py query-local-markets-rag ./vector_db "best crypto bet"

# Build local RAG from market data
python scripts/python/cli.py create-local-markets-rag ./market_data
```

### 3. AI Forecasting
```bash
# Ask superforecaster about prediction
python scripts/python/cli.py ask-superforecaster "Bitcoin ETF" "Will pass?" "yes"

# General LLM query
python scripts/python/cli.py ask-llm "What's your opinion on AI?"

# Market-aware LLM query
python scripts/python/cli.py ask-polymarket-llm "Best market opportunities today?"
```

### 4. Trading (Advanced)
```bash
# Market creation suggestions
python scripts/python/cli.py create-market

# Full autonomous trading pipeline
python scripts/python/cli.py run-autonomous-trader
```

---

## Starting the Environment

### Quick Start (Interactive)
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Set Python path (if not in shell profile)
export PYTHONPATH="."

# 3. Test installation
python -c "from agents.connectors.news import News; print('✓ Setup OK')"
```

### Development Server
```bash
# Start FastAPI REST server
.venv/bin/python scripts/python/server.py
# Server runs on http://localhost:8000
```

### Pre-commit Hooks
```bash
# Install black code formatter hooks
pre-commit install

# Run black formatter
black .
```

---

## Testing Installation

### Module Imports Test
```bash
export PYTHONPATH="."
.venv/bin/python -c "
from agents.connectors.news import News
from agents.connectors.chroma import PolymarketRAG
print('✓ All core modules imported successfully')
"
```

### Pip Package List
```bash
# Show all 174 installed packages
.venv/bin/pip list

# Show specific package
.venv/bin/pip show web3
```

---

## Common Issues & Solutions

### Issue: Private key error when running CLI
**Solution:** The CLI requires `POLYGON_WALLET_PRIVATE_KEY` in `.env`
- For read-only tests, you need a dummy Polygon wallet (address doesn't need funds yet)
- Generate one: `python -c "from eth_keys import keys; print(keys.PrivateKey(b'\\x01' * 32).public_key.to_hex())"`

### Issue: OpenAI API key errors
**Solution:** Ensure `OPENAI_API_KEY` is set in `.env`
- Get key from: https://platform.openai.com/api-keys
- Some features require gpt-3.5-turbo or gpt-4 access

### Issue: Chromadb collection errors
**Solution:** RAG database may need reset
```bash
rm -rf .chroma_db/
python scripts/python/cli.py create-local-markets-rag ./market_data
```

---

## Next Steps

### 1. Configure API Keys
- Get OpenAI API key from https://platform.openai.com
- (Optional) Get Tavily key for web search: https://tavily.com
- (Optional) Get NewsAPI key: https://newsapi.org

### 2. Test Market Data
```bash
export PYTHONPATH="."
python scripts/python/cli.py get-all-markets --limit 3
```

### 3. Build Custom Strategy
- Modify `agents/application/executor.py` for custom prompts
- Create custom data connectors in `agents/connectors/`
- Extend `agents/application/trade.py` for trading logic

### 4. Deploy to Production
- Use Docker: `./scripts/bash/build-docker.sh`
- Use Podman: Same scripts, may need `alias docker=podman`
- Deploy to cloud: Configure environment variables in deployment

---

## Docker & Podman Setup

### Docker Build
```bash
./scripts/bash/build-docker.sh
./scripts/bash/run-docker.sh
```

### Podman Build (macOS/Linux)
```bash
# Create docker alias if needed
alias docker=podman

./scripts/bash/build-docker.sh
./scripts/bash/run-docker-dev.sh

# Check running containers
podman ps
```

### Dockerfile Details
- Base: Python 3.9 official image
- All dependencies pre-installed
- Source code copied to `/home`
- No exposed ports (add in Dockerfile as needed)

---

## Repository Structure

```
agents/                          # Main application code
├── agents/
│   ├── application/            # Executor, Trader, Creator
│   ├── connectors/             # News, RAG, Search
│   ├── polymarket/             # Gamma & CLOB APIs
│   └── utils/                  # Data models, helpers
├── scripts/
│   ├── python/                 # CLI, Server
│   └── bash/                   # Docker, install helpers
├── tests/                      # Unit tests
├── docs/                       # Examples, images
├── requirements.txt            # 170 dependencies
├── .env.example                # Configuration template
├── Dockerfile                  # Container definition
├── README.md                   # Official documentation
└── METARUNE_QUICKSTART.md     # This file
```

---

## Resources & Documentation

- **Official Docs:** [Polymarket Developer Docs](https://polymarket.com/docs)
- **CLOB API:** [py_clob_client](https://github.com/Polymarket/py-clob-client)
- **Web3.py:** [Web3.py Docs](https://web3py.readthedocs.io)
- **LangChain:** [LangChain Docs](https://docs.langchain.com)
- **FastAPI:** [FastAPI Docs](https://fastapi.tiangolo.com)
- **Polygon Chain:** [Polygon Documentation](https://polygon.technology/developers)

---

## Support & Debugging

### Enable Debug Logging
```bash
export PYTHONPATH="."
.venv/bin/python -u scripts/python/cli.py get-all-markets --limit 1 2>&1 | head -50
```

### Check Web3 Connection
```bash
python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
print(f'Connected: {w3.is_connected()}')
print(f'Chain ID: {w3.eth.chain_id}')
"
```

### Test OpenAI Connection
```bash
python -c "
import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✓ OpenAI client initialized')
"
```

---

## Success Checklist

- [x] Python 3.9 virtual environment created
- [x] 174 dependencies installed
- [x] `.env` file configured with placeholders
- [x] Core modules import successfully
- [x] CLI entry point available
- [x] REST API server available
- [ ] API keys configured (OPENAI_API_KEY, POLYGON_WALLET_PRIVATE_KEY)
- [ ] Market data fetched successfully
- [ ] RAG database built
- [ ] Custom strategy tested

---

**Setup Date:** February 6, 2026
**Python Version:** 3.9.25
**Status:** ✓ Ready for Development

For issues or questions, refer to the official [Polymarket Agents README](README.md).
