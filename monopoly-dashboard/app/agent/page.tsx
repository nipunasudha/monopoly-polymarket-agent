'use client';

import { AgentStatus } from '@/components/agent/AgentStatus';
import { AgentControls } from '@/components/agent/AgentControls';
import { AgentStats } from '@/components/agent/AgentStats';
import { ActivityFeed } from '@/components/ActivityFeed';

export default function AgentPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Agent Control Panel</h2>
        <p className="mt-1 text-sm text-gray-500">
          Manage and monitor your Polymarket trading agent
        </p>
      </div>

      {/* Status and Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentStatus />
        <AgentControls />
      </div>

      {/* Statistics */}
      <AgentStats />

      {/* Activity Feed */}
      <ActivityFeed />
    </div>
  );
}
