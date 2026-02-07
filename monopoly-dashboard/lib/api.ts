/**
 * API client for FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      console.error(`API Error [${response.status}] ${endpoint}:`, errorText);
      throw new APIError(response.status, `API error: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    console.error(`Network error for ${endpoint}:`, error);
    throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// Agent API
export const agentAPI = {
  getStatus: () => 
    fetchAPI<import('@/lib/types').AgentStatus>('/api/agent/status'),
  
  start: () => 
    fetchAPI('/api/agent/start', { method: 'POST' }),
  
  stop: () => 
    fetchAPI('/api/agent/stop', { method: 'POST' }),
  
  pause: () => 
    fetchAPI('/api/agent/pause', { method: 'POST' }),
  
  resume: () => 
    fetchAPI('/api/agent/resume', { method: 'POST' }),
  
  runOnce: () => 
    fetchAPI<import('@/lib/types').AgentRunResult>('/api/agent/run-once', { method: 'POST' }),
  
  updateInterval: (interval_minutes: number) => 
    fetchAPI('/api/agent/interval', {
      method: 'POST',
      body: JSON.stringify({ interval_minutes }),
    }),
};

// Portfolio API
export const portfolioAPI = {
  getCurrent: () => 
    fetchAPI<import('@/lib/types').PortfolioSnapshot>('/api/portfolio'),
  
  getHistory: (limit = 30) => 
    fetchAPI<import('@/lib/types').PortfolioSnapshot[]>(`/api/portfolio/history?limit=${limit}`),
  
  syncBalance: () => 
    fetchAPI('/api/sync/balance', { method: 'POST' }),
};

// Forecast API
export const forecastAPI = {
  getRecent: (limit = 10) => 
    fetchAPI<import('@/lib/types').Forecast[]>(`/api/forecasts?limit=${limit}`),
  
  getById: (id: number) => 
    fetchAPI<import('@/lib/types').Forecast>(`/api/forecasts/${id}`),
  
  getByMarket: (marketId: string) => 
    fetchAPI<import('@/lib/types').Forecast[]>(`/api/markets/${marketId}/forecasts`),
};

// Trade API
export const tradeAPI = {
  getRecent: (limit = 10) => 
    fetchAPI<import('@/lib/types').Trade[]>(`/api/trades?limit=${limit}`),
  
  getById: (id: number) => 
    fetchAPI<import('@/lib/types').Trade>(`/api/trades/${id}`),
};

// Market API
export const marketAPI = {
  syncMarkets: () => 
    fetchAPI('/api/sync/markets', { method: 'POST' }),
};

// Markets API
export const marketsAPI = {
  getAll: () =>
    fetchAPI<import('@/lib/types').MarketsResponse>('/api/markets'),
};

// Health check
export const healthAPI = {
  check: () => 
    fetchAPI<{ status: string; timestamp: string }>('/health'),
};
