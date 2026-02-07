'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { useAgentStore } from '@/stores/agentStore';
import type { WSMessage, WSCommand } from '@/lib/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8080/ws';
const RECONNECT_DELAY = 2000;
const PING_INTERVAL = 30000;

// Global WebSocket instance to prevent duplicate connections
let globalWS: WebSocket | null = null;
let connectionCount = 0;

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingInterval = useRef<NodeJS.Timeout | null>(null);
  const isMounted = useRef(true);
  const previousStatusRef = useRef<string | null>(null);
  
  const patchRealtime = useAgentStore((s) => s.patchRealtime);
  const addActivity = useAgentStore((s) => s.addActivity);
  const reset = useAgentStore((s) => s.reset);

  const handleMessage = useCallback(
    (message: WSMessage) => {
      if (!isMounted.current) return;

      switch (message.type) {
        case 'init':
          // Set initial state without showing toast
          previousStatusRef.current = message.data.agent.state;
          patchRealtime({
            agent: message.data.agent,
            portfolio: message.data.portfolio,
          });
          break;
        case 'agent_status_changed':
          const newState = message.data.state;
          const previousState = previousStatusRef.current;
          
          // Show toast only if state actually changed (not on initial load)
          if (previousState !== null && previousState !== newState) {
            switch (newState) {
              case 'running':
                if (previousState === 'paused') {
                  toast.success('Agent resumed', { duration: 3000 });
                } else {
                  toast.success('Agent started', { duration: 3000 });
                }
                break;
              case 'paused':
                toast.info('Agent paused', { duration: 3000 });
                break;
              case 'stopped':
                toast('Agent stopped', { duration: 3000 });
                break;
              case 'error':
                toast.error('Agent error', {
                  description: message.data.last_error || 'An error occurred',
                  duration: 5000,
                });
                break;
            }
          }
          
          previousStatusRef.current = newState;
          patchRealtime({ agent: message.data });
          break;
        case 'portfolio_updated':
          patchRealtime({ portfolio: message.data });
          break;
        case 'forecast_created':
          addActivity('forecast', message.data);
          break;
        case 'trade_executed':
          addActivity('trade', message.data);
          break;
        case 'data_cleared':
          // Reset the store when data is cleared
          reset();
          patchRealtime({
            portfolio: null,
            activities: [],
          });
          console.log('[WebSocket] Data cleared:', message.data);
          break;
        case 'pong':
          break;
      }
    },
    [patchRealtime, addActivity, reset]
  );
  
  const connect = useCallback(() => {
    // Prevent duplicate connections
    if (globalWS && globalWS.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected, reusing connection');
      setIsConnected(true);
      return;
    }
    
    if (globalWS && globalWS.readyState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Connection already in progress');
      return;
    }
    
    try {
      console.log('[WebSocket] Connecting to', WS_URL);
      globalWS = new WebSocket(WS_URL);
      
      globalWS.onopen = () => {
        if (!isMounted.current) return;
        console.log('[WebSocket] ✅ Connected successfully');
        setIsConnected(true);
        setError(null);
        
        // Start ping interval
        if (pingInterval.current) clearInterval(pingInterval.current);
        pingInterval.current = setInterval(() => {
          if (globalWS?.readyState === WebSocket.OPEN) {
            send({ action: 'ping' });
          }
        }, PING_INTERVAL);
      };
      
      globalWS.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };
      
      globalWS.onerror = (event) => {
        if (!isMounted.current) return;
        // Don't log error here - it's logged by onclose
        // This prevents duplicate error messages
      };
      
      globalWS.onclose = (event) => {
        if (!isMounted.current) return;
        
        if (event.wasClean) {
          console.log(`[WebSocket] Connection closed cleanly (code: ${event.code})`);
        } else {
          console.warn(`[WebSocket] Connection lost (code: ${event.code}, reason: ${event.reason || 'unknown'})`);
          console.warn('[WebSocket] Make sure backend is running on port 8080');
          setError('WebSocket connection lost. Retrying...');
        }
        
        setIsConnected(false);
        globalWS = null;
        
        // Clear ping interval
        if (pingInterval.current) {
          clearInterval(pingInterval.current);
        }
        
        // Reconnect after delay
        if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = setTimeout(() => {
          if (isMounted.current) {
            console.log('[WebSocket] Attempting to reconnect...');
            connect();
          }
        }, RECONNECT_DELAY);
      };
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
      setError('Failed to connect to WebSocket');
      
      // Retry connection
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = setTimeout(() => {
        if (isMounted.current) connect();
      }, RECONNECT_DELAY);
    }
  }, [handleMessage]);
  
  const send = useCallback((command: WSCommand) => {
    if (globalWS?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Sending:', command.action);
      globalWS.send(JSON.stringify(command));
    } else {
      console.warn('[WebSocket] Not connected, cannot send command');
    }
  }, []);
  
  useEffect(() => {
    isMounted.current = true;
    connectionCount++;
    const currentConnection = connectionCount;
    
    console.log(`[WebSocket] Hook mounted (connection #${currentConnection})`);
    
    // Only connect if this is the first hook instance or if not connected
    if (!globalWS || globalWS.readyState === WebSocket.CLOSED) {
      connect();
    } else if (globalWS.readyState === WebSocket.OPEN) {
      setIsConnected(true);
    }
    
    return () => {
      isMounted.current = false;
      connectionCount--;
      console.log(`[WebSocket] Hook unmounted (remaining: ${connectionCount})`);
      
      // Only disconnect if this is the last hook instance
      if (connectionCount === 0) {
        console.log('[WebSocket] Last hook unmounted, closing connection');
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
        }
        if (pingInterval.current) {
          clearInterval(pingInterval.current);
        }
        if (globalWS) {
          globalWS.close();
          globalWS = null;
        }
      }
    };
  }, [connect]);
  
  return { 
    isConnected, 
    error,
    send,
    reconnect: connect
  };
}
