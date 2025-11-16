from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.services.base_service import BaseService
from app.services.activity_logger import activity_logger
import statistics
import asyncio

class AnomalyDetectionService(BaseService):
    """
    Enhanced AI-powered anomaly detection service that analyzes activity logs and system metrics
    to identify suspicious patterns, performance degradations, and security threats.
    """
    
    def __init__(self, threshold_multiplier: float = 2.0, error_rate_threshold: float = 0.2, activity_multiplier_high: float = 3.0, activity_multiplier_low: float = 0.2, isolation_rate_threshold: float = 0.7):
        super().__init__("AnomalyDetectionService")
        self.threshold_multiplier = threshold_multiplier
        self.error_rate_threshold = error_rate_threshold
        self.activity_multiplier_high = activity_multiplier_high
        self.activity_multiplier_low = activity_multiplier_low
        self.isolation_rate_threshold = isolation_rate_threshold
        self.window_size = 100  # Still unused, but kept for potential future rolling window implementations
        self.baseline_metrics = {}
        self.anomaly_history = []
        self.pattern_cache = {}
        self.learning_enabled = True
    
    async def initialize(self) -> bool:
        """Initialize the enhanced anomaly detection service with activity log integration"""
        try:
            self.log_info("Initializing enhanced anomaly detection service")
            self.baseline_metrics = self._load_baseline_metrics()
            
            # Initialize pattern learning from activity logs
            await self._learn_baseline_patterns()
            
            # Log initialization
            await activity_logger.log_activity(
                agent_id="anomaly-detector",
                action_type="initialization",
                message="Anomaly detection service initialized with AI-powered pattern recognition",
                severity="info",
                data={
                    'baseline_metrics_count': len(self.baseline_metrics),
                    'learning_enabled': self.learning_enabled,
                    'detection_methods': ['statistical_outlier', 'pattern_analysis', 'behavioral_anomaly'],
                    'metadata': {
                        'context': 'service_initialization',
                        'confidence': 1.0,
                        'impact_score': 7.0
                    }
                }
            )
            
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize anomaly detection service: {e}")
            
            # Log error
            await activity_logger.log_error(
                agent_id="anomaly-detector",
                error_type="InitializationError",
                error_message=str(e)
            )
            
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return True
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.anomaly_history.clear()
        self.baseline_metrics.clear()
        return True
    
    async def detect_anomalies(self, metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced anomaly detection combining statistical analysis with activity log pattern recognition.
        
        Args:
            metrics: Optional dictionary containing various system/agent metrics. 
                    If not provided, will gather metrics from activity logs.
            
        Returns:
            Dictionary containing detected anomalies and summary statistics
        """
        anomalies = []
        
        try:
            # If no metrics provided, gather basic metrics from activity logs
            if metrics is None:
                metrics = await self._gather_system_metrics()
            
            # 1. Statistical Anomaly Detection
            statistical_anomalies = await self._detect_statistical_anomalies(metrics)
            anomalies.extend(statistical_anomalies)
            
            # 2. Activity Pattern Anomaly Detection
            activity_anomalies = await self._detect_activity_pattern_anomalies()
            anomalies.extend(activity_anomalies)
            
            # 3. Behavioral Anomaly Detection
            behavioral_anomalies = await self._detect_behavioral_anomalies()
            anomalies.extend(behavioral_anomalies)
            
            # 4. Cross-Agent Correlation Anomalies
            correlation_anomalies = await self._detect_correlation_anomalies()
            anomalies.extend(correlation_anomalies)
            
            # Log detection results
            if anomalies:
                await activity_logger.log_activity(
                    agent_id="anomaly-detector",
                    action_type="analysis",
                    message=f"Detected {len(anomalies)} anomalies across {len(metrics)} metrics",
                    severity="high" if any(a['severity'] in ['critical', 'high'] for a in anomalies) else "medium",
                    data={
                        'anomalies_detected': len(anomalies),
                        'severity_breakdown': self._count_by_severity(anomalies),
                        'detection_methods': ['statistical', 'pattern', 'behavioral', 'correlation'],
                        'metrics_analyzed': list(metrics.keys()),
                        'metadata': {
                            'context': 'anomaly_detection',
                            'confidence': 0.92,
                            'impact_score': min(len(anomalies) * 2, 10)
                        }
                    }
                )
            
            # Store anomalies
            for anomaly in anomalies:
                self.anomaly_history.append(anomaly)
                
            # Keep history manageable
            if len(self.anomaly_history) > 1000:
                self.anomaly_history = self.anomaly_history[-1000:]
            
            self.update_timestamp()
            
            return {
                "anomalies": anomalies,
                "total_anomalies": len(anomalies),
                "severity_breakdown": self._count_by_severity(anomalies),
                "methods_used": ['statistical', 'pattern', 'behavioral', 'correlation'],
                "avg_confidence": statistics.mean([a.get('confidence', 0.5) for a in anomalies]) if anomalies else 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.log_error(f"Error detecting anomalies: {e}")
            
            # Log error
            await activity_logger.log_error(
                agent_id="anomaly-detector",
                error_type="AnomalyDetectionError",
                error_message=str(e),
                error_details={'metrics_count': len(metrics) if metrics else 0, 'function': 'detect_anomalies'}
            )
            
            return {
                "anomalies": [],
                "total_anomalies": 0,
                "severity_breakdown": {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                "methods_used": [],
                "avg_confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _is_anomalous(self, metric_name: str, value: float) -> bool:
        """Check if a metric value is anomalous"""
        if metric_name not in self.baseline_metrics:
            return False
        
        baseline = self.baseline_metrics[metric_name]
        mean = baseline.get("mean", 0)
        std = baseline.get("std", 1)
        
        # Simple statistical outlier detection
        threshold = std * self.threshold_multiplier
        return abs(value - mean) > threshold
    
    def _get_expected_range(self, metric_name: str) -> Dict[str, float]:
        """Get expected range for a metric"""
        if metric_name not in self.baseline_metrics:
            return {"min": 0, "max": 100}
        
        baseline = self.baseline_metrics[metric_name]
        mean = baseline.get("mean", 0)
        std = baseline.get("std", 1)
        threshold = std * self.threshold_multiplier
        
        return {
            "min": mean - threshold,
            "max": mean + threshold
        }
    
    def _calculate_severity(self, metric_name: str, value: float) -> str:
        """Calculate anomaly severity"""
        if metric_name not in self.baseline_metrics:
            return "low"
        
        baseline = self.baseline_metrics[metric_name]
        mean = baseline.get("mean", 0)
        std = baseline.get("std", 1)
        
        deviation = abs(value - mean) / std if std > 0 else 0
        
        if deviation > 4:
            return "critical"
        elif deviation > 3:
            return "high"
        elif deviation > 2:
            return "medium"
        else:
            return "low"
    
    def _load_baseline_metrics(self) -> Dict[str, Dict[str, float]]:
        """Load baseline metrics for anomaly detection"""
        # In a real implementation, this would load from database
        return {
            "cpu_usage": {"mean": 45.0, "std": 15.0},
            "memory_usage": {"mean": 60.0, "std": 20.0},
            "response_time": {"mean": 250.0, "std": 50.0},
            "error_rate": {"mean": 0.02, "std": 0.01},
            "request_count": {"mean": 1000.0, "std": 200.0}
        }
    
    def get_anomaly_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of anomalies in the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_anomalies = [
            a for a in self.anomaly_history
            if datetime.fromisoformat(a["timestamp"]) > cutoff_time
        ]
        
        severity_counts = {}
        for anomaly in recent_anomalies:
            severity = anomaly["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_anomalies": len(recent_anomalies),
            "severity_breakdown": severity_counts,
            "time_window": f"{hours} hours",
            "recent_anomalies": recent_anomalies[-10:]  # Last 10
        }
    
    async def _learn_baseline_patterns(self):
        """Learn baseline patterns from activity logs"""
        try:
            activities = await activity_logger.get_activities(limit=500)  # Made async assuming logger supports it
            
            if not activities:
                self.log_info("No activities found for baseline learning")
                return
            
            # Learn agent activity patterns
            agent_patterns = {}
            hourly_patterns = {}  # Still computed but unused; can be extended later
            
            min_ts = min(datetime.fromisoformat(a['timestamp']) for a in activities)
            max_ts = max(datetime.fromisoformat(a['timestamp']) for a in activities)
            duration_hours = (max_ts - min_ts).total_seconds() / 3600 if max_ts > min_ts else 1.0
            
            for activity in activities:
                agent_id = activity['agent_id']
                timestamp = datetime.fromisoformat(activity['timestamp'])
                hour = timestamp.hour
                
                # Agent activity frequency and execution time
                if agent_id not in agent_patterns:
                    agent_patterns[agent_id] = {'count': 0, 'execution_times': [], 'rate_per_hour': 0.0, 'avg_execution_time': 0.0}
                
                agent_patterns[agent_id]['count'] += 1
                
                if 'execution_time' in activity.get('data', {}):
                    agent_patterns[agent_id]['execution_times'].append(
                        activity['data']['execution_time']
                    )
                
                # Hourly patterns (unused for now)
                if hour not in hourly_patterns:
                    hourly_patterns[hour] = 0
                hourly_patterns[hour] += 1
            
            # Compute averages and rates
            for agent_id, patterns in agent_patterns.items():
                patterns['rate_per_hour'] = patterns['count'] / duration_hours
                if patterns['execution_times']:
                    patterns['avg_execution_time'] = statistics.mean(patterns['execution_times'])
            
            # Store learned patterns
            self.pattern_cache['agent_patterns'] = agent_patterns
            self.pattern_cache['hourly_patterns'] = hourly_patterns
            
            self.log_info(f"Learned baseline patterns for {len(agent_patterns)} agents")
            
        except Exception as e:
            self.log_error(f"Error learning baseline patterns: {e}")
    
    async def _detect_statistical_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect statistical outliers in metrics"""
        anomalies = []
        
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and self._is_anomalous(metric_name, value):
                anomaly = {
                    "id": f"STAT-{datetime.utcnow().timestamp():.0f}",
                    "type": "statistical_outlier",
                    "metric": metric_name,
                    "value": value,
                    "expected_range": self._get_expected_range(metric_name),
                    "severity": self._calculate_severity(metric_name, value),
                    "confidence": 0.85,
                    "timestamp": datetime.utcnow().isoformat(),
                    "detection_method": "statistical_analysis",
                    "description": f"Metric {metric_name} value {value} deviates significantly from baseline"
                }
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_activity_pattern_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in AI agent activity patterns"""
        anomalies = []
        
        try:
            # Get recent activities (last hour)
            recent_activities = await activity_logger.get_activities(  # Made async
                since=datetime.utcnow() - timedelta(hours=1),
                limit=200
            )
            
            if not recent_activities:
                return anomalies
            
            # Calculate recent duration
            min_ts = min(datetime.fromisoformat(a['timestamp']) for a in recent_activities)
            max_ts = max(datetime.fromisoformat(a['timestamp']) for a in recent_activities)
            recent_duration_hours = (max_ts - min_ts).total_seconds() / 3600 if max_ts > min_ts else 1.0
            
            # Check for unusual agent activity levels
            agent_activity_counts = {}
            error_counts = {}
            
            for activity in recent_activities:
                agent_id = activity['agent_id']
                severity = activity['severity']
                
                agent_activity_counts[agent_id] = agent_activity_counts.get(agent_id, 0) + 1
                
                if severity in ['critical', 'high'] or activity['action_type'] == 'error':
                    error_counts[agent_id] = error_counts.get(agent_id, 0) + 1
            
            # Check for anomalous activity levels using rates
            for agent_id, count in agent_activity_counts.items():
                recent_rate = count / recent_duration_hours
                baseline = self.pattern_cache.get('agent_patterns', {}).get(agent_id, {})
                baseline_rate = baseline.get('rate_per_hour', 10.0)  # Default baseline rate
                
                # If activity rate is significantly higher or lower than baseline
                if recent_rate > baseline_rate * self.activity_multiplier_high:
                    anomalies.append({
                        "id": f"PAT-{agent_id}-{datetime.utcnow().timestamp():.0f}",
                        "type": "activity_pattern",
                        "agent_id": agent_id,
                        "metric": "activity_rate_per_hour",
                        "value": recent_rate,
                        "expected_range": f"0-{baseline_rate * 2}",
                        "severity": "medium",
                        "confidence": 0.78,
                        "timestamp": datetime.utcnow().isoformat(),
                        "detection_method": "pattern_analysis",
                        "description": f"Agent {agent_id} showing unusually high activity rate: {recent_rate:.2f}/hr vs baseline {baseline_rate:.2f}/hr"
                    })
                elif recent_rate < baseline_rate * self.activity_multiplier_low and baseline_rate > 5:
                    anomalies.append({
                        "id": f"PAT-{agent_id}-{datetime.utcnow().timestamp():.0f}",
                        "type": "activity_pattern",
                        "agent_id": agent_id,
                        "metric": "activity_rate_per_hour",
                        "value": recent_rate,
                        "expected_range": f"{baseline_rate * 0.5}-{baseline_rate * 2}",
                        "severity": "low",
                        "confidence": 0.65,
                        "timestamp": datetime.utcnow().isoformat(),
                        "detection_method": "pattern_analysis",
                        "description": f"Agent {agent_id} showing unusually low activity rate: {recent_rate:.2f}/hr vs baseline {baseline_rate:.2f}/hr"
                    })
            
            # Check for unusual error rates
            for agent_id, error_count in error_counts.items():
                total_count = agent_activity_counts.get(agent_id, 1)
                error_rate = error_count / total_count
                
                if error_rate > self.error_rate_threshold:
                    anomalies.append({
                        "id": f"ERR-{agent_id}-{datetime.utcnow().timestamp():.0f}",
                        "type": "error_pattern",
                        "agent_id": agent_id,
                        "metric": "error_rate",
                        "value": error_rate,
                        "expected_range": f"0-{self.error_rate_threshold}",
                        "severity": "high",
                        "confidence": 0.92,
                        "timestamp": datetime.utcnow().isoformat(),
                        "detection_method": "error_analysis",
                        "description": f"Agent {agent_id} has high error rate: {error_rate:.1%} ({error_count}/{total_count})"
                    })
        
        except Exception as e:
            self.log_error(f"Error detecting activity pattern anomalies: {e}")
        
        return anomalies
    
    async def _detect_behavioral_anomalies(self) -> List[Dict[str, Any]]:
        """Detect behavioral anomalies in AI agent decision patterns"""
        anomalies = []
        
        try:
            # Get recent decision activities
            recent_activities = await activity_logger.get_activities(  # Made async
                action_type='decision',
                since=datetime.utcnow() - timedelta(hours=6),
                limit=100
            )
            
            if len(recent_activities) < 5:
                return anomalies
            
            # Analyze decision confidence patterns
            confidence_scores = []
            execution_times = []
            
            for activity in recent_activities:
                data = activity.get('data', {})
                metadata = data.get('metadata', {})
                
                if 'confidence' in metadata:
                    confidence_scores.append(metadata['confidence'])
                
                if 'execution_time' in data:
                    execution_times.append(data['execution_time'])
            
            # Check for unusual confidence patterns
            if confidence_scores:
                avg_confidence = statistics.mean(confidence_scores)
                
                if avg_confidence < 0.5:  # Very low confidence in decisions
                    anomalies.append({
                        "id": f"BEH-CONF-{datetime.utcnow().timestamp():.0f}",
                        "type": "behavioral_anomaly",
                        "metric": "decision_confidence",
                        "value": avg_confidence,
                        "expected_range": "0.7-0.95",
                        "severity": "medium",
                        "confidence": 0.80,
                        "timestamp": datetime.utcnow().isoformat(),
                        "detection_method": "behavioral_analysis",
                        "description": f"AI agents showing unusually low decision confidence: {avg_confidence:.2f}"
                    })
            
            # Check for execution time anomalies
            if execution_times:
                avg_exec_time = statistics.mean(execution_times)
                
                # Compare to baseline avg_execution_time if available
                baseline_avg_exec = self.pattern_cache.get('agent_patterns', {}).get('avg_execution_time', 2000.0)  # Default 2000ms
                if avg_exec_time > baseline_avg_exec * 2.5:  # Significantly slower than baseline
                    anomalies.append({
                        "id": f"BEH-PERF-{datetime.utcnow().timestamp():.0f}",
                        "type": "performance_anomaly",
                        "metric": "execution_time",
                        "value": avg_exec_time,
                        "expected_range": f"100-{baseline_avg_exec * 2}ms",
                        "severity": "medium",
                        "confidence": 0.88,
                        "timestamp": datetime.utcnow().isoformat(),
                        "detection_method": "performance_analysis",
                        "description": f"AI agents showing slow execution times: {avg_exec_time:.0f}ms average vs baseline {baseline_avg_exec:.0f}ms"
                    })
        
        except Exception as e:
            self.log_error(f"Error detecting behavioral anomalies: {e}")
        
        return anomalies
    
    async def _detect_correlation_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in cross-agent activity correlations"""
        anomalies = []
        
        try:
            # Get recent activities
            recent_activities = await activity_logger.get_activities(  # Made async
                since=datetime.utcnow() - timedelta(hours=2),
                limit=200
            )
            
            if len(recent_activities) < 10:
                return anomalies
            
            # Check for unusual agent interaction patterns
            agent_interactions = {}
            time_windows = {}
            
            # Group activities by 5-minute windows
            for activity in recent_activities:
                timestamp = datetime.fromisoformat(activity['timestamp'])
                window = timestamp.replace(minute=(timestamp.minute // 5) * 5, second=0, microsecond=0)
                
                if window not in time_windows:
                    time_windows[window] = set()
                
                time_windows[window].add(activity['agent_id'])
            
            # Check for windows with unusual agent activity isolation
            for window, agents in time_windows.items():
                if len(agents) == 1:  # Only one agent active in this window
                    lone_agent = list(agents)[0]
                    
                    # Count how often this agent works alone
                    if lone_agent not in agent_interactions:
                        agent_interactions[lone_agent] = {'alone_count': 0, 'total_windows': 0}
                    
                    agent_interactions[lone_agent]['alone_count'] += 1
                
                # Count total windows for each agent
                for agent in agents:
                    if agent not in agent_interactions:
                        agent_interactions[agent] = {'alone_count': 0, 'total_windows': 0}
                    agent_interactions[agent]['total_windows'] += 1
            
            # Detect agents working in isolation too often
            for agent, stats in agent_interactions.items():
                if stats['total_windows'] > 5:  # Enough data points
                    isolation_rate = stats['alone_count'] / stats['total_windows']
                    
                    if isolation_rate > self.isolation_rate_threshold:
                        anomalies.append({
                            "id": f"COR-{agent}-{datetime.utcnow().timestamp():.0f}",
                            "type": "correlation_anomaly",
                            "agent_id": agent,
                            "metric": "isolation_rate",
                            "value": isolation_rate,
                            "expected_range": f"0-{self.isolation_rate_threshold}",
                            "severity": "low",
                            "confidence": 0.65,
                            "timestamp": datetime.utcnow().isoformat(),
                            "detection_method": "correlation_analysis",
                            "description": f"Agent {agent} working in isolation {isolation_rate:.1%} of the time"
                        })
        
        except Exception as e:
            self.log_error(f"Error detecting correlation anomalies: {e}")
        
        return anomalies
    
    def _count_by_severity(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count anomalies by severity level"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    async def _gather_system_metrics(self) -> Dict[str, Any]:
        """Gather basic system metrics from activity logs for anomaly detection"""
        try:
            activities = await activity_logger.get_activities(limit=100)  # Made async
            
            if not activities:
                return {
                    "activity_count": 0,
                    "error_rate": 0.0,
                    "avg_execution_time": 0.0,
                    "active_agents": 0
                }
            
            # Calculate basic metrics
            total_activities = len(activities)
            error_count = sum(1 for a in activities if a['severity'] in ['critical', 'high'] or a['action_type'] == 'error')
            error_rate = error_count / total_activities if total_activities > 0 else 0.0
            
            # Calculate average execution time
            execution_times = [activity.get('data', {}).get('execution_time') for activity in activities if 'execution_time' in activity.get('data', {})]
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0.0
            
            # Count active agents
            active_agents = len(set(a['agent_id'] for a in activities))
            
            return {
                "activity_count": total_activities,
                "error_rate": error_rate,
                "avg_execution_time": avg_execution_time,
                "active_agents": active_agents,
                "recent_errors": error_count,
                "activity_per_agent": total_activities / active_agents if active_agents > 0 else 0
            }
            
        except Exception as e:
            self.log_error(f"Error gathering system metrics: {e}")
            return {
                "activity_count": 0,
                "error_rate": 0.0,
                "avg_execution_time": 0.0,
                "active_agents": 0
            }