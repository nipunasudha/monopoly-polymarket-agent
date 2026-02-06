# Background Agent Runner Demo

Quick demo of the new async background agent runner (Phase 2.4).

## Start the Server

```bash
cd agents
uv run uvicorn scripts.python.server:app --reload
```

Server starts at `http://localhost:8000`

## Check Agent Status

```bash
curl http://localhost:8000/api/agent/status | jq
```

Expected output:
```json
{
  "state": "stopped",
  "running": false,
  "last_run": null,
  "next_run": null,
  "interval_minutes": 60,
  "run_count": 0,
  "error_count": 0,
  "last_error": null,
  "total_forecasts": 0,
  "total_trades": 0
}
```

## Start the Agent

```bash
curl -X POST http://localhost:8000/api/agent/start | jq
```

Expected output:
```json
{
  "status": "started",
  "message": "Agent started with 60 minute interval",
  "next_run": "2026-02-07T01:00:00.123456"
}
```

## Check Status Again

```bash
curl http://localhost:8000/api/agent/status | jq
```

Now you'll see:
```json
{
  "state": "running",
  "running": true,
  "last_run": null,
  "next_run": "2026-02-07T01:00:00.123456",
  "interval_minutes": 60,
  "run_count": 0,
  "error_count": 0,
  "last_error": null,
  "total_forecasts": 0,
  "total_trades": 0
}
```

## Update the Interval

Change from 60 minutes to 30 minutes:

```bash
curl -X PUT http://localhost:8000/api/agent/interval \
  -H "Content-Type: application/json" \
  -d '{"interval_minutes": 30}' | jq
```

Expected output:
```json
{
  "status": "updated",
  "interval_minutes": 30,
  "message": "Interval updated to 30 minutes"
}
```

## Manually Trigger a Run

Run the agent immediately without waiting for the interval:

```bash
curl -X POST http://localhost:8000/api/agent/run-once | jq
```

Expected output:
```json
{
  "success": true,
  "started_at": "2026-02-07T00:30:00.123456",
  "completed_at": "2026-02-07T00:30:15.789012",
  "error": null
}
```

After this, check status again to see `run_count` incremented:

```bash
curl http://localhost:8000/api/agent/status | jq
```

## Pause the Agent

Temporarily pause without stopping:

```bash
curl -X POST http://localhost:8000/api/agent/pause | jq
```

Expected output:
```json
{
  "status": "paused",
  "message": "Agent paused"
}
```

## Resume the Agent

Resume from paused state:

```bash
curl -X POST http://localhost:8000/api/agent/resume | jq
```

Expected output:
```json
{
  "status": "resumed",
  "message": "Agent resumed"
}
```

## Stop the Agent

Completely stop the background runner:

```bash
curl -X POST http://localhost:8000/api/agent/stop | jq
```

Expected output:
```json
{
  "status": "stopped",
  "message": "Agent stopped successfully"
}
```

## View in Dashboard

The agent status is also visible in the web dashboard:

1. Open `http://localhost:8000` in your browser
2. Navigate to the Portfolio page
3. The agent status is displayed at the top

## Error Handling

If an error occurs during a run, it's tracked:

```bash
curl http://localhost:8000/api/agent/status | jq
```

```json
{
  "state": "running",
  "running": true,
  "last_run": "2026-02-07T00:45:00.123456",
  "next_run": "2026-02-07T01:15:00.123456",
  "interval_minutes": 30,
  "run_count": 2,
  "error_count": 1,
  "last_error": "Insufficient balance for trade",
  "total_forecasts": 2,
  "total_trades": 1
}
```

## Testing the Runner

Run the comprehensive test suite:

```bash
cd agents
uv run test-agents tests/integration/test_runner.py -v
```

All 22 tests should pass:
- Initialization tests
- Status tests
- Cycle execution tests
- Lifecycle tests (start/stop)
- Pause/resume tests
- Configuration tests
- Loop tests
- Error handling tests

## Key Features

✅ **Async-First**: Integrates with FastAPI's event loop  
✅ **Configurable**: Adjustable intervals via API  
✅ **Controllable**: Start, stop, pause, resume  
✅ **Observable**: Rich status and metrics  
✅ **Reliable**: Graceful error handling  
✅ **Testable**: 22 comprehensive tests

## Safety Notes

- Agent does NOT start automatically on server startup
- Default mode is `dry_run` (no real trades)
- Set `TRADING_MODE=live` in `.env` to enable real trading
- Always test with dry run first!

## Next Steps

- See `tests/PHASE2_4_SUMMARY.md` for implementation details
- See `UPGRADE.md` for Phase 3 roadmap (Multi-Agent Architecture)
- See `TESTING_QUICKSTART.md` for full test suite guide
