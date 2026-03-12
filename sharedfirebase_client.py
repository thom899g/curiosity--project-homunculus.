"""
Firebase Firestore client wrapper with robust error handling and connection management.
This ensures all services share the same Firestore instance configuration.
"""
import os
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError
from google.cloud.firestore_v1.client import Client

# Initialize logger
logger = logging.getLogger(__name__)

class FirebaseClient:
    """Singleton Firestore client with automatic reconnection and error handling."""
    
    _instance: Optional[Client] = None
    _app = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or initialize Firestore client with exponential backoff retry."""
        if cls._instance is None:
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Check for credentials file
                    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                    if not cred_path or not os.path.exists(cred_path):
                        raise FileNotFoundError(
                            f"Firebase credentials not found at: {cred_path}"
                        )
                    
                    # Initialize Firebase app if not already done
                    if not firebase_admin._apps:
                        cred = credentials.Certificate(cred_path)
                        cls._app = firebase_admin.initialize_app(cred)
                        logger.info("Firebase app initialized successfully")
                    
                    # Get Firestore client
                    cls._instance = firestore.client()
                    
                    # Test connection
                    test_doc = cls._instance.collection('system_health').document('connection_test')
                    test_doc.set({'timestamp': datetime.utcnow().isoformat()}, merge=True)
                    
                    logger.info("Firestore client initialized and tested successfully")
                    return cls._instance
                    
                except FileNotFoundError as e:
                    logger.error(f"Credentials file error: {e}")
                    raise
                except FirebaseError as e:
                    logger.error(f"Firebase error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                    # Exponential backoff
                    time.sleep(2 ** attempt)
                except Exception as e:
                    logger.error(f"Unexpected error initializing Firebase: {e}")
                    raise
        
        return cls._instance
    
    @classmethod
    def write_memory(
        cls, 
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Write a memory to Firestore with standardized structure."""
        client = cls.get_client()
        
        try:
            doc_ref = client.collection('memories').document()
            
            memory_data = {
                'type': memory_type,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat(),
                'vectorized': False,  # Will be updated by memory service
                'consolidated': False
            }
            
            doc_ref.set(memory_data)
            logger.info(f"Memory written: {doc_ref.id}")
            return doc_ref.id
            
        except FirebaseError as e:
            logger.error(f"Failed to write memory: {e}")
            raise
    
    @classmethod
    def update_decision_metrics(
        cls,
        decision_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Update decision quality metrics in Firestore."""
        client = cls.get_client()
        
        try:
            doc_ref = client.collection('decisions').document(decision_id)
            
            update_data = {
                'metrics': metrics,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            doc_ref.set(update_data, merge=True)
            logger.debug(f"Decision metrics updated: {decision_id}")
            
        except FirebaseError as e:
            logger.error(f"Failed to update decision metrics: {e}")
            raise

# Convenience function for other modules
def get_firestore_client() -> Client:
    """Public interface to get Firestore client."""
    return FirebaseClient.get_client()