import sqlite3
import json
import threading
import uuid
import logging
import atexit
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from queue import Queue, Empty
from contextlib import contextmanager
from .models import ProcessStatus, DatabaseError

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages caching of process results"""
    
    _instance: Optional['CacheManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs) -> 'CacheManager':
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, cache_dir: Optional[Path] = None):
        if hasattr(self, 'initialized'):
            return
            
        self.cache_dir = cache_dir or Path.home() / '.augmenta' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / 'cache.db'
        self.write_queue: Queue = Queue()
        self.is_running = True
        
        self._init_db()
        self._start_writer_thread()
        atexit.register(self.cleanup)
        self.initialized = True
    
    def _init_db(self) -> None:
        """Initialize the database schema"""
        with self._get_connection() as conn:
            conn.executescript('''
                PRAGMA foreign_keys = ON;
                
                CREATE TABLE IF NOT EXISTS processes (
                    process_id TEXT PRIMARY KEY,
                    config_hash TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed')),
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
                
                CREATE INDEX IF NOT EXISTS idx_process_status 
                ON processes(status, last_updated);
            ''')
    
    @contextmanager
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with retry logic"""
        MAX_RETRIES = 3
        DB_TIMEOUT = 30.0
        
        for attempt in range(MAX_RETRIES):
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=DB_TIMEOUT,
                    isolation_level='IMMEDIATE'
                )
                conn.row_factory = sqlite3.Row
                yield conn
                conn.commit()
                break
            except sqlite3.OperationalError as e:
                if attempt == MAX_RETRIES - 1:
                    raise DatabaseError(f"Database connection failed: {e}")
                logger.warning(f"Database connection attempt {attempt + 1} failed, retrying...")
            finally:
                conn.close()
    
    def _start_writer_thread(self) -> None:
        """Start the background writer thread"""
        self.writer_thread = threading.Thread(
            target=self._process_write_queue,
            daemon=True,
            name="CacheWriterThread"
        )
        self.writer_thread.start()
    
    def _process_write_queue(self) -> None:
        """Process the write queue in a separate thread"""
        QUEUE_TIMEOUT = 1.0
        
        while self.is_running or not self.write_queue.empty():
            try:
                item = self.write_queue.get(timeout=QUEUE_TIMEOUT)
                with self._get_connection() as conn:
                    query, params = item
                    conn.execute(query, params)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing write queue: {e}")
    
    def start_process(self, config_hash: str, total_rows: int) -> str:
        """Start a new process and return its ID"""
        process_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        self.write_queue.put((
            """INSERT INTO processes 
               (process_id, config_hash, start_time, last_updated, status, total_rows)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (process_id, config_hash, current_time, current_time, 'running', total_rows)
        ))
        return process_id
    
    def cache_result(
        self,
        process_id: str,
        row_index: int,
        query: str,
        result: str
    ) -> None:
        """Cache a result for a specific row"""
        current_time = datetime.now()
        
        self.write_queue.put((
            """INSERT OR REPLACE INTO results_cache 
               (process_id, row_index, query, result, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (process_id, row_index, query, result, current_time)
        ))
        
        self.write_queue.put((
            """UPDATE processes 
               SET processed_rows = processed_rows + 1,
                   last_updated = ?
               WHERE process_id = ?""",
            (current_time, process_id)
        ))
    
    def get_cached_results(self, process_id: str) -> Dict[int, Any]:
        """Get all cached results for a process"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT row_index, result FROM results_cache WHERE process_id = ?",
                (process_id,)
            ).fetchall()
            return {row['row_index']: json.loads(row['result']) for row in rows}
    
    def get_process_status(self, process_id: str) -> Optional[ProcessStatus]:
        """Get the status of a process"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM processes WHERE process_id = ?",
                (process_id,)
            ).fetchone()
            
            if row:
                return ProcessStatus(**dict(row))
            return None
    
    def find_unfinished_process(self, config_hash: str) -> Optional[ProcessStatus]:
        """Find the most recent unfinished process for a config hash"""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM processes 
                WHERE config_hash = ? 
                AND status = 'running'
                ORDER BY last_updated DESC 
                LIMIT 1
            """, (config_hash,)).fetchone()
            
            if row:
                return ProcessStatus(**dict(row))
            return None
    
    def get_process_summary(self, process: ProcessStatus) -> str:
        """Get a human-readable summary of a process"""
        time_diff = datetime.now() - process.last_updated
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            time_ago = f"{time_diff.seconds // 3600} hours ago"
        else:
            time_ago = f"{time_diff.seconds // 60} minutes ago"
            
        return (
            f"Found unfinished process from {time_ago}\n"
            f"Progress: {process.processed_rows}/{process.total_rows} rows completed"
        )
    
    def cleanup_old_processes(self, days: int = 30) -> None:
        """Clean up processes older than specified days"""
        if days < 0:
            raise ValueError("days must be non-negative")
            
        cutoff = datetime.now() - timedelta(days=days)
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM processes WHERE last_updated < ?",
                (cutoff,)
            )
    
    def cleanup(self) -> None:
        """Cleanup method called on program exit"""
        self.is_running = False
        if hasattr(self, 'writer_thread'):
            try:
                self.writer_thread.join(timeout=5.0)
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")