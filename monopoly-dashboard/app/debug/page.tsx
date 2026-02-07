'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { debugAPI } from '@/lib/api';
import { useAgentStore } from '@/stores/agentStore';

export default function DebugPage() {
  const router = useRouter();
  const resetStore = useAgentStore((state) => state.reset);
  const [loading, setLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleClearAll = async () => {
    if (!showConfirm) {
      setShowConfirm(true);
      return;
    }

    setLoading(true);

    try {
      const response = await debugAPI.clearAll();
      setShowConfirm(false);
      
      // Clear Zustand store
      resetStore();
      
      // Clear localStorage
      localStorage.removeItem('agent-storage');
      
      // Show success toast with details
      toast.success('Records cleared successfully', {
        description: `${response.total_deleted} records deleted (${response.forecasts_deleted} forecasts, ${response.trades_deleted} trades, ${response.portfolio_snapshots_deleted} snapshots)`,
        duration: 5000,
      });
      
      // Refresh the page to reload data
      setTimeout(() => {
        router.refresh();
      }, 1000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to clear records';
      setShowConfirm(false);
      
      // Show error toast
      toast.error('Failed to clear records', {
        description: errorMessage,
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Debug Tools</h1>
        <p className="mt-2 text-sm text-gray-600">
          Development and testing utilities
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Clear All Records</h2>
            <p className="text-sm text-gray-500 mt-1">
              Delete all forecasts, trades, and portfolio snapshots from the database
            </p>
          </div>
        </div>

        {!showConfirm ? (
          <button
            onClick={handleClearAll}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Clearing...' : 'Clear All Records'}
          </button>
        ) : (
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm font-medium text-red-800">
                ⚠️ Warning: This action cannot be undone!
              </p>
              <p className="text-sm text-red-700 mt-1">
                This will permanently delete all forecasts, trades, and portfolio snapshots.
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleClearAll}
                disabled={loading}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Clearing...' : 'Yes, Clear All'}
              </button>
              <button
                onClick={() => {
                  setShowConfirm(false);
                }}
                disabled={loading}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          <strong>Note:</strong> This page is for development and testing purposes only.
          Use with caution in production environments.
        </p>
      </div>
    </div>
  );
}
