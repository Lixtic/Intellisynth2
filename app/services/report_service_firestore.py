"""
Report Service - Firestore Implementation

Handles storage and retrieval of generated reports in Firebase Firestore.
Supports report persistence, history tracking, and querying.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from google.cloud import firestore
from app.firebase_config import firebase_config, Collections


class ReportServiceFirestore:
    """
    Service for managing reports in Firestore.
    
    Features:
    - Store generated reports
    - Retrieve report history
    - Query reports by type, time period, status
    - Track report metadata (generation time, size, etc.)
    """
    
    def __init__(self):
        """Initialize the report service with Firestore client"""
        self.db = None
        self.collection = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of Firestore connection"""
        if self._initialized:
            return
        
        # Ensure Firebase is initialized
        if not firebase_config.is_initialized():
            firebase_config.initialize()
        
        self.db = firebase_config.get_db()
        self.collection = self.db.collection(Collections.REPORTS)
        self._initialized = True
    
    async def create_report(
        self,
        report_type: str,
        time_period: str,
        data: Dict[str, Any],
        status: str = "completed"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new report in Firestore.
        
        Args:
            report_type: Type of report (agent_activity, security_summary, etc.)
            time_period: Time period covered (1h, 24h, 7d, 30d)
            data: Report data/results
            status: Report status (completed, failed, pending)
        
        Returns:
            Created report with ID and metadata
        """
        self._ensure_initialized()
        
        try:
            # Generate unique report ID
            timestamp = int(datetime.utcnow().timestamp())
            report_id = f"report-{timestamp}"
            
            # Create report document
            report_doc = {
                "id": report_id,
                "type": report_type,
                "time_period": time_period,
                "status": status,
                "data": data,
                "generated_at": datetime.utcnow(),
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "metadata": {
                    "data_size": len(str(data)),
                    "record_count": self._count_records(data),
                    "generator": "ai_flight_recorder"
                }
            }
            
            # Store in Firestore
            self.collection.document(report_id).set(report_doc)
            
            print(f"✓ Report created: {report_id} (type: {report_type})")
            
            return {
                "id": report_id,
                "type": report_type,
                "time_period": time_period,
                "status": status,
                "generated_at": report_doc["generated_at"].isoformat(),
                "data": data
            }
            
        except Exception as e:
            print(f"✗ Error creating report: {str(e)}")
            return None
    
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific report by ID.
        
        Args:
            report_id: Unique report identifier
        
        Returns:
            Report document or None if not found
        """
        self._ensure_initialized()
        
        try:
            doc = self.collection.document(report_id).get()
            
            if not doc.exists:
                return None
            
            report = doc.to_dict()
            
            # Convert timestamp to ISO string
            if "generated_at" in report and hasattr(report["generated_at"], "isoformat"):
                report["generated_at"] = report["generated_at"].isoformat()
            
            return report
            
        except Exception as e:
            print(f"✗ Error retrieving report {report_id}: {str(e)}")
            return None
    
    async def list_reports(
        self,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List reports with optional filtering.
        
        Args:
            report_type: Filter by report type
            status: Filter by status (completed, failed)
            limit: Maximum number of reports to return
            offset: Number of reports to skip
        
        Returns:
            List of report documents
        """
        self._ensure_initialized()
        
        try:
            query = self.collection
            
            # Apply filters
            if report_type:
                query = query.where("type", "==", report_type)
            
            if status:
                query = query.where("status", "==", status)
            
            # Order by generation time (newest first)
            query = query.order_by("generated_at", direction=firestore.Query.DESCENDING)
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            docs = query.stream()
            
            reports = []
            for doc in docs:
                report = doc.to_dict()
                
                # Convert timestamp
                if "generated_at" in report and hasattr(report["generated_at"], "isoformat"):
                    report["generated_at"] = report["generated_at"].isoformat()
                
                reports.append(report)
            
            return reports
            
        except Exception as e:
            print(f"✗ Error listing reports: {str(e)}")
            return []
    
    async def get_reports_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all reports.
        
        Returns:
            Summary with counts and statistics
        """
        self._ensure_initialized()
        
        try:
            # Get all reports
            all_docs = list(self.collection.stream())
            total_reports = len(all_docs)
            
            # Count reports in last 24 hours
            day_ago = datetime.utcnow() - timedelta(hours=24)
            reports_24h = 0
            successful_24h = 0
            
            for doc in all_docs:
                report = doc.to_dict()
                generated_at = report.get("generated_at")
                
                # Handle both datetime objects and timestamps
                if generated_at:
                    # Firestore timestamps are datetime objects, just remove timezone info for comparison
                    if hasattr(generated_at, 'replace'):
                        try:
                            generated_at = generated_at.replace(tzinfo=None)
                        except:
                            pass
                    
                    if generated_at > day_ago:
                        reports_24h += 1
                        if report.get("status") == "completed":
                            successful_24h += 1
            
            # Count available types
            types = set()
            for doc in all_docs:
                report = doc.to_dict()
                if "type" in report:
                    types.add(report["type"])
            
            return {
                "total_reports": total_reports,
                "reports_24h": reports_24h,
                "successful_24h": successful_24h,
                "available_types": len(types),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"✗ Error getting reports summary: {str(e)}")
            return {
                "total_reports": 0,
                "reports_24h": 0,
                "successful_24h": 0,
                "available_types": 5,
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def delete_report(self, report_id: str) -> bool:
        """
        Delete a report from Firestore.
        
        Args:
            report_id: Unique report identifier
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.collection.document(report_id).delete()
            print(f"✓ Report deleted: {report_id}")
            return True
            
        except Exception as e:
            print(f"✗ Error deleting report {report_id}: {str(e)}")
            return False
    
    async def delete_old_reports(self, days: int = 30) -> int:
        """
        Delete reports older than specified number of days.
        
        Args:
            days: Number of days to keep reports
        
        Returns:
            Number of reports deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Query old reports
            old_reports = self.collection.where(
                "generated_at", "<", cutoff_date
            ).stream()
            
            deleted_count = 0
            for doc in old_reports:
                doc.reference.delete()
                deleted_count += 1
            
            print(f"✓ Deleted {deleted_count} reports older than {days} days")
            return deleted_count
            
        except Exception as e:
            print(f"✗ Error deleting old reports: {str(e)}")
            return 0
    
    def _count_records(self, data: Dict[str, Any]) -> int:
        """
        Count the number of records in report data.
        
        Args:
            data: Report data dictionary
        
        Returns:
            Approximate record count
        """
        count = 0
        
        # Count based on common data structures
        if "total_activities" in data:
            count = data["total_activities"]
        elif "total_operations" in data:
            count = data["total_operations"]
        elif "total_checks" in data:
            count = data["total_checks"]
        elif "total_security_events" in data:
            count = data["total_security_events"]
        elif "anomalies_detected" in data:
            count = data["anomalies_detected"]
        
        return count


# Create singleton instance
report_service_firestore = ReportServiceFirestore()
