"""Thread-safe singleton manager for caching process results."""

import json
import threading
import uuid
import logging
import atexit
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from queue import Queue, Empty

from .models import ProcessStatus
from .database import DatabaseConnection
from augmenta.utils.validators import validate_string, validate_int

logger = logging.getLogger(__name__)

class CacheManager:
    """Thread-safe singleton manager for caching process results."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs) -> 'CacheManager':
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        with self._lock:
            if hasattr(self, 'initialized'):
                return
                
            self.cache_dir = cache_dir or Path(os.getcwd()) / '.augmenta' / 'cache'
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = self.cache_dir / 'cache.db'
            
            self.write_queue = Queue()
            self.is_running = True
            
            self.db = DatabaseConnection(self.db_path)
            self._start_writer_thread()
            atexit.register(self.cleanup)
            self.initialized = True
    
    def _start_writer_thread(self) -> None:
        self.writer_thread = threading.Thread(
            target=self._process_write_queue,
            daemon=True,
            name="CacheWriterThread"
        )
        self.writer_thread.start()
    
    def _process_write_queue(self) -> None:
        """Process database write operations asynchronously."""
        BATCH_SIZE = 100
        batch = []
        
        while self.is_running or not self.write_queue.empty():
            try:
                try:
                    while len(batch) < BATCH_SIZE:
                        item = self.write_queue.get(timeout=1.0)
                        batch.append(item)
                except Empty:
                    pass
                
                if batch:
                    with self.db.get_connection() as conn:
                        for query, params in batch:
                            conn.execute(query, params)
                    batch.clear()
                    
            except Exception as e:
                logger.error(f"Error processing write queue: {e}")
                batch.clear()
    
    def start_process(self, config_hash: str, total_rows: int) -> str:
        """Start a new process and return its ID."""
        validate_string(config_hash, "Config hash")
        validate_int(total_rows, "Total rows")
            
        process_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        self.write_queue.put((
            "INSERT INTO processes (process_id, config_hash, start_time, last_updated, status, total_rows) VALUES (?, ?, ?, ?, ?, ?)",
            (process_id, config_hash, current_time, current_time, 'running', total_rows)
        ))
        return process_id
    
    def cache_result(self, process_id: str, row_index: int, query: str, result: str) -> None:
        """Cache a result for a specific row."""
        validate_string(process_id, "Process ID")
        validate_int(row_index, "Row index")
        validate_string(query, "Query")
        validate_string(result, "Result")
            
        current_time = datetime.now()
        
        self.write_queue.put((
            "INSERT OR REPLACE INTO results_cache (process_id, row_index, query, result, created_at) VALUES (?, ?, ?, ?, ?)",
            (process_id, row_index, query, result, current_time)
        ))
        
        self.write_queue.put((
            "UPDATE processes SET processed_rows = processed_rows + 1, last_updated = ? WHERE process_id = ?",
            (current_time, process_id)
        ))
    
    def get_cached_results(self, process_id: str) -> Dict[int, Any]:
        """Get all cached results for a process."""
        validate_string(process_id, "Process ID")
            
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT row_index, result FROM results_cache WHERE process_id = ?",
                (process_id,)
            ).fetchall()
            return {row['row_index']: json.loads(row['result']) for row in rows}
    
    def get_process_status(self, process_id: str) -> Optional[ProcessStatus]:
        """Get the status of a process."""
        validate_string(process_id, "Process ID")
            
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM processes WHERE process_id = ?",
                (process_id,)
            ).fetchone()
            
            if row:
                row_dict = self.db.row_to_dict(row)
                return ProcessStatus(**row_dict)
            return None
    
    def find_unfinished_process(self, config_hash: str) -> Optional[ProcessStatus]:
        """Find the most recent unfinished process for a config hash."""
        validate_string(config_hash, "Config hash")
            
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM processes 
                WHERE config_hash = ? AND status = 'running'
                ORDER BY last_updated DESC LIMIT 1
            """, (config_hash,)).fetchone()
            
            if row:
                row_dict = self.db.row_to_dict(row)
                return ProcessStatus(**row_dict)
            return None
    
    def get_process_summary(self, process: ProcessStatus) -> str:
        """Get a human-readable summary of a process."""
        time_diff = datetime.now() - process.last_updated
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            time_ago = f"{time_diff.seconds // 3600} hours ago"
        else:
            time_ago = f"{time_diff.seconds // 60} minutes ago"
            
        return (
            f"Found unfinished process from {time_ago}\n"
            f"Progress: {process.processed_rows}/{process.total_rows} rows "
            f"({process.progress:.1f}%)"
        )
    
    def mark_process_completed(self, process_id: str) -> None:
        """Mark a process as completed."""
        validate_string(process_id, "Process ID")
        self.write_queue.put((
            "UPDATE processes SET status = 'completed', last_updated = ? WHERE process_id = ?",
            (datetime.now(), process_id)
        ))
    
    def cleanup_old_processes(self, days: int = 30) -> None:
        """Clean up processes older than specified days."""
        validate_int(days, "Days")
        cutoff = datetime.now() - timedelta(days=days)
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM processes WHERE last_updated < ?", (cutoff,))
    
    def cleanup(self) -> None:
        """Cleanup method called on program exit."""
        self.is_running = False
        if hasattr(self, 'writer_thread'):
            try:
                self.writer_thread.join(timeout=5.0)
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")