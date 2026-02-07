'use client';

import { useEffect, useState } from 'react';
import { trackingAPI } from '@/lib/api';
import type { TrackedTrade } from '@/lib/types';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TrackedAddress {
  name: string;
  portfolioValue: string;
  address: string;
}

const TRACKED_ADDRESSES: TrackedAddress[] = [
  { name: 'Theo4', portfolioValue: '$22,053,934', address: '0x56687bf447db6ffa42ffe2204a05edaa20f55839' },
  { name: 'Fredi9999', portfolioValue: '$16,619,507', address: '0x1f2dd6d473f3e824cd2f8a89d9c69fb96f6ad0cf' },
  { name: 'Len9311238', portfolioValue: '$8,709,973', address: '0x78b9ac44a6d7d7a076c14e0ad518b301b63c6b76' },
  { name: 'ascetic0x', portfolioValue: '$101,714.39', address: '0xfcbecc7e5186e88e03445b81f593685d62828f44' },
  { name: 'kch123', portfolioValue: '$9,294,989.00', address: '0x6a72f61820b26b1fe4d956e17b6dc2a1ea3033ee' },
  { name: 'zxgngl', portfolioValue: '$7,807,265.50', address: '0xd235973291b2b75ff4070e9c0b01728c520b0f29' },
  { name: 'Account88888', portfolioValue: '$645,489.60', address: '0x7f69983eb28245bba0d5083502a78744a8f66162' },
  { name: 'anoin123', portfolioValue: '$1,436,375.40', address: '0x96489abcb9f583d6835c8ef95ffc923d05a86825' },
  { name: 'BWArmageddon', portfolioValue: '$591,830.75', address: '0x9976874011b081e1e408444c579f48aa5b5967da' },
  { name: 'MrSparklySimpsons', portfolioValue: '$1,286,997.10', address: '0xd0b4c4c020abdc88ad9a884f999f3d8cff8ffed6' },
  { name: 'TheGuru', portfolioValue: '$18,138.90', address: '0xb5d2f38cdb5b71816dc4fdf5eb676a3b230d317b' },
];

export default function TrackingPage() {
  const [selectedAddress, setSelectedAddress] = useState<string>(TRACKED_ADDRESSES[0].address);
  const [trades, setTrades] = useState<TrackedTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedAddress) return;
    
    setLoading(true);
    setError(null);
    
    trackingAPI.getTrades(selectedAddress, 100) // Fetch more to filter recent ones
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

  const selectedAddressInfo = TRACKED_ADDRESSES.find(addr => addr.address === selectedAddress);

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

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Tracking</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Recent bets (last 30 days) for tracked wallets
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">Select Wallet</label>
              <Select value={selectedAddress} onValueChange={setSelectedAddress}>
                <SelectTrigger className="w-[320px]">
                  <SelectValue placeholder="Select a wallet">
                    {selectedAddressInfo && (
                      <span>
                        {selectedAddressInfo.name} • {selectedAddressInfo.portfolioValue}
                      </span>
                    )}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {TRACKED_ADDRESSES.map((addr) => (
                    <SelectItem key={addr.address} value={addr.address}>
                      <div className="flex items-center justify-between w-full gap-4">
                        <span className="font-medium">{addr.name}</span>
                        <span className="text-muted-foreground text-sm">{addr.portfolioValue}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="text-center py-12 text-muted-foreground">
              <p>Error: {error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Tracking</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Recent bets (last 30 days) for tracked wallets
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium">Select Wallet</label>
            <Select value={selectedAddress} onValueChange={setSelectedAddress}>
              <SelectTrigger className="w-[320px]">
                <SelectValue placeholder="Select a wallet">
                  {selectedAddressInfo && (
                    <span>
                      {selectedAddressInfo.name} • {selectedAddressInfo.portfolioValue}
                    </span>
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {TRACKED_ADDRESSES.map((addr) => (
                  <SelectItem key={addr.address} value={addr.address}>
                    <div className="flex items-center justify-between w-full gap-4">
                      <span className="font-medium">{addr.name}</span>
                      <span className="text-muted-foreground text-sm">{addr.portfolioValue}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <Card>
        <CardContent>
          {trades.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No trades found for this address
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
                    <TableHead>Time</TableHead>
                    <TableHead>Transaction</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trades.map((trade, index) => (
                    <TableRow key={`${trade.transactionHash}-${index}`}>
                      <TableCell className="font-medium max-w-xs">
                        <div className="line-clamp-2">{trade.title}</div>
                        {trade.slug && (
                          <a
                            href={getPolymarketUrl(trade.slug) || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-primary hover:underline inline-flex items-center gap-1 mt-1"
                          >
                            View on Polymarket
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{trade.outcome}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{trade.side}</Badge>
                      </TableCell>
                      <TableCell>${trade.size.toFixed(2)}</TableCell>
                      <TableCell>${trade.price.toFixed(4)}</TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {formatDate(trade.timestamp)}
                      </TableCell>
                      <TableCell>
                        {trade.transactionHash ? (
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
                        )}
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
