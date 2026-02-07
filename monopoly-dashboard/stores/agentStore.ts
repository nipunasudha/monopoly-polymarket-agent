import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AgentStatus, Activity, PortfolioSnapshot, RealtimeStatePatch, HubStatus } from '@/lib/types';

interface AgentStore {
  // Realtime state (updated via WebSocket)
  status: AgentStatus;
  portfolio: PortfolioSnapshot | null;
  activities: Activity[];
  hubStatus: HubStatus | null;
  loading: {
    starting: boolean;
    stopping: boolean;
    running: boolean;
  };

  /** Merge a partial update into realtime state. Add new slice keys here when you add new realtime fields. */
  patchRealtime: (updates: RealtimeStatePatch) => void;
  addActivity: (type: 'forecast' | 'trade', data: Activity['data']) => void;
  setLoading: (key: keyof AgentStore['loading'], value: boolean) => void;
  reset: () => void;
}

const initialRealtime = {
  status: {
    state: 'stopped' as const,
    running: false,
    last_run: null,
    next_run: null,
    interval_minutes: 60,
    run_count: 0,
    error_count: 0,
    last_error: null,
    total_forecasts: 0,
    total_trades: 0,
  },
  portfolio: null as PortfolioSnapshot | null,
  activities: [] as Activity[],
  hubStatus: null as HubStatus | null,
};

export const useAgentStore = create<AgentStore>()(
  persist(
    (set) => ({
      ...initialRealtime,
      loading: {
        starting: false,
        stopping: false,
        running: false,
      },

      patchRealtime: (updates) =>
        set((state) => {
          const next: Partial<AgentStore> = {};
          if (updates.agent !== undefined) {
            next.status = { ...state.status, ...updates.agent };
          }
          if (updates.portfolio !== undefined) {
            next.portfolio = updates.portfolio;
          }
          if (updates.activities !== undefined) {
            next.activities = updates.activities;
          }
          if (updates.hubStatus !== undefined) {
            next.hubStatus = updates.hubStatus;
          }
          return next;
        }),

      addActivity: (type, data) =>
        set((state) => ({
          activities: [
            { type, data, timestamp: new Date().toISOString() } as Activity,
            ...state.activities,
          ].slice(0, 20),
        })),

      setLoading: (key, value) =>
        set((state) => ({
          loading: { ...state.loading, [key]: value },
        })),

      reset: () =>
        set({
          ...initialRealtime,
          loading: { starting: false, stopping: false, running: false },
        }),
    }),
    {
      name: 'agent-storage', // unique name for localStorage key
      storage: createJSONStorage(() => localStorage),
      // Only persist these fields
      partialize: (state) => ({
        status: state.status,
        portfolio: state.portfolio,
        activities: state.activities,
        hubStatus: state.hubStatus,
      }),
    }
  )
);
