'use client';

import { useState, useEffect } from 'react';
import { trackingAPI } from '@/lib/api';
import type { TrackedAddress } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Plus, Trash2 } from 'lucide-react';
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

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-sm text-muted-foreground">Loading...</div>
        ) : addresses.length === 0 ? (
          <div className="p-4 text-sm text-muted-foreground text-center">
            No tracked addresses. Add one to get started.
          </div>
        ) : (
          <div className="p-2">
            {addresses.map((addr) => (
              <button
                key={addr.id}
                onClick={() => onSelectAddress(addr.address)}
                className={cn(
                  "w-full text-left p-3 rounded-md mb-1 transition-colors relative group",
                  "hover:bg-accent",
                  selectedAddress === addr.address && "bg-accent"
                )}
              >
                <div className="flex items-center justify-between">
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
                  <button
                    onClick={(e) => handleDelete(addr.address, e)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-destructive/10 rounded"
                    title="Remove"
                  >
                    <Trash2 className="h-3 w-3 text-destructive" />
                  </button>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
