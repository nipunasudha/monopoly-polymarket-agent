'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAgentStore } from '@/stores/agentStore';
import { Activity, Database, CheckCircle2, XCircle, Trash2 } from 'lucide-react';

export function HubOverview() {
  const hubStatus = useAgentStore((state) => state.hubStatus);
  
  if (!hubStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Hub Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Hub status not available
          </p>
        </CardContent>
      </Card>
    );
  }
  
  const totalActive = Object.values(hubStatus.lane_status).reduce(
    (sum, lane) => sum + lane.active, 0
  );
  const totalQueued = Object.values(hubStatus.lane_status).reduce(
    (sum, lane) => sum + lane.queued, 0
  );
  
  const stats = [
    {
      label: 'Hub State',
      value: (
        <Badge variant={hubStatus.running ? 'secondary' : 'outline'}>
          {hubStatus.running ? 'Running' : 'Stopped'}
        </Badge>
      ),
      icon: Activity,
    },
    {
      label: 'Active Tasks',
      value: totalActive,
      icon: Activity,
      color: totalActive > 0 ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground',
    },
    {
      label: 'Queued Tasks',
      value: totalQueued,
      icon: Database,
      color: totalQueued > 0 ? 'text-blue-600 dark:text-blue-400' : 'text-muted-foreground',
    },
    {
      label: 'Sessions',
      value: hubStatus.sessions,
      icon: Database,
    },
  ];
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Hub Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="flex items-center space-x-2">
                <Icon className={`h-4 w-4 ${stat.color || 'text-muted-foreground'}`} />
                <div>
                  <div className="text-xs text-muted-foreground">{stat.label}</div>
                  <div className="text-lg font-semibold">
                    {typeof stat.value === 'object' ? stat.value : stat.value}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Task Statistics */}
        <div className="mt-4 pt-4 border-t">
          <h4 className="text-sm font-medium mb-3">Task Statistics</h4>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
              <div>
                <div className="text-muted-foreground">Completed</div>
                <div className="font-semibold">{hubStatus.stats.tasks_completed}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              <div>
                <div className="text-muted-foreground">Failed</div>
                <div className="font-semibold">{hubStatus.stats.tasks_failed}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Trash2 className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              <div>
                <div className="text-muted-foreground">Cleaned</div>
                <div className="font-semibold">{hubStatus.stats.results_cleaned}</div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
