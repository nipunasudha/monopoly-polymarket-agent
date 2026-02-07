'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { TraderStats as TraderStatsType } from '@/lib/types';
import { DollarSign, TrendingUp, BarChart3, Calendar } from 'lucide-react';

interface TraderStatsProps {
  stats: TraderStatsType | null;
  loading: boolean;
}

export function TraderStats({ stats, loading }: TraderStatsProps) {
  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(2)}K`;
    return `$${value.toFixed(2)}`;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trader Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-8 w-24" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trader Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No statistics available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trader Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <BarChart3 className="h-4 w-4" />
              <span>Total Trades</span>
            </div>
            <div className="text-2xl font-bold">{stats.total_trades}</div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <DollarSign className="h-4 w-4" />
              <span>Total Volume</span>
            </div>
            <div className="text-2xl font-bold">{formatCurrency(stats.total_volume)}</div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <TrendingUp className="h-4 w-4" />
              <span>Avg Trade Size</span>
            </div>
            <div className="text-2xl font-bold">{formatCurrency(stats.avg_trade_size)}</div>
          </div>

          {stats.first_trade && stats.last_trade && stats.first_trade !== stats.last_trade && (
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Activity Period</span>
              </div>
              <div className="text-sm">
                <div>{formatDate(stats.first_trade)}</div>
                <div className="text-muted-foreground">to {formatDate(stats.last_trade)}</div>
              </div>
            </div>
          )}
          {stats.first_trade && stats.last_trade && stats.first_trade === stats.last_trade && (
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Last Activity</span>
              </div>
              <div className="text-sm">
                {formatDate(stats.last_trade)}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
