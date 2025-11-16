"""
Activity Logger - Firestore Version
Automatic logging of AI agent activities with Firestore persistence
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import hashlib
from app.services.firebase_service import FirestoreService
from app.firebase_config import Collections


class ActivityLoggerServiceFirestore:
    """Service for logging AI agent activities with Firestore immutable record keeping"""
    
    def __init__(self):
        self.firestore_service = FirestoreService(Collections.ACTIVITY_LOGS)
        # Keep small in-memory cache for quick access
        self._cache = []
        self._cache_limit = 100
    
    def generate_hash(self, activity_data: str) -> str:
        """Generate SHA-256 hash for immutable record verification"""
        return hashlib.sha256(activity_data.encode()).hexdigest()[:16]
    
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
        
        # Create unique ID
        activity_id = f'activity-{int(timestamp.timestamp())}-{activity_hash[:8]}'
        
        # Create activity record for Firestore
        activity_record = {
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
        
        try:
            # Save to Firestore
            created = await self.firestore_service.create(
                doc_id=activity_id,
                data=activity_record
            )
            
            # Update cache
            self._update_cache(created)
            
            return created
        except Exception as e:
            print(f"Firestore error logging activity: {e}")
            # Fallback to cache only
            activity_record['id'] = activity_id
            activity_record['created_at'] = timestamp.isoformat()
            activity_record['updated_at'] = timestamp.isoformat()
            self._update_cache(activity_record)
            return activity_record
    
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
    
    async def get_activities(
        self,
        limit: int = 100,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        severity: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered activities from Firestore"""
        try:
            filters = []
            
            # Apply filters
            if agent_id:
                filters.append(('agent_id', '==', agent_id))
            if action_type:
                filters.append(('action_type', '==', action_type))
            if severity:
                filters.append(('severity', '==', severity))
            if since:
                filters.append(('timestamp', '>', since.isoformat()))
            
            # Query Firestore with filters, ordered by timestamp (newest first)
            activities = await self.firestore_service.get_all(
                filters=filters if filters else None,
                order_by='-timestamp',  # Descending order
                limit=limit
            )
            
            return activities
        except Exception as e:
            print(f"Firestore error getting activities: {e}")
            # Fallback to cache on error
            filtered = self._cache.copy()
            
            if agent_id:
                filtered = [a for a in filtered if a.get('agent_id') == agent_id]
            if action_type:
                filtered = [a for a in filtered if a.get('action_type') == action_type]
            if severity:
                filtered = [a for a in filtered if a.get('severity') == severity]
            if since:
                filtered = [
                    a for a in filtered
                    if datetime.fromisoformat(a.get('timestamp', '')) > since
                ]
            
            filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return filtered[:limit]
    
    async def get_latest_activities(self, since: datetime, limit: int = 50) -> List[Dict[str, Any]]:
        """Get activities since a specific timestamp from Firestore"""
        try:
            activities = await self.firestore_service.get_all(
                filters=[('timestamp', '>', since.isoformat())],
                order_by='-timestamp',
                limit=limit
            )
            return activities
        except Exception as e:
            print(f"Firestore error getting latest activities: {e}")
            # Fallback to cache
            return [
                a for a in self._cache
                if datetime.fromisoformat(a.get('timestamp', '')) > since
            ][:limit]
    
    async def get_activity_stats(self) -> Dict[str, Any]:
        """Get aggregated activity statistics from Firestore"""
        try:
            # Get all activities (consider limiting this for large datasets)
            all_activities = await self.firestore_service.get_all(limit=10000)
            
            if not all_activities:
                return {
                    'total_activities': 0,
                    'decisions': 0,
                    'data_points': 0,
                    'errors': 0,
                    'avg_response_time': 0,
                    'active_agents': 0
                }
            
            total = len(all_activities)
            decisions = len([a for a in all_activities if a.get('action_type') == 'decision'])
            data_points = len([a for a in all_activities if a.get('action_type') == 'data_collection'])
            errors = len([
                a for a in all_activities
                if a.get('severity') == 'critical' or a.get('action_type') == 'error'
            ])
            
            # Calculate average execution time
            exec_times = [
                a.get('data', {}).get('execution_time', 0)
                for a in all_activities
                if a.get('data') and 'execution_time' in a.get('data', {})
            ]
            avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
            
            # Count unique agents
            active_agents = len(set(a.get('agent_id') for a in all_activities if a.get('agent_id')))
            
            return {
                'total_activities': total,
                'decisions': decisions,
                'data_points': data_points,
                'errors': errors,
                'avg_response_time': int(avg_exec_time),
                'active_agents': active_agents
            }
        except Exception as e:
            print(f"Firestore error getting activity stats: {e}")
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
            decisions = len([a for a in self._cache if a.get('action_type') == 'decision'])
            data_points = len([a for a in self._cache if a.get('action_type') == 'data_collection'])
            errors = len([
                a for a in self._cache
                if a.get('severity') == 'critical' or a.get('action_type') == 'error'
            ])
            
            exec_times = [
                a.get('data', {}).get('execution_time', 0)
                for a in self._cache
                if 'execution_time' in a.get('data', {})
            ]
            avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
            
            active_agents = len(set(a.get('agent_id') for a in self._cache if a.get('agent_id')))
            
            return {
                'total_activities': total,
                'decisions': decisions,
                'data_points': data_points,
                'errors': errors,
                'avg_response_time': int(avg_exec_time),
                'active_agents': active_agents
            }
    
    async def verify_integrity(self, activity_id: str) -> bool:
        """Verify the integrity of an activity log by recalculating its hash"""
        try:
            activity = await self.firestore_service.get(activity_id)
            
            if not activity:
                return False
            
            # Reconstruct hash input
            hash_input = f"{activity.get('agent_id')}-{activity.get('action_type')}-{activity.get('timestamp')}-{activity.get('message')}"
            expected_hash = self.generate_hash(hash_input)
            
            return activity.get('hash') == expected_hash
        except Exception as e:
            print(f"Error verifying integrity: {e}")
            return False
    
    async def get_agent_activity_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get activity summary for a specific agent"""
        try:
            activities = await self.get_activities(agent_id=agent_id, limit=1000)
            
            if not activities:
                return {
                    'agent_id': agent_id,
                    'total_activities': 0,
                    'last_active': None,
                    'activity_breakdown': {},
                    'error_count': 0,
                    'success_rate': 100
                }
            
            # Calculate breakdown by action type
            breakdown = {}
            for activity in activities:
                action_type = activity.get('action_type', 'unknown')
                breakdown[action_type] = breakdown.get(action_type, 0) + 1
            
            # Count errors
            errors = len([a for a in activities if a.get('severity') == 'critical'])
            
            # Calculate success rate
            total = len(activities)
            success_rate = ((total - errors) / total * 100) if total > 0 else 100
            
            # Get last active timestamp
            last_active = max(
                (datetime.fromisoformat(a.get('timestamp', '')) for a in activities if a.get('timestamp')),
                default=None
            )
            
            return {
                'agent_id': agent_id,
                'total_activities': total,
                'last_active': last_active.isoformat() if last_active else None,
                'activity_breakdown': breakdown,
                'error_count': errors,
                'success_rate': round(success_rate, 2)
            }
        except Exception as e:
            print(f"Error getting agent summary: {e}")
            return {
                'agent_id': agent_id,
                'total_activities': 0,
                'last_active': None,
                'activity_breakdown': {},
                'error_count': 0,
                'success_rate': 100
            }


# Global activity logger instance (Firestore version)
activity_logger_firestore = ActivityLoggerServiceFirestore()
