from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import random
import hashlib

# Import activity logger service
from app.services.activity_logger import activity_logger

# Pydantic models for activity logging
class ActivityLogCreate(BaseModel):
    agent_id: str = Field(..., description="Unique identifier for the agent")
    action_type: str = Field(..., description="Type of action performed")
    severity: str = Field("info", description="Severity level: info, warning, error, critical")
    message: str = Field(..., description="Human-readable description of the activity")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional structured data")
    user_id: Optional[str] = Field(None, description="User ID if applicable")
    session_id: Optional[str] = Field(None, description="Session ID if applicable")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced OpenAPI metadata with categorical organization
tags_metadata = [
    {
        "name": "🏠 Core Application",
        "description": "Main application endpoints including dashboard, login, and health checks",
    },
    {
        "name": "🔐 Authentication", 
        "description": "Authentication and authorization endpoints with demo account support",
    },
    {
        "name": "🔧 System Services",
        "description": "System service status and configuration endpoints",
    },
    {
        "name": "📊 Agent Monitoring",
        "description": "AI agent monitoring, metrics, and activity tracking endpoints",
    },
    {
        "name": "� Activity Log",
        "description": "Real-time activity logging with transparent immutable record of all AI agent interactions",
    },
    {
        "name": "�🔍 Audit & Compliance",
        "description": "Compliance monitoring and audit trail endpoints",
    },
    {
        "name": "🔒 Security & Anomalies",
        "description": "Security monitoring and anomaly detection endpoints",
    },
    {
        "name": "✅ Approval Workflows",
        "description": "Approval request management and workflow endpoints",
    },
]

# Initialize FastAPI with enhanced documentation
app = FastAPI(
    title="🚀 IntelliSynth Solution API",
    description="""
    **Comprehensive AI Agent Monitoring and Compliance System**
    
    A powerful monitoring platform for AI agents with real-time dashboards, 
    compliance tracking, anomaly detection, and comprehensive reporting capabilities.
    
    ## 🌟 Key Features
    
    * **Real-time Monitoring** - Live agent status and system metrics
    * **Compliance Engine** - Automated compliance checking and violations
    * **Security Monitoring** - Threat detection and anomaly analysis
    * **Interactive Dashboard** - Modern responsive UI with charts and widgets
    * **Approval Workflows** - Multi-level approval system for agent actions
    * **Comprehensive Reporting** - Detailed analytics and audit trails
    
    ## 🔗 Quick Access
    
    * **Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
    * **Login Page**: [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
    * **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    
    ## 🔑 Demo Credentials
    
    **Username**: `demo` | **Password**: `demo123`
    """,
    version="1.0.0",
    contact={
        "name": "IntelliSynth Solution Support",
        "email": "support@intellisynth.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=tags_metadata,
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 🏠 Core Application Endpoints
@app.get("/", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="Main Dashboard",
         description="Interactive dashboard with real-time monitoring, charts, and system status widgets")
async def dashboard(request: Request):
    """Main dashboard with comprehensive monitoring interface"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/compliance", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="Compliance Management",
         description="Comprehensive compliance management interface with violation tracking, rule management, and reporting")
async def compliance_management(request: Request):
    """Compliance management interface with full violation tracking and rule management"""
    return templates.TemplateResponse("compliance.html", {"request": request})

@app.get("/activity-log", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="Real-time Activity Log",
         description="Central hub that logs every AI agent action, decision, and data point creating a transparent immutable record")
async def activity_log(request: Request):
    """Real-time activity log - transparent immutable record of all AI agent interactions"""
    return templates.TemplateResponse("activity-log.html", {"request": request})

@app.get("/login", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="Login Page",
         description="User authentication page with demo credentials (demo/demo123)")
async def login(request: Request):
    """Login page for user authentication"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/test", tags=["🏠 Core Application"],
         summary="API Test Endpoint", 
         description="Simple test endpoint to verify API connectivity and response")
async def test():
    """Test endpoint for API connectivity"""
    return {
        "message": "IntelliSynth Solution API is running!",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "operational"
    }

@app.get("/health", tags=["🏠 Core Application"],
         summary="Health Check",
         description="System health check endpoint for monitoring and load balancer probes")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "99.9%",
        "version": "1.0.0"
    }

