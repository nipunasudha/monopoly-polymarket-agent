#!/bin/bash

echo "🎲 Starting Monopoly Agents Stack"
echo "=================================="
echo ""

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Backend already running on port 8000"
else
    echo "🚀 Starting backend on port 8000..."
    cd agents && uv run dev &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
fi

# Check if frontend is already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Frontend already running on port 3000"
else
    echo "🚀 Starting frontend on port 3000..."
    cd monopoly-dashboard && npm run dev &
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
fi

echo ""
echo "=================================="
echo "✅ Monopoly Agents is ready!"
echo ""
echo "📊 Dashboard:  http://localhost:3000"
echo "🔌 API:        http://localhost:8000/api"
echo "🌐 WebSocket:  ws://localhost:8000/ws"
echo "📜 Old UI:     http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================="

# Wait for user interrupt
wait
