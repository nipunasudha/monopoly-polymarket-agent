/**
 * Alpine.js Reactive Store for Agent State Management
 * Syncs with SSE events and provides centralized state for all components
 */

document.addEventListener('alpine:init', () => {
    Alpine.store('agent', {
        // Agent status
        status: {
            state: 'stopped',
            running: false,
            last_run: null,
            next_run: null,
            interval_minutes: 60,
            run_count: 0,
            error_count: 0,
            last_error: null,
            total_forecasts: 0,
            total_trades: 0
        },

        // Loading states
        loading: {
            starting: false,
            stopping: false,
            running: false,
        },

        // Recent activity
        activities: [],

        // Initialize the store
        init() {
            this.fetchStatus();
            this.fetchActivities();
            this.connectSSE();
        },

        // Fetch current status from API
        async fetchStatus() {
            try {
                const response = await fetch('/api/agent/status');
                const data = await response.json();
                this.updateStatus(data);
            } catch (error) {
                console.error('Failed to fetch status:', error);
            }
        },

        // Fetch recent activities
        async fetchActivities() {
            try {
                // Get recent forecasts and trades
                const [forecastsRes, tradesRes] = await Promise.all([
                    fetch('/api/forecasts?limit=10'),
                    fetch('/api/trades?limit=10')
                ]);
                
                const forecasts = await forecastsRes.json();
                const trades = await tradesRes.json();
                
                // Combine and sort by timestamp
                const activities = [
                    ...forecasts.map(f => ({ type: 'forecast', data: f, timestamp: f.created_at })),
                    ...trades.map(t => ({ type: 'trade', data: t, timestamp: t.created_at }))
                ];
                
                activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                this.activities = activities.slice(0, 20);
            } catch (error) {
                console.error('Failed to fetch activities:', error);
            }
        },

        // Connect to SSE stream
        connectSSE() {
            const eventSource = new EventSource('/api/events/stream');
            
            eventSource.addEventListener('agent_status_changed', (e) => {
                const data = JSON.parse(e.data);
                this.updateStatus(data);
            });
            
            eventSource.addEventListener('forecast_created', (e) => {
                const data = JSON.parse(e.data);
                this.addActivity('forecast', data);
                this.status.total_forecasts++;
            });
            
            eventSource.addEventListener('trade_executed', (e) => {
                const data = JSON.parse(e.data);
                this.addActivity('trade', data);
                this.status.total_trades++;
            });
            
            eventSource.addEventListener('portfolio_updated', (e) => {
                const data = JSON.parse(e.data);
                // Handle portfolio updates if needed
            });

            eventSource.onerror = () => {
                console.error('SSE connection error, reconnecting...');
            };
        },

        // Update status data
        updateStatus(data) {
            Object.assign(this.status, data);
        },

        // Add activity to feed
        addActivity(type, data) {
            this.activities.unshift({
                type,
                data,
                timestamp: data.timestamp || new Date().toISOString()
            });
            
            // Keep only last 20 activities
            if (this.activities.length > 20) {
                this.activities = this.activities.slice(0, 20);
            }
        },

        // Agent control actions (optimistic updates)
        async start() {
            this.loading.starting = true;
            
            // Optimistic update - change UI immediately
            const previousState = this.status.state;
            this.status.state = 'running';
            this.status.running = true;
            
            try {
                const response = await fetch('/api/agent/start', { method: 'POST' });
                if (!response.ok) throw new Error('Failed to start agent');
                const data = await response.json();
                console.log('Agent started:', data);
                // Fetch fresh status to get next_run time
                await this.fetchStatus();
            } catch (error) {
                console.error('Failed to start agent:', error);
                alert('Failed to start agent: ' + error.message);
                // Revert optimistic update on error
                this.status.state = previousState;
                this.status.running = false;
            } finally {
                this.loading.starting = false;
            }
        },

        async stop() {
            this.loading.stopping = true;
            
            // Optimistic update
            const previousState = this.status.state;
            this.status.state = 'stopped';
            this.status.running = false;
            this.status.next_run = null;
            
            try {
                const response = await fetch('/api/agent/stop', { method: 'POST' });
                if (!response.ok) throw new Error('Failed to stop agent');
                const data = await response.json();
                console.log('Agent stopped:', data);
                await this.fetchStatus();
            } catch (error) {
                console.error('Failed to stop agent:', error);
                alert('Failed to stop agent: ' + error.message);
                // Revert on error
                this.status.state = previousState;
                this.status.running = true;
            } finally {
                this.loading.stopping = false;
            }
        },

        async pause() {
            // Optimistic update
            const previousState = this.status.state;
            this.status.state = 'paused';
            
            try {
                const response = await fetch('/api/agent/pause', { method: 'POST' });
                if (!response.ok) throw new Error('Failed to pause agent');
                await response.json();
                await this.fetchStatus();
            } catch (error) {
                console.error('Failed to pause agent:', error);
                alert('Failed to pause agent: ' + error.message);
                this.status.state = previousState;
            }
        },

        async resume() {
            // Optimistic update
            const previousState = this.status.state;
            this.status.state = 'running';
            this.status.running = true;
            
            try {
                const response = await fetch('/api/agent/resume', { method: 'POST' });
                if (!response.ok) throw new Error('Failed to resume agent');
                await response.json();
                await this.fetchStatus();
            } catch (error) {
                console.error('Failed to resume agent:', error);
                alert('Failed to resume agent: ' + error.message);
                this.status.state = previousState;
                this.status.running = false;
            }
        },

        async runOnce() {
            this.loading.running = true;
            try {
                const response = await fetch('/api/agent/run-once', { method: 'POST' });
                const data = await response.json();
                console.log('Agent run result:', data);
                await this.fetchActivities();
            } catch (error) {
                console.error('Failed to run agent:', error);
                alert('Failed to run agent: ' + error.message);
            } finally {
                this.loading.running = false;
            }
        },

        async updateInterval(minutes) {
            try {
                const response = await fetch('/api/agent/interval', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ interval_minutes: parseInt(minutes) })
                });
                const data = await response.json();
                console.log('Interval updated:', data);
                this.status.interval_minutes = data.interval_minutes;
                return data;
            } catch (error) {
                console.error('Failed to update interval:', error);
                throw error;
            }
        },

        // Computed properties
        get stateColor() {
            const colors = {
                running: 'green',
                stopped: 'gray',
                paused: 'yellow',
                error: 'red'
            };
            return colors[this.status.state] || 'gray';
        },

        get stateLabel() {
            const labels = {
                running: 'Running',
                stopped: 'Stopped',
                paused: 'Paused',
                error: 'Error'
            };
            return labels[this.status.state] || 'Unknown';
        },

        get successRate() {
            if (this.status.run_count === 0) return 0;
            return ((this.status.run_count - this.status.error_count) / this.status.run_count * 100).toFixed(1);
        },

        get formattedLastRun() {
            if (!this.status.last_run) return 'Never';
            return new Date(this.status.last_run).toLocaleString();
        },

        get formattedNextRun() {
            if (!this.status.next_run) return 'N/A';
            return new Date(this.status.next_run).toLocaleString();
        }
    });
});
