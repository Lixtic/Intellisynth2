document.addEventListener('DOMContentLoaded', () => {
	const chatbotToggle = document.getElementById('chatbot-toggle');
	const chatbotWindow = document.getElementById('chatbot-window');
	const chatbotClose = document.getElementById('chatbot-close');
	const chatSend = document.getElementById('chat-send');
	const chatInput = document.getElementById('chat-input');
	const chatMessages = document.getElementById('chat-messages');

	if (!chatbotToggle || !chatbotWindow || !chatSend || !chatInput || !chatMessages) {
		return;
	}

	const sampleData = {
		logs: [
			{ timestamp: '2025-08-20T10:15:30Z', agent_id: 'agent-1', action: 'analysis', message: 'Processed data batch 123', severity: 'info' },
			{ timestamp: '2025-08-20T10:20:45Z', agent_id: 'agent-2', action: 'error', message: 'Failed to connect to database', severity: 'high' },
			{ timestamp: '2025-08-20T10:25:10Z', agent_id: 'anomaly-detector', action: 'detection', message: 'Detected 3 anomalies', severity: 'medium' },
			{ timestamp: '2025-08-20T10:30:00Z', agent_id: 'agent-3', action: 'decision', message: 'Approved transaction', severity: 'info' }
		],
		anomalies: [
			{ id: 'STAT-1724145930', type: 'statistical_outlier', metric: 'error_rate', value: 0.15, severity: 'medium', timestamp: '2025-08-20T10:25:30Z', description: 'Error rate higher than baseline' },
			{ id: 'PAT-agent1-1724145945', type: 'activity_pattern', agent_id: 'agent-1', metric: 'activity_rate_per_hour', value: 25, severity: 'low', timestamp: '2025-08-20T10:25:45Z', description: 'Low activity rate' }
		],
		metrics: {
			cpu_usage: 45,
			memory_usage: 68,
			error_rate: 0.02,
			active_agents: 11,
			tasks_completed: 1847,
			compliance_score: 89
		},
		appInfo: {
			version: '1.0.0',
			uptime: '99.9%',
			api_endpoints: 18,
			last_check: '5 min ago'
		}
	};

	const sendMessage = () => {
		const message = chatInput.value.trim();
		if (!message) return;

		addMessage('User', message);
		chatInput.value = '';
		chatMessages.scrollTop = chatMessages.scrollHeight;

		setTimeout(() => {
			const response = analyzeQuery(message);
			addMessage('AI', response);
			chatMessages.scrollTop = chatMessages.scrollHeight;
		}, 400);
	};

	const addMessage = (sender, content) => {
		const msgDiv = document.createElement('div');
		msgDiv.classList.add('flex', sender === 'User' ? 'justify-end' : 'justify-start');
		const bubbleClass = sender === 'User' ? 'bg-accent-blue text-white' : 'bg-slate-700 text-white';
		msgDiv.innerHTML = `<div class="${bubbleClass} px-4 py-2 rounded-lg max-w-[80%] whitespace-pre-wrap">${content}</div>`;
		chatMessages.appendChild(msgDiv);
	};

	const analyzeQuery = (query) => {
		const lowerQuery = query.toLowerCase();

		if (lowerQuery.includes('logs')) {
			if (lowerQuery.includes('error')) {
				const errorLogs = sampleData.logs.filter(log => log.severity === 'high' || log.action === 'error');
				return formatLogs(errorLogs, 'Error Logs:');
			}
			if (lowerQuery.includes('agent')) {
				const agentId = extractAgentId(query);
				if (agentId) {
					const agentLogs = sampleData.logs.filter(log => log.agent_id === agentId);
					return formatLogs(agentLogs, `Logs for ${agentId}:`);
				}
			}
			if (lowerQuery.includes('recent')) {
				const recentLogs = sampleData.logs.slice(-5);
				return formatLogs(recentLogs, 'Recent Logs:');
			}
			return formatLogs(sampleData.logs, 'All Logs:');
		}

		if (lowerQuery.includes('anomalies') || lowerQuery.includes('anomaly')) {
			if (lowerQuery.includes('recent')) {
				const recentAnomalies = sampleData.anomalies.slice(-3);
				return formatAnomalies(recentAnomalies, 'Recent Anomalies:');
			}
			if (lowerQuery.includes('critical') || lowerQuery.includes('high')) {
				const highSeverity = sampleData.anomalies.filter(a => a.severity === 'high' || a.severity === 'critical');
				return formatAnomalies(highSeverity, 'High Severity Anomalies:');
			}
			return formatAnomalies(sampleData.anomalies, 'Detected Anomalies:');
		}

		if (lowerQuery.includes('metrics') || lowerQuery.includes('usage') || lowerQuery.includes('performance')) {
			if (lowerQuery.includes('cpu')) {
				return `Current CPU Usage: ${sampleData.metrics.cpu_usage}%`;
			}
			if (lowerQuery.includes('memory')) {
				return `Current Memory Usage: ${sampleData.metrics.memory_usage}%`;
			}
			if (lowerQuery.includes('error rate')) {
				return `Current Error Rate: ${(sampleData.metrics.error_rate * 100).toFixed(2)}%`;
			}
			if (lowerQuery.includes('active agents')) {
				return `Active Agents: ${sampleData.metrics.active_agents}`;
			}
			if (lowerQuery.includes('tasks')) {
				return `Tasks Completed Today: ${sampleData.metrics.tasks_completed}`;
			}
			if (lowerQuery.includes('compliance')) {
				return `Compliance Score: ${sampleData.metrics.compliance_score}%`;
			}
			return formatMetrics(sampleData.metrics);
		}

		if (lowerQuery.includes('app info') || lowerQuery.includes('version') || lowerQuery.includes('uptime')) {
			return `App Version: ${sampleData.appInfo.version}\nUptime: ${sampleData.appInfo.uptime}\nAPI Endpoints: ${sampleData.appInfo.api_endpoints}\nLast Check: ${sampleData.appInfo.last_check}`;
		}

		return 'Sorry, I didn\'t understand that query. Please ask about logs, anomalies, metrics, or app information.';
	};

	const formatLogs = (logs, title) => {
		if (!logs.length) return 'No logs found.';
		const entries = logs.map(log => `[${log.timestamp}] ${log.agent_id}: ${log.message} (Severity: ${log.severity})`);
		return `${title}\n\n${entries.join('\n')}`;
	};

	const formatAnomalies = (anomalies, title) => {
		if (!anomalies.length) return 'No anomalies found.';
		const entries = anomalies.map(a => `ID: ${a.id} | Type: ${a.type} | Severity: ${a.severity} | ${a.description}`);
		return `${title}\n\n${entries.join('\n')}`;
	};

	const formatMetrics = (metrics) => {
		return `System Metrics:\n- CPU: ${metrics.cpu_usage}%\n- Memory: ${metrics.memory_usage}%\n- Error Rate: ${(metrics.error_rate * 100).toFixed(2)}%\n- Active Agents: ${metrics.active_agents}\n- Tasks Today: ${metrics.tasks_completed}\n- Compliance: ${metrics.compliance_score}%`;
	};

	const extractAgentId = (query) => {
		const match = query.match(/agent[\s-]?(\w+)/i);
		return match ? `agent-${match[1]}` : null;
	};

	chatbotToggle.addEventListener('click', () => {
		chatbotWindow.classList.toggle('hidden');
	});

	if (chatbotClose) {
		chatbotClose.addEventListener('click', () => {
			chatbotWindow.classList.add('hidden');
		});
	}

	chatSend.addEventListener('click', sendMessage);
	chatInput.addEventListener('keypress', (e) => {
		if (e.key === 'Enter') {
			sendMessage();
		}
	});

	addMessage('AI', 'Hello! I\'m the Data Analyst Assistant. Ask me about logs, anomalies, metrics, or app information.');
});
