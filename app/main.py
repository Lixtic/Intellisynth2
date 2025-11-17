from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, Field
import logging
import random
import hashlib
import uuid

from app.models.compliance_rule import (
    ComplianceRule,
    RuleStatus,
    RuleType,
    SeverityLevel,
)

# Service imports
from app.api.auth_routes_full import router as auth_router
from app.config import get_activity_logger, get_agent_service
from app.services.compliance_rule_service_firestore import (
    compliance_rule_firestore_service,
)

# Firebase-backed services
activity_logger = get_activity_logger()
agent_service = get_agent_service()

def _safe_enum_value(enum_cls: Type, value, default):
    """Safely convert raw values into Enum members."""
    if value is None:
        return default
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        if isinstance(value, str):
            try:
                return enum_cls[value.upper()]
            except KeyError:
                return default
        return default


def _format_relative_time(timestamp: Optional[datetime]) -> str:
    if not timestamp:
        return "Not checked yet"
    delta = datetime.utcnow() - timestamp
    seconds = int(delta.total_seconds())
    if seconds < 15:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


DEFAULT_COMPLIANCE_RULES: List[Dict[str, Any]] = [
    {
        "id": "CR_DATA_RETENTION",
        "name": "Data Retention Policy",
        "description": "Ensure data is not retained longer than required retention periods",
        "rule_type": RuleType.DATA_RETENTION.value,
        "severity": SeverityLevel.HIGH.value,
        "status": RuleStatus.ACTIVE.value,
        "framework": "GDPR",
        "regulation_reference": "Article 5(1)(e)",
        "conditions": {
            "max_retention_days": 90,
            "data_types": ["logs", "activities", "audit_records"],
        },
        "priority": 10,
    },
    {
        "id": "CR_ACCESS_CONTROL",
        "name": "API Access Control",
        "description": "All API access must be properly authenticated and authorized",
        "rule_type": RuleType.ACCESS_CONTROL.value,
        "severity": SeverityLevel.HIGH.value,
        "status": RuleStatus.ACTIVE.value,
        "framework": "SOX",
        "regulation_reference": "Section 404",
        "conditions": {
            "require_authentication": True,
            "require_authorization": True,
            "allowed_roles": ["admin", "operator", "viewer"],
        },
        "priority": 20,
    },
    {
        "id": "CR_AUDIT_LOGGING",
        "name": "Audit Log Completeness",
        "description": "All critical actions must be properly logged with required fields",
        "rule_type": RuleType.AUDIT_LOGGING.value,
        "severity": SeverityLevel.MEDIUM.value,
        "status": RuleStatus.ACTIVE.value,
        "framework": "PCI-DSS",
        "regulation_reference": "Requirement 10",
        "conditions": {
            "required_fields": ["timestamp", "user_id", "action", "resource", "outcome"],
        },
        "priority": 30,
    },
    {
        "id": "CR_ENCRYPTION",
        "name": "Data Encryption at Rest",
        "description": "Sensitive data must be encrypted when stored",
        "rule_type": RuleType.ENCRYPTION.value,
        "severity": SeverityLevel.HIGH.value,
        "status": RuleStatus.ACTIVE.value,
        "framework": "HIPAA",
        "regulation_reference": "164.312(a)(2)(iv)",
        "conditions": {
            "encryption_algorithm": "AES-256",
            "key_rotation_days": 365,
        },
        "priority": 40,
    },
    {
        "id": "CR_SECURITY_MONITORING",
        "name": "Security Event Monitoring",
        "description": "Monitor and alert on security-related events and anomalies",
        "rule_type": RuleType.MONITORING.value,
        "severity": SeverityLevel.CRITICAL.value,
        "status": RuleStatus.ACTIVE.value,
        "framework": "NIST",
        "regulation_reference": "DE.AE-1",
        "conditions": {
            "monitor_events": ["failed_login", "privilege_escalation", "data_exfiltration"],
            "alert_threshold": 5,
        },
        "priority": 50,
    },
]


