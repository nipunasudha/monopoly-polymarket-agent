# Monopoly Agents - UV Command Reference

## 🎯 Quick Start

### Start Full Stack (Backend + Frontend)
```bash
cd agents
uv run dev-full
```

This starts:
- Backend on http://localhost:8000
- Frontend on http://localhost:3000

## 📦 All UV Commands

### Development Servers

```bash
uv run dev            # Backend only (FastAPI with hot reload)
uv run dev-frontend   # Frontend only (Next.js)
uv run dev-full       # Both backend + frontend together
```

### Production

```bash
uv run start          # Backend in production mode (no hot reload)
```

### Other Tools

```bash
uv run monopoly       # CLI commands for agents
uv run test-agents    # Run test suite
```

## 🔧 What Each Command Does

### `uv run dev`
- Starts FastAPI backend on port 8000
- Enables hot reload for Python files
- Watches `agents/` directory for changes
- Graceful shutdown on Ctrl+C (2 second timeout)

### `uv run dev-frontend`
- Auto-installs npm dependencies if needed
- Starts Next.js on port 3000
- Enables React Fast Refresh
- TypeScript type checking

### `uv run dev-full`
- Starts backend first (port 8000)
- Waits 2 seconds for backend to initialize
- Starts frontend (port 3000)
- Single Ctrl+C stops both servers
- Shows status dashboard in terminal

### `uv run start`
- Production mode for backend
- No file watching
- Optimized for deployment
- Custom SIGINT handler for clean shutdown

## 🌐 Service URLs

| Service | URL | Port |
|---------|-----|------|
| Next.js Dashboard | http://localhost:3000 | 3000 |
| FastAPI Backend | http://localhost:8000 | 8000 |
| API Endpoints | http://localhost:8000/api | 8000 |
| WebSocket | ws://localhost:8000/ws | 8000 |
| Old Dashboard | http://localhost:8000 | 8000 |

## 📚 Project Structure

```
monopoly/
├── agents/                    # Backend (Python/FastAPI)
│   ├── scripts/python/
│   │   ├── server.py         # FastAPI server
│   │   ├── frontend.py       # Frontend launcher scripts
│   │   └── cli.py            # CLI commands
│   └── pyproject.toml        # UV project config
│
└── monopoly-dashboard/        # Frontend (Next.js/TypeScript)
    ├── app/                   # Pages
    ├── components/            # React components
    ├── lib/                   # API client, types
    ├── hooks/                 # React hooks
    ├── stores/                # Zustand stores
    └── package.json
```

## 🚀 Development Workflow

### Typical Development Session

```bash
# 1. Start full stack
cd agents
uv run dev-full

# 2. Open browser
# Navigate to http://localhost:3000

# 3. Make changes
# - Edit Python files in agents/ → backend hot reloads
# - Edit TypeScript files in monopoly-dashboard/ → frontend hot reloads

# 4. Stop services
# Press Ctrl+C once (waits 2 seconds)
# Press Ctrl+C twice to force quit
```

### Working on Backend Only

```bash
cd agents
uv run dev

# Test at http://localhost:8000/api
```

### Working on Frontend Only

```bash
# Start backend first
cd agents
uv run dev

# Then in another terminal
uv run dev-frontend

# Or use npm directly
cd ../monopoly-dashboard
npm run dev
```

## ⚡ Performance Notes

- **Backend hot reload**: ~1-2 seconds
- **Frontend hot reload**: Instant (React Fast Refresh)
- **Initial backend startup**: ~3-5 seconds
- **Initial frontend startup**: ~5-10 seconds
- **WebSocket reconnection**: ~2 seconds

## 🐛 Common Issues

### "Address already in use"
```bash
# Kill process on port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

### "Frontend directory not found"
Make sure you're running commands from the `agents/` directory:
```bash
cd agents
uv run dev-frontend  # ✅ Correct
```

### "npm: command not found"
Install Node.js:
```bash
brew install node  # macOS
```

### WebSocket connection fails
1. Make sure backend starts first
2. Check CORS is enabled in `server.py`
3. Verify `.env.local` has correct URLs

## 📖 Documentation

- [QUICK_START_NEXTJS.md](QUICK_START_NEXTJS.md) - Quick start guide
- [TESTING_CHECKLIST_NEXTJS.md](TESTING_CHECKLIST_NEXTJS.md) - Testing guide
- [NEXT_MIGRATION_COMPLETE.md](NEXT_MIGRATION_COMPLETE.md) - Migration details
- [monopoly-dashboard/README.md](monopoly-dashboard/README.md) - Frontend docs

## 🎉 What You Get

✅ **One command** to start everything: `uv run dev-full`  
✅ **Hot reload** on both backend and frontend  
✅ **WebSocket** real-time updates  
✅ **TypeScript** type safety  
✅ **Modern UI** with React and Tailwind  
✅ **Clean shutdown** with Ctrl+C  

Enjoy your new development setup! 🚀
