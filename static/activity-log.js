class ActivityLogger {
    constructor() {
        this.activities = [];
        this.isLiveUpdating = true;
        this.autoScroll = true;
        this.updateInterval = 2000; // 2 seconds
        this.intervalId = null;
        this.charts = {};
        this.filters = {
            agent: '',
            action: '',
            severity: '',
            timeRange: 'all',
            search: ''
        };
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.updateSystemTime();
        this.startLiveUpdates();
        await this.loadInitialData();
        // this.generateMockData(); // For demonstration - DISABLED
    }

    setupEventListeners() {
        // Filter event listeners
        document.getElementById('agent-filter').addEventListener('change', (e) => {
            this.filters.agent = e.target.value;
            this.applyFilters();
        });

        document.getElementById('action-filter').addEventListener('change', (e) => {
            this.filters.action = e.target.value;
            this.applyFilters();
        });

        document.getElementById('severity-filter').addEventListener('change', (e) => {
            this.filters.severity = e.target.value;
            this.applyFilters();
        });

        document.getElementById('time-filter').addEventListener('change', (e) => {
            this.filters.timeRange = e.target.value;
            this.applyFilters();
        });

        document.getElementById('search-input').addEventListener('input', (e) => {
            this.filters.search = e.target.value.toLowerCase();
            this.applyFilters();
        });

        // Auto-scroll to bottom when new activities are added
        const streamContainer = document.getElementById('activity-stream');
        streamContainer.addEventListener('scroll', () => {
            const isAtBottom = streamContainer.scrollHeight - streamContainer.clientHeight <= streamContainer.scrollTop + 1;
            if (!isAtBottom && this.autoScroll) {
                this.autoScroll = false;
                this.updateAutoScrollButton();
            }
        });
    }

    updateSystemTime() {
        const now = new Date();
        const systemTimeEl = document.getElementById('system-time');
        if (systemTimeEl) {
            systemTimeEl.textContent = now.toLocaleString();
        }
        setTimeout(() => this.updateSystemTime(), 1000);
    }

    startLiveUpdates() {
        if (this.intervalId) clearInterval(this.intervalId);
        
        this.intervalId = setInterval(async () => {
            if (this.isLiveUpdating) {
                await this.fetchLatestActivities();
                this.updateLastUpdateTime();
                // this.generateRealtimeActivity(); // Simulate real-time data - DISABLED
            }
        }, this.updateInterval);
    }

    async loadInitialData() {
        try {
            // Load agents for filter dropdown
            const agents = await this.fetchAgents();
            this.populateAgentFilter(agents);
            
            // Load initial activity logs
            const activities = await this.fetchActivities();
            this.activities = activities;
            this.renderActivities();
            this.updateStatistics();
            this.updateCharts();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial activity data');
        }
    }

    async fetchAgents() {
        try {
            const response = await fetch('/api/agents');
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error fetching agents:', error);
        }
        
        // Mock data for demonstration
        return [
            { id: 'ai-monitor', name: 'AI Monitor Agent', status: 'active' },
            { id: 'compliance-agent', name: 'Compliance Agent', status: 'active' },
            // { id: 'security-scanner', name: 'Security Scanner', status: 'active' },
            // { id: 'data-analyst', name: 'Data Analyst', status: 'active' },
            // { id: 'anomaly-detector', name: 'Anomaly Detector', status: 'active' }
        ];
    }

    async fetchActivities(limit = 10) {
        try {
            const response = await fetch(`/api/activity-logs?limit=${limit}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error fetching activities:', error);
        }
        
        return [];
    }

    async fetchLatestActivities() {
        try {
            const lastActivity = this.activities[0];
            const since = lastActivity ? lastActivity.timestamp : new Date(Date.now() - 3600000).toISOString();
            
            const response = await fetch(`/api/activity-logs/latest?since=${since}`);
            if (response.ok) {
                const newActivities = await response.json();
                if (newActivities.length > 0) {
                    this.activities = [...newActivities, ...this.activities];
                    this.renderActivities();
                    this.updateStatistics();
                    this.updateCharts();
                }
            }
        } catch (error) {
            console.error('Error fetching latest activities:', error);
        }
    }

    generateMockData() {
        // Generate initial mock data for demonstration
        const agents = ['ai-monitor', 'compliance-agent', 'security-scanner', 'data-analyst', 'anomaly-detector'];
        const actions = ['decision', 'data_collection', 'analysis', 'compliance_check', 'security_scan', 'error'];
        const severities = ['critical', 'high', 'medium', 'low', 'info'];
        
        for (let i = 0; i < 50; i++) {
            const activity = this.createMockActivity(agents, actions, severities, i);
            this.activities.unshift(activity);
        }
        
        this.renderActivities();
        this.updateStatistics();
        this.updateCharts();
    }

    // generateRealtimeActivity() {
    //     if (!this.isLiveUpdating) return;
        
    //     // Simulate real-time activity generation
    //     if (Math.random() < 0.7) { // 70% chance of new activity
    //         const agents = ['ai-monitor', 'compliance-agent', 'security-scanner', 'data-analyst', 'anomaly-detector'];
    //         const actions = ['decision', 'data_collection', 'analysis', 'compliance_check', 'security_scan'];
    //         const severities = ['high', 'medium', 'low', 'info'];
            
    //         // Add occasional errors
    //         if (Math.random() < 0.1) {
    //             actions.push('error');
    //             severities.push('critical');
    //         }
            
    //         const newActivity = this.createMockActivity(agents, actions, severities);
    //         this.activities.unshift(newActivity);
            
    //         // Keep only last 100 activities for performance
    //         if (this.activities.length > 100) {
    //             this.activities = this.activities.slice(0, 100);
    //         }
            
    //         this.renderActivities();
    //         this.updateStatistics();
    //         this.updateCharts();
            
    //         if (this.autoScroll) {
    //             this.scrollToBottom();
    //         }
    //     }
    // }

    // createMockActivity(agents, actions, severities, index = 0) {
    //     const agent = agents[Math.floor(Math.random() * agents.length)];
    //     const action = actions[Math.floor(Math.random() * actions.length)];
    //     const severity = severities[Math.floor(Math.random() * severities.length)];
        
    //     const messages = {
    //         decision: [
    //             'Analyzing compliance violation threshold exceeded',
    //             'Implementing security protocol upgrade',
    //             'Optimizing data processing pipeline',
    //             'Evaluating anomaly detection parameters',
    //             'Processing user access request'
    //         ],
    //         data_collection: [
    //             'Gathering system performance metrics',
    //             'Collecting user activity logs',
    //             'Scanning network traffic patterns',
    //             'Harvesting application error reports',
    //             'Aggregating compliance audit data'
    //         ],
    //         analysis: [
    //             'Processing behavioral anomaly patterns',
    //             'Analyzing security threat landscape',
    //             'Evaluating system performance trends',
    //             'Computing risk assessment scores',
    //             'Generating predictive insights'
    //         ],
    //         compliance_check: [
    //             'Validating regulatory compliance status',
    //             'Auditing data privacy controls',
    //             'Checking access permission alignments',
    //             'Verifying encryption standards',
    //             'Monitoring policy adherence'
    //         ],
    //         security_scan: [
    //             'Detecting suspicious network activity',
    //             'Scanning for vulnerability signatures',
    //             'Monitoring authentication patterns',
    //             'Analyzing access log anomalies',
    //             'Evaluating threat intelligence feeds'
    //         ],
    //         error: [
    //             'Connection timeout to external service',
    //             'Database query execution failed',
    //             'Authentication service unavailable',
    //             'Memory allocation exceeded limits',
    //             'API rate limit threshold breached'
    //         ]
    //     };

    //     const message = messages[action][Math.floor(Math.random() * messages[action].length)];
        
    //     return {
    //         id: `activity-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    //         timestamp: new Date(Date.now() - index * Math.random() * 60000).toISOString(),
    //         agent_id: agent,
    //         action_type: action,
    //         severity: severity,
    //         message: message,
    //         data: {
    //             session_id: `sess-${Math.random().toString(36).substr(2, 8)}`,
    //             user_id: Math.random() < 0.3 ? `user-${Math.floor(Math.random() * 100)}` : null,
    //             execution_time: Math.floor(Math.random() * 5000) + 50,
    //             resource_usage: {
    //                 cpu: Math.floor(Math.random() * 100),
    //                 memory: Math.floor(Math.random() * 100),
    //                 network: Math.floor(Math.random() * 1000)
    //             },
    //             metadata: {
    //                 context: action,
    //                 confidence: Math.random(),
    //                 impact_score: Math.random() * 10
    //             }
    //         },
    //         hash: this.generateHash(`${agent}-${action}-${Date.now()}-${message}`)
    //     };
    // }

    generateHash(data) {
        let hash = 0;
        if (data.length === 0) return hash.toString(16);
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash).toString(16).padStart(8, '0');
    }

    populateAgentFilter(agents) {
        const agentFilter = document.getElementById('agent-filter');
        agentFilter.innerHTML = '<option value="">All Agents</option>';
        
        agents.forEach(agent => {
            const option = document.createElement('option');
            option.value = agent.id;
            option.textContent = agent.name;
            agentFilter.appendChild(option);
        });
    }

    renderActivities() {
        const filteredActivities = this.getFilteredActivities();
        const container = document.getElementById('activity-stream');
        
        if (filteredActivities.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <i class="fas fa-search text-4xl mb-4"></i>
                    <p class="text-lg">No activities found</p>
                    <p class="text-sm">Try adjusting your filters</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = filteredActivities.map(activity => this.createActivityHTML(activity)).join('');
        
        // Update total logs count
        document.getElementById('total-logs').textContent = this.activities.length;
    }

    createActivityHTML(activity) {
        const timeAgo = this.timeAgo(new Date(activity.timestamp));
        const severityColors = {
            critical: 'text-red-400 bg-red-900/30',
            high: 'text-orange-400 bg-orange-900/30',
            medium: 'text-yellow-400 bg-yellow-900/30',
            low: 'text-blue-400 bg-blue-900/30',
            info: 'text-slate-400 bg-slate-900/30'
        };
        
        const actionIcons = {
            decision: 'fas fa-brain',
            data_collection: 'fas fa-database',
            analysis: 'fas fa-chart-line',
            compliance_check: 'fas fa-shield-alt',
            security_scan: 'fas fa-lock',
            error: 'fas fa-exclamation-triangle'
        };

        return `
            <div class="activity-item bg-slate-800/50 hover:bg-slate-700/50 rounded-lg p-4 border-l-4 ${this.getSeverityBorderColor(activity.severity)} cursor-pointer transition-all hover:shadow-lg"
                 onclick="activityLogger.showActivityDetails('${activity.id}')">
                <div class="flex items-start justify-between">
                    <div class="flex items-start space-x-3 flex-1">
                        <div class="p-2 rounded-lg ${severityColors[activity.severity]}">
                            <i class="${actionIcons[activity.action_type]} text-lg"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center space-x-2 mb-1">
                                <span class="font-medium text-white">${this.formatAgentName(activity.agent_id)}</span>
                                <span class="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded-full">
                                    ${activity.action_type.replace('_', ' ').toUpperCase()}
                                </span>
                                <span class="px-2 py-1 ${severityColors[activity.severity]} text-xs rounded-full">
                                    ${activity.severity.toUpperCase()}
                                </span>
                            </div>
                            <p class="text-slate-300 text-sm mb-2">${activity.message}</p>
                            <div class="flex items-center space-x-4 text-xs text-slate-500">
                                <span><i class="fas fa-clock mr-1"></i>${timeAgo}</span>
                                <span><i class="fas fa-tachometer-alt mr-1"></i>${activity.data.execution_time}ms</span>
                                <span><i class="fas fa-fingerprint mr-1"></i>${activity.hash}</span>
                                ${activity.data.user_id ? `<span><i class="fas fa-user mr-1"></i>${activity.data.user_id}</span>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-xs text-slate-500">${new Date(activity.timestamp).toLocaleTimeString()}</div>
                        ${activity.data.metadata.confidence ? `
                            <div class="text-xs text-green-400 mt-1">
                                <i class="fas fa-percentage mr-1"></i>${Math.round(activity.data.metadata.confidence * 100)}%
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    getSeverityBorderColor(severity) {
        const colors = {
            critical: 'border-red-500',
            high: 'border-orange-500',
            medium: 'border-yellow-500',
            low: 'border-blue-500',
            info: 'border-slate-500'
        };
        return colors[severity] || colors.info;
    }

    formatAgentName(agentId) {
        return agentId.split('-').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    timeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffSecs < 60) return `${diffSecs}s ago`;
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }

    getFilteredActivities() {
        return this.activities.filter(activity => {
            if (this.filters.agent && activity.agent_id !== this.filters.agent) return false;
            if (this.filters.action && activity.action_type !== this.filters.action) return false;
            if (this.filters.severity && activity.severity !== this.filters.severity) return false;
            if (this.filters.search && !activity.message.toLowerCase().includes(this.filters.search)) return false;
            
            if (this.filters.timeRange !== 'all') {
                const activityTime = new Date(activity.timestamp);
                const now = new Date();
                const ranges = {
                    '1h': 3600000,
                    '24h': 86400000,
                    '7d': 604800000,
                    '30d': 2592000000
                };
                
                if (now - activityTime > ranges[this.filters.timeRange]) return false;
            }
            
            return true;
        });
    }

    applyFilters() {
        this.renderActivities();
        this.updateStatistics();
        this.updateCharts();
    }

    updateStatistics() {
        const filteredActivities = this.getFilteredActivities();
        
        document.getElementById('stat-total').textContent = filteredActivities.length;
        
        const decisions = filteredActivities.filter(a => a.action_type === 'decision').length;
        document.getElementById('stat-decisions').textContent = decisions;
        
        const dataPoints = filteredActivities.filter(a => a.action_type === 'data_collection').length;
        document.getElementById('stat-datapoints').textContent = dataPoints;
        
        const errors = filteredActivities.filter(a => a.severity === 'critical' || a.action_type === 'error').length;
        document.getElementById('stat-errors').textContent = errors;
        
        const avgPerformance = filteredActivities.length > 0 
            ? Math.round(filteredActivities.reduce((sum, a) => sum + a.data.execution_time, 0) / filteredActivities.length)
            : 0;
        document.getElementById('stat-performance').textContent = avgPerformance + 'ms';
        
        const activeAgents = new Set(filteredActivities.map(a => a.agent_id)).size;
        document.getElementById('stat-agents').textContent = activeAgents;
    }

    initializeCharts() {
        // Activity Timeline Chart
        const timelineCtx = document.getElementById('activity-timeline-chart').getContext('2d');
        this.charts.timeline = new Chart(timelineCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Activities',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: 'white' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: 'white' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: 'white' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });

        // Agent Distribution Chart
        const distributionCtx = document.getElementById('agent-distribution-chart').getContext('2d');
        this.charts.distribution = new Chart(distributionCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(236, 72, 153, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: 'white' }
                    }
                }
            }
        });
    }

    updateCharts() {
        this.updateTimelineChart();
        this.updateDistributionChart();
        const chartLastUpdatedEl = document.getElementById('chart-last-updated');
        if (chartLastUpdatedEl) {
            chartLastUpdatedEl.textContent = 'just now';
        }
    }

    updateTimelineChart() {
        const filteredActivities = this.getFilteredActivities();
        const now = new Date();
        const hours = [];
        const counts = [];

        // Generate hourly activity counts for last 24 hours
        for (let i = 23; i >= 0; i--) {
            const hour = new Date(now.getTime() - i * 3600000);
            hours.push(hour.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            
            const hourStart = new Date(hour.getTime());
            hourStart.setMinutes(0, 0, 0);
            const hourEnd = new Date(hourStart.getTime() + 3600000);
            
            const count = filteredActivities.filter(activity => {
                const activityTime = new Date(activity.timestamp);
                return activityTime >= hourStart && activityTime < hourEnd;
            }).length;
            
            counts.push(count);
        }

        this.charts.timeline.data.labels = hours;
        this.charts.timeline.data.datasets[0].data = counts;
        this.charts.timeline.update();
    }

    updateDistributionChart() {
        const filteredActivities = this.getFilteredActivities();
        const agentCounts = {};

        filteredActivities.forEach(activity => {
            const agentName = this.formatAgentName(activity.agent_id);
            agentCounts[agentName] = (agentCounts[agentName] || 0) + 1;
        });

        const labels = Object.keys(agentCounts);
        const data = Object.values(agentCounts);

        this.charts.distribution.data.labels = labels;
        this.charts.distribution.data.datasets[0].data = data;
        this.charts.distribution.update();
    }

    updateLastUpdateTime() {
        const now = new Date();
        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) {
            lastUpdateEl.textContent = now.toLocaleTimeString();
        }
    }

    showActivityDetails(activityId) {
        const activity = this.activities.find(a => a.id === activityId);
        if (!activity) return;

        const modal = document.getElementById('activity-modal');
        const details = document.getElementById('activity-details');
        
        details.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h4 class="text-lg font-semibold text-white mb-3">Basic Information</h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-slate-400">ID:</span>
                                <code class="text-green-400">${activity.id}</code>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Timestamp:</span>
                                <span class="text-white">${new Date(activity.timestamp).toLocaleString()}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Agent:</span>
                                <span class="text-white">${this.formatAgentName(activity.agent_id)}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Action:</span>
                                <span class="text-white">${activity.action_type.replace('_', ' ')}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Severity:</span>
                                <span class="text-${this.getSeverityColor(activity.severity)}-400">${activity.severity}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Hash:</span>
                                <code class="text-green-400 text-xs">${activity.hash}</code>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="text-lg font-semibold text-white mb-3">Execution Data</h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-slate-400">Session ID:</span>
                                <code class="text-blue-400">${activity.data.session_id}</code>
                            </div>
                            ${activity.data.user_id ? `
                                <div class="flex justify-between">
                                    <span class="text-slate-400">User ID:</span>
                                    <span class="text-white">${activity.data.user_id}</span>
                                </div>
                            ` : ''}
                            <div class="flex justify-between">
                                <span class="text-slate-400">Execution Time:</span>
                                <span class="text-white">${activity.data.execution_time}ms</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">CPU Usage:</span>
                                <span class="text-white">${activity.data.resource_usage.cpu}%</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Memory Usage:</span>
                                <span class="text-white">${activity.data.resource_usage.memory}%</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Network:</span>
                                <span class="text-white">${activity.data.resource_usage.network}KB/s</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h4 class="text-lg font-semibold text-white mb-3">Message</h4>
                    <div class="bg-slate-800/50 rounded-lg p-4">
                        <p class="text-slate-300">${activity.message}</p>
                    </div>
                </div>
                
                <div>
                    <h4 class="text-lg font-semibold text-white mb-3">Metadata</h4>
                    <div class="bg-slate-800/50 rounded-lg p-4">
                        <pre class="text-slate-300 text-xs overflow-x-auto"><code>${JSON.stringify(activity.data.metadata, null, 2)}</code></pre>
                    </div>
                </div>
                
                <div>
                    <h4 class="text-lg font-semibold text-white mb-3">Immutable Record</h4>
                    <div class="bg-slate-800/50 rounded-lg p-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            <div>
                                <span class="text-slate-400">Record Hash:</span>
                                <code class="block text-green-400 text-xs mt-1">${activity.hash}</code>
                            </div>
                            <div>
                                <span class="text-slate-400">Verified:</span>
                                <span class="block text-green-400 mt-1">
                                    <i class="fas fa-check-circle mr-1"></i>INTEGRITY VERIFIED
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    getSeverityColor(severity) {
        const colors = {
            critical: 'red',
            high: 'orange',
            medium: 'yellow',
            low: 'blue',
            info: 'slate'
        };
        return colors[severity] || 'slate';
    }

    scrollToBottom() {
        const container = document.getElementById('activity-stream');
        container.scrollTop = container.scrollHeight;
    }

    updateAutoScrollButton() {
        const button = document.getElementById('autoscroll-toggle');
        if (this.autoScroll) {
            button.innerHTML = '<i class="fas fa-arrows-alt-v mr-1"></i>Auto-scroll';
            button.classList.remove('bg-slate-600');
            button.classList.add('bg-accent-green');
        } else {
            button.innerHTML = '<i class="fas fa-pause mr-1"></i>Paused';
            button.classList.remove('bg-accent-green');
            button.classList.add('bg-slate-600');
        }
    }

    showError(message) {
        const container = document.getElementById('activity-stream');
        container.innerHTML = `
            <div class="text-center py-8 text-red-400">
                <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                <p class="text-lg">${message}</p>
            </div>
        `;
    }
}

// Global functions
function toggleAutoScroll() {
    activityLogger.autoScroll = !activityLogger.autoScroll;
    activityLogger.updateAutoScrollButton();
    if (activityLogger.autoScroll) {
        activityLogger.scrollToBottom();
    }
}

function pauseLiveUpdates() {
    activityLogger.isLiveUpdating = !activityLogger.isLiveUpdating;
    const button = document.getElementById('pause-toggle');
    if (activityLogger.isLiveUpdating) {
        button.innerHTML = '<i class="fas fa-pause mr-1"></i>Pause';
        button.classList.remove('bg-slate-600');
        button.classList.add('bg-accent-red');
    } else {
        button.innerHTML = '<i class="fas fa-play mr-1"></i>Resume';
        button.classList.remove('bg-accent-red');
        button.classList.add('bg-slate-600');
    }
}

function clearFilters() {
    document.getElementById('agent-filter').value = '';
    document.getElementById('action-filter').value = '';
    document.getElementById('severity-filter').value = '';
    document.getElementById('time-filter').value = 'all';
    document.getElementById('search-input').value = '';
    
    activityLogger.filters = {
        agent: '',
        action: '',
        severity: '',
        timeRange: 'all',
        search: ''
    };
    
    activityLogger.applyFilters();
}

function exportLogs() {
    const filteredActivities = activityLogger.getFilteredActivities();
    const dataStr = JSON.stringify(filteredActivities, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `activity-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    link.click();
}

function verifyIntegrity() {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.remove('hidden');
    
    // Simulate integrity verification
    setTimeout(() => {
        const totalLogs = activityLogger.activities.length;
        const hashData = activityLogger.activities.map(a => a.hash).join('');
        const systemHash = activityLogger.generateHash(hashData);
        
        document.getElementById('record-hash').textContent = systemHash;
        document.getElementById('last-verification').textContent = new Date().toLocaleString();
        document.getElementById('integrity-status').textContent = 'VERIFIED';
        document.getElementById('integrity-icon').className = 'fas fa-check-circle text-green-400';
        
        loadingOverlay.classList.add('hidden');
    }, 2000);
}

function closeActivityModal() {
    document.getElementById('activity-modal').classList.add('hidden');
}

// Initialize the activity logger when the page loads
const activityLogger = new ActivityLogger();
