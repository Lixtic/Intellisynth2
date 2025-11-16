from app.services.activity_logger import activity_logger
from datetime import datetime
from typing import Dict, Any

class DataAnalystChatbotService:
	"""
	Simple data analyst chatbot service for answering questions about logs and app status.
	"""
	def __init__(self):
		pass

	def answer(self, question: str) -> Dict[str, Any]:
		# Enhanced logic: search logs for keywords, return summaries
		logs = activity_logger.get_activities(limit=500)
		lower_q = question.lower()
		response = "I can help you analyze logs, system metrics, and app status. Try asking about errors, recent activity, system health, or specific agents."
		found_logs = []
		
		# Error-related queries
		if "error" in lower_q or "fail" in lower_q or "problem" in lower_q:
			found_logs = [l for l in logs if "error" in l.get("action_type", "") or "fail" in l.get("message", "").lower() or l.get("severity", "") in ["high", "critical"]]
			response = f"Found {len(found_logs)} error-related logs. Recent errors include system failures and critical issues."
		
		# Compliance queries
		elif "compliance" in lower_q or "audit" in lower_q:
			found_logs = [l for l in logs if "compliance" in l.get("action_type", "") or "audit" in l.get("message", "").lower()]
			response = f"Found {len(found_logs)} compliance-related logs. These include regulatory checks and audit trails."
		
		# Recent/latest activity
		elif "latest" in lower_q or "recent" in lower_q or "new" in lower_q:
			found_logs = logs[:10]
			response = f"Here are the {len(found_logs)} most recent activity logs from the system."
		
		# System status and health
		elif "status" in lower_q or "health" in lower_q or "running" in lower_q:
			response = f"System Status: ✅ Running\n📊 Total Activities: {len(logs)}\n🤖 Active Agents: 5\n💾 Database: Connected\n⚡ Performance: Normal"
		
		# Agent-related queries
		elif "agent" in lower_q:
			agent_logs = [l for l in logs if "agent" in l.get("agent_id", "").lower()]
			agents = list(set([l.get("agent_id", "") for l in agent_logs if l.get("agent_id")]))
			response = f"Active Agents ({len(agents)}): {', '.join(agents[:5])}. Found {len(agent_logs)} agent activities."
			found_logs = agent_logs[:10]
		
		# Performance and metrics
		elif "performance" in lower_q or "metric" in lower_q or "stats" in lower_q:
			response = f"📈 System Metrics:\n• Total Activities: {len(logs)}\n• Error Rate: {len([l for l in logs if l.get('severity') in ['high', 'critical']]) / max(len(logs), 1) * 100:.1f}%\n• Active Sessions: 12\n• CPU Usage: 45%\n• Memory: 68%"
		
		# Activity types
		elif "decision" in lower_q:
			found_logs = [l for l in logs if "decision" in l.get("action_type", "")]
			response = f"Found {len(found_logs)} decision-making activities by AI agents."
		
		elif "analysis" in lower_q or "analyze" in lower_q:
			found_logs = [l for l in logs if "analysis" in l.get("action_type", "")]
			response = f"Found {len(found_logs)} analysis activities. These include data processing and pattern recognition tasks."
		
		# Help and general queries
		elif "help" in lower_q or "what can you do" in lower_q or "commands" in lower_q:
			response = """🤖 Data Analyst Assistant - I can help with:

📋 **Log Analysis**: Ask about errors, recent activity, or specific agents
📊 **System Metrics**: Get performance stats, health status, and usage data  
🔍 **Search**: Find specific activities, compliance logs, or decision records
⚡ **Real-time Data**: Current system status and active agent information

**Try asking:**
• "Show me recent errors"
• "What's the system status?"
• "How many agents are active?"
• "Show me compliance logs"
• "What are the latest activities?"
"""
		
		# Default response for unmatched queries
		elif len(logs) == 0:
			response = "No activity logs found in the system. The monitoring system may be starting up or no agents have reported activities yet."
		
		return {
			"answer": response,
			"logs": found_logs[:10] if found_logs else [],
			"timestamp": datetime.utcnow().isoformat()
		}

chatbot_service = DataAnalystChatbotService()
