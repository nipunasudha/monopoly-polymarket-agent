# Monopoly Dashboard - Next.js Frontend

Modern, reactive dashboard for the Monopoly Polymarket Agent System built with Next.js 15, TypeScript, and WebSocket real-time updates.

## Features

- **Real-time Updates**: WebSocket-based bidirectional communication for instant updates
- **Type-Safe**: Full TypeScript coverage with auto-completion
- **Modern Stack**: Next.js 15 App Router with React Server Components
- **Reactive State**: Zustand for lightweight, performant state management
- **Hot Reload**: Instant updates during development
- **Responsive Design**: Mobile-friendly UI with Tailwind CSS

## Tech Stack

- **Framework**: Next.js 15
- **Language**: TypeScript
- **State Management**: Zustand
- **Styling**: Tailwind CSS
- **Real-time**: Native WebSocket
- **Data Fetching**: Fetch API with custom client

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend server running on `localhost:8000`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The dashboard will be available at http://localhost:3000

### Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## Project Structure

```
monopoly-dashboard/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with navigation
│   ├── page.tsx           # Portfolio dashboard (home)
│   ├── agent/
│   │   └── page.tsx       # Agent control panel
│   ├── markets/
│   │   └── page.tsx       # Markets scanner
│   ├── trades/
│   │   └── page.tsx       # Trade history
│   └── forecasts/
│       └── page.tsx       # Forecasts view
├── components/            # React components
│   ├── agent/
│   │   ├── AgentStatus.tsx
│   │   ├── AgentControls.tsx
│   │   └── AgentStats.tsx
│   └── ActivityFeed.tsx
├── lib/
│   ├── api.ts            # API client
│   └── types.ts          # TypeScript types
├── hooks/
│   └── useWebSocket.ts   # WebSocket hook
└── stores/
    └── agentStore.ts     # Zustand store
```

## Features

### Agent Control Panel (`/agent`)

- View agent status (running, stopped, paused, error)
- Start/stop/pause/resume agent
- Run agent once manually
- View real-time statistics
- Monitor recent activity feed

### Portfolio Dashboard (`/`)

- Current balance and total value
- P&L tracking
- Open positions count
- Win rate statistics

### Trade History (`/trades`)

- All executed and simulated trades
- Filter by status
- Sort by date

### Forecasts (`/forecasts`)

- AI-generated predictions
- Probability and confidence scores
- Detailed reasoning

## WebSocket API

The dashboard connects to `ws://localhost:8000/ws` and handles the following message types:

### Received Messages

- `init` - Initial state on connection
- `agent_status_changed` - Agent state updates
- `forecast_created` - New forecast notifications
- `trade_executed` - Trade execution notifications
- `portfolio_updated` - Portfolio updates
- `pong` - Keepalive response

### Sent Commands

- `{ action: 'start' }` - Start agent
- `{ action: 'stop' }` - Stop agent
- `{ action: 'pause' }` - Pause agent
- `{ action: 'resume' }` - Resume agent
- `{ action: 'run_once' }` - Run agent once
- `{ action: 'ping' }` - Keepalive ping

## Development Workflow

1. Start the backend:
   ```bash
   cd ../agents
   uv run dev
   ```

2. Start the frontend:
   ```bash
   npm run dev
   ```

3. Open http://localhost:3000

## Building for Production

```bash
npm run build
npm start
```

## Deployment

### Vercel (Recommended)

```bash
vercel deploy
```

### Docker

```bash
docker build -t monopoly-dashboard .
docker run -p 3000:3000 monopoly-dashboard
```

## Comparison with Old Dashboard

| Feature | Old (HTMX/Alpine) | New (Next.js) |
|---------|-------------------|---------------|
| State Management | Scattered | Centralized (Zustand) |
| Updates | SSE + Manual | WebSocket (bidirectional) |
| Type Safety | None | Full TypeScript |
| Hot Reload | Template changes only | Full stack |
| Developer Experience | ⭐⭐ | ⭐⭐⭐⭐⭐ |

## License

MIT
