# Realtime Updates – Adding New Fields

The dashboard uses a **single realtime state** and **one patch action**. To add a new realtime-updated field, follow the steps below.

## Architecture

- **Backend**: `_get_realtime_state()` in `agents/scripts/python/server.py` builds the object sent on WebSocket `init`. All broadcasts send full objects (e.g. full agent status).
- **Frontend**: `patchRealtime(updates)` in `stores/agentStore.ts` merges partial updates into `status`, `portfolio`, and `activities`. The WebSocket hook maps message types to `patchRealtime` / `addActivity`.

## Adding a new field to **agent** (e.g. `last_cycle_seconds`)

1. **Backend** – `agents/agents/application/runner.py`  
   In `get_status()`, add the new key, e.g.:
   ```python
   return {
       ...
       "last_cycle_seconds": self.last_cycle_seconds,
   }
   ```

2. **Frontend types** – `lib/types.ts`  
   Add to `AgentStatus`:
   ```ts
   export interface AgentStatus {
     ...
     last_cycle_seconds?: number;
   }
   ```

3. **UI** – Use it in any component:
   ```ts
   const lastCycle = useAgentStore((s) => s.status.last_cycle_seconds);
   ```

No changes to WebSocket handler or store actions: agent updates are merged by `patchRealtime({ agent: ... })`.

---

## Adding a new field to **portfolio**

1. **Backend** – Include it in the portfolio snapshot (e.g. in the DB model and in `get_latest_portfolio_snapshot()` / `.to_dict()`, or in `_get_realtime_state()` when building the default portfolio dict).

2. **Frontend types** – `lib/types.ts`  
   Add to `PortfolioSnapshot`:
   ```ts
   export interface PortfolioSnapshot {
     ...
     daily_pnl?: number;
   }
   ```

3. **UI** – Read from store:
   ```ts
   const dailyPnl = useAgentStore((s) => s.portfolio?.daily_pnl);
   ```

---

## Adding a new **top-level** realtime slice (e.g. `alerts`)

1. **Backend** – `agents/scripts/python/server.py`  
   In `_get_realtime_state()`, add the new key:
   ```python
   def _get_realtime_state():
       ...
       return {
           "agent": agent_status,
           "portfolio": portfolio_data,
           "alerts": get_recent_alerts(),  # new
       }
   ```
   When alerts change, broadcast e.g. `{"type": "alerts_updated", "data": [...]}` (and optionally send that type from the backend).

2. **Frontend types** – `lib/types.ts`  
   Add to `RealtimeState` and `RealtimeStatePatch`:
   ```ts
   export interface RealtimeState {
     agent: AgentStatus;
     portfolio: PortfolioSnapshot | null;
     activities: Activity[];
     alerts: Alert[];  // new
   }
   export type RealtimeStatePatch = {
     agent?: Partial<AgentStatus>;
     portfolio?: PortfolioSnapshot | null;
     activities?: Activity[];
     alerts?: Alert[];  // new
   };
   ```

3. **Store** – `stores/agentStore.ts`  
   - Add `alerts: []` to `initialRealtime`.
   - In `patchRealtime`, handle the new key:
   ```ts
   if (updates.alerts !== undefined) {
     next.alerts = updates.alerts;
   }
   ```

4. **WebSocket** – `lib/types.ts`  
   Add the new message type:
   ```ts
   | { type: 'alerts_updated'; data: Alert[]; timestamp: string }
   ```
   In `hooks/useWebSocket.ts`, add:
   ```ts
   case 'alerts_updated':
     patchRealtime({ alerts: message.data });
     break;
   ```

5. **UI** – Use the slice:
   ```ts
   const alerts = useAgentStore((s) => s.alerts);
   ```

---

## Summary

| Goal                         | Backend change                    | Frontend change                                      |
|-----------------------------|------------------------------------|------------------------------------------------------|
| New **agent** field         | Add to `runner.get_status()`       | Add to `AgentStatus` in types; use in component      |
| New **portfolio** field     | Add to snapshot / default dict     | Add to `PortfolioSnapshot`; use in component         |
| New **top-level** slice     | Add to `_get_realtime_state()` + broadcast | Add to `RealtimeState` / `RealtimeStatePatch`, `patchRealtime`, WS message type and handler, then use in UI |

All agent/portfolio updates flow through `patchRealtime`; new fields are preserved because we merge instead of replace.
