from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from app.services.base_service import BaseService

class ApprovalService(BaseService):
    """
    Service for managing approval workflows for AI agent actions.
    """
    
    def __init__(self):
        super().__init__("ApprovalService")
        self.pending_approvals = []
        self.approval_history = []
        self.approval_rules = {}
    
    def initialize(self) -> bool:
        """Initialize the approval service"""
        try:
            self.log_info("Initializing approval service")
            self._load_approval_rules()
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize approval service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return True
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.pending_approvals.clear()
        self.approval_history.clear()
        return True
    
    def request_approval(self, action: Dict[str, Any]) -> str:
        """
        Request approval for an action.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            approval_id: Unique identifier for the approval request
        """
        approval_id = f"approval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        approval_request = {
            "id": approval_id,
            "action": action,
            "status": "pending",
            "requested_at": datetime.utcnow().isoformat(),
            "requested_by": action.get("agent_id", "unknown"),
            "priority": self._calculate_priority(action),
            "auto_approve": self._should_auto_approve(action),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        if approval_request["auto_approve"]:
            approval_request["status"] = "approved"
            approval_request["approved_at"] = datetime.utcnow().isoformat()
            approval_request["approved_by"] = "system"
            self.approval_history.append(approval_request)
        else:
            self.pending_approvals.append(approval_request)
        
        self.log_info(f"Approval request {approval_id} created with status: {approval_request['status']}")
        return approval_id
    
    def approve_request(self, approval_id: str, approver: str, notes: str = "") -> bool:
        """
        Approve a pending request.
        
        Args:
            approval_id: ID of the approval request
            approver: Who is approving the request
            notes: Optional approval notes
            
        Returns:
            True if approved successfully, False otherwise
        """
        for i, request in enumerate(self.pending_approvals):
            if request["id"] == approval_id:
                request["status"] = "approved"
                request["approved_at"] = datetime.utcnow().isoformat()
                request["approved_by"] = approver
                request["notes"] = notes
                
                # Move to history
                self.approval_history.append(request)
                self.pending_approvals.pop(i)
                
                self.log_info(f"Approval request {approval_id} approved by {approver}")
                return True
        
        self.log_warning(f"Approval request {approval_id} not found")
        return False
    
    def reject_request(self, approval_id: str, rejector: str, reason: str) -> bool:
        """
        Reject a pending request.
        
        Args:
            approval_id: ID of the approval request
            rejector: Who is rejecting the request
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully, False otherwise
        """
        for i, request in enumerate(self.pending_approvals):
            if request["id"] == approval_id:
                request["status"] = "rejected"
                request["rejected_at"] = datetime.utcnow().isoformat()
                request["rejected_by"] = rejector
                request["rejection_reason"] = reason
                
                # Move to history
                self.approval_history.append(request)
                self.pending_approvals.pop(i)
                
                self.log_info(f"Approval request {approval_id} rejected by {rejector}")
                return True
        
        self.log_warning(f"Approval request {approval_id} not found")
        return False
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        # Remove expired requests
        current_time = datetime.utcnow()
        self.pending_approvals = [
            req for req in self.pending_approvals
            if datetime.fromisoformat(req["expires_at"]) > current_time
        ]
        
        return self.pending_approvals.copy()
    
    def get_approval_status(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific approval request"""
        # Check pending approvals
        for request in self.pending_approvals:
            if request["id"] == approval_id:
                return request
        
        # Check history
        for request in self.approval_history:
            if request["id"] == approval_id:
                return request
        
        return None
    
    def _calculate_priority(self, action: Dict[str, Any]) -> str:
        """Calculate priority for an approval request"""
        action_type = action.get("type", "").lower()
        
        if "critical" in action_type or "emergency" in action_type:
            return "high"
        elif "sensitive" in action_type or "financial" in action_type:
            return "medium"
        else:
            return "low"
    
    def _should_auto_approve(self, action: Dict[str, Any]) -> bool:
        """Determine if an action should be auto-approved"""
        action_type = action.get("type", "").lower()
        
        # Auto-approve low-risk actions
        auto_approve_types = [
            "read_only", "status_check", "health_check", 
            "log_entry", "metric_collection"
        ]
        
        return any(safe_type in action_type for safe_type in auto_approve_types)
    
    def _load_approval_rules(self):
        """Load approval rules configuration"""
        self.approval_rules = {
            "auto_approve_types": [
                "read_only", "status_check", "health_check",
                "log_entry", "metric_collection"
            ],
            "high_priority_types": [
                "critical", "emergency", "system_shutdown"
            ],
            "require_approval_types": [
                "file_modification", "system_configuration",
                "user_data_access", "external_api_call"
            ]
        }
    
    def get_approval_summary(self) -> Dict[str, Any]:
        """Get summary of approval system status"""
        pending_count = len(self.pending_approvals)
        
        # Count by priority
        priority_counts = {}
        for request in self.pending_approvals:
            priority = request["priority"]
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Recent history stats
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_history = [
            req for req in self.approval_history
            if datetime.fromisoformat(req.get("approved_at", req.get("rejected_at", "1970-01-01"))) > recent_cutoff
        ]
        
        approved_count = len([req for req in recent_history if req["status"] == "approved"])
        rejected_count = len([req for req in recent_history if req["status"] == "rejected"])
        
        return {
            "pending_approvals": pending_count,
            "priority_breakdown": priority_counts,
            "last_24h": {
                "approved": approved_count,
                "rejected": rejected_count,
                "total": len(recent_history)
            },
            "total_history": len(self.approval_history)
        }