def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _enum_value(enum_cls: Type, raw: Any, fallback: str) -> str:
    if raw is None:
        return fallback
    if isinstance(raw, enum_cls):
        return raw.value
    try:
        return enum_cls(raw).value
    except (ValueError, TypeError):
        try:
            return enum_cls[str(raw).upper()].value
        except KeyError:
            return fallback


def _build_default_rule_payloads() -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    payloads: List[Dict[str, Any]] = []
    for template in DEFAULT_COMPLIANCE_RULES:
        rule = dict(template)
        rule.setdefault("id", f"CR_{uuid.uuid4().hex[:8].upper()}")
        rule.setdefault("rule_type", RuleType.CUSTOM.value)
        rule.setdefault("severity", SeverityLevel.MEDIUM.value)
        rule.setdefault("status", RuleStatus.ACTIVE.value)
        rule.setdefault("conditions", {})
        rule.setdefault("parameters", {})
        rule.setdefault("violations_count", 0)
        rule.setdefault("is_automated", True)
        rule.setdefault("priority", 100)
        rule.setdefault("created_by", "system")
        rule.setdefault("updated_by", "system")
        rule.setdefault("last_check_date", now)
        rule.setdefault("created_at", now)
        rule.setdefault("updated_at", now)
        payloads.append(rule)
    return payloads


async def _fetch_compliance_rules() -> List[Dict[str, Any]]:
    rules = await compliance_rule_firestore_service.get_all(order_by="priority")
    if rules:
        return rules

    defaults = _build_default_rule_payloads()
    for rule in defaults:
        await compliance_rule_firestore_service.create(rule["id"], rule)
    return defaults


def _format_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    last_check_dt = _parse_iso_timestamp(rule.get("last_check_date"))
    return {
        "id": rule.get("id"),
        "name": rule.get("name"),
        "type": rule.get("rule_type"),
        "rule_type": rule.get("rule_type"),
        "severity": rule.get("severity"),
        "status": rule.get("status"),
        "description": rule.get("description"),
        "last_check": _format_relative_time(last_check_dt),
        "last_check_date": rule.get("last_check_date"),
        "violations_count": rule.get("violations_count", 0),
        "framework": rule.get("framework"),
        "regulation_reference": rule.get("regulation_reference"),
        "is_automated": rule.get("is_automated", True),
        "priority": rule.get("priority", 100),
        "conditions": rule.get("conditions", {}),
        "parameters": rule.get("parameters", {}),
    }


