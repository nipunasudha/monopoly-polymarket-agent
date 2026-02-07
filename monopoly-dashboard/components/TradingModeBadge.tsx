'use client';

import { useAgentStore } from '@/stores/agentStore';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export function TradingModeBadge() {
  const { status } = useAgentStore();
  const tradingMode = status.trading_mode || 'dry_run';
  
  const tradingModeLabels = {
    dry_run: 'Dry Run',
    live: 'Live Mode',
  };
  
  return (
    <Badge 
      variant="secondary"
      className="gap-2"
    >
      <span className={cn(
        "h-2 w-2 rounded-full",
        tradingMode === 'live' ? 'bg-red-500' : 'bg-yellow-500'
      )} />
      {tradingModeLabels[tradingMode]}
    </Badge>
  );
}
