"""
Application Configuration
Manages environment-based configuration and database backend switching
"""

import os
from typing import Literal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


DatabaseType = Literal["sqlite", "firebase"]


class Config:
    """Application configuration"""
    
    # Database Configuration
    DATABASE_TYPE: DatabaseType = os.getenv('DATABASE_TYPE', 'sqlite')
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS', './intellisynth-c1050-firebase-adminsdk-fbsvc-61edd8337e.json')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'intellisynth-c1050')
    FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN', 'intellisynth-c1050.firebaseapp.com')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET', 'intellisynth-c1050.firebasestorage.app')
    
    # Application Settings
    APP_NAME = os.getenv('APP_NAME', 'AI Flight Recorder')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    # Server Configuration
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', '8000'))
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    ALGORITHM = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    
    # CORS Settings
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')
    
    @classmethod
    def is_firebase(cls) -> bool:
        """Check if using Firebase backend"""
        return cls.DATABASE_TYPE.lower() == 'firebase'
    
    @classmethod
    def is_sqlite(cls) -> bool:
        """Check if using SQLite backend"""
        return cls.DATABASE_TYPE.lower() == 'sqlite'
    
    @classmethod
    def get_database_info(cls) -> dict:
        """Get database configuration info"""
        return {
            'type': cls.DATABASE_TYPE,
            'backend': 'Firebase Firestore' if cls.is_firebase() else 'SQLite',
            'project_id': cls.FIREBASE_PROJECT_ID if cls.is_firebase() else None,
            'local_db': 'logs.db' if cls.is_sqlite() else None
        }


# Singleton config instance
config = Config()


def get_agent_service():
    """
    Get the appropriate agent service based on configuration
    
    Returns:
        AgentService (SQLite) or AgentServiceFirestore (Firebase)
    """
    if config.is_firebase():
        from app.services.agent_service_firestore import agent_service_firestore
        return agent_service_firestore
    else:
        from app.services.agent_service import agent_service
        return agent_service


def get_activity_logger():
    """
    Get the appropriate activity logger based on configuration
    
    Returns:
        ActivityLogger (SQLite) or ActivityLoggerFirestore (Firebase)
    """
    if config.is_firebase():
        # Will implement Firestore version next
        try:
            from app.services.activity_logger_firestore import activity_logger_firestore
            return activity_logger_firestore
        except ImportError:
            # Fallback to SQLite if Firestore version not available yet
            from app.services.activity_logger import activity_logger
            return activity_logger
    else:
        from app.services.activity_logger import activity_logger
        return activity_logger
