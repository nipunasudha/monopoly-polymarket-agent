'use client';

import { useEffect, useState } from 'react';
import { tradeAPI } from '@/lib/api';
import type { Trade } from '@/lib/types';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    tradeAPI.getRecent(50)
      .then(setTrades)
      .catch((err) => console.error('Failed to fetch trades:', err))
      .finally(() => setLoading(false));
  }, []);
  
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'executed':
        return 'secondary';
      case 'simulated':
        return 'outline';
      case 'failed':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getSideVariant = (side: string) => {
    return 'secondary';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96 mt-2" />
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Trade History</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          All executed and simulated trades
        </p>
      </div>

      <Card>
        <CardContent>
          {trades.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No trades yet
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Market</TableHead>
                    <TableHead>Outcome</TableHead>
                    <TableHead>Side</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Forecast</TableHead>
                    <TableHead>Edge</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Executed</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trades.map((trade) => (
                    <TableRow key={trade.id}>
                      <TableCell className="font-medium max-w-xs">
                        <div className="line-clamp-2">{trade.market_question}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{trade.outcome}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getSideVariant(trade.side)}>
                          {trade.side}
                        </Badge>
                      </TableCell>
                      <TableCell>${trade.size.toFixed(2)}</TableCell>
                      <TableCell>
                        {trade.price !== null ? `$${trade.price.toFixed(4)}` : '-'}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {(trade.forecast_probability * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        {trade.edge !== null ? (
                          <span className={trade.edge > 0 ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground'}>
                            {trade.edge > 0 ? '+' : ''}{(trade.edge * 100).toFixed(2)}%
                          </span>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(trade.status)}>
                          {trade.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {new Date(trade.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {trade.executed_at 
                          ? new Date(trade.executed_at).toLocaleString() 
                          : trade.status === 'simulated' 
                            ? 'Simulated' 
                            : trade.status === 'pending'
                              ? 'Pending'
                              : trade.status === 'failed'
                                ? 'Failed'
                                : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
