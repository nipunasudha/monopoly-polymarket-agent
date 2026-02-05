# Polymarket Agents - Setup Guide Index

**Status:** ✅ Setup Complete - Ready for Development

**Date:** February 6, 2026
**Location:** `/Users/nipuna/paragon/claude-projects/monopoly/agents`
**Python:** 3.9.25
**Packages:** 174 installed

---

## 📚 Documentation Files

### 1. **METARUNE_QUICKSTART.md** (Start Here!)
Complete setup guide with everything you need to know:
- Architecture overview with ASCII diagrams
- Key file locations reference table
- All 9 CLI commands with examples
- Configuration instructions
- Common issues & troubleshooting
- Testing procedures
- Next steps for custom strategies

**When to use:** First time setup, running CLI commands, understanding the system

### 2. **PODMAN_SETUP.md** (Container Deployment)
Detailed guide for running the project in containers:
- Podman installation instructions
- Docker alias option for existing scripts
- Direct Podman commands (recommended approach)
- Container management (run, logs, exec)
- Volume mounts and networking
- Podman Compose for multi-container setups
- Troubleshooting guide

**When to use:** Deploying to production, using containers, avoiding local installation issues

### 3. **SETUP_COMPLETE.txt** (Summary & Quick Reference)
High-level summary of what was completed:
- All 7 phases completed checklist
- Next immediate steps
- Quick commands reference
- Directory structure overview
- Security reminders
- Support resources

**When to use:** Quick reference, verification checklist, reminder of what's installed

### 4. **.env** (Configuration File)
Environment variables file with placeholders for:
- `POLYGON_WALLET_PRIVATE_KEY` - Wallet for trading on Polygon
- `OPENAI_API_KEY` - API key for LLM features
- `TAVILY_API_KEY` - Optional web search capability
- `NEWSAPI_API_KEY` - Optional news data source

**When to use:** After setup, configure with your actual API keys

### 5. **README.md** (Official Project Docs)
Original Polymarket agents repository documentation

---

## 🚀 Quick Start

### 1. Activate Environment
```bash
source .venv/bin/activate
export PYTHONPATH="."
```

### 2. Configure API Keys
Edit `.env` and add:
```bash
OPENAI_API_KEY="sk-..."
POLYGON_WALLET_PRIVATE_KEY="0x..."
```

### 3. Test Installation
```bash
python -c "from agents.connectors.news import News; print('✓ Works!')"
```

### 4. Run CLI Command
```bash
python scripts/python/cli.py get-all-markets --limit 5
```

---

## 📖 What's Installed

| Component | Details |
|-----------|---------|
| **Python** | 3.9.25 (via Homebrew) |
| **Virtual Env** | `.venv/` directory |
| **Packages** | 174 total dependencies |
| **Web3** | web3, eth-account, py_clob_client |
| **LLM** | openai, langchain, langgraph |
| **API** | fastapi, uvicorn |
| **Vector DB** | chromadb, chroma-hnswlib |
| **Data** | newsapi-python, tavily-python |
| **CLI** | typer, click |

---

## 🎯 Entry Points

| Purpose | File | Command |
|---------|------|---------|
| **CLI** | `scripts/python/cli.py` | `python scripts/python/cli.py --help` |
| **API Server** | `scripts/python/server.py` | `python scripts/python/server.py` |
| **Autonomous Trading** | `agents/application/trade.py` | `python scripts/python/cli.py run-autonomous-trader` |
| **Market Data** | `agents/polymarket/gamma.py` | Used internally by CLI |
| **Trading Engine** | `agents/polymarket/polymarket.py` | Used internally by trader |

---

## 🛠️ Common Tasks

### View Available CLI Commands
```bash
python scripts/python/cli.py --help
```

### Get Market Data
```bash
python scripts/python/cli.py get-all-markets --limit 5 --sort-by spread
```

