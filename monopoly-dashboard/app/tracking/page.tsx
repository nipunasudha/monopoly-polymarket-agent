'use client';

import { useEffect, useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import { trackingAPI } from '@/lib/api';
import type { TrackedTrade, TraderStats } from '@/lib/types';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrackingSidebar } from '@/components/tracking/TrackingSidebar';
import { TraderStats as TraderStatsComponent } from '@/components/tracking/TraderStats';
import { ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function TrackingPage() {
  const [selectedAddress, setSelectedAddress] = useState<string | null>(null);
  const [trades, setTrades] = useState<TrackedTrade[]>([]);
  const [stats, setStats] = useState<TraderStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'timestamp', desc: true }, // Default sort by timestamp descending
  ]);

  useEffect(() => {
    if (!selectedAddress) {
      setTrades([]);
      setStats(null);
      setLoading(false);
      return;
    }

    // Load trades
    setLoading(true);
    setError(null);
    
    trackingAPI.getTrades(selectedAddress, 100)
      .then((trades) => {
        // Filter to only show trades from last 30 days
        const thirtyDaysAgo = Math.floor(Date.now() / 1000) - (30 * 24 * 60 * 60);
        const recentTrades = trades.filter(trade => trade.timestamp >= thirtyDaysAgo);
        
        // Sort by timestamp descending (most recent first)
        const sorted = [...recentTrades].sort((a, b) => b.timestamp - a.timestamp);
        setTrades(sorted);
      })
      .catch((err) => {
        console.error('Failed to fetch tracked trades:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch trades');
      })
      .finally(() => setLoading(false));

    // Load stats
    setStatsLoading(true);
    trackingAPI.getStats(selectedAddress)
      .then((statsData) => {
        setStats(statsData);
      })
      .catch((err) => {
        console.error('Failed to fetch trader stats:', err);
      })
      .finally(() => setStatsLoading(false));
  }, [selectedAddress]);

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const getPolymarketUrl = (slug?: string | null) => {
    if (!slug) return null;
    return `https://polymarket.com/event/${slug}`;
  };

  const formatAsset = (asset: string) => {
    return asset.length > 12 ? `${asset.slice(0, 8)}...${asset.slice(-4)}` : asset;
  };

  const columns = useMemo<ColumnDef<TrackedTrade>[]>(
    () => [
      {
        accessorKey: 'title',
        header: 'Market',
        cell: ({ row }) => (
          <div className="font-medium max-w-xs">
            <div className="line-clamp-2">{row.original.title}</div>
            {row.original.slug && (
              <a
                href={getPolymarketUrl(row.original.slug) || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary hover:underline inline-flex items-center gap-1 mt-1"
              >
                View on Polymarket
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {row.original.conditionId && (
              <div className="text-xs text-muted-foreground mt-1 font-mono">
                {formatAddress(row.original.conditionId)}
              </div>
            )}
          </div>
        ),
        enableSorting: false,
      },
      {
        accessorKey: 'outcome',
        header: 'Outcome',
        cell: ({ row }) => (
          <Badge variant="outline">{row.original.outcome}</Badge>
        ),
      },
      {
        accessorKey: 'side',
        header: 'Side',
        cell: ({ row }) => (
          <Badge variant="secondary">{row.original.side}</Badge>
        ),
      },
      {
        accessorKey: 'asset',
        header: 'Asset',
        cell: ({ row }) => (
          <span className="text-sm font-mono" title={row.original.asset}>
            {formatAsset(row.original.asset)}
          </span>
        ),
      },
      {
        accessorKey: 'size',
        header: 'Size',
        cell: ({ row }) => `$${row.original.size.toFixed(2)}`,
        sortingFn: (rowA, rowB) => rowA.original.size - rowB.original.size,
      },
      {
        accessorKey: 'price',
        header: 'Price',
        cell: ({ row }) => `$${row.original.price.toFixed(4)}`,
        sortingFn: (rowA, rowB) => rowA.original.price - rowB.original.price,
      },
      {
        accessorKey: 'timestamp',
        header: 'Time',
        cell: ({ row }) => (
          <span className="text-muted-foreground text-sm">
            {formatDate(row.original.timestamp)}
          </span>
        ),
        sortingFn: (rowA, rowB) => rowA.original.timestamp - rowB.original.timestamp,
      },
      {
        accessorKey: 'transactionHash',
        header: 'Transaction',
        cell: ({ row }) => {
          const trade = row.original;
          return trade.transactionHash ? (
            <a
              href={`https://polygonscan.com/tx/${trade.transactionHash}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary hover:underline inline-flex items-center gap-1"
            >
              {formatAddress(trade.transactionHash)}
              <ExternalLink className="h-3 w-3" />
            </a>
          ) : (
            <span className="text-xs text-muted-foreground">-</span>
          );
        },
        enableSorting: false,
      },
    ],
    []
  );

  const table = useReactTable({
    data: trades,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
  });

  return (
    <div className="flex h-[calc(100vh-8rem)] -mx-8 -my-8">
      {/* Sidebar */}
      <TrackingSidebar
        selectedAddress={selectedAddress}
        onSelectAddress={setSelectedAddress}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 min-w-0">
        {!selectedAddress ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">Select an Address</h2>
              <p className="text-muted-foreground">
                Choose an address from the sidebar to view trades and statistics
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div>
              <h2 className="text-2xl font-bold">Tracking</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Recent bets (last 30 days) for {formatAddress(selectedAddress)}
              </p>
            </div>

            {/* Trader Stats */}
            <TraderStatsComponent stats={stats} loading={statsLoading} />

            {/* Trades Table */}
            {loading ? (
              <Card>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : error ? (
              <Card>
                <CardContent className="p-6">
                  <div className="text-center py-12 text-muted-foreground">
                    <p>Error: {error}</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <div className="overflow-x-auto">
                  {table.getRowModel().rows.length === 0 ? (
                    <CardContent>
                      <div className="text-center py-12 text-muted-foreground">
                        <p>No trades found for this address</p>
                        <p className="text-xs mt-2">Showing trades from the last 30 days</p>
                      </div>
                    </CardContent>
                  ) : (
                    <>
                      <Table>
                        <TableHeader>
                          {table.getHeaderGroups().map(headerGroup => (
                            <TableRow key={headerGroup.id}>
                              {headerGroup.headers.map(header => (
                                <TableHead key={header.id}>
                                  {header.isPlaceholder ? null : (
                                    <div
                                      className={cn(
                                        "flex items-center gap-2",
                                        header.column.getCanSort() && 'cursor-pointer select-none hover:text-foreground'
                                      )}
                                      onClick={header.column.getToggleSortingHandler()}
                                    >
                                      {flexRender(header.column.columnDef.header, header.getContext())}
                                      {header.column.getCanSort() && (
                                        <span className="text-muted-foreground">
                                          {{
                                            asc: ' ↑',
                                            desc: ' ↓',
                                          }[header.column.getIsSorted() as string] ?? ' ↕'}
                                        </span>
                                      )}
                                    </div>
                                  )}
                                </TableHead>
                              ))}
                            </TableRow>
                          ))}
                        </TableHeader>
                        <TableBody>
                          {table.getRowModel().rows.map(row => (
                            <TableRow key={row.id}>
                              {row.getVisibleCells().map(cell => (
                                <TableCell key={cell.id}>
                                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      <div className="px-4 py-3 border-t">
                        <div className="text-center text-sm text-muted-foreground">
                          Showing {table.getRowModel().rows.length} trades
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}
