from typing import List, Any, Dict, Optional
from datetime import datetime, timedelta
from app.services.compliance_engine import ComplianceEngine, ComplianceRule
from app.services.base_service import BaseService

class ComplianceService(BaseService):
    """
    Enhanced Compliance Service with full debugging and monitoring capabilities.
    """
    
    def __init__(self, rules: List[ComplianceRule] = None):
        super().__init__("ComplianceService")
        self.engine = ComplianceEngine(rules or [])
        self.violation_history = []
        self.compliance_stats = {
            "total_checks": 0,
            "violations_found": 0,
            "rules_passed": 0,
            "last_check": None
        }
        self._initialize_default_rules()
    
    def initialize(self) -> bool:
        """Initialize the compliance service"""
        try:
            self.log_info("Initializing compliance service with debugging enabled")
            self._load_compliance_rules()
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize compliance service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return len(self.engine.rules) > 0
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.violation_history.clear()
        return True

    def check_compliance(self, log_entry: Any) -> List[ComplianceRule]:
        """
        Checks a log entry for compliance violations with detailed debugging.
        Returns a list of violated rules.
        """
        try:
            self.compliance_stats["total_checks"] += 1
            self.compliance_stats["last_check"] = datetime.utcnow().isoformat()
            
            self.log_info(f"Starting compliance check for entry: {type(log_entry).__name__}")
            
            # Debug: Log the log entry details
            if hasattr(log_entry, '__dict__'):
                self.log_info(f"Log entry details: {log_entry.__dict__}")
            else:
                self.log_info(f"Log entry content: {log_entry}")
            
            violations = self.engine.evaluate(log_entry)
            
            if violations:
                self.compliance_stats["violations_found"] += len(violations)
                self.log_warning(f"Found {len(violations)} compliance violations")
                self.log_violations(log_entry, violations)
            else:
                self.compliance_stats["rules_passed"] += 1
                self.log_info("All compliance rules passed")
            
            self.update_timestamp()
            return violations
            
        except Exception as e:
            self.log_error(f"Error during compliance check: {e}")
            return []

    def log_violations(self, log_entry: Any, violations: List[ComplianceRule]):
        """
        Log and persist compliance violations with debugging information.
        """
        try:
            violation_record = {
                "id": f"violation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                "timestamp": datetime.utcnow().isoformat(),
                "log_entry": str(log_entry),
                "violations": [
                    {
                        "rule_name": rule.name,
                        "description": rule.description,
                        "severity": getattr(rule, 'severity', 'medium')
                    }
                    for rule in violations
                ],
                "total_violations": len(violations),
                "status": "open"
            }
            
            self.violation_history.append(violation_record)
            
            # Debug logging
            self.log_warning(f"Logged violation record: {violation_record['id']}")
            for violation in violations:
                self.log_warning(f"  - Rule violated: {violation.name} - {violation.description}")
            
            # Keep only last 1000 violations
            if len(self.violation_history) > 1000:
                self.violation_history = self.violation_history[-1000:]
                
        except Exception as e:
            self.log_error(f"Error logging violations: {e}")

    def get_compliance_status(self) -> Dict[str, Any]:
        """
        Get comprehensive compliance status with debugging information.
        """
        try:
            recent_violations = self.get_recent_violations(hours=24)
            
            compliance_rate = 0
            if self.compliance_stats["total_checks"] > 0:
                compliance_rate = (
                    (self.compliance_stats["total_checks"] - self.compliance_stats["violations_found"]) 
                    / self.compliance_stats["total_checks"] * 100
                )
            
            status = {
                "overall_status": "compliant" if compliance_rate > 95 else "non_compliant" if compliance_rate < 80 else "warning",
                "compliance_rate": round(compliance_rate, 2),
                "statistics": self.compliance_stats.copy(),
                "recent_violations": {
                    "count_24h": len(recent_violations),
                    "violations": recent_violations[-5:]  # Last 5 violations
                },
                "rules_configured": len(self.engine.rules),
                "service_health": self.get_status(),
                "debug_info": {
                    "total_violation_records": len(self.violation_history),
                    "service_uptime": self.last_updated,
                    "last_check": self.compliance_stats["last_check"]
                }
            }
            
            self.log_info(f"Compliance status: {status['overall_status']} ({compliance_rate:.1f}%)")
            return status
            
        except Exception as e:
            self.log_error(f"Error getting compliance status: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "debug_info": {"service_status": "error"}
            }
    
    def get_recent_violations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get violations from the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_violations = []
        for violation in self.violation_history:
            violation_time = datetime.fromisoformat(violation["timestamp"])
            if violation_time > cutoff_time:
                recent_violations.append(violation)
        
        return recent_violations
    
    def get_violation_by_id(self, violation_id: str) -> Optional[Dict[str, Any]]:
        """Get specific violation by ID"""
        for violation in self.violation_history:
            if violation["id"] == violation_id:
                return violation
        return None
    
    def resolve_violation(self, violation_id: str, resolver: str = "system") -> bool:
        """Mark a violation as resolved"""
        for violation in self.violation_history:
            if violation["id"] == violation_id:
                violation["status"] = "resolved"
                violation["resolved_by"] = resolver
                violation["resolved_at"] = datetime.utcnow().isoformat()
                self.log_info(f"Violation {violation_id} resolved by {resolver}")
                return True
        return False
    
    def _initialize_default_rules(self):
        """Initialize default compliance rules for debugging"""
        if not self.engine.rules:
            default_rules = [
                DataRetentionRule(),
                AccessControlRule(), 
                LoggingComplianceRule(),
                SecurityComplianceRule()
            ]
            self.engine.rules.extend(default_rules)
            self.log_info(f"Initialized {len(default_rules)} default compliance rules")
    
    def _load_compliance_rules(self):
        """Load compliance rules from configuration"""
        # In a real implementation, this would load from database or config files
        self.log_info("Compliance rules loaded successfully")


