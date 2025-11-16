from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.database import get_db
from app.services.integration import get_service_integrator
from app.models.anomaly import AnomalyDetection
from app.models.agent import Agent
from pydantic import BaseModel
import json

router = APIRouter()

# Pydantic models for request/response
class AnomalyResponse(BaseModel):
    id: str
    agent_id: str
    anomaly_type: str
    anomaly_score: float
    detected_at: datetime
    status: str
    risk_level: str
    description: str

class ActivityFeedResponse(BaseModel):
    id: str
    timestamp: datetime
    agent_id: str
    action_type: str
    description: str
    severity: str

class SystemMetricsResponse(BaseModel):
    timestamp: datetime
    active_agents: int
    total_logs: int
    error_rate: float
    avg_response_time: float
    compliance_score: float

class SessionResponse(BaseModel):
    id: str
    agent_id: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None
    action_count: int

@router.get("/anomalies", response_model=List[AnomalyResponse])
def get_anomalies(
    agent_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    hours: int = Query(24, description="Hours to look back"),
    db: Session = Depends(get_db)
):
    """Get anomaly detections with optional filters"""
    query = db.query(AnomalyDetection)
    
    # Apply filters
    if agent_id:
        query = query.filter(AnomalyDetection.agent_id == agent_id)
    if risk_level:
        query = query.filter(AnomalyDetection.risk_level == risk_level)
    if status:
        query = query.filter(AnomalyDetection.status == status)
    
    # Time filter
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(AnomalyDetection.detected_at >= since)
    
    return query.order_by(AnomalyDetection.detected_at.desc()).all()

@router.get("/sessions", response_model=List[SessionResponse])
def get_agent_sessions(
    agent_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    hours: int = Query(24),
    db: Session = Depends(get_db)
):
    """Get agent sessions with optional filters"""
    query = db.query(AgentSession)
    
    if agent_id:
        query = query.filter(AgentSession.agent_id == agent_id)
    if status:
        query = query.filter(AgentSession.status == status)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(AgentSession.started_at >= since)
    
    return query.order_by(AgentSession.started_at.desc()).all()

@router.get("/approvals/pending", response_model=List[ApprovalRequestResponse])
def get_pending_approvals(
    agent_id: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get pending approval requests"""
    query = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending")
    
    if agent_id:
        query = query.filter(ApprovalRequest.agent_id == agent_id)
    if urgency:
        query = query.filter(ApprovalRequest.urgency == urgency)
    
    return query.order_by(ApprovalRequest.requested_at.desc()).all()

@router.post("/approvals/{request_id}/approve")
def approve_request(
    request_id: str,
    approval_notes: Optional[str] = None,
    approved_by: str = "system",  # In real app, get from auth
    db: Session = Depends(get_db)
):
    """Approve a pending request"""
    request = db.query(ApprovalRequest).filter(
        ApprovalRequest.request_id == request_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")
    
    request.status = "approved"
    request.approved_by = approved_by
    request.approved_at = datetime.utcnow()
    request.approval_notes = approval_notes
    
    db.commit()
    return {"status": "approved", "request_id": request_id}

@router.post("/approvals/{request_id}/reject")
def reject_request(
    request_id: str,
    rejection_reason: str,
    approved_by: str = "system",
    db: Session = Depends(get_db)
):
    """Reject a pending request"""
    request = db.query(ApprovalRequest).filter(
        ApprovalRequest.request_id == request_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")
    
    request.status = "rejected"
    request.approved_by = approved_by
    request.approved_at = datetime.utcnow()
    request.rejection_reason = rejection_reason
    
    db.commit()
    return {"status": "rejected", "request_id": request_id}

@router.get("/compliance/violations")
def get_compliance_violations(
    agent_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    hours: int = Query(24),
    db: Session = Depends(get_db)
):
    """Get compliance violations"""
    query = db.query(ComplianceViolation).join(LogEntry)
    
    if agent_id:
        query = query.filter(LogEntry.agent_id == agent_id)
    if severity:
        query = query.filter(ComplianceViolation.severity == severity)
    if status:
        query = query.filter(ComplianceViolation.resolution_status == status)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(ComplianceViolation.detected_at >= since)
    
    return query.order_by(ComplianceViolation.detected_at.desc()).all()

@router.get("/audit/summary")
def get_audit_summary(
    agent_id: Optional[str] = Query(None),
    hours: int = Query(24),
    db: Session = Depends(get_db)
):
    """Get audit summary for dashboard"""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Base query
    log_query = db.query(LogEntry).filter(LogEntry.timestamp >= since)
    if agent_id:
        log_query = log_query.filter(LogEntry.agent_id == agent_id)
    
    # Collect metrics
    total_actions = log_query.count()
    failed_actions = log_query.filter(LogEntry.status == "failed").count()
    blocked_actions = log_query.filter(LogEntry.status == "blocked").count()
    
    violations = db.query(ComplianceViolation).join(LogEntry).filter(
        LogEntry.timestamp >= since
    )
    if agent_id:
        violations = violations.filter(LogEntry.agent_id == agent_id)
    
    anomalies = db.query(AnomalyDetection).filter(
        AnomalyDetection.detected_at >= since
    )
    if agent_id:
        anomalies = anomalies.filter(AnomalyDetection.agent_id == agent_id)
    
    pending_approvals = db.query(ApprovalRequest).filter(
        ApprovalRequest.status == "pending"
    )
    if agent_id:
        pending_approvals = pending_approvals.filter(ApprovalRequest.agent_id == agent_id)
    
    return {
        "period_hours": hours,
        "total_actions": total_actions,
        "failed_actions": failed_actions,
        "blocked_actions": blocked_actions,
        "success_rate": (total_actions - failed_actions - blocked_actions) / max(total_actions, 1),
        "compliance_violations": violations.count(),
        "critical_violations": violations.filter(ComplianceViolation.severity == "critical").count(),
        "anomalies_detected": anomalies.count(),
        "high_risk_anomalies": anomalies.filter(AnomalyDetection.risk_level == "high").count(),
        "pending_approvals": pending_approvals.count(),
        "critical_approvals": pending_approvals.filter(ApprovalRequest.urgency == "critical").count()
    }
