"""
Memory Consolidation Service
Core component for ingesting, vectorizing, and synthesizing memories.
Features autonomous knowledge gap detection and self-directed research scheduling.
"""
import os
import sys
import json
import logging
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

import nats
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np

# Add shared directory to path
sys.path.append(str(Path(__file__).parent.parent / 'shared'))
from firebase_client import FirebaseClient, get_firestore_client
from events import EventType, create_event, BaseEvent

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryConsolidationService:
    """Main service class for memory consolidation."""
    
    def __init__(self):
        """Initialize the service with all required components."""
        # Configuration
        self.nats_url = os.getenv('NATS_URL', 'nats://localhost:4222')
        self.local_db_path = Path('/app/data/memories.db')
        self.local_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._init_sqlite()
        self._init_chromadb()
        self._init_model()
        
        # State
        self.is_running = False
        self.nats_client = None
        self.nats_js = None
        
        logger.info("Memory Consolidation Service initialized")
    
    def _init_sqlite(self) -> None:
        """Initialize local SQLite database for performance."""
        try:
            self.local_conn = sqlite3.connect(self.local_db_path)
            self.local_cursor = self.local_conn.cursor()
            
            # Create tables if they don't exist
            self.local_cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp DATETIME,
                    vectorized BO