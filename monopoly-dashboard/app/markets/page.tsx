'use client';

import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import { marketsAPI } from '@/lib/api';
import type { Market } from '@/lib/types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { RotateCw, Search, X, BarChart3, CheckCircle2, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MarketsPage() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDryRun, setIsDryRun] = useState(false);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [daysFilter, setDaysFilter] = useState(7);
  const [showClosed, setShowClosed] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);
  const filterTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isLoadingRef = useRef(false); // Prevent concurrent API calls
  const offsetRef = useRef(0); // Track offset without causing re-renders
  const PAGE_SIZE = 20; // Reduced from 50 to save API quota

  // Sync ref with state
  useEffect(() => {
    offsetRef.current = offset;
  }, [offset]);

  const loadMarkets = useCallback(async (reset = false, customOffset?: number) => {
    // Prevent concurrent calls
    if (isLoadingRef.current) {
      return;
    }
    
    try {
      isLoadingRef.current = true;
      if (reset) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }
      setError(null);
      
      const currentOffset = customOffset !== undefined ? customOffset : (reset ? 0 : offsetRef.current);
      
      // Calculate end_date_min (now) and end_date_max based on days filter
      const now = new Date();
      const end_date_min = now.toISOString();
      
      let end_date_max: string | undefined;
      if (daysFilter > 0) {
        const maxDate = new Date(now);
        maxDate.setDate(maxDate.getDate() + daysFilter);
        end_date_max = maxDate.toISOString();
      }
      
      // Use server-side search if query provided, otherwise use regular listing
      const response = await marketsAPI.getAll({
        closed: showClosed ? undefined : false,
        end_date_min: globalFilter.trim().length >= 2 ? undefined : end_date_min, // Don't apply date filter when searching
        end_date_max: globalFilter.trim().length >= 2 ? undefined : end_date_max, // Don't apply date filter when searching
        limit: PAGE_SIZE,
        offset: currentOffset,
        q: globalFilter.trim().length >= 2 ? globalFilter.trim() : undefined, // Use Polymarket's powerful search API
      });
      
      if (reset) {
        setMarkets(response.markets);
        setOffset(PAGE_SIZE);
        offsetRef.current = PAGE_SIZE;
      } else {
        setMarkets(prev => [...prev, ...response.markets]);
        const newOffset = offsetRef.current + PAGE_SIZE;
        setOffset(newOffset);
        offsetRef.current = newOffset;
      }
      
      setIsDryRun(response.dry_run);
      
      // If we received fewer markets than requested, we've reached the end
      if (response.markets.length < PAGE_SIZE) {
        setHasMore(false);
      } else {
        setHasMore(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load markets');
    } finally {
      setLoading(false);
      setLoadingMore(false);
      isLoadingRef.current = false;
    }
  }, [globalFilter, daysFilter, showClosed, PAGE_SIZE]); // Removed offset from deps

  // Debounce filter changes (date/closed filters)
  useEffect(() => {
    if (filterTimeoutRef.current) {
      clearTimeout(filterTimeoutRef.current);
    }
    
    filterTimeoutRef.current = setTimeout(() => {
      if (!isLoadingRef.current) {
        setMarkets([]);
        setOffset(0);
        setHasMore(true);
        loadMarkets(true, 0);
      }
    }, 500);

    return () => {
      if (filterTimeoutRef.current) {
        clearTimeout(filterTimeoutRef.current);
      }
    };
  }, [daysFilter, showClosed]); // Removed loadMarkets from deps to prevent loops

  // Debounce search queries (longer delay to save API quota)
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Only search if query is at least 2 characters or empty (to clear search)
    // If query is 1 character, don't search yet (wait for more input) - saves API quota
    if (globalFilter.trim().length >= 2 || globalFilter.trim().length === 0) {
      searchTimeoutRef.current = setTimeout(() => {
        if (!isLoadingRef.current) {
          setMarkets([]);
          setOffset(0);
          setHasMore(true);
          loadMarkets(true, 0);
        }
      }, 800); // Longer debounce for search to save API quota
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [globalFilter]); // Removed loadMarkets from deps to prevent loops

  const loadMore = useCallback(() => {
    if (!loadingMore && !loading && hasMore && !isLoadingRef.current) {
      loadMarkets(false);
    }
  }, [loadingMore, loading, hasMore, loadMarkets]);

  // Disabled auto-scroll to save API quota - user must click "Load More"
  // Setup intersection observer for infinite scroll
  // useEffect(() => {
  //   if (observerRef.current) {
  //     observerRef.current.disconnect();
  //   }

  //   observerRef.current = new IntersectionObserver(
  //     (entries) => {
  //       if (entries[0].isIntersecting) {
  //         loadMore();
  //       }
  //     },
  //     { threshold: 0.1 }
  //   );

  //   if (loadMoreRef.current) {
  //     observerRef.current.observe(loadMoreRef.current);
  //   }

  //   return () => {
  //     if (observerRef.current) {
  //       observerRef.current.disconnect();
  //     }
  //   };
  // }, [loadMore]);

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

  const formatSpread = (spread?: number) => {
    if (spread === undefined || spread === null) return 'N/A';
    return `${(spread * 100).toFixed(2)}%`;
  };

  const getSpreadColor = (spread?: number) => {
    if (spread === undefined || spread === null) return 'text-muted-foreground';
    if (spread <= 0.01) return 'text-green-600 dark:text-green-400';
    if (spread <= 0.02) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const columns = useMemo<ColumnDef<Market>[]>(
    () => [
      {
        accessorKey: 'question',
        header: 'Market',
        cell: ({ row }) => (
          <div className="max-w-md">
            <div className="text-sm font-medium line-clamp-2">
              {row.original.question}
            </div>
            {row.original.description && (
              <div className="mt-0.5 text-xs text-muted-foreground line-clamp-1" title={row.original.description}>
                {row.original.description}
              </div>
            )}
          </div>
        ),
        enableSorting: false,
      },
      {
        accessorKey: 'outcomes',
        header: 'Outcomes',
        cell: ({ row }) => {
          const market = row.original;
          if (market.outcomes && market.outcome_prices && Array.isArray(market.outcomes) && Array.isArray(market.outcome_prices)) {
            return (
              <div className="flex flex-col gap-1">
                {market.outcomes.map((outcome, idx) => {
                  const price = market.outcome_prices[idx];
                  return (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">{outcome}:</span>
                      <span className={cn("px-2 py-0.5 rounded text-xs font-semibold", getPriceColor(price))}>
                        {formatPrice(price)}
                      </span>
                    </div>
                  );
                })}
              </div>
            );
          }
          return <span className="text-xs text-muted-foreground">N/A</span>;
        },
        enableSorting: false,
      },
      {
        accessorKey: 'volume',
        header: 'Volume',
        cell: ({ row }) => (
          <span className="text-sm">
            {row.original.volume ? formatVolume(row.original.volume) : 'N/A'}
          </span>
        ),
        sortingFn: (rowA, rowB) => {
          const volA = rowA.original.volume || 0;
          const volB = rowB.original.volume || 0;
          return volA - volB;
        },
      },
      {
        accessorKey: 'liquidity',
        header: 'Liquidity',
        cell: ({ row }) => (
          <span className="text-sm">
            {row.original.liquidity ? formatVolume(row.original.liquidity) : 'N/A'}
          </span>
        ),
        sortingFn: (rowA, rowB) => {
          const liqA = rowA.original.liquidity || 0;
          const liqB = rowB.original.liquidity || 0;
          return liqA - liqB;
        },
      },
      {
        accessorKey: 'spread',
        header: 'Spread',
        cell: ({ row }) => (
          <span className={`text-xs font-medium ${getSpreadColor(row.original.spread)}`}>
            {formatSpread(row.original.spread)}
          </span>
        ),
        sortingFn: (rowA, rowB) => {
          const spreadA = rowA.original.spread || 0;
          const spreadB = rowB.original.spread || 0;
          return spreadA - spreadB;
        },
      },
      {
        accessorKey: 'active',
        header: 'Status',
        cell: ({ row }) => {
          const market = row.original;
          return (
            <div className="flex flex-col gap-1">
              <Badge variant={market.active ? 'default' : 'secondary'}>
                {market.active ? 'Active' : 'Inactive'}
              </Badge>
              {market.funded !== undefined && (
                <Badge variant={market.funded ? 'default' : 'outline'}>
                  {market.funded ? 'Funded' : 'Unfunded'}
                </Badge>
              )}
            </div>
          );
        },
        sortingFn: (rowA, rowB) => {
          const activeA = rowA.original.active ? 1 : 0;
          const activeB = rowB.original.active ? 1 : 0;
          return activeA - activeB;
        },
      },
      {
        accessorKey: 'end',
        header: 'End Date',
        cell: ({ row }) => (
          <span className="text-sm text-muted-foreground">
            {formatDate(row.original.end)}
          </span>
        ),
        sortingFn: (rowA, rowB) => {
          const dateA = new Date(rowA.original.end).getTime();
          const dateB = new Date(rowB.original.end).getTime();
          return dateA - dateB;
        },
      },
    ],
    []
  );

  const table = useReactTable({
    data: markets,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    // No client-side filtering - search is done server-side via Polymarket's search API
    // globalFilterFn removed - all filtering happens on the server
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
  });

  const activeMarkets = markets.filter(m => m.active).length;
  const totalVolume = markets.reduce((sum, m) => sum + (m.volume || 0), 0);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96 mt-2" />
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <RotateCw className="animate-spin h-12 w-12 mx-auto text-primary" />
            <p className="mt-4 text-sm text-muted-foreground">Loading markets...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Market Scanner</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Browse and analyze prediction markets
          </p>
        </div>
        <Alert variant="destructive">
          <AlertTitle>Error Loading Markets</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={() => loadMarkets(true)}>
          <RotateCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Compact Stats */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-2xl font-bold">Market Scanner</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Browse and analyze prediction markets
              </p>
            </div>
            {/* Compact Stats */}
            <div className="flex items-center gap-4 ml-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <BarChart3 className="w-4 h-4" />
                <span className="font-medium">{markets.length}</span>
                <span>markets</span>
              </div>
              <div className="flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="font-medium text-green-600 dark:text-green-400">{activeMarkets}</span>
                <span>active</span>
              </div>
              <div className="flex items-center gap-1">
                <DollarSign className="w-4 h-4" />
                <span className="font-medium">{formatVolume(totalVolume)}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {isDryRun && (
            <Badge variant="secondary">Fixture</Badge>
          )}
          <Button
            onClick={() => loadMarkets(true)}
            variant="outline"
            size="sm"
          >
            <RotateCw className="w-3 h-3 mr-1" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="p-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {/* Days Ahead Filter */}
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium whitespace-nowrap">Ending within:</label>
              <select
                value={daysFilter}
                onChange={(e) => setDaysFilter(Number(e.target.value))}
                className="px-2 py-1.5 border border-input rounded-md text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value={7}>7 days</option>
                <option value={30}>30 days</option>
                <option value={90}>90 days</option>
                <option value={365}>1 year</option>
                <option value={0}>All time</option>
              </select>
            </div>

            {/* Show Closed Markets Toggle */}
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium whitespace-nowrap cursor-pointer flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={showClosed}
                  onChange={(e) => setShowClosed(e.target.checked)}
                  className="rounded"
                />
                Show closed
              </label>
            </div>

            {/* Search */}
            <div className="flex-1 relative">
              <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-muted-foreground" />
              </div>
              <Input
                type="text"
                placeholder="Search markets (powered by Polymarket search API)..."
                value={globalFilter ?? ''}
                onChange={(e) => setGlobalFilter(e.target.value)}
                className="pl-8 pr-8"
              />
              {globalFilter && (
                <button
                  onClick={() => setGlobalFilter('')}
                  className="absolute inset-y-0 right-0 pr-2 flex items-center"
                >
                  <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                </button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Markets Table */}
      {table.getRowModel().rows.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <BarChart3 className="mx-auto h-16 w-16 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-medium">
              {globalFilter ? 'No markets match your search' : 'No Markets Available'}
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {globalFilter ? 'Try adjusting your search query' : 'Could not fetch markets from Polymarket'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
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
          </div>

          {/* Manual Load More - No Auto-scroll to save API quota */}
          <div className="px-4 py-3 border-t">
            <div className="text-center text-sm text-muted-foreground">
              Showing {table.getFilteredRowModel().rows.length} of {markets.length} loaded markets
              {globalFilter && ` (filtered from search)`}
            </div>
            
            {/* Manual load more button */}
            {hasMore && (
              <div ref={loadMoreRef} className="py-4 text-center">
                {loadingMore ? (
                  <div className="flex items-center justify-center gap-2">
                    <RotateCw className="animate-spin h-5 w-5 text-primary" />
                    <span className="text-sm text-muted-foreground">Loading more markets...</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <Button
                      onClick={loadMore}
                      variant="outline"
                    >
                      Load {PAGE_SIZE} More Markets
                    </Button>
                    <span className="text-xs text-muted-foreground">Click to load more (saves API quota)</span>
                  </div>
                )}
              </div>
            )}
            
            {!hasMore && markets.length > 0 && (
              <div className="py-4 text-center text-sm text-muted-foreground">
                All available markets loaded ({markets.length} total)
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
