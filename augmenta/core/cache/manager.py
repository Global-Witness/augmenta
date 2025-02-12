"""
Thread-safe singleton manager for caching process results.
"""

import json
import threading
import uuid
import logging
import atexit
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from queue import Queue, Empty

from .models import ProcessStatus, ValidationError
from .database import DatabaseConnection

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Thread-safe singleton manager for caching process results.
    
    Implements a write-ahead logging pattern with a background writer thread
    to improve performance and prevent blocking operations.
    
    Attributes:
        cache_dir: Directory where cache files are stored
        db_path: Path to the SQLite database file
        is_running: Flag indicating if the writer thread is active
    """
    
    _instance: Optional['CacheManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs) -> 'CacheManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize the cache manager. Thread-safe singleton initialization.
        
        Args:
            cache_dir: Optional custom cache directory path
        """
        with self._lock:
            if hasattr(self, 'initialized'):
                return
                
            self.cache_dir = cache_dir or Path.home() / '.augmenta' / 'cache'
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = self.cache_dir / 'cache.db'
            
            self.write_queue: Queue = Queue()
            self.is_running = True
            
            self.db = DatabaseConnection(self.db_path)
            self._start_writer_thread()
            atexit.register(self.cleanup)
            self.initialized = True
    
    def _start_writer_thread(self) -> None:
        """Start the background writer thread for async database operations."""
        self.writer_thread = threading.Thread(
            target=self._process_write_queue,
            daemon=True,
            name="CacheWriterThread"
        )
        self.writer_thread.start()
    
    def _process_write_queue(self) -> None:
        """
        Process the write queue in a separate thread.
        Handles database write operations asynchronously.
        """
        QUEUE_TIMEOUT = 1.0
        BATCH_SIZE = 100
        batch: List[Tuple[str, tuple]] = []
        
        while self.is_running or not self.write_queue.empty():
            try:
                # Collect items for batch processing
                try:
                    while len(batch) < BATCH_SIZE:
                        item = self.write_queue.get(timeout=QUEUE_TIMEOUT)
                        batch.append(item)
                except Empty:
                    pass
                
                # Process batch if not empty
                if batch:
                    with self.db.get_connection() as conn:
                        for query, params in batch:
                            conn.execute(query, params)
                    batch.clear()
                    
            except Exception as e:
                logger.error(f"Error processing write queue: {e}")
                if batch:
                    logger.error(f"Failed batch size: {len(batch)}")
                batch.clear()
    
    def start_process(self, config_hash: str, total_rows: int) -> str:
        """
        Start a new process and return its ID.
        
        Args:
            config_hash: Hash of the configuration
            total_rows: Total number of rows to process
            
        Returns:
            str: Unique process ID
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not isinstance(config_hash, str) or not config_hash.strip():
            raise ValidationError("Config hash must be a non-empty string")
        if not isinstance(total_rows, int) or total_rows < 0:
            raise ValidationError("Total rows must be a non-negative integer")
            
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
        """
        Cache a result for a specific row.
        
        Args:
            process_id: Process identifier
            row_index: Index of the processed row
            query: Query that generated the result
            result: JSON-serializable result data
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not isinstance(process_id, str) or not process_id.strip():
            raise ValidationError("Process ID must be a non-empty string")
        if not isinstance(row_index, int) or row_index < 0:
            raise ValidationError("Row index must be a non-negative integer")
        if not isinstance(query, str):
            raise ValidationError("Query must be a string")
        if not isinstance(result, str):
            raise ValidationError("Result must be a string")
            
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
        """
        Get all cached results for a process.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Dict[int, Any]: Dictionary mapping row indices to their results
            
        Raises:
            ValidationError: If process_id is invalid
        """
        if not isinstance(process_id, str) or not process_id.strip():
            raise ValidationError("Process ID must be a non-empty string")
            
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT row_index, result FROM results_cache WHERE process_id = ?",
                (process_id,)
            ).fetchall()
            return {row['row_index']: json.loads(row['result']) for row in rows}
    
    def get_process_status(self, process_id: str) -> Optional[ProcessStatus]:
        """
        Get the status of a process.
        
        Args:
            process_id: Process identifier
            
        Returns:
            Optional[ProcessStatus]: Process status if found, None otherwise
            
        Raises:
            ValidationError: If process_id is invalid
        """
        if not isinstance(process_id, str) or not process_id.strip():
            raise ValidationError("Process ID must be a non-empty string")
            
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM processes WHERE process_id = ?",
                (process_id,)
            ).fetchone()
            
            if row:
                row_dict = self.db._convert_row_to_dict(row)
                return ProcessStatus(**row_dict)
            return None
    
    def find_unfinished_process(self, config_hash: str) -> Optional[ProcessStatus]:
        """
        Find the most recent unfinished process for a config hash.
        
        Args:
            config_hash: Hash of the configuration
            
        Returns:
            Optional[ProcessStatus]: Most recent unfinished process if found
            
        Raises:
            ValidationError: If config_hash is invalid
        """
        if not isinstance(config_hash, str) or not config_hash.strip():
            raise ValidationError("Config hash must be a non-empty string")
            
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM processes 
                WHERE config_hash = ? 
                AND status = 'running'
                ORDER BY last_updated DESC 
                LIMIT 1
            """, (config_hash,)).fetchone()
            
            if row:
                row_dict = self.db._convert_row_to_dict(row)
                return ProcessStatus(**row_dict)
            return None
    
    def get_process_summary(self, process: ProcessStatus) -> str:
        """
        Get a human-readable summary of a process.
        
        Args:
            process: Process status object
            
        Returns:
            str: Formatted summary string
            
        Raises:
            ValidationError: If process is invalid
        """
        if not isinstance(process, ProcessStatus):
            raise ValidationError("Process must be a ProcessStatus instance")
            
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
    
    def cleanup_old_processes(self, days: int = 30) -> None:
        """
        Clean up processes older than specified days.
        
        Args:
            days: Number of days to keep, defaults to 30
            
        Raises:
            ValidationError: If days is invalid
        """
        if not isinstance(days, int) or days < 0:
            raise ValidationError("Days must be a non-negative integer")
            
        cutoff = datetime.now() - timedelta(days=days)
        with self.db.get_connection() as conn:
            conn.execute(
                "DELETE FROM processes WHERE last_updated < ?",
                (cutoff,)
            )
    
    def cleanup(self) -> None:
        """
        Cleanup method called on program exit.
        Ensures proper shutdown of background thread.
        """
        self.is_running = False
        if hasattr(self, 'writer_thread'):
            try:
                self.writer_thread.join(timeout=5.0)
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")