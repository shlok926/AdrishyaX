"""
StegoForge v4.0 - Batch Processing Engine
========================================

Handles multi-file steganography and encryption operations with:
  - Job queue management
  - Progress tracking
  - Worker pool execution
  - Error recovery
  - Result aggregation

Status: Feature #3 Option C
"""

import uuid
import json
import threading
import queue
import logging
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================================
# ENUMS & TYPES
# ============================================================================

class JobStatus(Enum):
    """Batch job execution states"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileStatus(Enum):
    """Individual file processing state"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FileJob:
    """Individual file task within a batch"""
    file_id: str
    filename: str
    filepath: str
    status: FileStatus = FileStatus.PENDING
    progress: int = 0  # 0-100
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        data = asdict(self)
        data['status'] = self.status.value
        return data


@dataclass
class BatchJob:
    """Batch operation container"""
    batch_id: str
    job_type: str  # 'encrypt', 'decrypt', 'embed', 'extract'
    status: JobStatus = JobStatus.QUEUED
    total_files: int = 0
    processed_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    progress: int = 0  # 0-100
    files: Dict[str, FileJob] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self, include_files: bool = True) -> Dict:
        """Convert to JSON-serializable dict"""
        data = {
            'batch_id': self.batch_id,
            'job_type': self.job_type,
            'status': self.status.value,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'progress': self.progress,
            'options': self.options,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'duration_seconds': self.duration_seconds,
            'error_message': self.error_message,
        }
        if include_files:
            data['files'] = {fid: f.to_dict() for fid, f in self.files.items()}
        return data


# ============================================================================
# BATCH PROCESSOR
# ============================================================================

