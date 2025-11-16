/**
 * Reports Dashboard JavaScript
 * Handles report generation, display, and export functionality
 */

class ReportsManager {
    constructor() {
        this.currentReportId = null;
        this.currentReport = null;
        this.reports = [];
        this.isLoading = false;
        this.viewMode = 'json'; // 'json' or 'formatted'
        this.init();
    }

    init() {
        this.updateSystemTime();
        this.loadReportsSummary();
        this.loadReports();
        
        // Update system time every second
        setInterval(() => this.updateSystemTime(), 1000);
        
        // Auto-refresh reports every 30 seconds
        setInterval(() => this.loadReports(), 30000);
    }

    updateSystemTime() {
        const now = new Date();
        const timeStr = now.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        const timeElement = document.getElementById('system-time');
        if (timeElement) {
            timeElement.textContent = timeStr;
        }
    }

    async loadReportsSummary() {
        try {
            const response = await fetch('/api/reports/summary');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateSummaryDisplay(data.summary);
            }
        } catch (error) {
            console.error('Error loading reports summary:', error);
        }
    }

    updateSummaryDisplay(summary) {
        const elements = {
            'total-reports': summary.total_reports || 0,
            'reports-24h': summary.reports_24h || 0,
            'successful-reports': summary.successful_24h || 0,
            'available-types': summary.available_types || 5
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    async loadReports() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        const loadingElement = document.getElementById('reports-loading');
        const listElement = document.getElementById('reports-list');
        const noReportsElement = document.getElementById('no-reports');

        // Show loading state
        loadingElement?.classList.remove('hidden');
        listElement?.classList.add('hidden');
        noReportsElement?.classList.add('hidden');

        try {
            const response = await fetch('/api/reports');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.reports = data.reports || [];
                this.displayReports();
            } else {
                throw new Error('Failed to load reports');
            }
        } catch (error) {
            console.error('Error loading reports:', error);
            this.showError('Failed to load reports');
        } finally {
            this.isLoading = false;
            loadingElement?.classList.add('hidden');
        }
    }

    displayReports() {
        const listElement = document.getElementById('reports-list');
        const noReportsElement = document.getElementById('no-reports');

        if (!this.reports || this.reports.length === 0) {
            listElement?.classList.add('hidden');
            noReportsElement?.classList.remove('hidden');
            return;
        }

        noReportsElement?.classList.add('hidden');
        listElement?.classList.remove('hidden');

        if (listElement) {
            listElement.innerHTML = this.reports.map(report => this.createReportCard(report)).join('');
        }
    }

    createReportCard(report) {
        const statusColor = report.status === 'completed' ? 'green' : 
                           report.status === 'failed' ? 'red' : 'yellow';
        
        const reportTypeNames = {
            'agent_activity': 'Agent Activity',
            'system_status': 'System Status',
            'security_summary': 'Security Summary',
            'compliance_audit': 'Compliance Audit',
            'performance_metrics': 'Performance Metrics'
        };

        const typeName = reportTypeNames[report.type] || report.type;
        const generatedAt = new Date(report.generated_at).toLocaleString();

        return `
            <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/30 hover:border-slate-600/50 transition-all">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-3">
                            <div class="text-lg font-medium text-white">${typeName}</div>
                            <span class="px-2 py-1 text-xs rounded-full bg-${statusColor}-500/20 text-${statusColor}-400">
                                ${report.status.toUpperCase()}
                            </span>
                        </div>
                        <div class="text-sm text-slate-400 mt-1">
                            <i class="fas fa-clock mr-1"></i>Generated: ${generatedAt}
                        </div>
                        <div class="text-sm text-slate-400">
                            <i class="fas fa-tag mr-1"></i>ID: ${report.id}
                        </div>
                    </div>
                    
                    <div class="flex items-center space-x-2">
                        <button onclick="reportsManager.viewReport('${report.id}')" 
                                class="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded-lg text-sm transition-all">
                            <i class="fas fa-eye mr-1"></i>View
                        </button>
                        
                        <div class="relative">
                            <button onclick="reportsManager.toggleExportMenu('${report.id}')" 
                                    class="bg-slate-600 hover:bg-slate-700 px-3 py-2 rounded-lg text-sm transition-all">
                                <i class="fas fa-download mr-1"></i>Export
                            </button>
                            <div id="export-menu-${report.id}" class="hidden absolute right-0 mt-2 bg-dark-card border border-slate-600 rounded-lg shadow-lg z-10">
                                <button onclick="reportsManager.downloadReport('${report.id}', 'json')" 
                                        class="block w-full text-left px-4 py-2 hover:bg-slate-700 text-sm">JSON</button>
                                <button onclick="reportsManager.downloadReport('${report.id}', 'csv')" 
                                        class="block w-full text-left px-4 py-2 hover:bg-slate-700 text-sm">CSV</button>
                                <button onclick="reportsManager.downloadReport('${report.id}', 'text')" 
                                        class="block w-full text-left px-4 py-2 hover:bg-slate-700 text-sm">Text</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async generateReport() {
        const reportType = document.getElementById('report-type')?.value;
        const timePeriod = document.getElementById('time-period')?.value;

        if (!reportType) {
            this.showError('Please select a report type');
            return;
        }

        try {
            this.showLoading('Generating report...');
            
            const response = await fetch(`/api/reports/generate?report_type=${encodeURIComponent(reportType)}&time_period=${encodeURIComponent(timePeriod)}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showSuccess('Report generated successfully!');
                await this.loadReports();
                await this.loadReportsSummary();
            } else {
                throw new Error(data.detail || 'Failed to generate report');
            }
        } catch (error) {
            console.error('Error generating report:', error);
            this.showError('Failed to generate report: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async viewReport(reportId) {
        try {
            const response = await fetch(`/api/reports/${reportId}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentReportId = reportId;
                this.currentReport = data.report;
                this.showReportModal(data.report);
            } else {
                throw new Error('Failed to load report details');
            }
        } catch (error) {
            console.error('Error viewing report:', error);
            this.showError('Failed to load report details');
        }
    }

    showReportModal(report) {
        const modal = document.getElementById('report-modal');
        const title = document.getElementById('modal-title');

        if (title) {
            title.textContent = `${report.type.replace('_', ' ').toUpperCase()} Report`;
        }

        // Reset view mode to JSON
        this.viewMode = 'json';
        this.updateReportView();
        this.updateViewButtons();

        modal?.classList.remove('hidden');
    }

    updateReportView() {
        const jsonContent = document.getElementById('modal-content');
        const formattedContent = document.getElementById('modal-content-formatted');

        if (this.viewMode === 'json') {
            jsonContent?.classList.remove('hidden');
            formattedContent?.classList.add('hidden');
            
            if (jsonContent && this.currentReport) {
                jsonContent.textContent = JSON.stringify(this.currentReport, null, 2);
            }
        } else {
            jsonContent?.classList.add('hidden');
            formattedContent?.classList.remove('hidden');
            
            if (formattedContent && this.currentReport) {
                formattedContent.innerHTML = this.formatReportData(this.currentReport);
            }
        }
    }

    formatReportData(report) {
        const reportTypeNames = {
            'agent_activity': 'Agent Activity Report',
            'system_status': 'System Status Report',
            'security_summary': 'Security Summary Report',
            'compliance_audit': 'Compliance Audit Report',
            'performance_metrics': 'Performance Metrics Report'
        };

        const typeName = reportTypeNames[report.type] || report.type;
        let html = `
            <div class="space-y-6">
                <div class="border-b border-slate-600 pb-4">
                    <h2 class="text-xl font-bold text-white mb-2">${typeName}</h2>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                            <span class="text-slate-400">Report ID:</span>
                            <div class="font-mono text-blue-300">${report.id}</div>
                        </div>
                        <div>
                            <span class="text-slate-400">Generated:</span>
                            <div class="text-green-300">${new Date(report.generated_at).toLocaleString()}</div>
                        </div>
                        <div>
                            <span class="text-slate-400">Status:</span>
                            <div class="text-${report.status === 'completed' ? 'green' : 'red'}-300 font-semibold">
                                ${report.status.toUpperCase()}
                            </div>
                        </div>
                    </div>
                </div>
        `;

        // Format specific report data based on type
        if (report.data) {
            html += this.formatSpecificReportData(report.type, report.data);
        }

        html += '</div>';
        return html;
    }

    formatSpecificReportData(reportType, data) {
        switch (reportType) {
            case 'agent_activity':
                return this.formatAgentActivityData(data);
            case 'system_status':
                return this.formatSystemStatusData(data);
            case 'security_summary':
                return this.formatSecuritySummaryData(data);
            case 'compliance_audit':
                return this.formatComplianceAuditData(data);
            case 'performance_metrics':
                return this.formatPerformanceMetricsData(data);
            default:
                return this.formatGenericData(data);
        }
    }

    formatAgentActivityData(data) {
        let html = '';
        
        if (data.agent_stats) {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-orange-300 mb-3">
                        <i class="fas fa-users mr-2"></i>Agent Statistics
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-blue-300">${data.agent_stats.total_agents}</div>
                            <div class="text-xs text-slate-400">Total Agents</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-green-300">${data.agent_stats.active_agents}</div>
                            <div class="text-xs text-slate-400">Active</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-yellow-300">${data.agent_stats.idle_agents}</div>
                            <div class="text-xs text-slate-400">Idle</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-red-300">${data.agent_stats.offline_agents}</div>
                            <div class="text-xs text-slate-400">Offline</div>
                        </div>
                    </div>
                </div>
            `;
        }

        if (data.activity_metrics) {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-green-300 mb-3">
                        <i class="fas fa-tasks mr-2"></i>Activity Metrics
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-purple-300">${data.activity_metrics.total_tasks}</div>
                            <div class="text-xs text-slate-400">Total Tasks</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-green-300">${data.activity_metrics.completed_tasks}</div>
                            <div class="text-xs text-slate-400">Completed</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-red-300">${data.activity_metrics.failed_tasks}</div>
                            <div class="text-xs text-slate-400">Failed</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-blue-300">${data.activity_metrics.success_rate}</div>
                            <div class="text-xs text-slate-400">Success Rate</div>
                        </div>
                    </div>
                </div>
            `;
        }

        if (data.top_performing_agents && data.top_performing_agents.length > 0) {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-yellow-300 mb-3">
                        <i class="fas fa-trophy mr-2"></i>Top Performing Agents
                    </h3>
                    <div class="space-y-2">
            `;
            
            data.top_performing_agents.forEach((agent, index) => {
                const medals = ['🥇', '🥈', '🥉'];
                const medal = medals[index] || '🏆';
                html += `
                    <div class="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">${medal}</span>
                            <div>
                                <div class="text-white font-medium">${agent.name}</div>
                                <div class="text-slate-400 text-sm">ID: ${agent.id}</div>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-green-300 font-bold">${agent.tasks_completed}</div>
                            <div class="text-slate-400 text-xs">Tasks Completed</div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }

        return html;
    }

    formatSystemStatusData(data) {
        let html = '';
        
        if (data.system_health) {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-green-300 mb-3">
                        <i class="fas fa-heartbeat mr-2"></i>System Health
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-green-300">${data.system_health.overall_status.toUpperCase()}</div>
                            <div class="text-xs text-slate-400">Overall Status</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-blue-300">${data.system_health.uptime}</div>
                            <div class="text-xs text-slate-400">Uptime</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-green-300">${data.system_health.active_services}</div>
                            <div class="text-xs text-slate-400">Active Services</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-red-300">${data.system_health.failed_services}</div>
                            <div class="text-xs text-slate-400">Failed Services</div>
                        </div>
                    </div>
                </div>
            `;
        }

        if (data.resource_usage) {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-purple-300 mb-3">
                        <i class="fas fa-server mr-2"></i>Resource Usage
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-yellow-300">${data.resource_usage.cpu_usage}</div>
                            <div class="text-xs text-slate-400">CPU Usage</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-orange-300">${data.resource_usage.memory_usage}</div>
                            <div class="text-xs text-slate-400">Memory Usage</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-blue-300">${data.resource_usage.disk_usage}</div>
                            <div class="text-xs text-slate-400">Disk Usage</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-green-300">${data.resource_usage.network_io}</div>
                            <div class="text-xs text-slate-400">Network I/O</div>
                        </div>
                    </div>
                </div>
            `;
        }

        return html;
    }

    formatSecuritySummaryData(data) {
        let html = '';
        
        if (data.security_events) {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-red-300 mb-3">
                        <i class="fas fa-shield-alt mr-2"></i>Security Events
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-blue-300">${data.security_events.total_events}</div>
                            <div class="text-xs text-slate-400">Total Events</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-red-300">${data.security_events.high_severity}</div>
                            <div class="text-xs text-slate-400">High Severity</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-yellow-300">${data.security_events.medium_severity}</div>
                            <div class="text-xs text-slate-400">Medium Severity</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-green-300">${data.security_events.low_severity}</div>
                            <div class="text-xs text-slate-400">Low Severity</div>
                        </div>
                    </div>
                </div>
            `;
        }

        return html;
    }

    formatComplianceAuditData(data) {
        let html = '';
        
        if (data.compliance_status) {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-purple-300 mb-3">
                        <i class="fas fa-check-circle mr-2"></i>Compliance Status
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-green-300">${data.compliance_status.overall_score}</div>
                            <div class="text-xs text-slate-400">Overall Score</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-blue-300">${data.compliance_status.passed_checks}</div>
                            <div class="text-xs text-slate-400">Passed Checks</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-red-300">${data.compliance_status.failed_checks}</div>
                            <div class="text-xs text-slate-400">Failed Checks</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-2xl font-bold text-yellow-300">${data.compliance_status.pending_reviews}</div>
                            <div class="text-xs text-slate-400">Pending Reviews</div>
                        </div>
                    </div>
                </div>
            `;
        }

        return html;
    }

    formatPerformanceMetricsData(data) {
        let html = '';
        
        if (data.response_times) {
            html += `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-blue-300 mb-3">
                        <i class="fas fa-tachometer-alt mr-2"></i>Response Times
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-green-300">${data.response_times.avg_response_time}</div>
                            <div class="text-xs text-slate-400">Average</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-blue-300">${data.response_times.min_response_time}</div>
                            <div class="text-xs text-slate-400">Minimum</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-red-300">${data.response_times.max_response_time}</div>
                            <div class="text-xs text-slate-400">Maximum</div>
                        </div>
                        <div class="bg-slate-700/50 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-purple-300">${data.response_times['95th_percentile']}</div>
                            <div class="text-xs text-slate-400">95th Percentile</div>
                        </div>
                    </div>
                </div>
            `;
        }

        return html;
    }

    formatGenericData(data) {
        let html = '<div class="space-y-4">';
        
        Object.entries(data).forEach(([key, value]) => {
            html += `
                <div class="bg-slate-700/50 p-4 rounded-lg">
                    <h4 class="text-white font-semibold mb-2">${key.replace(/_/g, ' ').toUpperCase()}</h4>
                    <pre class="text-sm text-slate-300 whitespace-pre-wrap">${JSON.stringify(value, null, 2)}</pre>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }

    toggleReportView(mode) {
        this.viewMode = mode;
        this.updateReportView();
        this.updateViewButtons();
    }

    updateViewButtons() {
        const jsonBtn = document.getElementById('json-view-btn');
        const formattedBtn = document.getElementById('formatted-view-btn');

        if (this.viewMode === 'json') {
            jsonBtn?.classList.add('bg-blue-600', 'text-white');
            jsonBtn?.classList.remove('bg-slate-600', 'hover:bg-slate-500', 'text-slate-300');
            
            formattedBtn?.classList.remove('bg-blue-600', 'text-white');
            formattedBtn?.classList.add('bg-slate-600', 'hover:bg-slate-500', 'text-slate-300');
        } else {
            formattedBtn?.classList.add('bg-blue-600', 'text-white');
            formattedBtn?.classList.remove('bg-slate-600', 'hover:bg-slate-500', 'text-slate-300');
            
            jsonBtn?.classList.remove('bg-blue-600', 'text-white');
            jsonBtn?.classList.add('bg-slate-600', 'hover:bg-slate-500', 'text-slate-300');
        }
    }

    closeModal() {
        const modal = document.getElementById('report-modal');
        modal?.classList.add('hidden');
        this.currentReportId = null;
        this.currentReport = null;
        this.viewMode = 'json'; // Reset to default
    }

    async downloadReport(reportId, format) {
        try {
            const response = await fetch(`/api/reports/${reportId}/export?format=${format}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `report_${reportId}.${format}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showSuccess(`Report exported as ${format.toUpperCase()}`);
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Error exporting report:', error);
            this.showError('Failed to export report');
        }
        
        // Hide export menu
        this.toggleExportMenu(reportId, false);
    }

    toggleExportMenu(reportId, show = null) {
        const menu = document.getElementById(`export-menu-${reportId}`);
        if (menu) {
            if (show === null) {
                menu.classList.toggle('hidden');
            } else {
                menu.classList.toggle('hidden', !show);
            }
        }
    }

    async refreshReports() {
        await this.loadReports();
        await this.loadReportsSummary();
        this.showSuccess('Reports refreshed');
    }

    async exportReport(format) {
        if (this.currentReportId) {
            await this.downloadReport(this.currentReportId, format);
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showLoading(message) {
        this.showNotification(message, 'loading');
    }

    hideLoading() {
        // Remove loading notifications
        const notifications = document.querySelectorAll('.notification.loading');
        notifications.forEach(notification => notification.remove());
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type} fixed top-20 right-4 px-4 py-3 rounded-lg z-50 animate-slide-up`;
        
        const bgColors = {
            success: 'bg-green-600',
            error: 'bg-red-600',
            loading: 'bg-blue-600'
        };

        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            loading: 'fas fa-spinner fa-spin'
        };

        notification.className += ` ${bgColors[type]}`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="${icons[type]} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        if (type !== 'loading') {
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    }
}

// Initialize reports manager
let reportsManager;

document.addEventListener('DOMContentLoaded', function() {
    reportsManager = new ReportsManager();
});

// Global functions for HTML onclick handlers
function generateReport() {
    reportsManager.generateReport();
}

function refreshReports() {
    reportsManager.refreshReports();
}

function closeModal() {
    reportsManager.closeModal();
}

function exportReport(format) {
    reportsManager.exportReport(format);
}

function toggleReportView(mode) {
    reportsManager.toggleReportView(mode);
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('report-modal');
    if (event.target === modal) {
        reportsManager.closeModal();
    }
});

// Close export menus when clicking elsewhere
document.addEventListener('click', function(event) {
    if (!event.target.closest('.relative')) {
        document.querySelectorAll('[id^="export-menu-"]').forEach(menu => {
            menu.classList.add('hidden');
        });
    }
});
