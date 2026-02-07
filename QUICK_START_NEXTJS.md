# Quick Start Guide - New Next.js Dashboard

## 🚀 Starting the Dashboard

### Using UV (Recommended)

#### Option 1: Full Stack (Backend + Frontend)
```bash
cd agents
uv run dev-full
```

#### Option 2: Separate Terminals

**Terminal 1 - Backend:**
```bash
cd agents
uv run dev
```

**Terminal 2 - Frontend:**
```bash
cd agents
uv run dev-frontend
```

### Using NPM Directly

**Terminal 1 - Backend:**
```bash
cd agents
uv run dev
```

**Terminal 2 - Frontend:**
```bash
cd monopoly-dashboard
npm run dev
```

## 🌐 Access Points

- **Dashboard (New)**: http://localhost:3000
- **API**: http://localhost:8000/api
- **WebSocket**: ws://localhost:8000/ws
- **Old Dashboard**: http://localhost:8000 (fallback)

## ✅ What to Test

1. **Navigate to http://localhost:3000**
   - Should see portfolio page with stats

2. **Go to /agent page**
   - Click "Start Agent"
   - Watch status change instantly
   - See activity feed update in real-time

3. **Check browser console**
   - Should see: `[WebSocket] Connected`
   - No errors

4. **Refresh the page**
   - WebSocket reconnects automatically
   - Data loads quickly

## 🐛 Troubleshooting

### Backend not starting
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process
kill -9 <PID>
```

### Frontend not starting
```bash
# Check if port 3000 is already in use
lsof -i :3000

# Kill existing process
kill -9 <PID>

# Or reinstall dependencies
cd monopoly-dashboard
rm -rf node_modules
npm install
```

### WebSocket not connecting
- Make sure backend is running first
- Check browser console for errors
- Verify CORS is enabled in backend
- Check `.env.local` has correct WS_URL

### API 404 Errors
- Backend should return default values for empty data
- Check backend logs for errors
- Try hitting http://localhost:8000/api/portfolio directly

## 📝 Key Features

✅ **Real-time updates** via WebSocket  
✅ **Instant UI responses** with optimistic updates  
✅ **Type-safe** with TypeScript  
✅ **Hot reload** on both backend and frontend  
✅ **Auto-reconnect** if WebSocket drops  
✅ **Better error handling** with clear messages  

## 🎨 Pages

- `/` - Portfolio dashboard
- `/agent` - Agent control panel (main page)
- `/trades` - Trade history
- `/forecasts` - Forecast predictions
- `/markets` - Markets scanner

## 💡 Tips

- Use Chrome DevTools → Network → WS to debug WebSocket messages
- Check React DevTools to inspect component state
- Backend logs show WebSocket connection count
- Frontend console shows all WebSocket events

Enjoy your new reactive dashboard! 🎉
