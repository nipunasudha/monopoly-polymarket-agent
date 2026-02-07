/**
 * TypeScript types matching FastAPI Pydantic models
 */

export interface AgentStatus {
  state: 'stopped' | 'running' | 'paused' | 'error';
  running: boolean;
  last_run: string | null;
  next_run: string | null;
  interval_minutes: number;
  run_count: number;
  error_count: number;
  last_error: string | null;
  total_forecasts?: number;
  total_trades?: number;
  trading_mode?: 'dry_run' | 'live';
}

export interface Forecast {
  id: number;
  market_id: string;
  market_question: string;
  outcome: string;
  probability: number;
  confidence: number;
  base_rate: number | null;
  reasoning: string | null;
  evidence_for: string | null;
  evidence_against: string | null;
  key_factors: string | null;
  created_at: string;
}

export interface Trade {
  id: number;
  market_id: string;
  market_question: string;
  outcome: string;
  side: 'BUY' | 'SELL';
  size: number;
  price: number | null;
  forecast_probability: number;
  edge: number | null;
  status: 'pending' | 'executed' | 'failed' | 'simulated';
  execution_enabled: boolean;
  error_message: string | null;
  transaction_hash: string | null;
  created_at: string;
  executed_at: string | null;
}

export interface PortfolioSnapshot {
  id: number;
  balance: number;
  total_value: number;
  open_positions: number;
  total_pnl: number;
  win_rate: number | null;
  total_trades: number;
  created_at: string;
}

export interface Market {
  id: string;
  question: string;
  end: string;
  active: boolean;
  outcomes: string[];
  outcome_prices: string[];
  description?: string;
  volume?: number;
  liquidity?: number;
  spread?: number;
  funded?: boolean;
  clob_token_ids?: string[];
}

export interface MarketsResponse {
  markets: Market[];
  dry_run: boolean;
  error?: string;
}

export interface Activity {
  type: 'forecast' | 'trade';
  data: Forecast | Trade;
  timestamp: string;
}

/** All realtime-updated UI state. Add new fields here and in patchRealtime to support them. */
export interface RealtimeState {
  agent: AgentStatus;
  portfolio: PortfolioSnapshot | null;
  activities: Activity[];
}

/** Partial update for realtime state. Omitted keys are left unchanged. */
export type RealtimeStatePatch = {
  agent?: Partial<AgentStatus>;
  portfolio?: PortfolioSnapshot | null;
  activities?: Activity[];
};

// WebSocket message types
export type WSMessage = 
  | { type: 'init'; data: { agent: AgentStatus; portfolio: PortfolioSnapshot | null } }
  | { type: 'agent_status_changed'; data: AgentStatus; timestamp: string }
  | { type: 'forecast_created'; data: Forecast; timestamp: string }
  | { type: 'trade_executed'; data: Trade; timestamp: string }
  | { type: 'portfolio_updated'; data: PortfolioSnapshot; timestamp: string }
  | { type: 'data_cleared'; data: { forecasts_deleted: number; trades_deleted: number; portfolio_snapshots_deleted: number; total_deleted: number }; timestamp: string }
  | { type: 'pong'; timestamp: string };

export type WSCommand = 
  | { action: 'start' }
  | { action: 'stop' }
  | { action: 'pause' }
  | { action: 'resume' }
  | { action: 'run_once' }
  | { action: 'ping' };

// API Response types
export interface APIResponse<T> {
  data?: T;
  error?: string;
}

export interface AgentRunResult {
  success: boolean;
  started_at: string;
  completed_at: string;
  error: string | null;
}

export interface NewsSource {
  id: string | null;
  name: string | null;
}

export interface NewsArticle {
  source: NewsSource | null;
  author: string | null;
  title: string | null;
  description: string | null;
  url: string | null;
  urlToImage: string | null;
  publishedAt: string | null;
  content: string | null;
}

export interface NewsSearchResponse {
  articles: NewsArticle[];
  count: number;
  keywords: string;
  dry_run?: boolean;
}