@app.get("/api/info", tags=["🏠 Core Application"],
         summary="API Information",
         description="Comprehensive API information including version, features, and endpoint statistics")
async def api_info():
    """Get API information and statistics"""
    return {
        "name": "IntelliSynth Solution API",
        "version": "1.0.0",
        "description": "Comprehensive AI Agent Monitoring and Compliance System",
        "features": [
            "Real-time agent monitoring",
            "Compliance tracking",
            "Anomaly detection", 
            "Security monitoring",
            "Approval workflows",
            "Interactive dashboard"
        ],
        "endpoints": {
            "total": 18,
            "categories": 7,
            "documentation": "/docs"
        },
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

# 🔐 Authentication Endpoints
@app.post("/api/auth/login", tags=["🔐 Authentication"],
          summary="Main Login Endpoint",
          description="Primary authentication endpoint supporting JSON login with demo account (demo/demo123)")
async def login_api(credentials: dict):
    """Authenticate user with JSON credentials"""
    username = credentials.get("username")
    password = credentials.get("password")
    
    # Demo authentication
    if username == "demo" and password == "demo123":
        return {
            "success": True,
            "message": "Login successful",
            "token": f"demo_token_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "user": {
                "username": username,
                "role": "demo_user",
                "permissions": ["read", "monitor"]
            }
        }
    
    return {"success": False, "message": "Invalid credentials"}

@app.post("/login", tags=["🔐 Authentication"],
          summary="Form-based Login",
          description="Form-based authentication endpoint for web interface login")
async def login_form(request: Request):
    """Handle form-based login"""
    # This would typically process form data
    return {"message": "Login processed", "redirect": "/"}

@app.get("/api/auth/test", tags=["🔐 Authentication"],
         summary="Test Authentication",
         description="Test authentication endpoint with automatic demo credential validation")
async def test_auth():
    """Test authentication endpoint"""
    return {
        "message": "Authentication test endpoint",
        "demo_account": {
            "username": "demo",
            "password": "demo123",
            "note": "Use these credentials for testing"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/auth/status", tags=["🔐 Authentication"],
         summary="Authentication Status",
         description="Get current authentication status and demo account information")
async def auth_status():
    """Get authentication status"""
    return {
        "authenticated": False,
        "demo_available": True,
        "demo_credentials": {
            "username": "demo", 
            "password": "demo123"
        },
        "session_timeout": "24 hours",
        "timestamp": datetime.utcnow().isoformat()
    }

# � Activity Log Endpoints - Central hub for transparent, immutable record of all AI agent interactions
@app.get("/api/activity-logs", tags=["📋 Activity Log"],
         summary="Get Activity Logs",
         description="Retrieve activity logs with filtering and pagination for transparent AI agent monitoring")
async def get_activity_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    since: Optional[str] = Query(None, description="Get logs since timestamp")
):
    """Get activity logs with comprehensive filtering and immutable record tracking"""
    
    # Parse since parameter
    since_datetime = None
    if since:
        try:
            since_datetime = datetime.fromisoformat(since.replace('Z', ''))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format for 'since' parameter")
    
    # Get activities from the activity logger service
    activities = activity_logger.get_activities(
        limit=limit,
        agent_id=agent_id,
        action_type=action_type,
        severity=severity,
        since=since_datetime
    )
    return activities

@app.get("/api/activity-logs/latest", tags=["📋 Activity Log"],
         summary="Get Latest Activity Logs",
         description="Get the latest activity logs since a specific timestamp for real-time updates")