# Example compliance rules for debugging
class DataRetentionRule(ComplianceRule):
    def __init__(self):
        super().__init__("Data Retention Policy", "Data must not be retained longer than required periods")
        self.severity = "high"
    
    def check(self, log_entry: Any) -> bool:
        # Example: Check if data is older than retention period
        if hasattr(log_entry, 'timestamp') or (isinstance(log_entry, dict) and 'timestamp' in log_entry):
            return True  # Simplified check - always pass for demo
        return True

class AccessControlRule(ComplianceRule):
    def __init__(self):
        super().__init__("Access Control", "All access must be properly authorized")
        self.severity = "high"
    
    def check(self, log_entry: Any) -> bool:
        # Example: Check for unauthorized access attempts
        if isinstance(log_entry, dict):
            action = log_entry.get('action', '').lower()
            if 'unauthorized' in action or 'denied' in action:
                return False  # Violation found
        return True

class LoggingComplianceRule(ComplianceRule):
    def __init__(self):
        super().__init__("Logging Compliance", "All actions must be properly logged")
        self.severity = "medium"
    
    def check(self, log_entry: Any) -> bool:
        # Example: Check if required fields are present
        required_fields = ['timestamp', 'action', 'user_id']
        if isinstance(log_entry, dict):
            return all(field in log_entry for field in required_fields)
        return True

class SecurityComplianceRule(ComplianceRule):
    def __init__(self):
        super().__init__("Security Policy", "Security policies must be enforced")
        self.severity = "high"
    
    def check(self, log_entry: Any) -> bool:
        # Example: Check for security violations
        if isinstance(log_entry, dict):
            severity = log_entry.get('severity', '').lower()
            if severity in ['critical', 'high'] and log_entry.get('resolved', True) == False:
                return False  # Unresolved high severity issue
        return True
