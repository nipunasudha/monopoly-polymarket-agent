'use client';

import { useAgentStore } from '@/stores/agentStore';
import { useWebSocket } from '@/hooks/useWebSocket';

export function AgentStatus() {
  const { status } = useAgentStore();
  const { isConnected } = useWebSocket();
  
  const stateColors = {
    running: 'bg-green-100 text-green-800 border-green-200',
    stopped: 'bg-gray-100 text-gray-800 border-gray-200',
    paused: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    error: 'bg-red-100 text-red-800 border-red-200',
  };
  
  const stateLabels = {
    running: 'Running',
    stopped: 'Stopped',
    paused: 'Paused',
    error: 'Error',
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Agent Status</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <dt className="text-sm text-gray-600">State</dt>
          <dd className="mt-1">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${stateColors[status.state]}`}>
              <span className={`w-2 h-2 mr-2 rounded-full ${status.state === 'running' ? 'bg-green-500' : status.state === 'error' ? 'bg-red-500' : status.state === 'paused' ? 'bg-yellow-500' : 'bg-gray-500'}`}></span>
              {stateLabels[status.state]}
            </span>
          </dd>
        </div>
        
        <div>
          <dt className="text-sm text-gray-600">Connection</dt>
          <dd className="mt-1">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${isConnected ? 'bg-green-100 text-green-800 border-green-200' : 'bg-red-100 text-red-800 border-red-200'}`}>
              <span className={`w-2 h-2 mr-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </dd>
        </div>
        
        <div>
          <dt className="text-sm text-gray-600">Interval</dt>
          <dd className="mt-1 text-lg font-semibold text-gray-900">{status.interval_minutes} minutes</dd>
        </div>
        
        <div>
          <dt className="text-sm text-gray-600">Last Run</dt>
          <dd className="mt-1 text-sm text-gray-900">
            {status.last_run ? new Date(status.last_run).toLocaleString() : 'Never'}
          </dd>
        </div>
        
        <div>
          <dt className="text-sm text-gray-600">Next Run</dt>
          <dd className="mt-1 text-sm text-gray-900">
            {status.next_run ? new Date(status.next_run).toLocaleString() : 'N/A'}
          </dd>
        </div>
        
        <div>
          <dt className="text-sm text-gray-600">Run Count</dt>
          <dd className="mt-1 text-lg font-semibold text-gray-900">{status.run_count}</dd>
        </div>
      </div>
      
      {status.last_error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm font-medium text-red-800">Last Error</p>
          <p className="text-sm text-red-600 mt-1">{status.last_error}</p>
        </div>
      )}
    </div>
  );
}
