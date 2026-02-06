<!-- Monopoly Polymarket Agent System -->
<!-- Copyright (c) 2026 Metarune Labs Pvt Ltd. (metarunelabs.dev) -->
<!-- Forked from Polymarket/agents (MIT License) -->

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://metarunelabs.dev">
    <img src="docs/images/cli.png" alt="Logo" width="466" height="262">
  </a>

<h3 align="center">Monopoly Polymarket Agent System</h3>

  <p align="center">
    Trade autonomously on Polymarket using AI Agents
    <br />
    <em>by <a href="https://metarunelabs.dev">Metarune Labs Pvt Ltd.</a></em>
    <br />
    <br />
    <a href="https://github.com/polymarket/agents">Upstream Repo</a>
    ·
    <a href="https://metarunelabs.dev">Metarune Labs</a>
  </p>
</div>


# Monopoly Agents

Monopoly Polymarket Agent System is a developer framework and set of utilities for building AI trading agents for Polymarket, maintained by [Metarune Labs Pvt Ltd.](https://metarunelabs.dev).

Based on the open-source [Polymarket Agents](https://github.com/polymarket/agents) project (MIT License). See [terms of service](#terms-of-service).

## Features

- Integration with Polymarket API
- AI agent utilities for prediction markets
- Local and remote RAG (Retrieval-Augmented Generation) support
- Data sourcing from betting services, news providers, and web search
- Comprehensive LLM tools for prompt engineering

## Architecture

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

## Key Files

| Purpose | File Path |
|---------|-----------|
| CLI Entry Point | `scripts/python/cli.py` |
| REST API Server | `scripts/python/server.py` |
| Autonomous Trading | `agents/application/trade.py` |
| LLM Executor | `agents/application/executor.py` |
| Gamma API Client | `agents/polymarket/gamma.py` |
| Trading CLOB Client | `agents/polymarket/polymarket.py` |
| Vector RAG Database | `agents/connectors/chroma.py` |
| News Connector | `agents/connectors/news.py` |
| Web Search | `agents/connectors/search.py` |
| Data Models | `agents/utils/objects.py` |
| Tests | `tests/test.py` |

# Getting Started

This repo uses [uv](https://docs.astral.sh/uv/) for dependency management and requires Python 3.9+.

1. Clone the repository

   ```
   git clone https://github.com/{username}/monopoly-agents.git
   cd monopoly-agents
   ```

2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it:

   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Install dependencies (this also creates the `.venv` automatically):

   ```
   uv sync
   ```

4. Set up your environment variables:

   ```
   cp .env.example .env
   ```

   Edit `.env` and add your keys:

   ```
   POLYGON_WALLET_PRIVATE_KEY=""   # Required: Polygon wallet
   OPENAI_API_KEY=""               # Required: OpenAI API key
   TAVILY_API_KEY=""               # Optional: web search
   NEWSAPI_API_KEY=""              # Optional: news data
   ```

5. Load your wallet with USDC.

6. Try the CLI or go trade:

   ```
   uv run monopoly --help
   uv run monopoly run-autonomous-trader
   ```

## CLI Commands

### Market Discovery
```bash
uv run monopoly get-all-markets --limit 5 --sort-by spread
uv run monopoly get-all-events --limit 3
```

### Data & Research
```bash
uv run monopoly get-relevant-news "bitcoin" "ethereum"
uv run monopoly create-local-markets-rag ./market_data
uv run monopoly query-local-markets-rag ./vector_db "best crypto bet"
```

### AI Forecasting
```bash
uv run monopoly ask-superforecaster "Bitcoin ETF" "Will pass?" "yes"
uv run monopoly ask-llm "What's your opinion on AI?"
uv run monopoly ask-polymarket-llm "Best market opportunities today?"
```

### Trading
```bash
uv run monopoly create-market
uv run monopoly run-autonomous-trader
```

## Container Setup

### Docker

```bash
./scripts/bash/build-docker.sh
./scripts/bash/run-docker-dev.sh
```

Or manually:

```bash
docker build -t monopoly-agents:latest .
docker run -it -v $(pwd):/home -v $(pwd)/.env:/home/.env \
  monopoly-agents:latest /bin/bash
```

### Podman

Podman works as a drop-in replacement for Docker. See [PODMAN_SETUP.md](PODMAN_SETUP.md) for details.

```bash
podman build -t monopoly-agents:latest .
podman run -it -v $(pwd):/home -v $(pwd)/.env:/home/.env \
  monopoly-agents:latest /bin/bash
```

## Troubleshooting

**"Private key is needed" error** — Add a key to `.env` (use a test key for read-only testing):
```bash
POLYGON_WALLET_PRIVATE_KEY="0x0000000000000000000000000000000000000000000000000000000000000001"
```

**"OpenAI API error"** — Ensure `OPENAI_API_KEY` is set in `.env` with a valid key.

**Chromadb collection errors** — Reset the RAG database:
```bash
rm -rf .chroma_db/
uv run monopoly create-local-markets-rag ./market_data
```

## APIs

- `Chroma.py`: Chroma DB for vectorizing news sources and other API data. Developers can add their own vector database implementations.

- `Gamma.py`: `GammaMarketClient` class interfacing with the Polymarket Gamma API to fetch and parse market and event metadata.

- `Polymarket.py`: Interacts with the Polymarket API to retrieve and manage market/event data and execute orders on the Polymarket DEX.

- `Objects.py`: Pydantic data models for trades, markets, events, and related entities.

# Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Submit a pull request.

Please run pre-commit hooks before contributing:
```
uv run pre-commit install
```

# Related Repos

- [Polymarket Agents](https://github.com/polymarket/agents): Upstream project this is based on
- [py-clob-client](https://github.com/Polymarket/py-clob-client): Python client for the Polymarket CLOB
- [python-order-utils](https://github.com/Polymarket/python-order-utils): Python utilities to generate and sign orders from Polymarket's CLOB
- [Polymarket CLOB client](https://github.com/Polymarket/clob-client): Typescript client for Polymarket CLOB
- [Langchain](https://github.com/langchain-ai/langchain): Utility for building context-aware reasoning applications
- [Chroma](https://docs.trychroma.com/getting-started): AI-native open-source vector database

# Prediction Markets Reading

- Prediction Markets: Bottlenecks and the Next Major Unlocks, Mikey 0x: https://mirror.xyz/1kx.eth/jnQhA56Kx9p3RODKiGzqzHGGEODpbskivUUNdd7hwh0
- The promise and challenges of crypto + AI applications, Vitalik Buterin: https://vitalik.eth.limo/general/2024/01/30/cryptoai.html
- Superforecasting: How to Upgrade Your Company's Judgement, Schoemaker and Tetlock: https://hbr.org/2016/05/superforecasting-how-to-upgrade-your-companys-judgment

# License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.

Originally developed by [Polymarket](https://github.com/polymarket/agents). Modified and maintained by [Metarune Labs Pvt Ltd.](https://metarunelabs.dev).

# Contact

For questions or inquiries, visit [metarunelabs.dev](https://metarunelabs.dev).

# Terms of Service

[Terms of Service](https://polymarket.com/tos) prohibit US persons and persons from certain other jurisdictions from trading on Polymarket (via UI & API and including agents developed by persons in restricted jurisdictions), although data and information is viewable globally.
