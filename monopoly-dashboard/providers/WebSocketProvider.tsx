'use client';

import { useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

/**
 * WebSocket Provider Component
 * Initializes WebSocket connection once at the app level
 */
export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  useWebSocket();
  
  return <>{children}</>;
}