async def get_latest_activities(
    since: str = Query(..., description="Get activities since this timestamp"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of activities to return")
):
    """Get latest activity logs for real-time streaming"""
    
    try:
        since_datetime = datetime.fromisoformat(since.replace('Z', ''))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")
    
    # Get latest activities
    activities = activity_logger.get_latest_activities(since_datetime, limit)
    return activities

@app.get("/api/activity-logs/stats", tags=["📋 Activity Log"],
         summary="Get Activity Statistics",
         description="Get aggregated statistics for activity logs including counts, performance metrics, and agent activity")
async def get_activity_stats(
    since: Optional[str] = Query(None, description="Calculate stats since this timestamp")
):
    """Get comprehensive activity log statistics"""
    
    # Get stats from the activity logger service
    stats = activity_logger.get_activity_stats()
    # Remove simulated values: always return empty hourly_activity and agent_distribution if no activities
    if not stats.get('total_activities'):
        stats['hourly_activity'] = [0] * 24
        stats['agent_distribution'] = {}
    return stats

@app.get("/api/agents", tags=["📋 Activity Log"],
         summary="Get Active Agents",
         description="Get list of active AI agents with their current status and activity metrics")
async def get_agents():
    """Get list of active AI agents for filtering and monitoring"""
    
    # Return empty list (no simulated agents)
    return []

@app.get("/api/activity-logs/verify-integrity", tags=["📋 Activity Log"],
         summary="Verify Record Integrity",
         description="Verify the integrity of the immutable activity log records using cryptographic hashes")
async def verify_integrity():
    """Verify the integrity of the immutable activity log records"""
    
    # Use the activity logger's verify_integrity method
    return activity_logger.verify_integrity()

# Helper functions for generating sample and real-time data
async def generate_sample_activities():
    """Generate sample activities for demonstration"""
    agents = ['ai-monitor', 'compliance-agent', 'security-scanner', 'data-analyst', 'anomaly-detector']
    actions = ['decision', 'data_collection', 'analysis', 'compliance_check', 'security_scan']
    
    # Generate 50 sample activities
    for i in range(50):
        agent = random.choice(agents)
        action = random.choice(actions)
        
        # Create activity based on action type
        if action == 'decision':
            await activity_logger.log_decision(
                agent_id=agent,
                decision=f"Sample decision {i+1}",
                reasoning=f"Based on analysis of current system state",
                confidence=random.uniform(0.7, 0.95)
            )
        elif action == 'data_collection':
            await activity_logger.log_data_collection(
                agent_id=agent,
                data_source=f"data_source_{random.randint(1, 5)}",
                records_collected=random.randint(10, 500),
                processing_time=random.uniform(0.5, 3.0)
            )
        elif action == 'analysis':
            await activity_logger.log_analysis(
                agent_id=agent,
                analysis_type=f"analysis_type_{random.randint(1, 3)}",
                results={"status": "completed", "findings": random.randint(1, 10)},
                accuracy=random.uniform(0.85, 0.99)
            )
        elif action == 'compliance_check':
            violations = random.randint(0, 3)
            await activity_logger.log_compliance_check(
                agent_id=agent,
                rule_id=f"rule_{random.randint(1, 10)}",
                rule_name=f"Compliance Rule {random.randint(1, 10)}",
                compliance_status="compliant" if violations == 0 else "violation",
                violations_found=violations
            )
        elif action == 'security_scan':
            threats = random.randint(0, 2)
            await activity_logger.log_security_scan(
                agent_id=agent,
                scan_type=f"security_scan_{random.randint(1, 3)}",
                threats_detected=threats,
                scan_duration=random.uniform(1.0, 5.0),
                severity_level="high" if threats > 0 else "low"
            )

async def generate_realtime_activity():
    """Generate a single real-time activity"""
    agents = ['ai-monitor', 'compliance-agent', 'security-scanner', 'data-analyst', 'anomaly-detector']
    actions = ['decision', 'data_collection', 'analysis', 'compliance_check', 'security_scan']
    
    agent = random.choice(agents)
    action = random.choice(actions)
    
    if action == 'decision':
        await activity_logger.log_decision(
            agent_id=agent,
            decision="Real-time decision",
            reasoning="Based on current system state",
            confidence=random.uniform(0.8, 0.95)
        )
    elif action == 'data_collection':
        await activity_logger.log_data_collection(
            agent_id=agent,
            data_source="real_time_source",
            records_collected=random.randint(1, 50),
            processing_time=random.uniform(0.1, 2.0)
        )
    elif action == 'analysis':
        await activity_logger.log_analysis(
            agent_id=agent,
            analysis_type="real_time_analysis",
            results={"status": "completed", "priority": "normal"},
            accuracy=random.uniform(0.9, 0.99)
        )
    else:
        # Generic activity for other types
        await activity_logger.log_activity(
            agent_id=agent,
            action_type=action,
            message=f"Real-time {action} operation completed",
            severity=random.choice(['info', 'low', 'medium']),
            data={
                'real_time': True,
                'execution_time': random.randint(100, 2000),
                'metadata': {
                    'context': action,
                    'confidence': random.uniform(0.8, 0.95),
                    'impact_score': random.uniform(3, 7)
                }
            }
        )

# �🔧 System Services Endpoint
@app.get("/api/services/status", tags=["🔧 System Services"],
         summary="Service Status Overview",
         description="Comprehensive overview of all system services including health status and performance metrics")
async def services_status():
    """Get status of all system services"""
    return {
        "services": {
            "authentication": {"status": "running", "uptime": "99.9%"},
            "monitoring": {"status": "running", "uptime": "99.8%"},
            "compliance": {"status": "running", "uptime": "99.7%"},
            "security": {"status": "running", "uptime": "99.9%"},
            "reporting": {"status": "running", "uptime": "99.6%"},
            "approval": {"status": "running", "uptime": "99.8%"},
            "integration": {"status": "running", "uptime": "99.5%"},
            "anomaly_detection": {"status": "running", "uptime": "99.7%"}
        },
        "overall_health": "excellent",
        "timestamp": datetime.utcnow().isoformat()
    }

# 📊 Agent Monitoring Endpoints
@app.get("/api/monitoring/metrics", tags=["📊 Agent Monitoring"],
         summary="Dashboard Metrics",
         description="Real-time system metrics for dashboard widgets including CPU, memory, and performance data")
async def get_metrics():
    """Get current system metrics for dashboard"""
    return {
        "cpu_usage": 0.0,
        "memory_usage": 0.0,
        "active_agents": 0,
        "completed_tasks": 0,
        "error_rate": 0.0,
        "response_time": 0,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/monitoring/activity", tags=["📊 Agent Monitoring"],
         summary="Activity Feed",
         description="Recent activity feed showing agent actions, system events, and task completions")
async def get_activity():
    """Get recent system activity"""
    return {
        "activities": [],
        "total_today": 0,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/monitoring/agents", tags=["📊 Agent Monitoring"],
         summary="Connected Agents (Primary)",
         description="Comprehensive list of all connected AI agents with detailed status, capabilities, and performance metrics. Includes 11 agents with 6 API-integrated agents using curl commands.")
async def get_agents():
    """Get all connected agents with comprehensive details"""
    return {
        "agents": [],
        "total_count": 0,
        "active_count": 0,
        "api_integrated_count": 0,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/monitoring/system", tags=["📊 Agent Monitoring"],
         summary="System Metrics",
         description="Detailed system performance metrics including resource usage, network statistics, and performance indicators")
async def get_system_metrics():
    """Get detailed system metrics"""
    return {
        "system": {
            "cpu": {"usage": 0.0, "cores": 0, "load_avg": [0.0, 0.0, 0.0]},
            "memory": {"used": 0.0, "total": "0GB", "available": "0GB"},
            "disk": {"used": 0.0, "total": "0GB", "free": "0GB"},
            "network": {"rx": "0GB", "tx": "0MB", "connections": 0}
        },
        "database": {
            "connections": 0,
            "queries_per_sec": 0,
            "cache_hit_ratio": 0.0,
            "size": "0GB"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# 🔍 Audit & Compliance Endpoints
@app.get("/api/monitoring/audit/summary", tags=["🔍 Audit & Compliance"],
         summary="Audit Summary",
         description="Comprehensive audit trail summary with compliance status, violations, and recent activities")
async def get_audit_summary(hours: int = Query(24, description="Number of hours to look back for audit data")):
    """Get audit trail summary"""
    return {
        "period": f"Last {hours} hours",
        "total_events": 0,
        "compliance_score": 0.0,
        "violations": {
            "critical": 0,
            "major": 0,
            "minor": 0,
            "resolved": 0
        },
        "recent_audits": [],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/monitoring/compliance/violations", tags=["🔍 Audit & Compliance"],
         summary="Compliance Violations",
         description="Active compliance violations requiring attention with severity levels and resolution status")
async def get_compliance_violations():
    """Get current compliance violations based on real activity data"""
    # Get recent activity logs to analyze for compliance issues
    recent_activities = activity_logger.get_activities(limit=100)
    
    violations = []
    violation_count = 0
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    # Analyze activities for compliance patterns
    error_activities = [a for a in recent_activities if a.get('severity') == 'critical' or a.get('action_type') == 'error']
    security_activities = [a for a in recent_activities if a.get('action_type') == 'security_scan']
    compliance_activities = [a for a in recent_activities if a.get('action_type') == 'compliance_check']
    
    # Generate violations based on real activity patterns
    if error_activities:
        violations.append({
            "id": f"CV{len(violations)+1:03d}",
            "type": "system_error",
            "severity": "high",
            "description": f"Critical errors detected in system operations ({len(error_activities)} incidents)",
            "affected_agent": error_activities[0].get('agent_id', 'Unknown Agent'),
            "detected": f"{len(error_activities) * 5} minutes ago",
            "status": "investigating"
        })
        high_count += 1
        violation_count += 1
    
    # Check for data retention issues (logs older than certain time)
    old_activities = [a for a in recent_activities if 'timestamp' in a]
    if old_activities:
        oldest_activity = min(old_activities, key=lambda x: x.get('timestamp', ''))
        if oldest_activity.get('timestamp'):
            try:
                oldest_time = datetime.fromisoformat(oldest_activity['timestamp'].replace('Z', '+00:00'))
                if datetime.now().astimezone() - oldest_time > timedelta(days=7):  # 7 days for demo
                    violations.append({
                        "id": f"CV{len(violations)+1:03d}",
                        "type": "data_retention",
                        "severity": "medium",
                        "description": f"Activity logs older than 7 days detected (oldest: {oldest_time.strftime('%Y-%m-%d')})",
                        "affected_agent": "Activity Logger",
                        "detected": "1 hour ago",
                        "status": "monitoring"
                    })
                    medium_count += 1
                    violation_count += 1
            except:
                pass
    
    # Check for authentication patterns
    failed_auth_pattern = len([a for a in recent_activities if 'auth' in a.get('message', '').lower() and 'fail' in a.get('message', '').lower()])
    if failed_auth_pattern > 0:
        violations.append({
            "id": f"CV{len(violations)+1:03d}",
            "type": "access_control",
            "severity": "high",
            "description": f"Authentication irregularities detected ({failed_auth_pattern} incidents)",
            "affected_agent": "Security Agent",
            "detected": "30 minutes ago",
            "status": "resolved"
        })
        high_count += 1
        violation_count += 1
    
    # Calculate dynamic resolution rate based on resolved vs active violations
    if violation_count == 0:
        resolution_rate = 100  # Perfect compliance when no violations exist
    else:
        resolved_violations = len([v for v in violations if v['status'] == 'resolved'])
        resolution_rate = int((resolved_violations / violation_count) * 100)
    
    return {
        "violations": violations,
        "total_count": violation_count,
        "by_severity": {
            "critical": critical_count, 
            "high": high_count, 
            "medium": medium_count, 
            "low": low_count
        },
        "resolution_rate": f"{resolution_rate}%",
        "timestamp": datetime.utcnow().isoformat(),
        "data_source": "real-time_activity_analysis"
    }

@app.get("/api/compliance/rules", tags=["🔍 Audit & Compliance"],
         summary="Compliance Rules",
         description="Get all compliance rules with their status and violation counts")
async def get_compliance_rules():
    """Get compliance rules for management interface"""
    rules = []
    return {
        "rules": rules,
        "total_count": 0,
        "active_count": 0,
        "coverage_percentage": 0.0,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/rules", tags=["🔍 Audit & Compliance"],
         summary="Rules List",
         description="Get compliance rules list (compatibility endpoint)")
async def get_rules():
    """Get compliance rules - compatibility endpoint for frontend"""
    # This is a compatibility endpoint that returns the same data as /api/compliance/rules
    # but in the format expected by the compliance.js frontend
    rules_data = await get_compliance_rules()
    return rules_data

@app.post("/api/compliance/rules", tags=["🔍 Audit & Compliance"],
          summary="Add Compliance Rule",
          description="Create a new compliance rule for monitoring")
async def create_compliance_rule(rule_data: dict):
    """Create a new compliance rule"""
    # In a real implementation, this would save to database
    new_rule = {
        "id": f"R{len(rule_data) + 1:03d}",
        "name": rule_data.get("name", "New Rule"),
        "type": rule_data.get("type", "data_retention"),
        "severity": rule_data.get("severity", "MEDIUM"),
        "status": "ACTIVE",
        "description": rule_data.get("description", ""),
        "last_check": "Just created",
        "violations_count": 0,
        "created": datetime.utcnow().isoformat(),
        "updated": datetime.utcnow().isoformat()
    }
    
    return {
        "success": True,
        "rule": new_rule,
        "message": f"Compliance rule '{new_rule['name']}' created successfully"
    }

@app.put("/api/compliance/violations/{violation_id}/resolve", tags=["🔍 Audit & Compliance"],
         summary="Resolve Violation", 
         description="Mark a compliance violation as resolved")
async def resolve_violation(violation_id: str):
    """Resolve a compliance violation"""
    return {
        "success": True,
        "violation_id": violation_id,
        "status": "resolved",
        "resolved_at": datetime.utcnow().isoformat(),
        "message": f"Violation {violation_id} marked as resolved"
    }

@app.put("/api/compliance/violations/{violation_id}/snooze", tags=["🔍 Audit & Compliance"],
         summary="Snooze Violation",
         description="Snooze a compliance violation for 24 hours") 
async def snooze_violation(violation_id: str):
    """Snooze a compliance violation"""
    snooze_until = datetime.utcnow() + timedelta(hours=24)
    
    return {
        "success": True,
        "violation_id": violation_id,
        "status": "snoozed",
        "snoozed_until": snooze_until.isoformat(),
        "message": f"Violation {violation_id} snoozed until {snooze_until.strftime('%Y-%m-%d %H:%M')}"
    }

# 🔒 Security & Anomalies Endpoint
@app.get("/api/monitoring/anomalies", tags=["🔒 Security & Anomalies"],
         summary="Anomaly Detection",
         description="Real-time anomaly detection results including statistical outliers and security threats")
async def get_anomalies():
    """Get detected anomalies using enhanced AI-powered detection"""
    try:
        # Initialize anomaly detection service
        from app.services.anomaly_detection import AnomalyDetectionService
        anomaly_service = AnomalyDetectionService()
        
        # Get real anomalies from enhanced detection
        result = await anomaly_service.detect_anomalies()
        
        # Log the anomaly detection activity
        try:
            await activity_logger.log_activity(
                agent_id="anomaly_detector",
                action_type="detection", 
                action_name="anomaly_scan",
                severity="info",
                data={
                    "total_anomalies": result["total_anomalies"],
                    "severity_breakdown": result["severity_breakdown"],
                    "detection_methods": ["statistical", "pattern", "behavioral", "correlation"],
                    "execution_time": "~500ms"
                }
            )
        except Exception as log_error:
            logger.warning(f"Failed to log anomaly detection activity: {log_error}")
        
        return {
            "anomalies": result["anomalies"],
            "total_count": result["total_anomalies"],
            "by_severity": result["severity_breakdown"],
            "detection_methods": result.get("methods_used", ["statistical", "pattern", "behavioral", "correlation"]),
            "confidence_avg": result.get("avg_confidence", 0.75),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Anomaly detection service error: {e}", exc_info=True)
        
        # Fallback to basic mock data if there's an error
        try:
            await activity_logger.log_activity(
                agent_id="anomaly_detector",
                action_type="error",
                action_name="anomaly_detection_failure",
                severity="high",
                data={
                    "error": str(e),
                    "fallback_mode": True
                }
            )
        except Exception as log_error:
            logger.warning(f"Failed to log anomaly detection error: {log_error}")
        
        return {
            "anomalies": [
                {
                    "id": "SYS-ERROR-001",
                    "type": "system_error",
                    "severity": "high",
                    "metric": "detection_service",
                    "description": f"Anomaly detection service error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "service_error"
                }
            ],
            "total_count": 1,
            "by_severity": {"high": 1, "medium": 0, "low": 0},
            "error": "Service degraded - using fallback mode",
            "timestamp": datetime.utcnow().isoformat()
        }

# ✅ Approval Workflows Endpoint
@app.get("/api/monitoring/approvals/pending", tags=["✅ Approval Workflows"],
         summary="Pending Approvals",
         description="List of pending approval requests requiring manual review and authorization")
async def get_pending_approvals():
    """Get pending approval requests"""
    approvals = [
        {
            "id": "APP001",
            "type": "configuration_change",
            "priority": "medium",
            "requested_by": "System Optimizer",
            "description": "Update monitoring thresholds",
            "submitted": "2 hours ago",
            "expires": "22 hours",
            "estimated_impact": "low"
        },
        {
            "id": "APP002",
            "type": "data_export",
            "priority": "high", 
            "requested_by": "Analytics Agent",
            "description": "Export compliance data for audit",
            "submitted": "30 minutes ago",
            "expires": "23.5 hours",
            "estimated_impact": "medium"
        }
    ]
    
    return {
        "pending_approvals": approvals,
        "total_count": len(approvals),
        "by_priority": {"high": 1, "medium": 1, "low": 0},
        "avg_response_time": "4.2 hours",
        "timestamp": datetime.utcnow().isoformat()
    }

# 18th Endpoint - Real-time Dashboard Data
@app.get("/api/monitoring/dashboard", tags=["📊 Agent Monitoring"],
         summary="Get comprehensive dashboard data",
         description="Get all dashboard data in one call for real-time monitoring")
async def get_dashboard_data():
    """
    Get comprehensive dashboard data combining metrics, agents, alerts, and system status.
    Perfect for real-time dashboard updates with all necessary information.
    """
    dashboard_data = {
        "system_status": {
            "status": "UNKNOWN",
            "version": "0.0.0",
            "uptime": "0%",
            "last_update": datetime.utcnow().isoformat()
        },
        "metrics": {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_up": 0.0,
            "network_down": 0.0,
            "response_time": 0,
            "error_rate": 0.0
        },
        "agents": {
            "total": 0,
            "active": 0,
            "idle": 0,
            "busy": 0,
            "connected": 0,
            "disconnected": 0
        },
        "tasks": {
            "completed_today": 0,
            "success_rate": 0.0,
            "average_duration": "0s",
            "queue_length": 0
        },
        "compliance": {
            "score": 0,
            "violations": 0,
            "resolved_today": 0,
            "last_audit": ""
        },
        "security": {
            "anomalies": 0,
            "threats_blocked": 0,
            "security_score": 0,
            "last_scan": ""
        },
        "alerts": [],
        "recent_activity": [],
        "system_resources": {
            "cpu_cores": 0,
            "total_memory_gb": 0,
            "used_memory_gb": 0.0,
            "total_storage_gb": 0,
            "used_storage_gb": 0,
            "active_connections": 0
        },
        "timestamp": datetime.utcnow().isoformat(),
        "refresh_interval": 30
    }
    return dashboard_data

# 📋 POST endpoint for Activity Logs - Create new activity log entries
@app.post("/api/activity-logs", tags=["📋 Activity Log"],
          summary="Create Activity Log Entry",
          description="Create a new activity log entry for AI agent actions and decisions")
async def create_activity_log(activity: ActivityLogCreate):
    """
    Create a new activity log entry with immutable record keeping.
    
    This endpoint allows external agents to log their activities including:
    - Agent decisions and reasoning
    - Data collection operations
    - Analysis results and insights
    - Compliance checks and violations
    - Security scan results
    - Error events and exceptions
    
    Each entry receives a cryptographic hash for integrity verification.
    """
    try:
        # Generate hash for immutable record
        hash_data = f"{activity.agent_id}-{activity.action_type}-{datetime.utcnow()}-{activity.message}"
        activity_hash = hashlib.sha256(hash_data.encode()).hexdigest()[:16]
        
        # Create activity entry
        activity_entry = {
            "id": f"activity-{datetime.utcnow().timestamp()}-{activity_hash}",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": activity.agent_id,
            "action_type": activity.action_type,
            "severity": activity.severity,
            "message": activity.message,
            "data": activity.data,
            "user_id": activity.user_id,
            "session_id": activity.session_id,
            "hash": activity_hash
        }
        
        # Log the activity using the activity logger service
        await activity_logger.log_activity(
            agent_id=activity.agent_id,
            action_type=activity.action_type,
            message=activity.message,
            severity=activity.severity,
            data=activity.data,
            user_id=activity.user_id,
            session_id=activity.session_id
        )
        
        return activity_entry
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create activity log: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
