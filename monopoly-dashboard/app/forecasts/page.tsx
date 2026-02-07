'use client';

import { useEffect, useState } from 'react';
import { forecastAPI } from '@/lib/api';
import type { Forecast } from '@/lib/types';

export default function ForecastsPage() {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    forecastAPI.getRecent(50)
      .then(setForecasts)
      .catch((err) => console.error('Failed to fetch forecasts:', err))
      .finally(() => setLoading(false));
  }, []);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Forecasts</h2>
        <p className="mt-1 text-sm text-gray-500">
          AI-generated market predictions
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {forecasts.map((forecast) => (
          <div key={forecast.id} className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {forecast.market_question}
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Outcome:</span>
                <span className="text-sm font-medium text-gray-900">{forecast.outcome}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Probability:</span>
                <span className="text-sm font-medium text-gray-900">
                  {(forecast.probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Confidence:</span>
                <span className="text-sm font-medium text-gray-900">
                  {(forecast.confidence * 100).toFixed(1)}%
                </span>
              </div>
              {forecast.reasoning && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-600">Reasoning:</p>
                  <p className="text-sm text-gray-900 mt-1">{forecast.reasoning}</p>
                </div>
              )}
              <div className="mt-2 text-xs text-gray-500">
                Created: {new Date(forecast.created_at).toLocaleString()}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {forecasts.length === 0 && (
        <div className="bg-white shadow rounded-lg p-12 text-center text-gray-500">
          No forecasts yet
        </div>
      )}
    </div>
  );
}
