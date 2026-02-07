'use client';

import { useAgentStore } from '@/stores/agentStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, Square, Pause, RotateCw, Zap } from 'lucide-react';

export function AgentControls() {
  const { status, loading, setLoading } = useAgentStore();
  const { send } = useWebSocket();
  
  const startAgent = () => {
    setLoading('starting', true);
    send({ action: 'start' });
    setTimeout(() => setLoading('starting', false), 2000);
  };
  
  const stopAgent = () => {
    setLoading('stopping', true);
    send({ action: 'stop' });
    setTimeout(() => setLoading('stopping', false), 2000);
  };
  
  const pauseAgent = () => {
    send({ action: 'pause' });
  };
  
  const resumeAgent = () => {
    send({ action: 'resume' });
  };
  
  const runOnce = () => {
    setLoading('running', true);
    send({ action: 'run_once' });
    setTimeout(() => setLoading('running', false), 2000);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Controls</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-3">
          {(status.state === 'stopped' || status.state === 'error') && (
            <Button
              onClick={startAgent}
              disabled={loading.starting}
              variant="default"
              className="bg-green-600 hover:bg-green-700"
            >
              {loading.starting ? (
                <>
                  <RotateCw className="animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play />
                  Start Agent
                </>
              )}
            </Button>
          )}
          
          {status.state === 'running' && (
            <>
              <Button
                onClick={stopAgent}
                disabled={loading.stopping}
                variant="destructive"
              >
                <Square />
                {loading.stopping ? 'Stopping...' : 'Stop Agent'}
              </Button>
              
              <Button
                onClick={pauseAgent}
                variant="outline"
              >
                <Pause />
                Pause
              </Button>
            </>
          )}
          
          {status.state === 'paused' && (
            <>
              <Button
                onClick={resumeAgent}
                variant="default"
                className="bg-green-600 hover:bg-green-700"
              >
                <Play />
                Resume
              </Button>
              
              <Button
                onClick={stopAgent}
                disabled={loading.stopping}
                variant="destructive"
              >
                Stop
              </Button>
            </>
          )}
          
          <Button
            onClick={runOnce}
            disabled={loading.running}
            variant="outline"
          >
            {loading.running ? (
              <>
                <RotateCw className="animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Zap />
                Run Once
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
