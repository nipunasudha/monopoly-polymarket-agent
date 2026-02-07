import { create } from 'zustand';
import type { AgentStatus, Activity, PortfolioSnapshot } from '@/lib/types';

interface AgentStore {
  // State
  status: AgentStatus;
  portfolio: PortfolioSnapshot | null;
  activities: Activity[];
  loading: {
    starting: boolean;
    stopping: boolean;
    running: boolean;
  };
  
  // Actions
  setAgentStatus: (status: AgentStatus) => void;
  setPortfolio: (portfolio: PortfolioSnapshot | null) => void;
  addActivity: (type: 'forecast' | 'trade', data: any) => void;
  setLoading: (key: keyof AgentStore['loading'], value: boolean) => void;
  reset: () => void;
}

const initialState = {
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
  portfolio: null,
  activities: [],
  loading: {
    starting: false,
    stopping: false,
    running: false,
  },
};

export const useAgentStore = create<AgentStore>((set) => ({
  ...initialState,
  
  setAgentStatus: (status) => 
    set({ status }),
  
  setPortfolio: (portfolio) => 
    set({ portfolio }),
  
  addActivity: (type, data) => 
    set((state) => ({
      activities: [
        { type, data, timestamp: new Date().toISOString() },
        ...state.activities
      ].slice(0, 20) // Keep only last 20 activities
    })),
  
  setLoading: (key, value) => 
    set((state) => ({
      loading: { ...state.loading, [key]: value }
    })),
  
  reset: () => 
    set(initialState),
}));
