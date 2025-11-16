from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Integer, Enum as SQLEnum
from datetime import datetime
import uuid
import enum
from app.database import Base

class SeverityLevel(enum.Enum):
    """Enumeration for compliance rule severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"  
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RuleType(enum.Enum):
    """Enumeration for compliance rule types"""
    DATA_RETENTION = "data_retention"
    ACCESS_CONTROL = "access_control"
    AUDIT_LOGGING = "audit_logging"
    ENCRYPTION = "encryption"
    BACKUP_POLICY = "backup_policy"
    SECURITY_POLICY = "security_policy"
    PRIVACY_POLICY = "privacy_policy"
    MONITORING = "monitoring"
    CUSTOM = "custom"

class RuleStatus(enum.Enum):
    """Enumeration for compliance rule status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISABLED = "DISABLED"
    DRAFT = "DRAFT"

class ComplianceRule(Base):
    """
    SQLAlchemy model for compliance rules in the AI Flight Recorder system.
    
    This model represents compliance rules that can be dynamically configured
    and applied to monitor activities for regulatory and policy compliance.
    """
    __tablename__ = "compliance_rules"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: f"CR_{uuid.uuid4().hex[:8].upper()}")
    
    # Rule metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    rule_type = Column(SQLEnum(RuleType), nullable=False, default=RuleType.CUSTOM)
    
    # Rule configuration
    severity = Column(SQLEnum(SeverityLevel), nullable=False, default=SeverityLevel.MEDIUM)
    status = Column(SQLEnum(RuleStatus), nullable=False, default=RuleStatus.ACTIVE)
    
    # Rule logic and conditions
    conditions = Column(JSON, nullable=True)  # JSON configuration for rule conditions
    parameters = Column(JSON, nullable=True)  # Additional parameters for rule execution
    
    # Monitoring and metrics
    violations_count = Column(Integer, default=0)  # Total violations detected
    last_violation_date = Column(DateTime, nullable=True)
    last_check_date = Column(DateTime, nullable=True)
    
    # Rule management
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Rule configuration
    is_automated = Column(Boolean, default=True)  # Whether rule runs automatically
    priority = Column(Integer, default=100)  # Priority for rule execution (lower = higher priority)
    
    # Compliance framework support
    framework = Column(String(100), nullable=True)  # e.g., "GDPR", "SOX", "HIPAA", "PCI-DSS"
    regulation_reference = Column(String(255), nullable=True)  # Reference to specific regulation
    
    # Rule versioning
    version = Column(String(20), default="1.0")
    parent_rule_id = Column(String, nullable=True)  # For rule versioning/inheritance

    def __repr__(self):
        return f"<ComplianceRule(id='{self.id}', name='{self.name}', type='{self.rule_type.value}', severity='{self.severity.value}', status='{self.status.value}')>"

    def to_dict(self):
        """Convert the compliance rule to a dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type.value if self.rule_type else None,
            "severity": self.severity.value if self.severity else None,
            "status": self.status.value if self.status else None,
            "conditions": self.conditions,
            "parameters": self.parameters,
            "violations_count": self.violations_count or 0,
            "last_violation_date": self.last_violation_date.isoformat() if self.last_violation_date else None,
            "last_check_date": self.last_check_date.isoformat() if self.last_check_date else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_automated": self.is_automated,
            "priority": self.priority,
            "framework": self.framework,
            "regulation_reference": self.regulation_reference,
            "version": self.version,
            "parent_rule_id": self.parent_rule_id
        }

    def is_active(self):
        """Check if the rule is currently active"""
        return self.status == RuleStatus.ACTIVE

    def increment_violations(self):
        """Increment the violation count and update the last violation date"""
        self.violations_count = (self.violations_count or 0) + 1
        self.last_violation_date = datetime.utcnow()

    def update_last_check(self):
        """Update the last check timestamp"""
        self.last_check_date = datetime.utcnow()

    @classmethod
    def create_default_rules(cls):
        """
        Create a set of default compliance rules for common scenarios.
        Returns a list of ComplianceRule instances.
        """
        default_rules = []
        
        # Data Retention Rule
        data_retention_rule = cls(
            name="Data Retention Policy",
            description="Ensure data is not retained longer than required retention periods",
            rule_type=RuleType.DATA_RETENTION,
            severity=SeverityLevel.HIGH,
            conditions={
                "max_retention_days": 90,
                "data_types": ["logs", "activities", "audit_records"],
                "exceptions": ["critical_incidents", "ongoing_investigations"]
            },
            framework="GDPR",
            regulation_reference="Article 5(1)(e) - Storage limitation"
        )
        default_rules.append(data_retention_rule)
        
        # Access Control Rule
        access_control_rule = cls(
            name="API Access Control",
            description="All API access must be properly authenticated and authorized",
            rule_type=RuleType.ACCESS_CONTROL,
            severity=SeverityLevel.HIGH,
            conditions={
                "require_authentication": True,
                "require_authorization": True,
                "allowed_roles": ["admin", "operator", "viewer"],
                "forbidden_actions": ["unauthorized_access", "privilege_escalation"]
            },
            framework="SOX",
            regulation_reference="Section 404 - Internal Controls"
        )
        default_rules.append(access_control_rule)
        
        # Audit Logging Rule
        audit_logging_rule = cls(
            name="Audit Log Completeness",
            description="All critical actions must be properly logged with required fields",
            rule_type=RuleType.AUDIT_LOGGING,
            severity=SeverityLevel.MEDIUM,
            conditions={
                "required_fields": ["timestamp", "user_id", "action", "resource", "outcome"],
                "critical_actions": ["login", "logout", "data_access", "configuration_change"],
                "log_level": "INFO"
            },
            framework="PCI-DSS",
            regulation_reference="Requirement 10 - Log and monitor all access"
        )
        default_rules.append(audit_logging_rule)
        
        # Encryption Rule
        encryption_rule = cls(
            name="Data Encryption at Rest",
            description="Sensitive data must be encrypted when stored",
            rule_type=RuleType.ENCRYPTION,
            severity=SeverityLevel.HIGH,
            conditions={
                "encryption_algorithm": "AES-256",
                "sensitive_data_types": ["pii", "financial", "health", "credentials"],
                "key_rotation_days": 365
            },
            framework="HIPAA",
            regulation_reference="164.312(a)(2)(iv) - Encryption and decryption"
        )
        default_rules.append(encryption_rule)
        
        # Security Monitoring Rule
        security_monitoring_rule = cls(
            name="Security Event Monitoring",
            description="Monitor and alert on security-related events and anomalies",
            rule_type=RuleType.MONITORING,
            severity=SeverityLevel.CRITICAL,
            conditions={
                "monitor_events": ["failed_login", "privilege_escalation", "data_exfiltration"],
                "alert_threshold": 5,
                "time_window_minutes": 15,
                "notification_channels": ["email", "slack", "sms"]
            },
            framework="NIST",
            regulation_reference="DE.AE-1 - Anomalies and events are analyzed"
        )
        default_rules.append(security_monitoring_rule)
        
        return default_rules

    @staticmethod
    def get_severity_color(severity):
        """Get color representation for severity level (for UI display)"""
        color_map = {
            SeverityLevel.LOW: "#10b981",      # green
            SeverityLevel.MEDIUM: "#f59e0b",   # yellow  
            SeverityLevel.HIGH: "#ef4444",     # red
            SeverityLevel.CRITICAL: "#dc2626"  # dark red
        }
        return color_map.get(severity, "#6b7280")  # default gray

    @staticmethod
    def get_type_icon(rule_type):
        """Get icon representation for rule type (for UI display)"""
        icon_map = {
            RuleType.DATA_RETENTION: "fas fa-archive",
            RuleType.ACCESS_CONTROL: "fas fa-lock", 
            RuleType.AUDIT_LOGGING: "fas fa-file-alt",
            RuleType.ENCRYPTION: "fas fa-shield-alt",
            RuleType.BACKUP_POLICY: "fas fa-save",
            RuleType.SECURITY_POLICY: "fas fa-security",
            RuleType.PRIVACY_POLICY: "fas fa-user-shield",
            RuleType.MONITORING: "fas fa-eye",
            RuleType.CUSTOM: "fas fa-cog"
        }
        return icon_map.get(rule_type, "fas fa-cog")  # default cog icon