'use client';

import { useAgentStore } from '@/stores/agentStore';
import { formatDistanceToNow } from 'date-fns';
import type { Activity } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ActivityFeed() {
  const { activities } = useAgentStore();
  
  if (activities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <p>No recent activity</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flow-root">
          <ul role="list" className="-mb-8">
            {activities.map((activity, activityIdx) => (
              <li key={`${activity.type}-${activity.data.id}-${activityIdx}`}>
                <div className="relative pb-8">
                  {activityIdx !== activities.length - 1 && (
                    <span
                      className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-border"
                      aria-hidden="true"
                    />
                  )}
                  <div className="relative flex space-x-3">
                    <div>
                      <span
                        className={cn(
                          "h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-background",
                          activity.type === 'forecast' ? 'bg-green-500' : 'bg-blue-500'
                        )}
                      >
                        {activity.type === 'forecast' ? (
                          <CheckCircle2 className="h-5 w-5 text-white" />
                        ) : (
                          <TrendingUp className="h-5 w-5 text-white" />
                        )}
                      </span>
                    </div>
                    <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                      <div>
                        <p className="text-sm font-medium">
                          {activity.type === 'forecast' ? 'Forecast Created' : 'Trade Executed'}
                        </p>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {activity.data.market_question}
                        </p>
                        {activity.type === 'forecast' && 'probability' in activity.data && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Probability: {(activity.data.probability * 100).toFixed(1)}%
                          </p>
                        )}
                        {activity.type === 'trade' && 'side' in activity.data && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {activity.data.side} • Size: ${activity.data.size.toFixed(2)}
                          </p>
                        )}
                      </div>
                      <div className="whitespace-nowrap text-right text-sm text-muted-foreground">
                        <time dateTime={activity.timestamp}>
                          {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                        </time>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
