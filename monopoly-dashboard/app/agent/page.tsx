'use client';

import { AgentStatus } from '@/components/agent/AgentStatus';
import { AgentControls } from '@/components/agent/AgentControls';
import { AgentStats } from '@/components/agent/AgentStats';
import { ActivityFeed } from '@/components/ActivityFeed';
import { HubOverview } from '@/components/hub/HubOverview';
import { LaneStatusCard } from '@/components/hub/LaneStatusCard';
import { useAgentStore } from '@/stores/agentStore';

export default function AgentPage() {
  const hubStatus = useAgentStore((state) => state.hubStatus);
  
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold">Agent Control & System Monitor</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your trading agent and monitor the TradingHub architecture
        </p>
      </div>

      {/* Agent Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentStatus />
        <AgentControls />
      </div>

      {/* Agent Statistics */}
      <AgentStats />

      {/* Hub System Monitoring */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">System Monitor</h3>
          <p className="text-sm text-muted-foreground">
            Real-time hub status, lane concurrency, and task execution
          </p>
        </div>
        
        {/* Hub Overview */}
        <HubOverview />
        
        {/* Lane Status Grid */}
        {hubStatus?.lane_status && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <LaneStatusCard 
              name="MAIN" 
              status={hubStatus.lane_status.main}
            />
            <LaneStatusCard 
              name="RESEARCH" 
              status={hubStatus.lane_status.research}
            />
            <LaneStatusCard 
              name="MONITOR" 
              status={hubStatus.lane_status.monitor}
            />
            <LaneStatusCard 
              name="CRON" 
              status={hubStatus.lane_status.cron}
            />
          </div>
        )}
      </div>

      {/* Activity Feed */}
      <ActivityFeed />
    </div>
  );
}
