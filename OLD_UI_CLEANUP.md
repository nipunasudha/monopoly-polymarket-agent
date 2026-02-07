# Old UI & SSE Cleanup

## Removed Components

### ✅ Backend (`agents/scripts/python/server.py`)

**Removed:**
- All HTMLResponse routes (`/`, `/markets`, `/trades`, `/forecasts`, `/agent`, `/agent/reactive`)
- All HTMX partial endpoints (`/partials/*`)
- SSE endpoint (`/api/events/stream`)
- Jinja2 templates setup
- Static file mounting (`/static`)
- Unused imports: `HTMLResponse`, `StreamingResponse`, `StaticFiles`, `Jinja2Templates`, `Request`, `Path`, `asyncio`

**Kept:**
- All `/api/*` REST endpoints (forecasts, trades, portfolio, agent status, etc.)
- WebSocket endpoint (`/ws`)
- CORS middleware for Next.js frontend

### ✅ EventBroadcaster (`agents/agents/connectors/events.py`)

**Removed:**
- SSE connection management (`_connections`, `_lock`, `_shutdown`)
- `connect()` method (SSE generator)
- `_format_sse_message()` method
- `close_all_connections()` method
- `connection_count()` method

**Kept:**
- WebSocket broadcasting via `_ws_manager`
- Event emission methods (`emit_forecast_created`, `emit_trade_executed`, etc.)
- `broadcast()` method (WebSocket only)

### ✅ Files Deleted

**Entire directory removed:**
- `/agents/dashboard/` - All old UI files:
  - `templates/*.html` - Jinja2 templates (base, agent, portfolio, markets, trades, forecasts)
  - `partials/*.html` - HTMX partials (agent-status, agent-controls, portfolio-stats, etc.)
  - `components/*.html` - Reusable components
  - `static/js/agent-store.js` - Alpine.js reactive store

## Current Architecture

### Backend
- **FastAPI** - REST API + WebSocket only
- **WebSocket** (`/ws`) - Real-time bidirectional communication
- **REST API** (`/api/*`) - JSON endpoints for Next.js frontend

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe frontend
- **Zustand** - State management with persistence
- **WebSocket** - Real-time updates via `useWebSocket` hook

## Migration Summary

| Old (HTMX/Alpine.js) | New (Next.js/WebSocket) |
|---------------------|------------------------|
| Jinja2 templates | React components |
| HTMX partials | React components |
| SSE (`/api/events/stream`) | WebSocket (`/ws`) |
| Alpine.js store | Zustand store |
| Server-rendered HTML | Client-side React |
| Static JS files | TypeScript modules |

## Benefits

1. **Simpler backend** - No template rendering, no SSE connection management
2. **Better DX** - TypeScript, hot reload, modern React patterns
3. **Unified realtime** - Single WebSocket connection instead of SSE + WebSocket
4. **Easier to extend** - Adding new realtime fields is straightforward (see `REALTIME_UPDATES.md`)
5. **Better performance** - Client-side routing, no full page reloads

## Testing

After cleanup, verify:
- ✅ Backend starts without errors
- ✅ WebSocket connects (`/ws`)
- ✅ REST API endpoints work (`/api/portfolio`, `/api/forecasts`, etc.)
- ✅ Next.js frontend loads and connects
- ✅ Real-time updates work via WebSocket

## Files Modified

1. `agents/scripts/python/server.py` - Removed ~500 lines of old UI/SSE code
2. `agents/agents/connectors/events.py` - Simplified to WebSocket only (~200 lines removed)
3. `agents/dashboard/` - Entire directory deleted (~22 HTML files + 1 JS file)

## Next Steps

The backend is now a clean API server. All UI is handled by the Next.js frontend at `monopoly-dashboard/`.