class BatchProcessor:
    """
    Multi-threaded batch processing engine for steganography operations.
    
    Features:
      - Configurable worker pool (default: 4 workers)
      - In-memory job queue with persistence option
      - Per-file progress tracking (0-100%)
      - Aggregate batch progress reporting
      - Error recovery and logging
      - Cancellation support
    
    Usage:
      processor = BatchProcessor(max_workers=4)
      batch = processor.create_batch('encrypt', files, options)
      processor.submit_batch(batch, handler_func)
      status = processor.get_batch_status(batch.batch_id)
    """

    def __init__(self, max_workers: int = 4, logger: Optional[logging.Logger] = None):
        """
        Initialize batch processor.
        
        Args:
            max_workers: Number of concurrent worker threads
            logger: Optional logger instance; creates default if None
        """
        self.max_workers = max_workers
        self.logger = logger or self._setup_logger()
        
        # Job storage (in-memory; consider Redis for distributed deployments)
        self.batches: Dict[str, BatchJob] = {}
        self.lock = threading.RLock()
        
        # Thread pool for concurrent file processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="stego-worker-")
        
        # Futures tracking for cancellation
        self.futures: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(f"BatchProcessor initialized: max_workers={max_workers}")

    def _setup_logger(self) -> logging.Logger:
        """Create default logger for batch operations"""
        logger = logging.getLogger("batch_processor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def create_batch(
        self,
        job_type: str,
        files: List[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> BatchJob:
        """
        Create a new batch job.
        
        Args:
            job_type: Type of operation ('encrypt', 'decrypt', 'embed', 'extract')
            files: List of file paths to process
            options: Job-specific options (password, cipher, etc.)
            
        Returns:
            BatchJob instance (queued, not yet started)
        """
        batch_id = str(uuid.uuid4())[:8]
        batch = BatchJob(
            batch_id=batch_id,
            job_type=job_type,
            total_files=len(files),
            options=options or {},
        )
        
        # Create FileJob for each input file
        for filepath in files:
            path = Path(filepath)
            file_id = str(uuid.uuid4())[:8]
            file_job = FileJob(
                file_id=file_id,
                filename=path.name,
                filepath=str(path.absolute()),
            )
            batch.files[file_id] = file_job
        
        with self.lock:
            self.batches[batch_id] = batch
        
        self.logger.info(f"Batch {batch_id} created: {len(files)} files, type={job_type}")
        return batch

    def submit_batch(
        self,
        batch: BatchJob,
        handler: Callable[[FileJob, Dict[str, Any]], Dict[str, Any]],
        on_progress: Optional[Callable[[str, int], None]] = None,
    ) -> str:
        """
        Submit batch for processing.
        
        Args:
            batch: BatchJob instance
            handler: Callback(file_job, options) -> result dict
            on_progress: Optional callback(batch_id, progress_percent) for UI updates
            
        Returns:
            batch_id for tracking
        """
        batch_id = batch.batch_id
        
        with self.lock:
            batch.status = JobStatus.IN_PROGRESS
            batch.started_at = datetime.utcnow().isoformat()
        
        # Submit all files to executor
        file_futures = {}
        for file_id, file_job in batch.files.items():
            future = self.executor.submit(
                self._process_file,
                batch_id,
                file_id,
                file_job,
                batch.options,
                handler,
            )
            file_futures[file_id] = future
        
        # Store futures for potential cancellation
        with self.lock:
            self.futures[batch_id] = {
                'futures': file_futures,
                'on_progress': on_progress,
            }
        
        # Start background thread to monitor completion
        monitor_thread = threading.Thread(
            target=self._monitor_batch,
            args=(batch_id, file_futures, on_progress),
            daemon=True,
        )
        monitor_thread.start()
        
        self.logger.info(f"Batch {batch_id} submitted with {len(file_futures)} files")
        return batch_id

    def _process_file(
        self,
        batch_id: str,
        file_id: str,
        file_job: FileJob,
        options: Dict[str, Any],
        handler: Callable,
    ) -> Dict[str, Any]:
        """
        Worker thread: Process individual file.
        
        Args:
            batch_id: Parent batch ID
            file_id: File job ID
            file_job: FileJob instance
            options: Batch options
            handler: Processing function
            
        Returns:
            Result dict from handler
        """
        start_time = time.time()
        
        try:
            with self.lock:
                batch = self.batches[batch_id]
                file_job.status = FileStatus.PROCESSING
                file_job.started_at = datetime.utcnow().isoformat()
                file_job.progress = 0
            
            self.logger.debug(f"Processing {file_job.filename} ({batch_id}/{file_id})")
            
            # Call handler to process file
            result = handler(file_job, options)
            
            # Mark success
            with self.lock:
                batch = self.batches[batch_id]
                file_job.status = FileStatus.SUCCESS
                file_job.progress = 100
                file_job.result_data = result
                batch.successful_files += 1
            
            return result
            
        except Exception as e:
            # Capture error
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.logger.error(f"File {file_job.filename} error: {error_msg}")
            
            with self.lock:
                batch = self.batches[batch_id]
                file_job.status = FileStatus.ERROR
                file_job.error_message = error_msg
                batch.failed_files += 1
            
            return {'error': error_msg, 'file_id': file_id}
            
        finally:
            # Update completion metadata
            duration = time.time() - start_time
            with self.lock:
                batch = self.batches[batch_id]
                file_job.completed_at = datetime.utcnow().isoformat()
                file_job.duration_seconds = duration
                batch.processed_files += 1

    def _monitor_batch(
        self,
        batch_id: str,
        file_futures: Dict[str, Any],
        on_progress: Optional[Callable],
    ):
        """
        Monitor batch completion and update progress.
        """
        completed = 0
        total = len(file_futures)
        
        for future in as_completed(file_futures.values()):
            completed += 1
            with self.lock:
                batch = self.batches[batch_id]
                progress = int((completed / total) * 100) if total > 0 else 100
                batch.progress = progress
            
            # Notify UI of progress update
            if on_progress:
                on_progress(batch_id, batch.progress)
        
        # Finalize batch
        with self.lock:
            batch = self.batches[batch_id]
            batch.progress = 100
            batch.status = JobStatus.COMPLETED if batch.failed_files == 0 else JobStatus.FAILED
            batch.completed_at = datetime.utcnow().isoformat()
            
            # Calculate total duration
            if batch.started_at:
                started = datetime.fromisoformat(batch.started_at)
                completed = datetime.fromisoformat(batch.completed_at)
                batch.duration_seconds = (completed - started).total_seconds()
        
        self.logger.info(
            f"Batch {batch_id} completed: {batch.successful_files}/{batch.total_files} "
            f"successful, {batch.failed_files} failed, duration={batch.duration_seconds:.2f}s"
        )

    def get_batch_status(self, batch_id: str, include_files: bool = True) -> Optional[Dict]:
        """
        Retrieve batch status.
        
        Args:
            batch_id: ID of batch to check
            include_files: Whether to include per-file details
            
        Returns:
            BatchJob dict or None if not found
        """
        with self.lock:
            batch = self.batches.get(batch_id)
            if batch:
                return batch.to_dict(include_files=include_files)
        return None

    def list_batches(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        List all batches with optional filtering.
        
        Args:
            status: Filter by JobStatus
            job_type: Filter by job_type
            
        Returns:
            List of BatchJob dicts
        """
        with self.lock:
            batches = list(self.batches.values())
        
        # Apply filters
        if status:
            batches = [b for b in batches if b.status == status]
        if job_type:
            batches = [b for b in batches if b.job_type == job_type]
        
        # Sort by creation time (newest first)
        batches.sort(key=lambda b: b.created_at, reverse=True)
        
        return [b.to_dict(include_files=False) for b in batches]

    def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel pending batch job.
        
        Args:
            batch_id: Batch to cancel
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        with self.lock:
            batch = self.batches.get(batch_id)
            if not batch:
                return False
            
            if batch.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                return False
            
            # Cancel all pending futures
            batch_futures = self.futures.get(batch_id, {}).get('futures', {})
            cancelled_count = 0
            for future in batch_futures.values():
                if future.cancel():
                    cancelled_count += 1
            
            batch.status = JobStatus.CANCELLED
            self.logger.info(f"Batch {batch_id} cancelled ({cancelled_count} futures)")
            return True

    def clear_batch(self, batch_id: str) -> bool:
        """
        Remove completed batch from memory.
        
        Args:
            batch_id: Batch to clear
            
        Returns:
            True if cleared
        """
        with self.lock:
            if batch_id in self.batches:
                del self.batches[batch_id]
            if batch_id in self.futures:
                del self.futures[batch_id]
        return True

    def shutdown(self, wait: bool = True):
        """
        Shutdown batch processor and thread pool.
        
        Args:
            wait: Whether to wait for pending tasks
        """
        self.executor.shutdown(wait=wait)
        self.logger.info("BatchProcessor shutdown complete")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    """Example: Batch encrypt with simple file duplication handler"""
    
    # Setup
    processor = BatchProcessor(max_workers=2)
    
    # Create test files
    test_dir = Path("/tmp/batch_test")
    test_dir.mkdir(exist_ok=True)
    for i in range(3):
        (test_dir / f"file_{i}.txt").write_text(f"Test data {i}")
    
    # Create batch
    files = [str(test_dir / f"file_{i}.txt") for i in range(3)]
    batch = processor.create_batch(
        job_type='encrypt',
        files=files,
        options={'cipher': 'AES-256-GCM', 'password': 'test123'},
    )
    
    # Process handler (simulates encryption)
    def encrypt_handler(file_job: FileJob, options: Dict) -> Dict:
        time.sleep(0.5)  # Simulate work
        file_job.progress = 50
        time.sleep(0.5)
        file_job.progress = 100
        return {
            'encrypted': True,
            'output_file': f"{file_job.filepath}.enc",
            'cipher': options.get('cipher'),
        }
    
    # Submit and monitor
    def on_progress(batch_id: str, progress: int):
        print(f"  Batch {batch_id}: {progress}%")
    
    processor.submit_batch(batch, encrypt_handler, on_progress)
    
    # Poll status
    while True:
        status = processor.get_batch_status(batch.batch_id, include_files=False)
        print(f"Status: {status['status']}, Progress: {status['progress']}%")
        if status['status'] == 'completed':
            break
        time.sleep(0.5)
    
    # Print final report
    final_status = processor.get_batch_status(batch.batch_id)
    print(f"\nBatch Report:")
    print(f"  Total: {final_status['total_files']}")
    print(f"  Successful: {final_status['successful_files']}")
    print(f"  Failed: {final_status['failed_files']}")
    print(f"  Duration: {final_status['duration_seconds']:.2f}s")
    
    processor.shutdown()
