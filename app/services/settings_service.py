from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from app.services.base_service import BaseService

class SettingsService(BaseService):
    """
    Service for managing application settings and configuration.
    """
    
    def __init__(self):
        super().__init__("SettingsService")
        self.settings = {}
        self.settings_history = []
        self._initialize_default_settings()
    
    def initialize(self) -> bool:
        """Initialize the settings service"""
        try:
            self.log_info("Initializing settings service")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize settings service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return len(self.settings) > 0
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.settings_history.clear()
        return True
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key (supports dot notation for nested settings)
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_setting(self, key: str, value: Any, user: str = "system") -> bool:
        """
        Set a setting value.
        
        Args:
            key: Setting key (supports dot notation for nested settings)
            value: New value
            user: User making the change
            
        Returns:
            True if setting was updated successfully
        """
        try:
            # Store old value for history
            old_value = self.get_setting(key)
            
            # Update setting
            keys = key.split('.')
            setting_dict = self.settings
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in setting_dict:
                    setting_dict[k] = {}
                setting_dict = setting_dict[k]
            
            # Set the value
            setting_dict[keys[-1]] = value
            
            # Record change in history
            change_record = {
                "key": key,
                "old_value": old_value,
                "new_value": value,
                "changed_by": user,
                "changed_at": datetime.utcnow().isoformat()
            }
            self.settings_history.append(change_record)
            
            self.log_info(f"Setting {key} updated by {user}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to set setting {key}: {e}")
            return False
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.copy()
    
    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a specific category"""
        return self.settings.get(category, {}).copy()
    
    def reset_setting(self, key: str, user: str = "system") -> bool:
        """
        Reset a setting to its default value.
        
        Args:
            key: Setting key to reset
            user: User making the change
            
        Returns:
            True if reset successful
        """
        default_value = self._get_default_value(key)
        if default_value is not None:
            return self.set_setting(key, default_value, user)
        return False
    
    def get_settings_history(self, key: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get settings change history.
        
        Args:
            key: Optional key to filter history
            limit: Maximum number of records to return
            
        Returns:
            List of change records
        """
        history = self.settings_history
        
        if key:
            history = [record for record in history if record["key"] == key]
        
        return history[-limit:] if history else []
    
    def export_settings(self, format: str = "json") -> str:
        """
        Export settings in the specified format.
        
        Args:
            format: Export format (json, text)
            
        Returns:
            Formatted settings data
        """
        if format.lower() == "json":
            return json.dumps(self.settings, indent=2)
        elif format.lower() == "text":
            return self._export_settings_to_text()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_settings(self, settings_data: str, format: str = "json", user: str = "system") -> bool:
        """
        Import settings from formatted data.
        
        Args:
            settings_data: Formatted settings data
            format: Data format (json)
            user: User performing the import
            
        Returns:
            True if import successful
        """
        try:
            if format.lower() == "json":
                new_settings = json.loads(settings_data)
                
                # Update each setting individually to maintain history
                for key, value in self._flatten_dict(new_settings).items():
                    self.set_setting(key, value, user)
                
                self.log_info(f"Settings imported successfully by {user}")
                return True
            else:
                raise ValueError(f"Unsupported import format: {format}")
                
        except Exception as e:
            self.log_error(f"Failed to import settings: {e}")
            return False
    
    def validate_setting(self, key: str, value: Any) -> Dict[str, Any]:
        """
        Validate a setting value.
        
        Args:
            key: Setting key
            value: Value to validate
            
        Returns:
            Validation result
        """
        # Basic validation rules
        validation_rules = {
            "monitoring.alert_threshold": {"type": (int, float), "min": 0, "max": 100},
            "security.max_failed_logins": {"type": int, "min": 1, "max": 10},
            "system.log_level": {"type": str, "choices": ["DEBUG", "INFO", "WARNING", "ERROR"]},
            "agents.max_concurrent": {"type": int, "min": 1, "max": 100}
        }
        
        if key not in validation_rules:
            return {"valid": True, "message": "No validation rules defined"}
        
        rule = validation_rules[key]
        
        # Type check
        if "type" in rule and not isinstance(value, rule["type"]):
            return {"valid": False, "message": f"Expected type {rule['type']}, got {type(value)}"}
        
        # Range check for numbers
        if isinstance(value, (int, float)):
            if "min" in rule and value < rule["min"]:
                return {"valid": False, "message": f"Value must be >= {rule['min']}"}
            if "max" in rule and value > rule["max"]:
                return {"valid": False, "message": f"Value must be <= {rule['max']}"}
        
        # Choice check for strings
        if "choices" in rule and value not in rule["choices"]:
            return {"valid": False, "message": f"Value must be one of: {rule['choices']}"}
        
        return {"valid": True, "message": "Valid"}
    
    def _initialize_default_settings(self):
        """Initialize default application settings"""
        self.settings = {
            "system": {
                "app_name": "AI Flight Recorder",
                "version": "1.0.0",
                "debug_mode": False,
                "log_level": "INFO",
                "timezone": "UTC"
            },
            "monitoring": {
                "enabled": True,
                "collection_interval": 60,
                "alert_threshold": 80,
                "retention_days": 30
            },
            "security": {
                "enable_auth": True,
                "session_timeout": 1440,  # minutes
                "max_failed_logins": 5,
                "ip_blocking_enabled": True
            },
            "agents": {
                "max_concurrent": 50,
                "heartbeat_interval": 30,
                "auto_restart": True,
                "log_agent_activity": True
            },
            "compliance": {
                "enabled": True,
                "strict_mode": False,
                "audit_retention": 90,  # days
                "notification_email": "admin@example.com"
            },
            "reporting": {
                "enabled": True,
                "auto_generate": True,
                "schedule": "daily",
                "export_format": "json"
            }
        }
    
    def _get_default_value(self, key: str) -> Any:
        """Get default value for a setting key"""
        # This would typically load from a defaults configuration file
        default_settings = self.settings.copy()
        return self.get_setting(key)  # Simplified - in real implementation, load from defaults
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """Flatten nested dictionary for easier processing"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _export_settings_to_text(self) -> str:
        """Export settings to text format"""
        lines = ["AI Flight Recorder Settings", "=" * 30, ""]
        
        def write_section(data: Dict[str, Any], indent: int = 0):
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append("  " * indent + f"{key}:")
                    write_section(value, indent + 1)
                else:
                    lines.append("  " * indent + f"{key}: {value}")
        
        write_section(self.settings)
        return "\n".join(lines)
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """Get summary of settings service status"""
        return {
            "total_settings": len(self._flatten_dict(self.settings)),
            "categories": list(self.settings.keys()),
            "last_changed": self.settings_history[-1]["changed_at"] if self.settings_history else None,
            "total_changes": len(self.settings_history),
            "recent_changes": len([
                h for h in self.settings_history
                if datetime.fromisoformat(h["changed_at"]) > 
                datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ])
        }