### Run API Server (Development)
```bash
python scripts/python/server.py
# Access at http://localhost:8000
```

### Run in Docker/Podman
```bash
# Docker
docker build -t polymarket-agents:latest .
docker run -it -v $(pwd):/home -v $(pwd)/.env:/home/.env \
  polymarket-agents:latest python scripts/python/cli.py get-all-markets

# Podman
podman build -t polymarket-agents:latest .
podman run -it -v $(pwd):/home -v $(pwd)/.env:/home/.env \
  polymarket-agents:latest python scripts/python/cli.py get-all-markets
```

### Search News
```bash
python scripts/python/cli.py get-relevant-news "bitcoin" "ethereum"
```

### Ask Superforecaster
```bash
python scripts/python/cli.py ask-superforecaster "Bitcoin ETF" "Will pass?" "yes"
```

---

## 📋 Setup Checklist

- [x] Repository cloned from GitHub
- [x] Python 3.9 installed and configured
- [x] Virtual environment created
- [x] 174 dependencies installed
- [x] .env file created with placeholders
- [x] Core modules verified to import
- [x] CLI entry point available
- [x] API server available
- [x] Complete documentation created
- [x] Container deployment guide created
- [ ] API keys configured (your next step)
- [ ] Market data fetched (after API keys)
- [ ] Custom strategy implemented (advanced)

---

## 🔗 Resource Links

**Official Documentation:**
- [Polymarket Developers](https://polymarket.com/docs)
- [py-clob-client](https://github.com/Polymarket/py-clob-client)
- [Web3.py](https://web3py.readthedocs.io)
- [LangChain](https://docs.langchain.com)
- [FastAPI](https://fastapi.tiangolo.com)

**Get API Keys:**
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Tavily API](https://tavily.com) (optional)
- [NewsAPI](https://newsapi.org) (optional)

**Tutorials:**
- [Polymarket Market Making](https://polymarket.com/docs/market-making)
- [Web3.py Getting Started](https://web3py.readthedocs.io/en/latest/index.html)
- [LangChain Quickstart](https://python.langchain.com/docs/get_started/quickstart)

---

## ⚠️ Important Security Notes

1. **Never commit .env** - Already in `.gitignore`, but double-check
2. **Keep private keys secret** - Don't share `POLYGON_WALLET_PRIVATE_KEY`
3. **API keys are credentials** - Treat like passwords
4. **Don't fund wallet yet** - Test with read-only commands first
5. **US person restrictions** - Check Polymarket ToS for trading eligibility

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Make sure PYTHONPATH is set
export PYTHONPATH="."
```

### "Private key is needed" error
```bash
# Add to .env:
POLYGON_WALLET_PRIVATE_KEY="0x0000000000000000000000000000000000000000000000000000000000000001"
# (test key, don't fund this wallet)
```

### "OpenAI API error"
```bash
# Ensure you have a valid API key in .env
OPENAI_API_KEY="sk-your-actual-key-here"
```

### Container issues
- See **PODMAN_SETUP.md** for detailed troubleshooting
- Run `podman logs <container>` to see errors
- Try interactive mode: `podman run -it ...`

---

## 📞 Support

1. **Setup Issues** → See METARUNE_QUICKSTART.md "Common Issues" section
2. **Container Issues** → See PODMAN_SETUP.md "Troubleshooting" section
3. **API Issues** → Check Polymarket official documentation
4. **Code Questions** → Review agents/ source code with comments

---

## 🎓 Next Steps

1. **Read METARUNE_QUICKSTART.md** for complete orientation
2. **Configure your API keys** in `.env`
3. **Test a simple command** like `get-all-markets`
4. **Explore the CLI** with different commands
5. **Review the code** in `agents/` directory
6. **Build a custom strategy** using the framework

---

**Last Updated:** February 6, 2026
**Setup Status:** ✅ Complete and Ready for Use

For details, see the documentation files listed above.
