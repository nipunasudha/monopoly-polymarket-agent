'use client';

import { useAgentStore } from '@/stores/agentStore';

export function TradingModeBadge() {
  const { status } = useAgentStore();
  const tradingMode = status.trading_mode || 'dry_run';
  
  const tradingModeColors = {
    dry_run: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    live: 'bg-red-100 text-red-800 border-red-200',
  };
  const tradingModeLabels = {
    dry_run: 'Dry Run',
    live: 'Live Trading',
  };
  
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${tradingModeColors[tradingMode]}`}>
      <span className={`w-2 h-2 mr-2 rounded-full ${tradingMode === 'live' ? 'bg-red-500' : 'bg-yellow-500'}`}></span>
      {tradingModeLabels[tradingMode]}
    </span>
  );
}
