"""
Activity Logger Integration
Automatic logging of AI agent activities across the system
"""

from datetime import datetime
from typing import Dict, Any, Optional
import hashlib
import json
from functools import wraps
import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.activity_log import ActivityLog, Base

# Create tables
Base.metadata.create_all(bind=engine)

class ActivityLoggerService:
    """Service for logging AI agent activities with immutable record keeping"""
    
    def __init__(self):
        # Keep in-memory cache for backward compatibility and quick access
        self._cache = []
        self._cache_limit = 100  # Only cache last 100 for performance
    
    def generate_hash(self, activity_data: str) -> str:
        """Generate SHA-256 hash for immutable record verification"""
        return hashlib.sha256(activity_data.encode()).hexdigest()[:16]
    
    def _get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    def _update_cache(self, activity: Dict[str, Any]):
        """Update in-memory cache"""
        self._cache.append(activity)
        if len(self._cache) > self._cache_limit:
            self._cache = self._cache[-self._cache_limit:]
    
    async def log_activity(
        self,
        agent_id: str,
        action_type: str,
        message: str,
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log an AI agent activity with immutable record keeping
        
        Args:
            agent_id: ID of the AI agent performing the action
            action_type: Type of action (decision, data_collection, analysis, etc.)
            message: Human-readable description of the activity
            severity: Severity level (critical, high, medium, low, info)
            data: Additional structured data about the activity
            user_id: Optional user ID if action was user-initiated
            session_id: Optional session ID for tracking related activities
            
        Returns:
            Dictionary containing the logged activity with hash for integrity verification
        """
        
        timestamp = datetime.utcnow()
        activity_data = data or {}
        
        # Ensure required fields in data
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
        
        # Generate immutable hash
        hash_input = f"{agent_id}-{action_type}-{timestamp.isoformat()}-{message}"
        activity_hash = self.generate_hash(hash_input)
        
        # Create activity record for database
        db_activity = ActivityLog(
            id=f'activity-{timestamp.timestamp()}-{activity_hash[:8]}',
            timestamp=timestamp,
            agent_id=agent_id,
            action_type=action_type,
            severity=severity,
            message=message,
            data=activity_data,
            user_id=user_id,
            session_id=session_id,
            hash=activity_hash
        )
        
        # Save to database
        db = self._get_db()
        try:
            db.add(db_activity)
            db.commit()
            db.refresh(db_activity)
            
            # Convert to dict for return and cache
            activity = db_activity.to_dict()
            self._update_cache(activity)
            
            return activity
        except Exception as e:
            db.rollback()
            # Log error but don't fail - fall back to cache only
            print(f"Database error logging activity: {e}")
            # Create dict manually as fallback
            activity = {
                'id': db_activity.id,
                'timestamp': timestamp.isoformat(),
                'agent_id': agent_id,
                'action_type': action_type,
                'severity': severity,
                'message': message,
                'data': activity_data,
                'user_id': user_id,
                'session_id': session_id,
                'hash': activity_hash
            }
            self._update_cache(activity)
            return activity
        finally:
            db.close()
    
    async def log_decision(
        self,
        agent_id: str,
        decision: str,
        reasoning: str,
        confidence: float = 1.0,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """Log an AI agent decision"""
        await self.log_activity(
            agent_id=agent_id,
            action_type="decision",
            message=f"Decision: {decision} | Reasoning: {reasoning}",
            severity="medium",
            data={
                'decision': decision,
                'reasoning': reasoning,
                'confidence': confidence,
                'context': context or {},
                'metadata': {
                    'context': 'decision_making',
                    'confidence': confidence,
                    'impact_score': confidence * 8
                }
            },
            user_id=user_id
        )
    
    async def log_data_collection(
        self,
        agent_id: str,
        data_source: str,
        records_collected: int,
        processing_time: float,
        data_quality: str = "good"
    ):
        """Log data collection activity"""
        await self.log_activity(
            agent_id=agent_id,
            action_type="data_collection",
            message=f"Collected {records_collected} records from {data_source} in {processing_time:.2f}s",
            severity="info",
            data={
                'data_source': data_source,
                'records_collected': records_collected,
                'data_quality': data_quality,
                'execution_time': int(processing_time * 1000),
                'metadata': {
                    'context': 'data_collection',
                    'confidence': 0.9,
                    'impact_score': min(records_collected / 100, 10)
                }
            }
        )
    
    async def log_analysis(
        self,
        agent_id: str,
        analysis_type: str,
        results: Dict[str, Any],
        accuracy: float = 0.95,
        processing_time: float = 1.0
    ):
        """Log analysis activity"""
        await self.log_activity(
            agent_id=agent_id,
            action_type="analysis",
            message=f"Completed {analysis_type} analysis with {accuracy:.1%} accuracy",
            severity="info",
            data={
                'analysis_type': analysis_type,
                'results': results,
                'accuracy': accuracy,
                'execution_time': int(processing_time * 1000),
                'metadata': {
                    'context': 'analysis',
                    'confidence': accuracy,
                    'impact_score': accuracy * 9
                }
            }
        )
    
    async def log_compliance_check(
        self,
        agent_id: str,
        rule_id: str,
        rule_name: str,
        compliance_status: str,
        violations_found: int = 0,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log compliance check activity"""
        severity = "critical" if violations_found > 0 else "info"
        
        await self.log_activity(
            agent_id=agent_id,
            action_type="compliance_check",
            message=f"Compliance check for '{rule_name}': {compliance_status} ({violations_found} violations)",
            severity=severity,
            data={
                'rule_id': rule_id,
                'rule_name': rule_name,
                'compliance_status': compliance_status,
                'violations_found': violations_found,
                'details': details or {},
                'metadata': {
                    'context': 'compliance_monitoring',
                    'confidence': 1.0,
                    'impact_score': violations_found * 2 + 3
                }
            }
        )
    
    async def log_security_scan(
        self,
        agent_id: str,
        scan_type: str,
        threats_detected: int,
        scan_duration: float,
        severity_level: str = "low"
    ):
        """Log security scan activity"""
        message_severity = "critical" if threats_detected > 0 else "info"
        
        await self.log_activity(
            agent_id=agent_id,
            action_type="security_scan",
            message=f"{scan_type} scan completed: {threats_detected} threats detected in {scan_duration:.1f}s",
            severity=message_severity,
            data={
                'scan_type': scan_type,
                'threats_detected': threats_detected,
                'severity_level': severity_level,
                'execution_time': int(scan_duration * 1000),
                'metadata': {
                    'context': 'security_monitoring',
                    'confidence': 0.95,
                    'impact_score': threats_detected * 3 + 2
                }
            }
        )
    
    async def log_error(
        self,
        agent_id: str,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """Log error or anomaly"""
        await self.log_activity(
            agent_id=agent_id,
            action_type="error",
            message=f"Error: {error_type} - {error_message}",
            severity="critical",
            data={
                'error_type': error_type,
                'error_message': error_message,
                'error_details': error_details or {},
                'metadata': {
                    'context': 'error_handling',
                    'confidence': 1.0,
                    'impact_score': 9
                }
            },
            user_id=user_id
        )
    
    def get_activities(
        self,
        limit: int = 100,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        severity: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> list:
        """Get filtered activities from database"""
        db = self._get_db()
        try:
            # Start with base query
            query = db.query(ActivityLog)
            
            # Apply filters
            if agent_id:
                query = query.filter(ActivityLog.agent_id == agent_id)
            if action_type:
                query = query.filter(ActivityLog.action_type == action_type)
            if severity:
                query = query.filter(ActivityLog.severity == severity)
            if since:
                query = query.filter(ActivityLog.timestamp > since)
            
            # Sort by timestamp (newest first) and limit
            activities = query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
            
            # Convert to dictionaries
            return [activity.to_dict() for activity in activities]
        except Exception as e:
            print(f"Database error getting activities: {e}")
            # Fallback to cache on error
            filtered = self._cache.copy()
            
            # Apply filters to cache
            if agent_id:
                filtered = [a for a in filtered if a['agent_id'] == agent_id]
            if action_type:
                filtered = [a for a in filtered if a['action_type'] == action_type]
            if severity:
                filtered = [a for a in filtered if a['severity'] == severity]
            if since:
                filtered = [a for a in filtered if datetime.fromisoformat(a['timestamp']) > since]
            
            # Sort by timestamp (newest first) and limit
            filtered.sort(key=lambda x: x['timestamp'], reverse=True)
            return filtered[:limit]
        finally:
            db.close()
    
    def get_latest_activities(self, since: datetime, limit: int = 50) -> list:
        """Get activities since a specific timestamp from database"""
        db = self._get_db()
        try:
            activities = db.query(ActivityLog).filter(
                ActivityLog.timestamp > since
            ).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
            
            return [activity.to_dict() for activity in activities]
        except Exception as e:
            print(f"Database error getting latest activities: {e}")
            # Fallback to cache
            return [
                a for a in self._cache
                if datetime.fromisoformat(a['timestamp']) > since
            ][:limit]
        finally:
            db.close()
    
    def get_activity_stats(self) -> Dict[str, Any]:
        """Get aggregated activity statistics from database"""
        db = self._get_db()
        try:
            # Get all activities for stats (could optimize with SQL aggregations)
            all_activities = db.query(ActivityLog).all()
            
            if not all_activities:
                return {
                    'total_activities': 0,
                    'decisions': 0,
                    'data_points': 0,
                    'errors': 0,
                    'avg_response_time': 0,
                    'active_agents': 0
                }
            
            # Convert to dicts for processing
            activities_dict = [a.to_dict() for a in all_activities]
            
            total = len(activities_dict)
            decisions = len([a for a in activities_dict if a['action_type'] == 'decision'])
            data_points = len([a for a in activities_dict if a['action_type'] == 'data_collection'])
            errors = len([a for a in activities_dict if a['severity'] == 'critical' or a['action_type'] == 'error'])
            
            # Calculate average execution time
            exec_times = [
                a['data']['execution_time'] for a in activities_dict
                if a.get('data') and 'execution_time' in a['data']
            ]
            avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
            
            # Count unique agents
            active_agents = len(set(a['agent_id'] for a in activities_dict))
            
            return {
                'total_activities': total,
                'decisions': decisions,
                'data_points': data_points,
                'errors': errors,
                'avg_response_time': int(avg_exec_time),
                'active_agents': active_agents
            }
        except Exception as e:
            print(f"Database error getting activity stats: {e}")
            # Fallback to cache
            if not self._cache:
                return {
                    'total_activities': 0,
                    'decisions': 0,
                    'data_points': 0,
                    'errors': 0,
                    'avg_response_time': 0,
                    'active_agents': 0
                }
            
            total = len(self._cache)
            decisions = len([a for a in self._cache if a['action_type'] == 'decision'])
            data_points = len([a for a in self._cache if a['action_type'] == 'data_collection'])
            errors = len([a for a in self._cache if a['severity'] == 'critical' or a['action_type'] == 'error'])
            
            exec_times = [
                a['data']['execution_time'] for a in self._cache
                if 'execution_time' in a.get('data', {})
            ]
            avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
            
            active_agents = len(set(a['agent_id'] for a in self._cache))
            
            return {
                'total_activities': total,
                'decisions': decisions,
                'data_points': data_points,
                'errors': errors,
                'avg_response_time': int(avg_exec_time),
                'active_agents': active_agents
            }
        finally:
            db.close()
    
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify integrity of all activity records in database"""
        db = self._get_db()
        try:
            all_activities = db.query(ActivityLog).all()
            
            verified_count = 0
            invalid_hashes = []
            
            for activity in all_activities:
                # Recreate hash and verify
                hash_input = f"{activity.agent_id}-{activity.action_type}-{activity.timestamp.isoformat()}-{activity.message}"
                expected_hash = self.generate_hash(hash_input)
                
                if activity.hash == expected_hash:
                    verified_count += 1
                else:
                    invalid_hashes.append(activity.id)
            
            total_records = len(all_activities)
            integrity_percentage = (verified_count / total_records * 100) if total_records > 0 else 100
            
            # Generate system hash
            all_hashes = [a.hash for a in all_activities]
            system_hash = self.generate_hash(''.join(all_hashes))
            
            return {
                'status': 'verified' if len(invalid_hashes) == 0 else 'compromised',
                'total_records': total_records,
                'verified_records': verified_count,
                'invalid_records': len(invalid_hashes),
                'integrity_percentage': round(integrity_percentage, 2),
                'system_hash': system_hash,
                'verification_timestamp': datetime.utcnow().isoformat(),
                'invalid_hashes': invalid_hashes[:10]
            }
        except Exception as e:
            print(f"Database error verifying integrity: {e}")
            # Fallback to cache
            verified_count = 0
            invalid_hashes = []
            
            for activity in self._cache:
                hash_input = f"{activity['agent_id']}-{activity['action_type']}-{activity['timestamp']}-{activity['message']}"
                expected_hash = self.generate_hash(hash_input)
                
                if activity['hash'] == expected_hash:
                    verified_count += 1
                else:
                    invalid_hashes.append(activity['id'])
            
            total_records = len(self._cache)
            integrity_percentage = (verified_count / total_records * 100) if total_records > 0 else 100
            
            all_hashes = [a['hash'] for a in self._cache]
            system_hash = self.generate_hash(''.join(all_hashes))
            
            return {
                'status': 'verified' if len(invalid_hashes) == 0 else 'compromised',
                'total_records': total_records,
                'verified_records': verified_count,
                'invalid_records': len(invalid_hashes),
                'integrity_percentage': round(integrity_percentage, 2),
                'system_hash': system_hash,
                'verification_timestamp': datetime.utcnow().isoformat(),
                'invalid_hashes': invalid_hashes[:10]
            }
        finally:
            db.close()

# Global activity logger instance
activity_logger = ActivityLoggerService()

def log_agent_activity(
    agent_id: str,
    action_type: str = "general",
    severity: str = "info",
    include_execution_time: bool = True
):
    """
    Decorator to automatically log agent activities
    
    Usage:
    @log_agent_activity("compliance-agent", "compliance_check", "medium")
    async def check_compliance():
        # Your function implementation
        pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import time
            
            start_time = time.time()
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Log successful activity
                await activity_logger.log_activity(
                    agent_id=agent_id,
                    action_type=action_type,
                    message=f"Successfully executed {func.__name__}",
                    severity=severity,
                    data={
                        'function_name': func.__name__,
                        'execution_time': int(execution_time * 1000),
                        'success': True,
                        'metadata': {
                            'context': action_type,
                            'confidence': 1.0,
                            'impact_score': 5.0
                        }
                    }
                )
                
                return result
                
            except Exception as e:
                # Log error activity
                execution_time = time.time() - start_time
                
                await activity_logger.log_error(
                    agent_id=agent_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    error_details={
                        'function_name': func.__name__,
                        'execution_time': int(execution_time * 1000),
                        'args': str(args)[:200],  # Limit length
                        'kwargs': str(kwargs)[:200]
                    }
                )
                
                raise  # Re-raise the exception
        
        return wrapper
    return decorator
