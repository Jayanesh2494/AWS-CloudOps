import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
import threading

class SessionStore:
    """Simple JSON-based session store for deployment state persistence"""

    def __init__(self, store_file: str = "sessions.json"):
        self.store_file = store_file
        self._lock = threading.Lock()
        self._ensure_store_exists()

    def _ensure_store_exists(self):
        """Create store file if it doesn't exist"""
        if not os.path.exists(self.store_file):
            with open(self.store_file, 'w') as f:
                json.dump({}, f, indent=2)

    def _load_store(self) -> Dict:
        """Load sessions from file"""
        try:
            with open(self.store_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_store(self, store: Dict):
        """Save sessions to file"""
        with self._lock:
            with open(self.store_file, 'w') as f:
                json.dump(store, f, indent=2)

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        store = self._load_store()
        store[session_id] = {
            "sessionId": session_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "accountMode": "our",
            "region": "us-east-1",
            "deployments": [],
            "lastActivity": datetime.now(timezone.utc).isoformat(),
            "conversationState": {
                "currentIntent": None,
                "selectedTemplate": None,
                "size": None,
                "readyToDeploy": False,
                "awaitingConfirmation": False,
                "pendingAction": None,
                "collectedParams": {},
                "lastIntent": None,
                "lastMessage": None
            }
        }
        self._save_store(store)
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        store = self._load_store()
        return store.get(session_id)

    def update_session(self, session_id: str, updates: Dict):
        """Update session data"""
        store = self._load_store()
        if session_id not in store:
            return False

        store[session_id].update(updates)
        store[session_id]["lastActivity"] = datetime.now(timezone.utc).isoformat()
        self._save_store(store)
        return True

    def add_deployment(self, session_id: str, deployment: Dict):
        """Add a deployment to session"""
        store = self._load_store()
        if session_id not in store:
            return False

        deployment["deploymentId"] = str(uuid.uuid4())
        deployment["createdAt"] = datetime.now(timezone.utc).isoformat()

        store[session_id]["deployments"].append(deployment)
        store[session_id]["lastDeploymentId"] = deployment["deploymentId"]
        self._save_store(store)
        return True

    def get_deployments(self, session_id: str) -> List[Dict]:
        """Get all deployments for session"""
        session = self.get_session(session_id)
        return session.get("deployments", []) if session else []

    def get_last_deployment(self, session_id: str) -> Optional[Dict]:
        """Get the most recent deployment"""
        deployments = self.get_deployments(session_id)
        return deployments[-1] if deployments else None

    def update_deployment(self, session_id: str, deployment_id: str, updates: Dict):
        """Update a specific deployment"""
        store = self._load_store()
        if session_id not in store:
            return False

        deployments = store[session_id].get("deployments", [])
        for deployment in deployments:
            if deployment.get("deploymentId") == deployment_id:
                deployment.update(updates)
                deployment["updatedAt"] = datetime.now(timezone.utc).isoformat()
                self._save_store(store)
                return True
        return False

    def delete_deployment(self, session_id: str, deployment_id: str):
        """Remove a deployment from session"""
        store = self._load_store()
        if session_id not in store:
            return False

        deployments = store[session_id].get("deployments", [])
        store[session_id]["deployments"] = [
            d for d in deployments if d.get("deploymentId") != deployment_id
        ]
        self._save_store(store)
        return True

    def get_conversation_state(self, session_id: str) -> Optional[Dict]:
        """Get conversation state for session"""
        session = self.get_session(session_id)
        return session.get("conversationState") if session else None

    def update_conversation_state(self, session_id: str, state_updates: Dict):
        """Update conversation state within session"""
        store = self._load_store()
        if session_id in store:
            store[session_id]["conversationState"].update(state_updates)
            store[session_id]["lastActivity"] = datetime.now(timezone.utc).isoformat()
            self._save_store(store)
            return True
        return False

    def reset_conversation_state(self, session_id: str):
        """Reset conversation state to initial values"""
        initial_state = {
            "currentIntent": None,
            "selectedTemplate": None,
            "size": None,
            "readyToDeploy": False,
            "awaitingConfirmation": False,
            "pendingAction": None,
            "collectedParams": {},
            "lastIntent": None,
            "lastMessage": None
        }
        return self.update_conversation_state(session_id, initial_state)

    def cleanup_old_sessions(self, days: int = 30):
        """Remove sessions older than specified days"""
        store = self._load_store()
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)

        to_remove = []
        for session_id, session_data in store.items():
            try:
                last_activity = datetime.fromisoformat(session_data.get("lastActivity", "")).timestamp()
                if last_activity < cutoff:
                    to_remove.append(session_id)
            except:
                # If we can't parse the date, consider it old
                to_remove.append(session_id)

        for session_id in to_remove:
            del store[session_id]

        if to_remove:
            self._save_store(store)
            print(f"Cleaned up {len(to_remove)} old sessions")

# Global session store instance
session_store = SessionStore()
