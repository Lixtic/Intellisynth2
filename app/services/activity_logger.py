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

class ActivityLoggerService:
    """Service for logging AI agent activities with immutable record keeping"""
    
    def __init__(self):
        self.activities = []  # In-memory store for demonstration
    
    def generate_hash(self, activity_data: str) -> str:
        """Generate SHA-256 hash for immutable record verification"""
        return hashlib.sha256(activity_data.encode()).hexdigest()[:16]
    
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
        
        # Create activity record
        activity = {
            'id': f'activity-{timestamp.timestamp()}-{activity_hash[:8]}',
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
        
        # Store activity (in real implementation, this would go to database)
        self.activities.append(activity)
        
        # Keep only last 1000 activities for performance
        if len(self.activities) > 1000:
            self.activities = self.activities[-1000:]
        
        return activity
    
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
        """Get filtered activities"""
        filtered = self.activities.copy()
        
        # Apply filters
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
    
    def get_latest_activities(self, since: datetime, limit: int = 50) -> list:
        """Get activities since a specific timestamp"""
        return [
            a for a in self.activities
            if datetime.fromisoformat(a['timestamp']) > since
        ][:limit]
    
    def get_activity_stats(self) -> Dict[str, Any]:
        """Get aggregated activity statistics"""
        if not self.activities:
            return {
                'total_activities': 0,
                'decisions': 0,
                'data_points': 0,
                'errors': 0,
                'avg_response_time': 0,
                'active_agents': 0
            }
        
        total = len(self.activities)
        decisions = len([a for a in self.activities if a['action_type'] == 'decision'])
        data_points = len([a for a in self.activities if a['action_type'] == 'data_collection'])
        errors = len([a for a in self.activities if a['severity'] == 'critical' or a['action_type'] == 'error'])
        
        # Calculate average execution time
        exec_times = [
            a['data']['execution_time'] for a in self.activities
            if 'execution_time' in a['data']
        ]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        # Count unique agents
        unique_agents = len(set([a['agent_id'] for a in self.activities]))
        
        return {
            'total_activities': total,
            'decisions': decisions,
            'data_points': data_points,
            'errors': errors,
            'avg_response_time': avg_exec_time,
            'active_agents': unique_agents,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify integrity of all activity records"""
        verified_count = 0
        invalid_hashes = []
        
        for activity in self.activities:
            # Recreate hash and verify
            hash_input = f"{activity['agent_id']}-{activity['action_type']}-{activity['timestamp']}-{activity['message']}"
            expected_hash = self.generate_hash(hash_input)
            
            if activity['hash'] == expected_hash:
                verified_count += 1
            else:
                invalid_hashes.append(activity['id'])
        
        total_records = len(self.activities)
        integrity_percentage = (verified_count / total_records * 100) if total_records > 0 else 100
        
        # Generate system hash
        all_hashes = [a['hash'] for a in self.activities]
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
