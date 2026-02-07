'use client';

import { useEffect, useState } from 'react';
import { portfolioAPI } from '@/lib/api';
import type { PortfolioSnapshot } from '@/lib/types';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAgentStore } from '@/stores/agentStore';

export default function HomePage() {
  const [portfolio, setPortfolio] = useState<PortfolioSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { portfolio: wsPortfolio } = useAgentStore();
  
  // Initialize WebSocket
  useWebSocket();
  
  // Fetch initial portfolio data
  useEffect(() => {
    portfolioAPI.getCurrent()
      .then(setPortfolio)
      .catch((err) => {
        console.error('Failed to fetch portfolio:', err);
        setError(err.message || 'Failed to load portfolio');
      })
      .finally(() => setLoading(false));
  }, []);
  
  // Update from WebSocket
  useEffect(() => {
    if (wsPortfolio) {
      setPortfolio(wsPortfolio);
      setError(null);
    }
  }, [wsPortfolio]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading portfolio</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
              <button 
                onClick={() => window.location.reload()} 
                className="mt-2 text-red-800 underline hover:text-red-900"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  const stats = [
    {
      label: 'Balance',
      value: `$${portfolio?.balance.toFixed(2) || '0.00'}`,
      change: portfolio?.total_pnl ? `${portfolio.total_pnl >= 0 ? '+' : ''}$${portfolio.total_pnl.toFixed(2)}` : null,
      changeType: portfolio?.total_pnl && portfolio.total_pnl >= 0 ? 'positive' : 'negative',
    },
    {
      label: 'Total Value',
      value: `$${portfolio?.total_value.toFixed(2) || '0.00'}`,
    },
    {
      label: 'Open Positions',
      value: portfolio?.open_positions || 0,
    },
    {
      label: 'Win Rate',
      value: portfolio?.win_rate ? `${(portfolio.win_rate * 100).toFixed(1)}%` : 'N/A',
    },
  ];
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Portfolio Overview</h2>
        <p className="mt-1 text-sm text-gray-500">
          Your current portfolio performance and statistics
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <dt className="text-sm font-medium text-gray-500 truncate">{stat.label}</dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900">{stat.value}</dd>
              {stat.change && (
                <dd className={`mt-1 text-sm ${stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'}`}>
                  {stat.change}
                </dd>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Portfolio Details */}
      {portfolio && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Details</h3>
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Total Trades</dt>
              <dd className="mt-1 text-sm text-gray-900">{portfolio.total_trades}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(portfolio.created_at).toLocaleString()}
              </dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
