from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json
from io import StringIO
from app.services.base_service import BaseService

class ReportService(BaseService):
    """
    Service for generating various reports and analytics.
    """
    
    def __init__(self):
        super().__init__("ReportService")
        self.report_templates = {}
        self.generated_reports = []
        self._initialize_templates()
    
    def initialize(self) -> bool:
        """Initialize the report service"""
        try:
            self.log_info("Initializing report service")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize report service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return True
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.generated_reports.clear()
        return True
    
    def generate_report(self, report_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a report of the specified type.
        
        Args:
            report_type: Type of report to generate
            parameters: Report parameters
            
        Returns:
            Generated report data
        """
        if parameters is None:
            parameters = {}
        
        report_id = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            if report_type == "system_status":
                report_data = self._generate_system_status_report(parameters)
            elif report_type == "agent_activity":
                report_data = self._generate_agent_activity_report(parameters)
            elif report_type == "security_summary":
                report_data = self._generate_security_summary_report(parameters)
            elif report_type == "compliance_audit":
                report_data = self._generate_compliance_audit_report(parameters)
            elif report_type == "performance_metrics":
                report_data = self._generate_performance_metrics_report(parameters)
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            report = {
                "id": report_id,
                "type": report_type,
                "parameters": parameters,
                "data": report_data,
                "generated_at": datetime.utcnow().isoformat(),
                "generated_by": "system",
                "status": "completed"
            }
            
            self.generated_reports.append(report)
            self.log_info(f"Report {report_id} generated successfully")
            
            return report
            
        except Exception as e:
            self.log_error(f"Failed to generate report {report_id}: {e}")
            
            error_report = {
                "id": report_id,
                "type": report_type,
                "parameters": parameters,
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat(),
                "status": "failed"
            }
            
            self.generated_reports.append(error_report)
            return error_report
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific report by ID"""
        for report in self.generated_reports:
            if report["id"] == report_id:
                return report
        return None
    
    def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent reports"""
        return self.generated_reports[-limit:] if self.generated_reports else []
    
    def export_report(self, report_id: str, format: str = "json") -> str:
        """
        Export a report in the specified format.
        
        Args:
            report_id: ID of the report to export
            format: Export format (json, csv, text)
            
        Returns:
            Formatted report content
        """
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        if format.lower() == "json":
            return json.dumps(report, indent=2)
        elif format.lower() == "csv":
            return self._export_to_csv(report)
        elif format.lower() == "text":
            return self._export_to_text(report)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _generate_system_status_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system status report"""
        return {
            "summary": {
                "report_type": "System Status Report",
                "generated_at": datetime.utcnow().isoformat(),
                "time_period": parameters.get("time_period", "current")
            },
            "system_health": {
                "overall_status": "healthy",
                "uptime": "99.9%",
                "active_services": 8,
                "failed_services": 0
            },
            "resource_usage": {
                "cpu_usage": "45.2%",
                "memory_usage": "68.5%",
                "disk_usage": "34.1%",
                "network_io": "1024.5 KB/s"
            },
            "alerts": {
                "total": 3,
                "critical": 0,
                "warnings": 2,
                "info": 1
            }
        }
    
    def _generate_agent_activity_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent activity report"""
        return {
            "summary": {
                "report_type": "Agent Activity Report",
                "generated_at": datetime.utcnow().isoformat(),
                "time_period": parameters.get("time_period", "24h")
            },
            "agent_stats": {
                "total_agents": 11,
                "active_agents": 8,
                "idle_agents": 2,
                "offline_agents": 1
            },
            "activity_metrics": {
                "total_tasks": 1847,
                "completed_tasks": 1845,
                "failed_tasks": 2,
                "success_rate": "99.9%"
            },
            "top_performing_agents": [
                {"id": "agent_001", "name": "Data Collection Agent", "tasks_completed": 450},
                {"id": "agent_002", "name": "Monitoring Agent", "tasks_completed": 387},
                {"id": "agent_004", "name": "Security Agent", "tasks_completed": 298}
            ]
        }
    
    def _generate_security_summary_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security summary report"""
        return {
            "summary": {
                "report_type": "Security Summary Report",
                "generated_at": datetime.utcnow().isoformat(),
                "time_period": parameters.get("time_period", "24h")
            },
            "security_events": {
                "total_events": 15,
                "high_severity": 2,
                "medium_severity": 8,
                "low_severity": 5
            },
            "threat_detection": {
                "threats_detected": 3,
                "threats_blocked": 2,
                "false_positives": 1
            },
            "access_control": {
                "blocked_ips": 5,
                "failed_logins": 12,
                "successful_logins": 847
            }
        }
    
    def _generate_compliance_audit_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance audit report"""
        return {
            "summary": {
                "report_type": "Compliance Audit Report",
                "generated_at": datetime.utcnow().isoformat(),
                "time_period": parameters.get("time_period", "30d")
            },
            "compliance_status": {
                "overall_score": "92%",
                "passed_checks": 187,
                "failed_checks": 15,
                "pending_reviews": 3
            },
            "policy_violations": {
                "total_violations": 8,
                "critical": 1,
                "major": 3,
                "minor": 4
            },
            "remediation_status": {
                "resolved": 5,
                "in_progress": 2,
                "pending": 1
            }
        }
    
    def _generate_performance_metrics_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance metrics report"""
        return {
            "summary": {
                "report_type": "Performance Metrics Report",
                "generated_at": datetime.utcnow().isoformat(),
                "time_period": parameters.get("time_period", "24h")
            },
            "response_times": {
                "avg_response_time": "145.3ms",
                "min_response_time": "23ms",
                "max_response_time": "2.1s",
                "95th_percentile": "298ms"
            },
            "throughput": {
                "requests_per_second": 127.5,
                "peak_rps": 256,
                "total_requests": 11_025_600
            },
            "error_rates": {
                "overall_error_rate": "0.02%",
                "4xx_errors": 156,
                "5xx_errors": 23,
                "timeout_errors": 8
            }
        }
    
    def _export_to_csv(self, report: Dict[str, Any]) -> str:
        """Export report to CSV format"""
        output = StringIO()
        
        # Write header
        output.write("Report Type,Generated At,Status\n")
        output.write(f"{report['type']},{report['generated_at']},{report['status']}\n\n")
        
        # Write data (simplified)
        if "data" in report:
            output.write("Section,Key,Value\n")
            self._write_dict_to_csv(report["data"], output)
        
        return output.getvalue()
    
    def _write_dict_to_csv(self, data: Dict[str, Any], output: StringIO, prefix: str = ""):
        """Helper to write nested dict to CSV"""
        for key, value in data.items():
            if isinstance(value, dict):
                self._write_dict_to_csv(value, output, f"{prefix}.{key}" if prefix else key)
            else:
                output.write(f"{prefix},{key},{value}\n")
    
    def _export_to_text(self, report: Dict[str, Any]) -> str:
        """Export report to text format"""
        output = StringIO()
        
        output.write(f"Report Type: {report['type']}\n")
        output.write(f"Generated: {report['generated_at']}\n")
        output.write(f"Status: {report['status']}\n")
        output.write("=" * 50 + "\n\n")
        
        if "data" in report:
            self._write_dict_to_text(report["data"], output)
        
        return output.getvalue()
    
    def _write_dict_to_text(self, data: Dict[str, Any], output: StringIO, indent: int = 0):
        """Helper to write nested dict to text"""
        for key, value in data.items():
            if isinstance(value, dict):
                output.write("  " * indent + f"{key}:\n")
                self._write_dict_to_text(value, output, indent + 1)
            else:
                output.write("  " * indent + f"{key}: {value}\n")
    
    def _initialize_templates(self):
        """Initialize report templates"""
        self.report_templates = {
            "system_status": "System Status Report Template",
            "agent_activity": "Agent Activity Report Template",
            "security_summary": "Security Summary Report Template",
            "compliance_audit": "Compliance Audit Report Template",
            "performance_metrics": "Performance Metrics Report Template"
        }
    
    def get_available_report_types(self) -> List[str]:
        """Get list of available report types"""
        return list(self.report_templates.keys())
    
    def get_report_summary(self) -> Dict[str, Any]:
        """Get summary of report service status"""
        recent_reports = [r for r in self.generated_reports 
                         if datetime.fromisoformat(r["generated_at"]) > 
                         datetime.utcnow() - timedelta(hours=24)]
        
        successful_reports = len([r for r in recent_reports if r["status"] == "completed"])
        failed_reports = len([r for r in recent_reports if r["status"] == "failed"])
        
        return {
            "total_reports": len(self.generated_reports),
            "reports_24h": len(recent_reports),
            "successful_24h": successful_reports,
            "failed_24h": failed_reports,
            "available_types": len(self.report_templates),
            "last_generated": self.generated_reports[-1]["generated_at"] if self.generated_reports else None
        }
