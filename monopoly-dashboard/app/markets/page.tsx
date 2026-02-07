'use client';

import { useState, useEffect, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import { marketsAPI } from '@/lib/api';
import type { Market } from '@/lib/types';

export default function MarketsPage() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDryRun, setIsDryRun] = useState(false);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [daysFilter, setDaysFilter] = useState(7); // Days ahead to filter (7, 30, 90, all)
  const [showClosed, setShowClosed] = useState(false);

  useEffect(() => {
    loadMarkets();
  }, [daysFilter, showClosed]);

  const loadMarkets = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Calculate end_date_min (now) and end_date_max based on days filter
      const now = new Date();
      const end_date_min = now.toISOString();
      
      let end_date_max: string | undefined;
      if (daysFilter > 0) {
        const maxDate = new Date(now);
        maxDate.setDate(maxDate.getDate() + daysFilter);
        end_date_max = maxDate.toISOString();
      }
      
      const response = await marketsAPI.getAll({
        closed: showClosed ? undefined : false,
        end_date_min,
        end_date_max,
        limit: 100,
      });
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

  const formatSpread = (spread?: number) => {
    if (spread === undefined || spread === null) return 'N/A';
    return `${(spread * 100).toFixed(2)}%`;
  };

  const getSpreadColor = (spread?: number) => {
    if (spread === undefined || spread === null) return 'text-gray-500';
    if (spread <= 0.01) return 'text-green-600';
    if (spread <= 0.02) return 'text-yellow-600';
    return 'text-red-600';
  };

  const columns = useMemo<ColumnDef<Market>[]>(
    () => [
      {
        accessorKey: 'question',
        header: 'Market',
        cell: ({ row }) => (
          <div className="max-w-md">
            <div className="text-sm font-medium text-gray-900 line-clamp-2">
              {row.original.question}
            </div>
            {row.original.description && (
              <div className="mt-0.5 text-xs text-gray-500 line-clamp-1" title={row.original.description}>
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
                      <span className="text-xs text-gray-600">{outcome}:</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getPriceColor(price)}`}>
                        {formatPrice(price)}
                      </span>
                    </div>
                  );
                })}
              </div>
            );
          }
          return <span className="text-xs text-gray-400">N/A</span>;
        },
        enableSorting: false,
      },
      {
        accessorKey: 'volume',
        header: 'Volume',
        cell: ({ row }) => (
          <span className="text-sm text-gray-900">
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
          <span className="text-sm text-gray-900">
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
              {market.active ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                  Active
                </span>
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                  Inactive
                </span>
              )}
              {market.funded !== undefined && (
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  market.funded 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {market.funded ? 'Funded' : 'Unfunded'}
                </span>
              )}
              {market.clob_token_ids && market.clob_token_ids.length > 0 && (
                <span 
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800"
                  title={`CLOB Tokens: ${market.clob_token_ids.join(', ')}`}
                >
                  CLOB: {market.clob_token_ids.length}
                </span>
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
          <span className="text-sm text-gray-500">
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
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: (row, columnId, filterValue) => {
      const search = filterValue.toLowerCase();
      const market = row.original;
      return (
        market.question.toLowerCase().includes(search) ||
        (market.description && market.description.toLowerCase().includes(search)) ||
        (market.outcomes && market.outcomes.some(o => o.toLowerCase().includes(search)))
      );
    },
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize: 20,
      },
    },
  });

  const activeMarkets = markets.filter(m => m.active).length;
  const totalVolume = markets.reduce((sum, m) => sum + (m.volume || 0), 0);

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
    <div className="space-y-4">
      {/* Header with Compact Stats */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Market Scanner</h2>
              <p className="mt-1 text-sm text-gray-500">
                Browse and analyze prediction markets
              </p>
            </div>
            {/* Compact Stats */}
            <div className="flex items-center gap-4 ml-4 text-xs text-gray-600">
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span className="font-medium text-gray-900">{markets.length}</span>
                <span>markets</span>
              </div>
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium text-green-600">{activeMarkets}</span>
                <span>active</span>
              </div>
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium text-gray-900">{formatVolume(totalVolume)}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {isDryRun && (
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              Fixture
            </span>
          )}
          <button
            onClick={loadMarkets}
            className="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white shadow rounded-lg p-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          {/* Days Ahead Filter */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500 whitespace-nowrap">Ending within:</label>
            <select
              value={daysFilter}
              onChange={(e) => setDaysFilter(Number(e.target.value))}
              className="px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
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
            <label className="text-xs text-gray-500 whitespace-nowrap">
              <input
                type="checkbox"
                checked={showClosed}
                onChange={(e) => setShowClosed(e.target.checked)}
                className="mr-1.5 rounded"
              />
              Show closed
            </label>
          </div>

          {/* Search */}
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Search markets..."
              value={globalFilter ?? ''}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="block w-full pl-8 pr-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
            {globalFilter && (
              <button
                onClick={() => setGlobalFilter('')}
                className="absolute inset-y-0 right-0 pr-2 flex items-center"
              >
                <svg className="h-4 w-4 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Markets Table */}
      {table.getRowModel().rows.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            {globalFilter ? 'No markets match your search' : 'No Markets Available'}
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            {globalFilter ? 'Try adjusting your search query' : 'Could not fetch markets from Polymarket'}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                {table.getHeaderGroups().map(headerGroup => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map(header => (
                      <th
                        key={header.id}
                        className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        {header.isPlaceholder ? null : (
                          <div
                            className={`flex items-center gap-2 ${
                              header.column.getCanSort() ? 'cursor-pointer select-none hover:text-gray-700' : ''
                            }`}
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {header.column.getCanSort() && (
                              <span className="text-gray-400">
                                {{
                                  asc: ' ↑',
                                  desc: ' ↓',
                                }[header.column.getIsSorted() as string] ?? ' ↕'}
                              </span>
                            )}
                          </div>
                        )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {table.getRowModel().rows.map(row => (
                  <tr key={row.id} className="hover:bg-gray-50">
                    {row.getVisibleCells().map(cell => (
                      <td key={cell.id} className="px-4 py-2">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing{' '}
                  <span className="font-medium">{table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}</span>
                  {' '}to{' '}
                  <span className="font-medium">
                    {Math.min(
                      (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                      table.getFilteredRowModel().rows.length
                    )}
                  </span>
                  {' '}of{' '}
                  <span className="font-medium">{table.getFilteredRowModel().rows.length}</span>
                  {' '}results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    onClick={() => table.setPageIndex(0)}
                    disabled={!table.getCanPreviousPage()}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">First</span>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M15.707 15.707a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 010 1.414zm-6 0a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 1.414L5.414 10l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                  <button
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                    className="relative inline-flex items-center px-2 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Previous</span>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                  <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                    Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
                  </span>
                  <button
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                    className="relative inline-flex items-center px-2 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Next</span>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                  <button
                    onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                    disabled={!table.getCanNextPage()}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Last</span>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      <path fillRule="evenodd" d="M10.293 4.293a1 1 0 011.414 0l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414-1.414L14.586 10l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
