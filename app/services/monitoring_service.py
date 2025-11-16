from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.services.base_service import BaseService

class MonitoringService(BaseService):
    """
    Service for system and agent monitoring.
    """
    
    def __init__(self):
        super().__init__("MonitoringService")
        self.metrics_history = []
        self.alerts = []
        self.thresholds = {}
        self._initialize_thresholds()
    
    def initialize(self) -> bool:
        """Initialize the monitoring service"""
        try:
            self.log_info("Initializing monitoring service")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize monitoring service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return True
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.metrics_history.clear()
        self.alerts.clear()
        return True
    
    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect current system metrics.
        
        Returns:
            Dictionary of current metrics
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_usage": 45.2,
                "memory_usage": 68.5,
                "disk_usage": 34.1,
                "network_io": 1024.5
            },
            "application": {
                "active_agents": 11,
                "pending_tasks": 23,
                "completed_tasks": 1847,
                "error_count": 2,
                "response_time": 145.3
            },
            "database": {
                "connections": 5,
                "query_time": 12.4,
                "cache_hit_ratio": 0.95
            }
        }
        
        # Store in history
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Check for alerts
        self._check_thresholds(metrics)
        
        return metrics
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get metrics history for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of historical metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_metrics = []
        for metric in self.metrics_history:
            metric_time = datetime.fromisoformat(metric["timestamp"])
            if metric_time > cutoff_time:
                filtered_metrics.append(metric)
        
        return filtered_metrics
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status"""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics available"}
        
        latest_metrics = self.metrics_history[-1]
        system_metrics = latest_metrics["system"]
        app_metrics = latest_metrics["application"]
        
        # Determine overall status
        status = "healthy"
        issues = []
        
        if system_metrics["cpu_usage"] > 80:
            status = "warning"
            issues.append("High CPU usage")
        
        if system_metrics["memory_usage"] > 85:
            status = "warning"
            issues.append("High memory usage")
        
        if app_metrics["error_count"] > 10:
            status = "critical"
            issues.append("High error count")
        
        return {
            "status": status,
            "timestamp": latest_metrics["timestamp"],
            "issues": issues,
            "metrics": latest_metrics
        }
    
    def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get alerts from the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of alerts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_alerts = []
        for alert in self.alerts:
            alert_time = datetime.fromisoformat(alert["timestamp"])
            if alert_time > cutoff_time:
                filtered_alerts.append(alert)
        
        return filtered_alerts
    
    def create_alert(self, severity: str, message: str, metric_name: str, value: float) -> str:
        """
        Create a new alert.
        
        Args:
            severity: Alert severity (info, warning, critical)
            message: Alert message
            metric_name: Name of the metric that triggered the alert
            value: Current value of the metric
            
        Returns:
            Alert ID
        """
        alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        alert = {
            "id": alert_id,
            "severity": severity,
            "message": message,
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False
        }
        
        self.alerts.append(alert)
        self.log_info(f"Alert created: {alert_id} - {message}")
        
        return alert_id
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of the alert to acknowledge
            
        Returns:
            True if acknowledgment successful
        """
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_at"] = datetime.utcnow().isoformat()
                self.log_info(f"Alert {alert_id} acknowledged")
                return True
        
        self.log_warning(f"Alert {alert_id} not found")
        return False
    
    def _initialize_thresholds(self):
        """Initialize monitoring thresholds"""
        self.thresholds = {
            "system.cpu_usage": {"warning": 70, "critical": 90},
            "system.memory_usage": {"warning": 80, "critical": 95},
            "system.disk_usage": {"warning": 85, "critical": 95},
            "application.error_count": {"warning": 5, "critical": 15},
            "application.response_time": {"warning": 500, "critical": 1000}
        }
    
    def _check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and create alerts if needed"""
        def check_nested_metric(metric_dict: Dict[str, Any], prefix: str = ""):
            for key, value in metric_dict.items():
                if isinstance(value, dict):
                    check_nested_metric(value, f"{prefix}.{key}" if prefix else key)
                elif isinstance(value, (int, float)):
                    metric_path = f"{prefix}.{key}" if prefix else key
                    if metric_path in self.thresholds:
                        threshold = self.thresholds[metric_path]
                        
                        if value >= threshold["critical"]:
                            self.create_alert(
                                "critical",
                                f"{metric_path} is critically high: {value}",
                                metric_path,
                                value
                            )
                        elif value >= threshold["warning"]:
                            self.create_alert(
                                "warning", 
                                f"{metric_path} is above warning threshold: {value}",
                                metric_path,
                                value
                            )
        
        # Skip timestamp and check other metrics
        metrics_to_check = {k: v for k, v in metrics.items() if k != "timestamp"}
        check_nested_metric(metrics_to_check)
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get summary of monitoring system status"""
        total_alerts = len(self.alerts)
        unacknowledged_alerts = len([a for a in self.alerts if not a["acknowledged"]])
        
        # Recent metrics stats
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            avg_cpu = sum(m["system"]["cpu_usage"] for m in self.metrics_history[-10:]) / min(10, len(self.metrics_history))
            avg_memory = sum(m["system"]["memory_usage"] for m in self.metrics_history[-10:]) / min(10, len(self.metrics_history))
        else:
            latest_metrics = None
            avg_cpu = 0
            avg_memory = 0
        
        return {
            "total_alerts": total_alerts,
            "unacknowledged_alerts": unacknowledged_alerts,
            "metrics_collected": len(self.metrics_history),
            "latest_collection": latest_metrics["timestamp"] if latest_metrics else None,
            "avg_cpu_10min": round(avg_cpu, 1),
            "avg_memory_10min": round(avg_memory, 1)
        }
