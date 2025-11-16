from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.services.base_service import BaseService

class SecurityService(BaseService):
    """
    Service for security monitoring and threat detection.
    """
    
    def __init__(self):
        super().__init__("SecurityService")
        self.security_events = []
        self.threat_patterns = []
        self.blocked_ips = set()
        self._initialize_threat_patterns()
    
    def initialize(self) -> bool:
        """Initialize the security service"""
        try:
            self.log_info("Initializing security service")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize security service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return True
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.security_events.clear()
        return True
    
    def log_security_event(self, event_type: str, source: str, details: Dict[str, Any]) -> str:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            source: Source of the event (IP, user, agent, etc.)
            details: Additional event details
            
        Returns:
            Event ID
        """
        event_id = f"sec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        event = {
            "id": event_id,
            "type": event_type,
            "source": source,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": self._calculate_severity(event_type),
            "status": "open"
        }
        
        self.security_events.append(event)
        self.log_info(f"Security event logged: {event_id} - {event_type}")
        
        # Check if immediate action is needed
        self._evaluate_threat(event)
        
        return event_id
    
    def detect_threats(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze log entries for potential threats.
        
        Args:
            log_entries: List of log entries to analyze
            
        Returns:
            List of detected threats
        """
        threats = []
        
        for entry in log_entries:
            for pattern in self.threat_patterns:
                if self._matches_pattern(entry, pattern):
                    threat = {
                        "id": f"threat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                        "pattern": pattern["name"],
                        "severity": pattern["severity"],
                        "log_entry": entry,
                        "detected_at": datetime.utcnow().isoformat(),
                        "action_taken": None
                    }
                    threats.append(threat)
                    
                    # Log as security event
                    self.log_security_event(
                        "threat_detected",
                        entry.get("source", "unknown"),
                        {"pattern": pattern["name"], "log_entry": entry}
                    )
        
        return threats
    
    def block_ip(self, ip_address: str, reason: str) -> bool:
        """
        Block an IP address.
        
        Args:
            ip_address: IP address to block
            reason: Reason for blocking
            
        Returns:
            True if blocking successful
        """
        if ip_address in self.blocked_ips:
            self.log_warning(f"IP {ip_address} already blocked")
            return False
        
        self.blocked_ips.add(ip_address)
        
        # Log security event
        self.log_security_event(
            "ip_blocked",
            ip_address,
            {"reason": reason}
        )
        
        self.log_info(f"IP {ip_address} blocked: {reason}")
        return True
    
    def unblock_ip(self, ip_address: str) -> bool:
        """
        Unblock an IP address.
        
        Args:
            ip_address: IP address to unblock
            
        Returns:
            True if unblocking successful
        """
        if ip_address not in self.blocked_ips:
            self.log_warning(f"IP {ip_address} not in blocked list")
            return False
        
        self.blocked_ips.remove(ip_address)
        
        # Log security event
        self.log_security_event(
            "ip_unblocked",
            ip_address,
            {"action": "manual_unblock"}
        )
        
        self.log_info(f"IP {ip_address} unblocked")
        return True
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is blocked"""
        return ip_address in self.blocked_ips
    
    def get_security_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get security events from the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of security events
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_events = []
        for event in self.security_events:
            event_time = datetime.fromisoformat(event["timestamp"])
            if event_time > cutoff_time:
                filtered_events.append(event)
        
        return filtered_events
    
    def get_blocked_ips(self) -> List[str]:
        """Get list of blocked IP addresses"""
        return list(self.blocked_ips)
    
    def _calculate_severity(self, event_type: str) -> str:
        """Calculate severity based on event type"""
        high_severity_types = [
            "unauthorized_access", "brute_force", "malware_detected",
            "data_breach", "privilege_escalation"
        ]
        
        medium_severity_types = [
            "suspicious_activity", "failed_login", "unusual_pattern",
            "policy_violation"
        ]
        
        if event_type in high_severity_types:
            return "high"
        elif event_type in medium_severity_types:
            return "medium"
        else:
            return "low"
    
    def _matches_pattern(self, log_entry: Dict[str, Any], pattern: Dict[str, Any]) -> bool:
        """Check if log entry matches threat pattern"""
        # Simple pattern matching - in production, use more sophisticated methods
        keywords = pattern.get("keywords", [])
        message = str(log_entry.get("message", "")).lower()
        
        for keyword in keywords:
            if keyword.lower() in message:
                return True
        
        return False
    
    def _evaluate_threat(self, event: Dict[str, Any]):
        """Evaluate threat and take immediate action if needed"""
        if event["severity"] == "high":
            # For high severity events, consider blocking source
            source = event["source"]
            if self._is_ip_address(source):
                self.block_ip(source, f"High severity security event: {event['type']}")
    
    def _is_ip_address(self, text: str) -> bool:
        """Simple check if text looks like an IP address"""
        parts = text.split('.')
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except ValueError:
            return False
    
    def _initialize_threat_patterns(self):
        """Initialize threat detection patterns"""
        self.threat_patterns = [
            {
                "name": "SQL Injection Attempt",
                "keywords": ["union select", "drop table", "'; --", "' or '1'='1"],
                "severity": "high"
            },
            {
                "name": "Brute Force Attack",
                "keywords": ["failed login", "authentication failed", "invalid password"],
                "severity": "medium"
            },
            {
                "name": "Suspicious File Access",
                "keywords": ["unauthorized file access", "permission denied", "access violation"],
                "severity": "medium"
            },
            {
                "name": "Malware Signature",
                "keywords": ["virus detected", "malware", "trojan", "suspicious executable"],
                "severity": "high"
            },
            {
                "name": "Data Exfiltration",
                "keywords": ["large data transfer", "bulk download", "data export"],
                "severity": "high"
            }
        ]
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get summary of security status"""
        recent_events = self.get_security_events(24)
        
        severity_counts = {}
        event_type_counts = {}
        
        for event in recent_events:
            # Count by severity
            severity = event["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by type
            event_type = event["type"]
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        return {
            "total_events_24h": len(recent_events),
            "severity_breakdown": severity_counts,
            "event_type_breakdown": event_type_counts,
            "blocked_ips": len(self.blocked_ips),
            "threat_patterns": len(self.threat_patterns),
            "last_updated": datetime.utcnow().isoformat()
        }
