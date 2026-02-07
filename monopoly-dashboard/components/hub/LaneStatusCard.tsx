'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LaneStatus } from '@/lib/types';
import { Activity, Brain, Eye, Clock } from 'lucide-react';

interface LaneStatusCardProps {
  name: string;
  status: LaneStatus | undefined;
}

const laneConfig = {
  MAIN: { 
    icon: Activity, 
    color: 'text-blue-600 dark:text-blue-400',
    description: 'Trading decisions (sequential)'
  },
  RESEARCH: { 
    icon: Brain, 
    color: 'text-purple-600 dark:text-purple-400',
    description: 'Background research (parallel)'
  },
  MONITOR: { 
    icon: Eye, 
    color: 'text-green-600 dark:text-green-400',
    description: 'Position monitoring (parallel)'
  },
  CRON: { 
    icon: Clock, 
    color: 'text-orange-600 dark:text-orange-400',
    description: 'Scheduled tasks (sequential)'
  },
};

export function LaneStatusCard({ name, status }: LaneStatusCardProps) {
  const config = laneConfig[name as keyof typeof laneConfig];
  const Icon = config.icon;
  
  // Handle undefined status
  if (!status) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
          <CardTitle className="text-sm font-medium">
            <div className="flex items-center gap-2">
              <Icon className={`h-4 w-4 ${config.color}`} />
              {name}
            </div>
          </CardTitle>
          <Badge variant="outline">N/A</Badge>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-muted-foreground">
            Status not available
          </div>
        </CardContent>
      </Card>
    );
  }
  
  const utilization = status.limit > 0 ? (status.active / status.limit) * 100 : 0;
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
        <CardTitle className="text-sm font-medium">
          <div className="flex items-center gap-2">
            <Icon className={`h-4 w-4 ${config.color}`} />
            {name}
          </div>
        </CardTitle>
        <Badge variant={status.active > 0 ? 'secondary' : 'outline'}>
          {status.active}/{status.limit}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="text-xs text-muted-foreground mb-2">
          {config.description}
        </div>
        
        {/* Concurrency Bar */}
        <div className="mb-2">
          <div className="flex justify-between text-xs mb-1">
            <span>Capacity</span>
            <span>{utilization.toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full ${status.active > 0 ? 'bg-primary' : 'bg-muted-foreground/20'}`}
              style={{ width: `${utilization}%` }}
            />
          </div>
        </div>
        
        {/* Queue Info */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <div className="text-muted-foreground">Active</div>
            <div className="font-semibold">{status.active}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Queued</div>
            <div className="font-semibold">{status.queued}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Limit</div>
            <div className="font-semibold">{status.limit}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
