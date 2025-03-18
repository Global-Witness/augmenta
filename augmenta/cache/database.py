"""Database operations for the cache system."""

import sqlite3
from contextlib import contextmanager
from typing import Generator
from pathlib import Path
from datetime import datetime

from augmenta.utils.exceptions import DatabaseError

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Handles database connections and schema management."""
    
    SCHEMA = '''
        PRAGMA foreign_keys = ON;
        PRAGMA journal_mode = WAL;
        
        CREATE TABLE IF NOT EXISTS processes (
            process_id TEXT PRIMARY KEY,
            config_hash TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            last_updated TIMESTAMP NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('running', 'completed')),
            total_rows INTEGER NOT NULL CHECK(total_rows >= 0),
            processed_rows INTEGER NOT NULL DEFAULT 0 CHECK(processed_rows >= 0)
        );
        
        CREATE TABLE IF NOT EXISTS results_cache (
            process_id TEXT NOT NULL,
            row_index INTEGER NOT NULL CHECK(row_index >= 0),
            query TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            PRIMARY KEY (process_id, row_index),
            FOREIGN KEY (process_id) REFERENCES processes(process_id)
                ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_process_status ON processes(status, last_updated);
        CREATE INDEX IF NOT EXISTS idx_config_hash ON processes(config_hash, last_updated);
    '''
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(self.SCHEMA)
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with retry logic."""
        MAX_RETRIES = 3
        DB_TIMEOUT = 30.0
        
        for attempt in range(MAX_RETRIES):
            conn = None
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=DB_TIMEOUT,
                    isolation_level='IMMEDIATE',
                    detect_types=sqlite3.PARSE_DECLTYPES
                )
                conn.row_factory = sqlite3.Row
                yield conn
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if attempt == MAX_RETRIES - 1:
                    raise DatabaseError(f"Database connection failed: {e}")
                logger.warning(f"Database connection attempt {attempt + 1} failed, retrying...")
            finally:
                if conn:
                    conn.close()

    def row_to_dict(self, row: sqlite3.Row) -> dict:
        """Convert SQLite row to dictionary with proper type conversion."""
        if not row:
            return None
            
        result = dict(row)
        for field in ['start_time', 'last_updated', 'created_at']:
            if field in result and isinstance(result[field], str):
                result[field] = datetime.fromisoformat(result[field])
        return result