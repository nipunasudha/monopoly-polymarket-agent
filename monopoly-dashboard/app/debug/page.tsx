'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { debugAPI } from '@/lib/api';
import { useAgentStore } from '@/stores/agentStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

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
        <h1 className="text-3xl font-bold">Debug Tools</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Development and testing utilities
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Clear All Records</CardTitle>
          <CardDescription>
            Delete all forecasts, trades, and portfolio snapshots from the database
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!showConfirm ? (
            <Button
              onClick={handleClearAll}
              disabled={loading}
              variant="destructive"
            >
              {loading ? 'Clearing...' : 'Clear All Records'}
            </Button>
          ) : (
            <div className="space-y-4">
              <Alert variant="destructive">
                <AlertTitle>⚠️ Warning: This action cannot be undone!</AlertTitle>
                <AlertDescription>
                  This will permanently delete all forecasts, trades, and portfolio snapshots.
                </AlertDescription>
              </Alert>
              <div className="flex gap-3">
                <Button
                  onClick={handleClearAll}
                  disabled={loading}
                  variant="destructive"
                >
                  {loading ? 'Clearing...' : 'Yes, Clear All'}
                </Button>
                <Button
                  onClick={() => {
                    setShowConfirm(false);
                  }}
                  disabled={loading}
                  variant="outline"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Alert>
        <AlertTitle>Note</AlertTitle>
        <AlertDescription>
          This page is for development and testing purposes only.
          Use with caution in production environments.
        </AlertDescription>
      </Alert>
    </div>
  );
}
