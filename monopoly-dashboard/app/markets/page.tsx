'use client';

import { useState, useEffect } from 'react';
import { marketsAPI } from '@/lib/api';
import type { Market } from '@/lib/types';

export default function MarketsPage() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDryRun, setIsDryRun] = useState(false);

  useEffect(() => {
    loadMarkets();
  }, []);

  const loadMarkets = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await marketsAPI.getAll();
      setMarkets(response.markets);
      setIsDryRun(response.dry_run);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load markets');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: string) => {
    const num = parseFloat(price);
    return `${(num * 100).toFixed(1)}%`;
  };

  const formatVolume = (volume?: number) => {
    if (!volume) return 'N/A';
    if (volume >= 1000000) return `$${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `$${(volume / 1000).toFixed(0)}K`;
    return `$${volume.toFixed(0)}`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  const getPriceColor = (price: string) => {
    const num = parseFloat(price);
    if (num >= 0.7) return 'text-green-600 bg-green-50';
    if (num >= 0.5) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Market Scanner</h2>
          <p className="mt-1 text-sm text-gray-500">
            Browse and analyze prediction markets
          </p>
        </div>
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Loading markets...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Market Scanner</h2>
          <p className="mt-1 text-sm text-gray-500">
            Browse and analyze prediction markets
          </p>
        </div>
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">Error Loading Markets</h3>
          <p className="mt-2 text-sm text-gray-500">{error}</p>
          <button
            onClick={loadMarkets}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Market Scanner</h2>
          <p className="mt-1 text-sm text-gray-500">
            Browse and analyze prediction markets
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {isDryRun && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              Fixture Data
            </span>
          )}
          <button
            onClick={loadMarkets}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-6">
            <div>
              <span className="text-gray-500">Total Markets:</span>
              <span className="ml-2 font-semibold text-gray-900">{markets.length}</span>
            </div>
            <div>
              <span className="text-gray-500">Active:</span>
              <span className="ml-2 font-semibold text-green-600">
                {markets.filter(m => m.active).length}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Total Volume:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {formatVolume(markets.reduce((sum, m) => sum + (m.volume || 0), 0))}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Markets List */}
      {markets.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No Markets Available</h3>
          <p className="mt-2 text-sm text-gray-500">
            Could not fetch markets from Polymarket
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {markets.map((market) => (
            <div
              key={market.id}
              className="bg-white shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
            >
              <div className="px-6 py-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900 leading-tight">
                      {market.question}
                    </h3>
                    <div className="mt-2 flex items-center flex-wrap gap-3 text-sm text-gray-500">
                      <span className="truncate max-w-xs" title={market.id}>
                        ID: #{market.id.slice(0, 8)}...
                      </span>
                      <span>•</span>
                      <span>Ends: {formatDate(market.end)}</span>
                      <span>•</span>
                      {market.active ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          Inactive
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Description */}
                {market.description && (
                  <div className="mt-3">
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {market.description}
                    </p>
                  </div>
                )}

                {/* Outcomes */}
                {market.outcomes && market.outcome_prices && (
                  <div className="mt-4 border-t border-gray-200 pt-4">
                    <div className="grid grid-cols-2 gap-4">
                      {market.outcomes.map((outcome, idx) => {
                        const price = market.outcome_prices[idx];
                        return (
                          <div key={idx} className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-700">
                              {outcome}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getPriceColor(price)}`}>
                              {formatPrice(price)}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Market Stats */}
                {(market.volume || market.liquidity) && (
                  <div className="mt-4 flex items-center space-x-6 text-sm">
                    {market.volume && (
                      <div>
                        <span className="text-gray-500">Volume:</span>
                        <span className="ml-1.5 font-medium text-gray-900">
                          {formatVolume(market.volume)}
                        </span>
                      </div>
                    )}
                    {market.liquidity && (
                      <div>
                        <span className="text-gray-500">Liquidity:</span>
                        <span className="ml-1.5 font-medium text-gray-900">
                          {formatVolume(market.liquidity)}
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
