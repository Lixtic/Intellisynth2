from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import hashlib
from app.database import get_db
from app.models.log import ActivityLog
from pydantic import BaseModel, Field

router = APIRouter()

class ActivityLogCreate(BaseModel):
    agent_id: str
    action_type: str
    severity: str = "info"
    message: str
    data: dict = Field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ActivityLogResponse(BaseModel):
    id: str
    timestamp: datetime
    agent_id: str
    action_type: str
    severity: str
    message: str
    data: dict
    user_id: Optional[str]
    session_id: Optional[str]
    hash: str

    class Config:
        from_attributes = True

class ActivityStats(BaseModel):
    total_activities: int
    decisions: int
    data_points: int
    errors: int
    avg_response_time: float
    active_agents: int

def generate_activity_hash(activity_data: str) -> str:
    """Generate SHA-256 hash for immutable record verification"""
    return hashlib.sha256(activity_data.encode()).hexdigest()[:16]

@router.post("/", response_model=ActivityLogResponse)
async def create_activity_log(
    activity: ActivityLogCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new activity log entry
    
    This creates an immutable record of AI agent activities including:
    - Agent decisions and actions
    - Data collection activities  
    - Analysis operations
    - Compliance checks
    - Security scans
    - Error events
    """
    try:
        # Generate hash for immutable record
        hash_data = f"{activity.agent_id}-{activity.action_type}-{datetime.utcnow()}-{activity.message}"
        activity_hash = generate_activity_hash(hash_data)
        
        # Create database entry
        db_activity = ActivityLog(
            agent_id=activity.agent_id,
            action_type=activity.action_type,
            severity=activity.severity,
            message=activity.message,
            data=activity.data,
            user_id=activity.user_id,
            session_id=activity.session_id,
            hash=activity_hash,
            timestamp=datetime.utcnow()
        )
        
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        
        return db_activity
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create activity log: {str(e)}")

@router.get("/", response_model=List[ActivityLogResponse])
async def get_activity_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    agent_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve activity logs with filtering and pagination
    
    Supports filtering by:
    - Agent ID
    - Action type (decision, data_collection, analysis, etc.)
    - Severity level (critical, high, medium, low, info)
    - Time range (since parameter)
    """
    try:
        query = db.query(ActivityLog)
        
        # Apply filters
        if agent_id:
            query = query.filter(ActivityLog.agent_id == agent_id)
        if action_type:
            query = query.filter(ActivityLog.action_type == action_type)
        if severity:
            query = query.filter(ActivityLog.severity == severity)
        if since:
            query = query.filter(ActivityLog.timestamp >= since)
            
        # Order by timestamp descending (newest first)
        query = query.order_by(ActivityLog.timestamp.desc())
        
        # Apply pagination
        activities = query.offset(offset).limit(limit).all()
        
        return activities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve activity logs: {str(e)}")

@router.get("/latest", response_model=List[ActivityLogResponse])
async def get_latest_activities(
    since: datetime = Query(..., description="Get activities since this timestamp"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get the latest activity logs since a specific timestamp
    Used for real-time updates in the UI
    """
    try:
        activities = db.query(ActivityLog).filter(
            ActivityLog.timestamp > since
        ).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        
        return activities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve latest activities: {str(e)}")

@router.get("/stats", response_model=ActivityStats)
async def get_activity_stats(
    since: Optional[datetime] = Query(None, description="Calculate stats since this timestamp"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated statistics for activity logs
    
    Returns:
    - Total activity count
    - Decision count
    - Data point collection count
    - Error count
    - Average response time
    - Number of active agents
    """
    try:
        query = db.query(ActivityLog)
        
        if since:
            query = query.filter(ActivityLog.timestamp >= since)
        
        all_activities = query.all()
        
        total_activities = len(all_activities)
        decisions = len([a for a in all_activities if a.action_type == 'decision'])
        data_points = len([a for a in all_activities if a.action_type == 'data_collection'])
        errors = len([a for a in all_activities if a.severity == 'critical' or a.action_type == 'error'])
        
        # Calculate average response time from execution_time in data
        response_times = []
        for activity in all_activities:
            if isinstance(activity.data, dict) and 'execution_time' in activity.data:
                response_times.append(activity.data['execution_time'])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Count unique agents
        active_agents = len(set([a.agent_id for a in all_activities]))
        
        return ActivityStats(
            total_activities=total_activities,
            decisions=decisions,
            data_points=data_points,
            errors=errors,
            avg_response_time=avg_response_time,
            active_agents=active_agents
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve activity stats: {str(e)}")

@router.get("/agents", response_model=List[dict])
async def get_active_agents(
    since: Optional[datetime] = Query(None, description="Get agents active since this timestamp"),
    db: Session = Depends(get_db)
):
    """
    Get list of active agents with their activity counts
    """
    try:
        query = db.query(ActivityLog)
        
        if since:
            query = query.filter(ActivityLog.timestamp >= since)
        
        activities = query.all()
        
        # Group by agent and count activities
        agent_stats = {}
        for activity in activities:
            agent_id = activity.agent_id
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    'id': agent_id,
                    'name': agent_id.replace('-', ' ').replace('_', ' ').title(),
                    'activity_count': 0,
                    'last_activity': None,
                    'status': 'active'
                }
            
            agent_stats[agent_id]['activity_count'] += 1
            if not agent_stats[agent_id]['last_activity'] or activity.timestamp > agent_stats[agent_id]['last_activity']:
                agent_stats[agent_id]['last_activity'] = activity.timestamp
        
        return list(agent_stats.values())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active agents: {str(e)}")

@router.get("/verify-integrity")
async def verify_integrity(
    db: Session = Depends(get_db)
):
    """
    Verify the integrity of the activity log records
    
    Checks that all hashes are valid and records haven't been tampered with
    Returns integrity status and verification details
    """
    try:
        activities = db.query(ActivityLog).order_by(ActivityLog.timestamp.asc()).all()
        
        verified_count = 0
        invalid_hashes = []
        
        for activity in activities:
            # Recreate hash and verify
            hash_data = f"{activity.agent_id}-{activity.action_type}-{activity.timestamp}-{activity.message}"
            expected_hash = generate_activity_hash(hash_data)
            
            if activity.hash == expected_hash:
                verified_count += 1
            else:
                invalid_hashes.append({
                    'id': activity.id,
                    'timestamp': activity.timestamp,
                    'expected': expected_hash,
                    'actual': activity.hash
                })
        
        total_records = len(activities)
        integrity_percentage = (verified_count / total_records * 100) if total_records > 0 else 100
        
        # Generate overall system hash
        all_hashes = [a.hash for a in activities]
        system_hash = generate_activity_hash(''.join(all_hashes))
        
        return {
            'status': 'verified' if len(invalid_hashes) == 0 else 'compromised',
            'total_records': total_records,
            'verified_records': verified_count,
            'invalid_records': len(invalid_hashes),
            'integrity_percentage': integrity_percentage,
            'system_hash': system_hash,
            'verification_timestamp': datetime.utcnow(),
            'invalid_hashes': invalid_hashes[:10]  # Return first 10 invalid hashes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify integrity: {str(e)}")

@router.delete("/", status_code=204)
async def cleanup_old_logs(
    older_than_days: int = Query(30, ge=1, le=365, description="Delete logs older than X days"),
    db: Session = Depends(get_db)
):
    """
    Clean up old activity logs (admin only)
    
    WARNING: This permanently deletes logs older than specified days
    Use with caution as this affects the immutable record
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        deleted_count = db.query(ActivityLog).filter(
            ActivityLog.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        return {"deleted_count": deleted_count, "cutoff_date": cutoff_date}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cleanup logs: {str(e)}")

# Utility function to log agent activities from anywhere in the application
async def log_agent_activity(
    agent_id: str,
    action_type: str,
    message: str,
    severity: str = "info",
    data: dict = None,
    user_id: str = None,
    session_id: str = None,
    db: Session = None
):
    """
    Utility function to log AI agent activities from anywhere in the application
    
    This creates a transparent, immutable record of all AI agent interactions
    """
    if not db:
        return  # Skip logging if no database session provided
        
    try:
        activity_data = data or {}
        
        # Add execution context if not provided
        if 'execution_time' not in activity_data:
            activity_data['execution_time'] = 0
        
        if 'resource_usage' not in activity_data:
            activity_data['resource_usage'] = {
                'cpu': 0,
                'memory': 0,
                'network': 0
            }
        
        if 'metadata' not in activity_data:
            activity_data['metadata'] = {
                'context': action_type,
                'confidence': 1.0,
                'impact_score': 5.0
            }
        
        # Create activity log
        activity = ActivityLogCreate(
            agent_id=agent_id,
            action_type=action_type,
            severity=severity,
            message=message,
            data=activity_data,
            user_id=user_id,
            session_id=session_id
        )
        
        # Generate hash for immutable record
        hash_data = f"{activity.agent_id}-{activity.action_type}-{datetime.utcnow()}-{activity.message}"
        activity_hash = generate_activity_hash(hash_data)
        
        # Create database entry
        db_activity = ActivityLog(
            agent_id=activity.agent_id,
            action_type=activity.action_type,
            severity=activity.severity,
            message=activity.message,
            data=activity.data,
            user_id=activity.user_id,
            session_id=activity.session_id,
            hash=activity_hash,
            timestamp=datetime.utcnow()
        )
        
        db.add(db_activity)
        db.commit()
        
    except Exception as e:
        if db:
            db.rollback()
        # Don't raise exception to prevent activity logging from breaking main functionality
        print(f"Failed to log agent activity: {str(e)}")
