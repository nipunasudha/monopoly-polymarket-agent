'use client';

import { useState, useEffect } from 'react';
import { trackingAPI } from '@/lib/api';
import type { TrackedAddress } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Plus, Trash2, Eye, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TrackingSidebarProps {
  selectedAddress: string | null;
  onSelectAddress: (address: string) => void;
}

export function TrackingSidebar({ selectedAddress, onSelectAddress }: TrackingSidebarProps) {
  const [addresses, setAddresses] = useState<TrackedAddress[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newAddress, setNewAddress] = useState('');
  const [newName, setNewName] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [watchDialogOpen, setWatchDialogOpen] = useState(false);
  const [pendingWatchAddress, setPendingWatchAddress] = useState<{ address: string; currentWatched: boolean } | null>(null);

  useEffect(() => {
    loadAddresses();
  }, []);

  const loadAddresses = async () => {
    try {
      setLoading(true);
      const data = await trackingAPI.getAddresses();
      setAddresses(data);
      // Auto-select first address if none selected
      if (!selectedAddress && data.length > 0) {
        onSelectAddress(data[0].address);
      }
    } catch (err) {
      console.error('Failed to load tracked addresses:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!newAddress.trim()) return;
    
    try {
      setIsAdding(true);
      await trackingAPI.addAddress(newAddress.trim(), newName.trim() || undefined);
      setNewAddress('');
      setNewName('');
      setIsDialogOpen(false);
      await loadAddresses();
      // Select the newly added address
      onSelectAddress(newAddress.trim());
    } catch (err) {
      console.error('Failed to add address:', err);
      alert(err instanceof Error ? err.message : 'Failed to add address');
    } finally {
      setIsAdding(false);
    }
  };

  const handleDelete = async (address: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Remove ${address} from tracking?`)) return;
    
    try {
      await trackingAPI.deleteAddress(address);
      await loadAddresses();
      // If deleted address was selected, select first available or null
      if (selectedAddress === address) {
        const remaining = addresses.filter(a => a.address !== address);
        if (remaining.length > 0) {
          onSelectAddress(remaining[0].address);
        } else {
          onSelectAddress('');
        }
      }
    } catch (err) {
      console.error('Failed to delete address:', err);
      alert(err instanceof Error ? err.message : 'Failed to delete address');
    }
  };

  const handleToggleWatchedClick = (address: string, currentWatched: boolean, e: React.MouseEvent | React.ChangeEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setPendingWatchAddress({ address, currentWatched });
    setWatchDialogOpen(true);
  };

  const handleConfirmWatch = async () => {
    if (!pendingWatchAddress) return;
    
    const { address, currentWatched } = pendingWatchAddress;
    const newWatched = !currentWatched;
    
    try {
      await trackingAPI.toggleWatched(address, newWatched);
      await loadAddresses();
      setWatchDialogOpen(false);
      setPendingWatchAddress(null);
    } catch (err) {
      console.error('Failed to toggle watched status:', err);
      alert(err instanceof Error ? err.message : 'Failed to toggle watched status');
    }
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <div className="w-64 border-r bg-muted/30 flex flex-col h-full flex-shrink-0">
      <div className="p-4 border-b">
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-full" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Address
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Tracked Address</DialogTitle>
              <DialogDescription>
                Enter a wallet address to track trades and statistics.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Address</label>
                <Input
                  placeholder="0x..."
                  value={newAddress}
                  onChange={(e) => setNewAddress(e.target.value)}
                  disabled={isAdding}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Name (optional)</label>
                <Input
                  placeholder="Display name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  disabled={isAdding}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
                disabled={isAdding}
              >
                Cancel
              </Button>
              <Button onClick={handleAdd} disabled={isAdding || !newAddress.trim()}>
                {isAdding ? 'Adding...' : 'Add'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Watch Confirmation Dialog */}
      <Dialog open={watchDialogOpen} onOpenChange={setWatchDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {pendingWatchAddress && !pendingWatchAddress.currentWatched ? 'Watch Address?' : 'Stop Watching?'}
            </DialogTitle>
            <DialogDescription>
              {pendingWatchAddress && (
                <>
                  {pendingWatchAddress.currentWatched ? (
                    <>
                      Stop watching {addresses.find(a => a.address === pendingWatchAddress.address)?.name || formatAddress(pendingWatchAddress.address)}?
                      <br /><br />
                      The bot will stop following this address's trade patterns.
                    </>
                  ) : (
                    <>
                      Watch {addresses.find(a => a.address === pendingWatchAddress.address)?.name || formatAddress(pendingWatchAddress.address)}?
                      <br /><br />
                      The bot will follow this address's trade patterns to inform your bets.
                    </>
                  )}
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setWatchDialogOpen(false);
                setPendingWatchAddress(null);
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleConfirmWatch}>
              {pendingWatchAddress && pendingWatchAddress.currentWatched ? 'Stop Watching' : 'Watch'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-sm text-muted-foreground">Loading...</div>
        ) : addresses.length === 0 ? (
          <div className="p-4 text-sm text-muted-foreground text-center">
            No tracked addresses. Add one to get started.
          </div>
        ) : (
          <div className="p-1">
            {addresses.map((addr) => (
              <div
                key={addr.id}
                className={cn(
                  "w-full rounded-md transition-colors relative group cursor-pointer",
                  "hover:bg-accent/50",
                  selectedAddress === addr.address && "bg-accent"
                )}
                onClick={() => onSelectAddress(addr.address)}
              >
                <div className="p-2 flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    {addr.name ? (
                      <>
                        <div className="font-medium text-sm truncate">{addr.name}</div>
                        <div className="text-xs text-muted-foreground font-mono truncate">
                          {formatAddress(addr.address)}
                        </div>
                      </>
                    ) : (
                      <div className="text-sm font-mono truncate">{formatAddress(addr.address)}</div>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                    {addr.watched ? (
                      <Eye className="h-3.5 w-3.5 text-primary" />
                    ) : (
                      <EyeOff className="h-3.5 w-3.5 text-muted-foreground" />
                    )}
                    <div
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleWatchedClick(addr.address, addr.watched, e);
                      }}
                      className="cursor-pointer"
                    >
                      <Switch
                        checked={addr.watched}
                        onCheckedChange={(checked) => {
                          // Prevent default toggle - handled by dialog
                        }}
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                        }}
                        className="flex-shrink-0 pointer-events-none"
                        title={addr.watched ? 'Stop watching' : 'Watch'}
                      />
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(addr.address, e);
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-destructive/10 rounded"
                      title="Remove"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-destructive" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
