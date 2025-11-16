"""
Firebase Configuration and Initialization
Manages Firebase Admin SDK setup and Firestore database connection
"""

import os
import json
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

class FirebaseConfig:
    """Firebase configuration and connection management"""
    
    def __init__(self):
        self._app = None
        self._db = None
        self._initialized = False
    
    def initialize(self, credentials_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase Admin SDK
        
        Args:
            credentials_path: Path to Firebase service account JSON file
                            If None, will look for FIREBASE_CREDENTIALS env var
                            or firebase-credentials.json in project root
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            print("Firebase already initialized")
            return True
        
        try:
            # Determine credentials path
            if credentials_path is None:
                # Check environment variable
                credentials_path = os.getenv('FIREBASE_CREDENTIALS')
                
                # Check for file in project root
                if credentials_path is None:
                    default_path = Path(__file__).parent.parent / 'firebase-credentials.json'
                    if default_path.exists():
                        credentials_path = str(default_path)
            
            # Initialize Firebase
            if credentials_path and os.path.exists(credentials_path):
                print(f"Initializing Firebase with credentials: {credentials_path}")
                cred = credentials.Certificate(credentials_path)
                self._app = firebase_admin.initialize_app(cred)
            else:
                print("Warning: No Firebase credentials found. Using default application credentials.")
                print("Note: This requires Google Cloud Application Default Credentials to be set up.")
                # Try to initialize without explicit credentials (uses ADC)
                self._app = firebase_admin.initialize_app()
            
            # Get Firestore database instance
            self._db = firestore.client()
            self._initialized = True
            
            print("✓ Firebase initialized successfully!")
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize Firebase: {e}")
            print("\nTo use Firebase:")
            print("1. Create a Firebase project at https://console.firebase.google.com")
            print("2. Generate a service account key (Project Settings > Service Accounts)")
            print("3. Save the JSON file as 'firebase-credentials.json' in the project root")
            print("   OR set the FIREBASE_CREDENTIALS environment variable to the file path")
            return False
    
    def get_db(self):
        """Get Firestore database instance"""
        if not self._initialized:
            raise Exception("Firebase not initialized. Call initialize() first.")
        return self._db
    
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized"""
        return self._initialized
    
    def close(self):
        """Close Firebase connection"""
        if self._app:
            try:
                firebase_admin.delete_app(self._app)
                self._initialized = False
                self._db = None
                self._app = None
                print("Firebase connection closed")
            except Exception as e:
                print(f"Error closing Firebase: {e}")


# Global Firebase instance
firebase_config = FirebaseConfig()


def get_firestore_db():
    """
    Get Firestore database instance
    Automatically initializes Firebase if not already done
    """
    if not firebase_config.is_initialized():
        firebase_config.initialize()
    return firebase_config.get_db()


# Collection names
class Collections:
    """Firestore collection names"""
    AGENTS = "agents"
    ACTIVITY_LOGS = "activity_logs"
    COMPLIANCE_RULES = "compliance_rules"
    COMPLIANCE_VIOLATIONS = "compliance_violations"
    USERS = "users"
    SESSIONS = "sessions"


# Helper functions for Firestore operations
def firestore_doc_to_dict(doc) -> dict:
    """Convert Firestore document to dictionary"""
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['id'] = doc.id
    return data


def firestore_docs_to_list(docs) -> list:
    """Convert Firestore documents to list of dictionaries"""
    return [firestore_doc_to_dict(doc) for doc in docs if doc.exists]
