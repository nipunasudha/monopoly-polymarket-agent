# Testing Checklist - Next.js Dashboard

## Pre-Test Setup

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Browser console open for debugging
- [ ] Network tab open to monitor WebSocket

## Start Commands

### Using UV (Recommended)
```bash
cd agents
uv run dev-full
```

### Manual (Two Terminals)
```bash
# Terminal 1
cd agents && uv run dev

# Terminal 2
cd agents && uv run dev-frontend
```

## Test Cases

### 1. Initial Load
- [ ] Navigate to http://localhost:3000
- [ ] Portfolio page loads without errors
- [ ] Stats cards display (Balance, Total Value, etc.)
- [ ] No 404 errors in console
- [ ] Browser console shows: `[WebSocket] Connected`

### 2. WebSocket Connection
- [ ] Check Network tab → WS section
- [ ] WebSocket connection status is "101 Switching Protocols"
- [ ] Initial "init" message received
- [ ] Frontend console shows WebSocket logs

### 3. Agent Control Page
- [ ] Navigate to http://localhost:3000/agent
- [ ] Agent status displays correctly
- [ ] Control buttons are visible
- [ ] Statistics cards show numbers
- [ ] Activity feed is empty or shows recent activities

### 4. Start Agent
- [ ] Click "Start Agent" button
- [ ] Button changes to "Starting..." immediately
- [ ] Status badge changes to "Running" (optimistic)
- [ ] WebSocket sends `{action: 'start'}` command
- [ ] Backend responds with status update
- [ ] Next run time appears
- [ ] Statistics update

### 5. Run Once
- [ ] Click "Run Once" button
- [ ] Button shows "Running..."
- [ ] Activity feed updates when forecast/trade created
- [ ] Statistics increment
- [ ] Button returns to normal state

### 6. Stop Agent
- [ ] Click "Stop Agent" button
- [ ] Status changes to "Stopped" immediately
- [ ] Next run time disappears
- [ ] Button changes back to "Start Agent"

### 7. Real-time Updates
- [ ] With agent running, watch activity feed
- [ ] New forecasts appear automatically
- [ ] New trades appear automatically
- [ ] Timestamps update correctly
- [ ] No page refresh needed

### 8. Page Navigation
- [ ] Navigate between pages (Portfolio, Agent, Trades, Forecasts)
- [ ] WebSocket stays connected during navigation
- [ ] No duplicate connections created
- [ ] Each page loads correctly

### 9. Trades Page
- [ ] Navigate to http://localhost:3000/trades
- [ ] Trade table displays
- [ ] Shows correct columns (Market, Side, Size, Status, Created)
- [ ] Status badges are colored correctly
- [ ] Empty state shows if no trades

### 10. Forecasts Page
- [ ] Navigate to http://localhost:3000/forecasts
- [ ] Forecast cards display in grid
- [ ] Shows probability and confidence
- [ ] Shows reasoning if available
- [ ] Empty state shows if no forecasts

### 11. Reconnection
- [ ] Stop backend server
- [ ] Frontend console shows "WebSocket disconnected"
- [ ] Restart backend server
- [ ] Frontend automatically reconnects within 2 seconds
- [ ] Data loads correctly after reconnect

### 12. Hot Reload
- [ ] Edit a frontend file (e.g., change text in AgentControls.tsx)
- [ ] Save the file
- [ ] Page updates instantly without full refresh
- [ ] WebSocket connection maintained
- [ ] State preserved

### 13. Error Handling
- [ ] Stop backend
- [ ] Refresh frontend page
- [ ] Should show friendly error message
- [ ] "Try again" button works
- [ ] No crash or white screen

### 14. Multiple Tabs
- [ ] Open http://localhost:3000/agent in two browser tabs
- [ ] Click "Start Agent" in tab 1
- [ ] Both tabs update simultaneously
- [ ] Click "Stop Agent" in tab 2
- [ ] Tab 1 also updates

### 15. Performance
- [ ] Check Chrome DevTools → Performance tab
- [ ] No memory leaks
- [ ] No excessive re-renders
- [ ] WebSocket messages are efficient
- [ ] Page load time < 2 seconds

## Expected Console Output

### Frontend (Browser Console)
```
[WebSocket] Connecting to ws://localhost:8000/ws
[WebSocket] Connected
[WebSocket] Received: init
[WebSocket] Received: agent_status_changed
[WebSocket] Received: forecast_created
```

### Backend (Terminal)
```
INFO: WebSocket connected. Total connections: 1
INFO: WebSocket command received: start
INFO: Agent runner started
INFO: Broadcast agent_status_changed event: running
INFO: WebSocket connected. Total connections: 2
```

## Common Issues & Fixes

### Issue: "API error: Not Found"
**Fix**: Backend endpoint returning 404. Check that backend is running and CORS is enabled.

### Issue: WebSocket not connecting
**Fix**: 
1. Verify backend is running on port 8000
2. Check `.env.local` has correct `NEXT_PUBLIC_WS_URL`
3. Check CORS middleware is configured

### Issue: "Module not found" errors in frontend
**Fix**:
```bash
cd monopoly-dashboard
rm -rf .next node_modules
npm install
npm run dev
```

### Issue: Port already in use
**Fix**:
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

## Success Criteria

✅ All pages load without errors  
✅ WebSocket connects automatically  
✅ Agent controls work instantly  
✅ Real-time updates appear without refresh  
✅ Hot reload works on both backend and frontend  
✅ Multiple tabs stay in sync  
✅ Reconnection works after backend restart  

## Next Steps After Testing

Once all tests pass:
1. Remove old Jinja2 templates and HTMX routes
2. Deploy frontend to Vercel
3. Add more features (charts, filters, etc.)
4. Add E2E tests with Playwright