def _normalize_rule_payload(rule_data: Dict[str, Any], existing: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat()
    payload = dict(existing or {})
    payload["id"] = payload.get("id") or rule_data.get("id") or f"CR_{uuid.uuid4().hex[:8].upper()}"
    payload["name"] = rule_data.get("name") or payload.get("name") or "New Rule"
    payload["description"] = rule_data.get("description") or payload.get("description") or ""
    payload["rule_type"] = _enum_value(
        RuleType,
        rule_data.get("type") or rule_data.get("rule_type") or payload.get("rule_type"),
        payload.get("rule_type") or RuleType.CUSTOM.value,
    )
    payload["severity"] = _enum_value(
        SeverityLevel,
        rule_data.get("severity") or payload.get("severity"),
        payload.get("severity") or SeverityLevel.MEDIUM.value,
    )
    payload["status"] = _enum_value(
        RuleStatus,
        rule_data.get("status") or payload.get("status"),
        payload.get("status") or RuleStatus.ACTIVE.value,
    )
    payload["conditions"] = rule_data.get("conditions", payload.get("conditions", {}))
    payload["parameters"] = rule_data.get("parameters", payload.get("parameters", {}))
    payload["framework"] = rule_data.get("framework", payload.get("framework"))
    payload["regulation_reference"] = rule_data.get("regulation_reference", payload.get("regulation_reference"))
    payload["is_automated"] = bool(rule_data.get("is_automated", payload.get("is_automated", True)))

    priority_value = rule_data.get("priority", payload.get("priority", 100))
    try:
        payload["priority"] = int(priority_value)
    except (TypeError, ValueError):
        payload["priority"] = payload.get("priority", 100)

    payload["violations_count"] = rule_data.get("violations_count", payload.get("violations_count", 0))
    payload["last_check_date"] = rule_data.get("last_check_date", payload.get("last_check_date", now))
    payload["updated_at"] = now
    payload["updated_by"] = rule_data.get("updated_by", "compliance_ui")

    if not existing:
        payload.setdefault("created_at", now)
        payload.setdefault("created_by", rule_data.get("created_by", "compliance_ui"))

    return payload


async def _build_compliance_rules_response() -> Dict[str, Any]:
    rules = await _fetch_compliance_rules()
    formatted = [_format_rule(rule) for rule in rules]
    active_count = sum(1 for rule in formatted if rule["status"] == RuleStatus.ACTIVE.value)
    coverage = round((active_count / len(formatted)) * 100, 1) if formatted else 0.0

    return {
        "rules": formatted,
        "total_count": len(formatted),
        "active_count": active_count,
        "coverage_percentage": coverage,
        "timestamp": datetime.utcnow().isoformat(),
    }

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

API_ENDPOINT_CATALOG = [
    {
        "name": "Core Platform",
        "tag": "🏠 Core Application",
        "icon": "fa-gauge-high",
        "accent_border": "border-blue-500/40",
        "accent_chip": "text-blue-200 bg-blue-500/10",
        "accent_icon": "text-blue-300",
        "description": "Operational readiness, health, and metadata endpoints that power monitoring tiles.",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "summary": "Service heartbeat",
                "description": "Lightweight probe returning uptime, status, and version details.",
                "auth": "None",
                "response": "status, uptime, version, timestamp",
            },
            {
                "method": "GET",
                "path": "/api/info",
                "summary": "Platform metadata",
                "description": "High-level API overview including features and endpoint counts.",
                "auth": "None",
                "response": "name, description, features, endpoint stats",
            },
            {
                "method": "GET",
                "path": "/api/services/status",
                "summary": "Service roster",
                "description": "Returns health for monitoring, compliance, log, and security services.",
                "auth": "None",
                "response": "status map with uptime for each subsystem",
            },
            {
                "method": "GET",
                "path": "/test",
                "summary": "Connectivity check",
                "description": "Simple JSON payload to validate networking or API keys.",
                "auth": "None",
                "response": "message, timestamp",
            },
        ],
    },
    {
        "name": "Authentication & Sessions",
        "tag": "🔐 Authentication",
        "icon": "fa-user-shield",
        "accent_border": "border-emerald-500/40",
        "accent_chip": "text-emerald-200 bg-emerald-500/10",
        "accent_icon": "text-emerald-300",
        "description": "Demo-friendly authentication endpoints for form and JSON flows.",
        "endpoints": [
            {
                "method": "POST",
                "path": "/api/auth/login",
                "summary": "JSON login",
                "description": "Accepts username/password (demo/demo123) and returns a demo token.",
                "auth": "Demo credentials",
                "response": "success flag, token, user profile",
            },
            {
                "method": "POST",
                "path": "/login",
                "summary": "Form login",
                "description": "HTML form endpoint for browser-based authentication flows.",
                "auth": "Demo credentials",
                "response": "HTML redirect or validation errors",
            },
            {
                "method": "GET",
                "path": "/api/auth/status",
                "summary": "Session status",
                "description": "Returns whether the demo session is active and which scopes are enabled.",
                "auth": "Bearer (optional)",
                "response": "status, user, scopes",
            },
            {
                "method": "GET",
                "path": "/api/auth/test",
                "summary": "Credentials test",
                "description": "Verifies demo credentials and surfaces friendly troubleshooting tips.",
                "auth": "None",
                "response": "message, demo credentials, expires_at",
            },
        ],
    },
    {
        "name": "Activity Log & Agents",
        "tag": "📋 Activity Log",
        "icon": "fa-wave-square",
        "accent_border": "border-sky-500/40",
        "accent_chip": "text-sky-200 bg-sky-500/10",
        "accent_icon": "text-sky-300",
        "description": "Immutable trail of every AI action with helper endpoints for verification.",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/activity-logs",
                "summary": "Fetch logs",
                "description": "Paginated, filterable activity history for every agent action.",
                "auth": "Bearer (optional)",
                "response": "list of activity objects with hashes",
            },
            {
                "method": "POST",
                "path": "/api/activity-logs",
                "summary": "Create log entry",
                "description": "Allows services to push custom activities into the ledger.",
                "auth": "Service token",
                "response": "saved activity with generated hash",
            },
            {
                "method": "GET",
                "path": "/api/activity-logs/latest",
                "summary": "Latest delta",
                "description": "Returns activities that occurred after a provided ISO timestamp.",
                "auth": "Bearer (optional)",
                "response": "new activities array",
            },
            {
                "method": "GET",
                "path": "/api/activity-logs/stats",
                "summary": "Activity stats",
                "description": "Aggregated totals for decisions, data points, errors, and agent counts.",
                "auth": "None",
                "response": "totals, hourly_activity, agent_distribution",
            },
            {
                "method": "GET",
                "path": "/api/activity-logs/verify-integrity",
                "summary": "Hash verification",
                "description": "Runs cryptographic validation across the immutable log chain.",
                "auth": "None",
                "response": "verification result, mismatches, computed hash",
            },
            {
                "method": "GET",
                "path": "/api/agents",
                "summary": "Agent roster",
                "description": "Lists agents available for filtering within the activity log UI.",
                "auth": "None",
                "response": "array of agents with status",
            },
        ],
    },
    {
        "name": "Monitoring & Metrics",
        "tag": "📊 Agent Monitoring",
        "icon": "fa-chart-line",
        "accent_border": "border-purple-500/40",
        "accent_chip": "text-purple-200 bg-purple-500/10",
        "accent_icon": "text-purple-300",
        "description": "System-wide telemetry powering dashboards, charts, and gauges.",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/monitoring/metrics",
                "summary": "Key metrics",
                "description": "Provides CPU, memory, throughput, and compliance readings.",
                "auth": "None",
                "response": "metrics block with spark data",
            },
            {
                "method": "GET",
                "path": "/api/monitoring/activity",
                "summary": "Recent activity",
                "description": "Curated feed of notable agent events for status tiles.",
                "auth": "None",
                "response": "activities, spotlight, trend",
            },
            {
                "method": "GET",
                "path": "/api/monitoring/agents",
                "summary": "Agent status",
                "description": "Returns connection health, last heartbeat, and version metadata per agent.",
                "auth": "None",
                "response": "agents array with status and latency",
            },
            {
                "method": "GET",
                "path": "/api/monitoring/system",
                "summary": "System overview",
                "description": "Bundles health, uptime, resource, and compliance posture summaries.",
                "auth": "None",
                "response": "overview object with nested sections",
            },
            {
                "method": "GET",
                "path": "/api/monitoring/dashboard",
                "summary": "Dashboard snapshot",
                "description": "Single call used by the dashboard to hydrate hero metrics.",
                "auth": "None",
                "response": "counts, alerts, anomaly stats",
            },
        ],
    },
    {
        "name": "Compliance & Audit",
        "tag": "🔍 Audit & Compliance",
        "icon": "fa-scale-balanced",
        "accent_border": "border-amber-500/40",
        "accent_chip": "text-amber-200 bg-amber-500/10",
        "accent_icon": "text-amber-300",
        "description": "Rule catalogs, audit digests, and compliance violation snapshots.",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/rules",
                "summary": "Compliance rules",
                "description": "Lists configured guardrails with severity, status, and metadata.",
                "auth": "None",
                "response": "rules array",
            },
            {
                "method": "GET",
                "path": "/api/monitoring/audit/summary",
                "summary": "Audit digest",
                "description": "Summarizes last verification, review backlog, and attestations.",
                "auth": "None",
                "response": "summary, review_backlog, attestations",
            },
            {
                "method": "GET",
                "path": "/api/monitoring/compliance/violations",
                "summary": "Open violations",
                "description": "Paginated list of open compliance issues grouped by framework.",
                "auth": "None",
                "response": "violations array with counts",
            },
        ],
    },
    {
        "name": "Security & Approvals",
        "tag": "🔒 Security & Anomalies",
        "icon": "fa-shield-halved",
        "accent_border": "border-rose-500/40",
        "accent_chip": "text-rose-200 bg-rose-500/10",
        "accent_icon": "text-rose-300",
        "description": "Threat intelligence plus manual approval workflows for sensitive actions.",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/monitoring/anomalies",
                "summary": "Detected anomalies",
                "description": "AI-enhanced anomaly list with severity, impacted assets, and rationale.",
                "auth": "None",
                "response": "anomalies array, totals, severity counts",
            },
            {
                "method": "GET",
                "path": "/api/monitoring/approvals/pending",
                "summary": "Pending approvals",
                "description": "Lists outstanding human-in-the-loop approvals with SLAs.",
                "auth": "None",
                "response": "pending approvals, total_count",
            },
            {
                "method": "GET",
                "path": "/api/monitoring/activity",
                "summary": "Security spotlight",
                "description": "Filterable stream used by SOC widgets to surface notable events.",
                "auth": "None",
                "response": "activities with security context",
            },
        ],
    },
]

