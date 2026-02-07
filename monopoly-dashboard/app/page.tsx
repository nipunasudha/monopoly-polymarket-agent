'use client';

import { useEffect, useState } from 'react';
import { portfolioAPI } from '@/lib/api';
import { useAgentStore } from '@/stores/agentStore';

export default function HomePage() {
  const portfolio = useAgentStore((state) => state.portfolio);
  const patchRealtime = useAgentStore((state) => state.patchRealtime);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!portfolio) {
      setLoading(true);
      portfolioAPI.getCurrent()
        .then((data) => {
          patchRealtime({ portfolio: data });
        })
        .catch((err) => console.error('[Portfolio] Failed to fetch:', err))
        .finally(() => setLoading(false));
    }
  }, [portfolio, patchRealtime]);
  
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
  
  if (loading || !portfolio) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }
  
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
    </div>
  );
}
