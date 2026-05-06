"""
Deployment Manager - tracks and manages AWS deployments
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
import threading

class DeploymentManager:
    """Manages deployment lifecycle tracking"""

    def __init__(self, db_file: str = "deployments.json"):
        self.db_file = db_file
        self._lock = threading.Lock()
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Create DB file if it doesn't exist"""
        if not os.path.exists(self.db_file):
            with open(self.db_file, 'w') as f:
                json.dump({"deployments": []}, f, indent=2)

    def _load_db(self) -> Dict:
        """Load deployments database"""
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"deployments": []}

    def _save_db(self, db: Dict):
        """Save deployments database"""
        with self._lock:
            with open(self.db_file, 'w') as f:
                json.dump(db, f, indent=2)

    def create_deployment(self, template_id: str, deployment_name: str, params: Dict, 
                         account_mode: str, region: str = "us-east-1",
                         session_id: str = None, account_id: str = None) -> str:
        """Create new deployment record"""
        deployment_id = str(uuid.uuid4())
        db = self._load_db()
        
        deployment = {
            "deployment_id": deployment_id,
            "deployment_name": deployment_name,
            "session_id": session_id,
            "template_id": template_id,
            "stack_name": f"cloudops-{template_id}-{deployment_id[:8]}",
            "region": region,
            "account_mode": account_mode,
            "account_id": account_id,
            "params": params,
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "outputs": {},
            "error": None
        }
        
        db["deployments"].append(deployment)
        self._save_db(db)
        return deployment_id

    def update_deployment(self, deployment_id: str, updates: Dict):
        """Update deployment record"""
        db = self._load_db()
        
        for dep in db["deployments"]:
            if dep["deployment_id"] == deployment_id:
                dep.update(updates)
                dep["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save_db(db)
                return True
        return False

    def get_deployment(self, deployment_id: str) -> Optional[Dict]:
        """Get deployment by ID"""
        db = self._load_db()
        for dep in db["deployments"]:
            if dep["deployment_id"] == deployment_id:
                return dep
        return None

    def list_deployments(self, account_mode: str = None, 
                        account_id: str = None, status: str = None) -> List[Dict]:
        """List deployments with optional filters"""
        db = self._load_db()
        deployments = db.get("deployments", [])
        
        # Filter
        if account_mode:
            deployments = [d for d in deployments if d.get("account_mode") == account_mode]
        if account_id:
            deployments = [d for d in deployments if d.get("account_id") == account_id]
        if status:
            deployments = [d for d in deployments if d.get("status") == status]
        
        # Sort by created_at descending
        deployments.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return deployments

    def delete_deployment(self, deployment_id: str):
        """Delete deployment record"""
        db = self._load_db()
        db["deployments"] = [d for d in db["deployments"] 
                            if d["deployment_id"] != deployment_id]
        self._save_db(db)

    def get_active_deployments(self) -> List[Dict]:
        """Get all active/running deployments"""
        return self.list_deployments(status="ACTIVE")

    def get_deployment_by_name(self, deployment_name: str, session_id: str = None) -> Optional[Dict]:
        """Get deployment by name"""
        db = self._load_db()
        for deployment in db["deployments"]:
            if deployment.get("deployment_name") == deployment_name:
                if session_id and deployment.get("session_id") != session_id:
                    continue
                return deployment
        return None

    def list_deployments(self) -> List[Dict]:
        """List all deployments"""
        db = self._load_db()
        return db["deployments"]

    def mark_terminated(self, deployment_id: str):
        """Mark deployment as terminated"""
        self.update_deployment(deployment_id, {
            "status": "TERMINATED",
            "terminated_at": datetime.now(timezone.utc).isoformat()
        })

    def mark_deployed(self, deployment_id: str, api_url: str = None, outputs: dict = None):
        """Mark deployment as successfully deployed"""
        updates = {
            "status": "ACTIVE",
            "deployed_at": datetime.now(timezone.utc).isoformat()
        }
        if api_url:
            updates["api_url"] = api_url
        if outputs:
            updates["outputs"] = outputs
        self.update_deployment(deployment_id, updates)

    def mark_terminated(self, deployment_id: str):
        """Mark deployment as terminated"""
        self.update_deployment(deployment_id, {
            "status": "TERMINATED",
            "terminated_at": datetime.now(timezone.utc).isoformat()
        })


# Global instance
deployment_manager = DeploymentManager()

