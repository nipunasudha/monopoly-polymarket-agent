'use client';

import { useAgentStore } from '@/stores/agentStore';
import { Card, CardContent } from '@/components/ui/card';
import { DollarSign, TrendingUp, BarChart3, Target } from 'lucide-react';
import { cn } from '@/lib/utils';

export function AgentStats() {
  const { status, portfolio } = useAgentStore();
  
  const forecastToTradeRatio = status.total_trades > 0 && status.total_forecasts > 0
    ? ((status.total_trades / status.total_forecasts) * 100).toFixed(1)
    : '0.0';
  
  const stats = [
    {
      label: 'Portfolio Value',
      value: portfolio ? `$${portfolio.total_value.toFixed(2)}` : '$0.00',
      icon: DollarSign,
      iconColor: 'text-green-600 dark:text-green-400',
    },
    {
      label: 'Total P&L',
      value: portfolio 
        ? `${portfolio.total_pnl >= 0 ? '+' : ''}$${portfolio.total_pnl.toFixed(2)}`
        : '$0.00',
      icon: TrendingUp,
      iconColor: portfolio && portfolio.total_pnl >= 0 
        ? 'text-green-600 dark:text-green-400' 
        : 'text-red-600 dark:text-red-400',
      valueColor: portfolio && portfolio.total_pnl >= 0 
        ? 'text-green-600 dark:text-green-400' 
        : portfolio && portfolio.total_pnl < 0
          ? 'text-red-600 dark:text-red-400'
          : '',
    },
    {
      label: 'Win Rate',
      value: portfolio?.win_rate 
        ? `${(portfolio.win_rate * 100).toFixed(1)}%`
        : 'N/A',
      icon: Target,
      iconColor: 'text-blue-600 dark:text-blue-400',
    },
    {
      label: 'Forecasts',
      value: status.total_forecasts || 0,
      icon: BarChart3,
      iconColor: 'text-purple-600 dark:text-purple-400',
      description: `${status.total_trades || 0} trades`,
    },
  ];
  
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.label}>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Icon className={`h-6 w-6 ${stat.iconColor}`} />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dt className="text-sm font-medium text-muted-foreground truncate">{stat.label}</dt>
                  <dd className={cn("text-lg font-semibold", stat.valueColor)}>{stat.value}</dd>
                  {stat.description && (
                    <dd className="text-xs text-muted-foreground mt-0.5">{stat.description}</dd>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
