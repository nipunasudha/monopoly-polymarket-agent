'use client';

import { useEffect, useState } from 'react';
import { forecastAPI } from '@/lib/api';
import type { Forecast } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export default function ForecastsPage() {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    forecastAPI.getRecent(50)
      .then(setForecasts)
      .catch((err) => console.error('Failed to fetch forecasts:', err))
      .finally(() => setLoading(false));
  }, []);
  
  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96 mt-2" />
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-3/4" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Forecasts</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          AI-generated market predictions
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {forecasts.map((forecast) => (
          <Card key={forecast.id}>
            <CardHeader>
              <CardTitle className="text-lg">{forecast.market_question}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Outcome:</span>
                  <span className="text-sm font-medium">{forecast.outcome}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Probability:</span>
                  <span className="text-sm font-medium">
                    {(forecast.probability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Confidence:</span>
                  <span className="text-sm font-medium">
                    {(forecast.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                {forecast.reasoning && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm text-muted-foreground">Reasoning:</p>
                    <p className="text-sm mt-1">{forecast.reasoning}</p>
                  </div>
                )}
                <div className="mt-2 text-xs text-muted-foreground">
                  Created: {new Date(forecast.created_at).toLocaleString()}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {forecasts.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">No forecasts yet</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