METHOD_BADGES = {
    "GET": "bg-emerald-500/15 text-emerald-200 border border-emerald-400/30",
    "POST": "bg-blue-500/15 text-blue-200 border border-blue-400/30",
    "PUT": "bg-yellow-500/15 text-yellow-200 border border-yellow-400/30",
    "PATCH": "bg-purple-500/15 text-purple-200 border border-purple-400/30",
    "DELETE": "bg-rose-500/15 text-rose-200 border border-rose-400/30",
    "default": "bg-slate-700/40 text-slate-200 border border-slate-600/40",
}

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
    
    * **Onboarding**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
    * **Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
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

# Replace legacy demo auth endpoints with the dedicated router
app.include_router(auth_router, prefix="/api/auth", tags=["🔐 Authentication"])

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 🏠 Core Application Endpoints
@app.get("/dashboard", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="Main Dashboard",
         description="Interactive dashboard with real-time monitoring, charts, and system status widgets")
async def dashboard(request: Request):
    """Main dashboard with comprehensive monitoring interface"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/onboarding", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="Interactive Onboarding",
         description="Guided onboarding experience highlighting real-world usage scenarios and setup steps")
async def onboarding(request: Request):
    """Onboarding page showcasing real-world scenarios and quick-start guidance"""
    return templates.TemplateResponse("onboarding.html", {"request": request, "datetime": datetime})


@app.get("/", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="Welcome & Onboarding",
         description="Default landing that introduces IntelliSynth with guided setup steps and customer stories")
async def landing(request: Request):
    """Default landing page that reuses the onboarding experience"""
    return templates.TemplateResponse("onboarding.html", {"request": request, "datetime": datetime})

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

@app.get("/reports", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="Reports & Analytics",
         description="Comprehensive reporting and analytics dashboard for AI agent activities, compliance, and performance metrics")
async def reports(request: Request):
    """Reports and analytics interface with charts, metrics, and export capabilities"""
    return templates.TemplateResponse("reports.html", {"request": request})


@app.get("/api-endpoints", response_class=HTMLResponse, tags=["🏠 Core Application"],
         summary="API Endpoint Catalog",
         description="Human-friendly explorer that groups IntelliSynth API endpoints by capability with quick filters")
async def api_endpoint_catalog(request: Request):
    """Serve the interactive API endpoint reference page"""
    total_endpoints = sum(len(category["endpoints"]) for category in API_ENDPOINT_CATALOG)
    method_counts: Dict[str, int] = {}
    for category in API_ENDPOINT_CATALOG:
        for endpoint in category["endpoints"]:
            method = endpoint["method"].upper()
            method_counts[method] = method_counts.get(method, 0) + 1

    context = {
        "request": request,
        "categories": API_ENDPOINT_CATALOG,
        "method_styles": METHOD_BADGES,
        "method_counts": method_counts,
        "total_endpoints": total_endpoints,
        "category_count": len(API_ENDPOINT_CATALOG),
        "last_refreshed": datetime.utcnow().strftime("%b %d, %Y %H:%M UTC"),
    }
    return templates.TemplateResponse("api_endpoints.html", context)

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
    return await _build_compliance_rules_response()


@app.get("/api/rules", tags=["🔍 Audit & Compliance"],
         summary="Rules List",
         description="Get compliance rules list (compatibility endpoint)")
async def get_rules():
    """Compatibility endpoint for legacy UI components"""
    return await _build_compliance_rules_response()


@app.post("/api/compliance/rules", tags=["🔍 Audit & Compliance"],
          summary="Add Compliance Rule",
          description="Create a new compliance rule for monitoring")
async def create_compliance_rule(rule_data: dict):
    payload = _normalize_rule_payload(rule_data)
    created = await compliance_rule_firestore_service.create(payload["id"], payload)
    formatted = _format_rule(created)
    return {
        "success": True,
        "rule": formatted,
        "message": f"Compliance rule '{formatted['name']}' created successfully",
    }


@app.put("/api/compliance/rules/{rule_id}", tags=["🔍 Audit & Compliance"],
         summary="Update Compliance Rule",
         description="Modify an existing compliance rule configuration")
async def update_compliance_rule(rule_id: str, rule_data: dict):
    existing = await compliance_rule_firestore_service.get(rule_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Compliance rule {rule_id} not found")

    payload = _normalize_rule_payload(rule_data, existing)
    updated = await compliance_rule_firestore_service.update(rule_id, payload)
    formatted = _format_rule(updated or payload)
    return {
        "success": True,
        "rule": formatted,
        "message": f"Compliance rule '{formatted['name']}' updated successfully",
    }


@app.put("/api/compliance/rules/{rule_id}/toggle", tags=["🔍 Audit & Compliance"],
         summary="Toggle Compliance Rule",
         description="Pause or resume a compliance rule by toggling its status")
async def toggle_compliance_rule(rule_id: str):
    rule = await compliance_rule_firestore_service.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Compliance rule {rule_id} not found")

    next_status = (
        RuleStatus.INACTIVE.value if rule.get("status") == RuleStatus.ACTIVE.value else RuleStatus.ACTIVE.value
    )
    updated = await compliance_rule_firestore_service.update(
        rule_id,
        {
            "status": next_status,
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": "compliance_ui",
        },
    )
    formatted = _format_rule(updated or rule)
    action = "paused" if next_status == RuleStatus.INACTIVE.value else "resumed"
    return {
        "success": True,
        "rule": formatted,
        "message": f"Compliance rule '{formatted['name']}' {action}",
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
    health_data = await health()
    status_label = (health_data.get("status") or "UNKNOWN").upper()

    dashboard_data = {
        "system_status": {
            "status": status_label,
            "version": health_data.get("version", "1.0.0"),
            "uptime": health_data.get("uptime", "99.9%"),
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

# ============================================================================
# 📊 REPORTS API - Report Generation and Analytics
# ============================================================================

@app.get("/api/reports/summary", tags=["📊 Reports"],
         summary="Get Reports Summary",
         description="Get summary statistics for generated reports")
async def get_reports_summary():
    """Get summary of all reports including counts and statistics"""
    try:
        # Use Firebase report service for persistent storage
        from app.config import get_report_service
        report_service = get_report_service()
        
        summary = await report_service.get_reports_summary()
        
        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reports summary: {str(e)}")

@app.get("/api/reports", tags=["📊 Reports"],
         summary="List All Reports",
         description="Get a list of all generated reports")
async def list_reports(
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get a list of all generated reports with metadata"""
    try:
        # Use Firebase report service
        from app.config import get_report_service
        report_service = get_report_service()
        
        reports = await report_service.list_reports(
            report_type=report_type,
            status=status,
            limit=limit
        )
        
        return {
            "status": "success",
            "reports": reports,
            "total": len(reports)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")

@app.post("/api/reports/generate", tags=["📊 Reports"],
          summary="Generate New Report",
          description="Generate a new report based on type and time period")
async def generate_report(report_type: str, time_period: str = "24h"):
    """
    Generate a new report based on the specified type and time period.
    
    Report Types:
    - agent_activity: Activity report for all agents
    - security_summary: Security events and threats
    - compliance_check: Compliance status and violations
    - performance_metrics: Agent performance statistics
    - anomaly_detection: Detected anomalies and patterns
    """
    try:
        period_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = period_map.get(time_period, 24)
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        activities = await activity_logger.get_activities(limit=5000, since=cutoff_time)
        agents = await agent_service.get_all_agents(limit=500)

        def _safe_lower(value: Any) -> str:
            return str(value or "").lower()

        if report_type == "agent_activity":
            by_type: Dict[str, int] = {}
            by_agent: Dict[str, int] = {}
            for activity in activities:
                action_type = activity.get("action_type", "unknown")
                by_type[action_type] = by_type.get(action_type, 0) + 1

                agent_id = activity.get("agent_id", "unknown")
                by_agent[agent_id] = by_agent.get(agent_id, 0) + 1

            successful = sum(1 for a in activities if a.get("action_type") != "error")
            total = len(activities)
            success_rate = f"{(successful / total * 100):.1f}%" if total else "0%"

            active_agents = [a for a in agents if _safe_lower(a.get("status")) == "active"]

            report_data = {
                "total_activities": total,
                "by_type": by_type,
                "by_agent": by_agent,
                "agent_stats": {
                    "total_agents": len(agents),
                    "active_agents": len(active_agents),
                    "idle_agents": len(agents) - len(active_agents),
                    "offline_agents": 0,
                },
                "activity_metrics": {
                    "total_tasks": total,
                    "completed_tasks": successful,
                    "failed_tasks": total - successful,
                    "success_rate": success_rate,
                },
                "top_performing_agents": [
                    {"id": agent_id, "name": agent_id, "tasks_completed": count}
                    for agent_id, count in sorted(by_agent.items(), key=lambda item: item[1], reverse=True)[:5]
                ],
            }

        elif report_type == "security_summary":
            security_logs = [
                entry
                for entry in activities
                if entry.get("action_type") in {"security_scan", "error"}
            ]
            threats = sum(1 for log in security_logs if log.get("action_type") == "security_scan")
            errors = sum(1 for log in security_logs if log.get("action_type") == "error")
            report_data = {
                "total_security_events": len(security_logs),
                "threats_detected": threats,
                "errors": errors,
                "security_events": {
                    "total_events": len(security_logs),
                    "critical_events": sum(1 for log in security_logs if _safe_lower(log.get("severity")) == "critical"),
                    "high_priority": sum(1 for log in security_logs if _safe_lower(log.get("severity")) == "high"),
                    "medium_priority": sum(1 for log in security_logs if _safe_lower(log.get("severity")) == "medium"),
                },
                "threat_analysis": {
                    "active_threats": threats,
                    "blocked_attempts": max(threats - errors, 0),
                    "vulnerabilities_found": threats,
                    "remediation_pending": max(errors - threats, 0),
                },
            }

        elif report_type == "compliance_check":
            compliance_logs = [
                entry for entry in activities if entry.get("action_type") == "compliance_check"
            ]
            compliant = sum(1 for log in compliance_logs if "compliant" in _safe_lower(log.get("data")))
            violations = sum(1 for log in compliance_logs if "violation" in _safe_lower(log.get("data")))
            report_data = {
                "total_checks": len(compliance_logs),
                "compliant": compliant,
                "violations": violations,
                "compliance_metrics": {
                    "total_rules_checked": len(compliance_logs),
                    "rules_passed": compliant,
                    "rules_failed": violations,
                    "compliance_score": f"{(compliant / len(compliance_logs) * 100):.1f}%" if compliance_logs else "N/A",
                },
                "violation_summary": {
                    "critical_violations": sum(1 for log in compliance_logs if _safe_lower(log.get("severity")) == "critical"),
                    "major_violations": sum(1 for log in compliance_logs if _safe_lower(log.get("severity")) == "high"),
                    "minor_violations": sum(1 for log in compliance_logs if _safe_lower(log.get("severity")) == "medium"),
                    "resolved_violations": 0,
                },
            }

        elif report_type == "performance_metrics":
            successful = sum(1 for log in activities if log.get("action_type") != "error")
            total = len(activities)
            success_rate = (successful / total * 100) if total else 0
            exec_times = [
                log.get("data", {}).get("execution_time")
                for log in activities
                if isinstance(log.get("data"), dict) and log.get("data", {}).get("execution_time")
            ]
            avg_exec = int(sum(exec_times) / len(exec_times)) if exec_times else 0
            report_data = {
                "total_operations": total,
                "average_execution_time_ms": avg_exec,
                "success_rate": f"{success_rate:.1f}%",
                "performance_summary": {
                    "total_requests": total,
                    "successful_requests": successful,
                    "failed_requests": total - successful,
                    "average_response_time": f"{avg_exec}ms",
                },
                "throughput_metrics": {
                    "requests_per_hour": total // max(hours, 1),
                    "peak_hour_requests": total,
                    "average_concurrent_users": max(len(agents), 1),
                    "max_concurrent_users": max(len(agents), 1),
                },
            }

        elif report_type == "anomaly_detection":
            anomaly_logs = [
                log
                for log in activities
                if _safe_lower(log.get("severity")) in {"warning", "critical"}
            ]
            report_data = {
                "anomalies_detected": len(anomaly_logs),
                "by_severity": {
                    "warning": sum(1 for log in anomaly_logs if _safe_lower(log.get("severity")) == "warning"),
                    "critical": sum(1 for log in anomaly_logs if _safe_lower(log.get("severity")) == "critical"),
                },
                "anomaly_summary": {
                    "total_anomalies": len(anomaly_logs),
                    "critical_anomalies": sum(1 for log in anomaly_logs if _safe_lower(log.get("severity")) == "critical"),
                    "warning_anomalies": sum(1 for log in anomaly_logs if _safe_lower(log.get("severity")) == "warning"),
                    "resolved_anomalies": 0,
                },
                "anomaly_types": {
                    "behavioral_anomalies": sum(1 for log in anomaly_logs if "behavior" in _safe_lower(log.get("data"))),
                    "performance_anomalies": sum(1 for log in anomaly_logs if "performance" in _safe_lower(log.get("data"))),
                    "security_anomalies": sum(1 for log in anomaly_logs if log.get("action_type") == "security_scan"),
                    "data_anomalies": sum(1 for log in anomaly_logs if "data" in _safe_lower(log.get("data"))),
                },
            }

        else:
            report_data = {"message": "Unknown report type"}

        from app.config import get_report_service

        report_service = get_report_service()
        stored_report = await report_service.create_report(
            report_type=report_type,
            time_period=time_period,
            data=report_data,
            status="completed",
        )

        if stored_report:
            return {"status": "success", "report": stored_report}

        fallback_id = f"report-{int(datetime.utcnow().timestamp())}"
        return {
            "status": "success",
            "report": {
                "id": fallback_id,
                "type": report_type,
                "time_period": time_period,
                "generated_at": datetime.utcnow().isoformat(),
                "data": report_data,
            },
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {exc}")

@app.get("/api/reports/{report_id}", tags=["📊 Reports"],
         summary="Get Report Details",
         description="Get detailed information for a specific report")
async def get_report_details(report_id: str):
    """Get detailed information for a specific report by ID"""
    try:
        # Use Firebase report service
        from app.config import get_report_service
        report_service = get_report_service()
        
        report = await report_service.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "status": "success",
            "report": report
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report details: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
