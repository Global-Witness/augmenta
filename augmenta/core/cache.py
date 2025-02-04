import sqlite3
import json
import threading
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
from queue import Queue, Empty
import atexit


class CacheManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, cache_dir: Optional[str] = None):
        if not hasattr(self, 'initialized'):
            self.cache_dir = Path(cache_dir or Path.home() / '.augmenta' / 'cache')
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = self.cache_dir / 'cache.db'
            self.write_queue = Queue()
            self.is_running = True
            
            # Initialize database
            self._init_db()
            
            # Start writer thread
            self.writer_thread = threading.Thread(target=self._process_write_queue, daemon=True)
            self.writer_thread.start()
            
            # Register cleanup on exit
            atexit.register(self.cleanup)
            
            self.initialized = True
    
    def _init_db(self):
        """Initialize SQLite database with required tables"""
        with self._get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS processes (
                    process_id TEXT PRIMARY KEY,
                    config_hash TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    total_rows INTEGER NOT NULL,
                    processed_rows INTEGER NOT NULL DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS results_cache (
                    process_id TEXT NOT NULL,
                    row_index INTEGER NOT NULL,
                    query TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (process_id, row_index),
                    FOREIGN KEY (process_id) REFERENCES processes(process_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_process_status 
                ON processes(status, last_updated);
            ''')
    
    @contextmanager
    def _get_connection(self):
        """Thread-safe database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _process_write_queue(self):
        """Process the write queue in a separate thread"""
        while self.is_running or not self.write_queue.empty():
            try:
                item = self.write_queue.get(timeout=1.0)
                with self._get_connection() as conn:
                    query, params = item
                    conn.execute(query, params)
            except Empty:
                continue
            except Exception as e:
                print(f"Error processing write queue: {e}")
    
    def start_process(self, config_hash: str, total_rows: int) -> str:
        """Start a new process and return its ID"""
        process_id = str(uuid.uuid4())
        self.write_queue.put((
            """INSERT INTO processes 
               (process_id, config_hash, start_time, last_updated, status, total_rows)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (process_id, config_hash, datetime.now(), datetime.now(), 'running', total_rows)
        ))
        return process_id
    
    def cache_result(self, process_id: str, row_index: int, query: str, result: str):
        """Cache a result for a specific row"""
        self.write_queue.put((
            """INSERT OR REPLACE INTO results_cache 
               (process_id, row_index, query, result, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (process_id, row_index, query, result, datetime.now())
        ))
        
        self.write_queue.put((
            """UPDATE processes 
               SET processed_rows = processed_rows + 1,
                   last_updated = ?
               WHERE process_id = ?""",
            (datetime.now(), process_id)
        ))
    
    def get_cached_results(self, process_id: str) -> Dict[int, Any]:
        """Get all cached results for a process"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT row_index, result FROM results_cache WHERE process_id = ?",
                (process_id,)
            ).fetchall()
            return {row['row_index']: json.loads(row['result']) for row in rows}
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """Get the status of a process"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM processes WHERE process_id = ?",
                (process_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def cleanup_old_processes(self, days: int = 7):
        """Clean up processes older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        with self._get_connection() as conn:
            # Get old processes
            old_processes = conn.execute(
                "SELECT process_id FROM processes WHERE last_updated < ?",
                (cutoff,)
            ).fetchall()
            
            # Delete their cached results
            conn.executemany(
                "DELETE FROM results_cache WHERE process_id = ?",
                [(p['process_id'],) for p in old_processes]
            )
            
            # Delete the processes
            conn.execute(
                "DELETE FROM processes WHERE last_updated < ?",
                (cutoff,)
            )
    
    def cleanup(self):
        """Cleanup method called on program exit"""
        self.is_running = False
        if hasattr(self, 'writer_thread'):
            self.writer_thread.join(timeout=5.0)