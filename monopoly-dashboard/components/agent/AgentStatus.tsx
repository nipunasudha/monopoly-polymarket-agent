'use client';

import { useAgentStore } from '@/stores/agentStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

export function AgentStatus() {
  const { status } = useAgentStore();
  const { isConnected } = useWebSocket();
  
  const getStateVariant = (state: string) => {
    switch (state) {
      case 'running':
        return 'secondary';
      case 'error':
        return 'outline';
      case 'paused':
        return 'secondary';
      default:
        return 'outline';
    }
  };
  
  const stateLabels = {
    running: 'Running',
    stopped: 'Stopped',
    paused: 'Paused',
    error: 'Error',
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-muted-foreground">State</dt>
            <dd className="mt-1">
              <Badge variant={getStateVariant(status.state)} className="gap-2">
                <span className={cn(
                  "h-2 w-2 rounded-full",
                  status.state === 'running' && 'bg-green-500',
                  status.state === 'error' && 'bg-red-500',
                  status.state === 'paused' && 'bg-yellow-500',
                  status.state === 'stopped' && 'bg-gray-500'
                )} />
                {stateLabels[status.state]}
              </Badge>
            </dd>
          </div>
          
          <div>
            <dt className="text-sm text-muted-foreground">Connection</dt>
            <dd className="mt-1">
              <Badge variant={isConnected ? 'secondary' : 'outline'} className="gap-2">
                <span className={cn(
                  "h-2 w-2 rounded-full",
                  isConnected ? 'bg-green-500' : 'bg-gray-500'
                )} />
                {isConnected ? 'Connected' : 'Disconnected'}
              </Badge>
            </dd>
          </div>
          
          <div>
            <dt className="text-sm text-muted-foreground">Interval</dt>
            <dd className="mt-1 text-lg font-semibold">{status.interval_minutes} minutes</dd>
          </div>
          
          <div>
            <dt className="text-sm text-muted-foreground">Last Run</dt>
            <dd className="mt-1 text-sm">
              {status.last_run ? new Date(status.last_run).toLocaleString() : 'Never'}
            </dd>
          </div>
          
          <div>
            <dt className="text-sm text-muted-foreground">Next Run</dt>
            <dd className="mt-1 text-sm">
              {status.next_run ? new Date(status.next_run).toLocaleString() : 'N/A'}
            </dd>
          </div>
          
          <div>
            <dt className="text-sm text-muted-foreground">Run Count</dt>
            <dd className="mt-1 text-lg font-semibold">{status.run_count}</dd>
          </div>
        </div>
        
        {status.last_error && (
          <Alert variant="destructive" className="mt-4">
            <AlertTitle>Last Error</AlertTitle>
            <AlertDescription>{status.last_error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
