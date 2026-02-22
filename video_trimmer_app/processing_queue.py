#!/usr/bin/env python3
"""
Processing Queue Manager
Handles batch processing, queue management, and concurrent video processing.
"""

import threading
import time
from queue import Queue, Empty
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Union, Set
from pathlib import Path
from loguru import logger
import uuid
from concurrent.futures import ThreadPoolExecutor
import psutil

# Constants
DEFAULT_MAX_WORKERS = 2
MAX_QUEUE_SIZE = 100
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
PROGRESS_UPDATE_INTERVAL = 1.0  # seconds
CLEANUP_INTERVAL = 60.0  # seconds
MAX_COMPLETED_JOBS = 50
PRIORITY_HIGH = 10
PRIORITY_NORMAL = 5
PRIORITY_LOW = 1


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """Represents a video processing job.
    
    Attributes:
        id: Unique job identifier
        input_path: Path to input video file
        output_path: Path for output video file
        trim_start: Start time for trimming (seconds)
        trim_end: End time for trimming (seconds)
        from_start: Whether trim_start is from beginning or end
        engine: Processing engine ('ffmpeg', 'moviepy')
        priority: Job priority (higher = more priority)
        status: Current job status
        progress: Processing progress (0.0 to 1.0)
        error_message: Error details if failed
        created_time: When job was created (timestamp)
        start_time: When processing started (timestamp)
        end_time: When processing finished (timestamp)
        estimated_time: Estimated processing duration
        settings: Additional processing settings
        retry_count: Number of retry attempts
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_path: str = ""
    output_path: str = ""
    trim_start: float = 0.0
    trim_end: float = 0.0
    from_start: bool = True
    engine: str = "ffmpeg"
    priority: int = PRIORITY_NORMAL
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    error_message: str = ""
    created_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    estimated_time: Optional[float] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    
    @property
    def duration(self) -> Optional[float]:
        """Get job processing duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed processing time."""
        if self.start_time:
            end_time = self.end_time or time.time()
            return end_time - self.start_time
        return None


class ProcessingQueue:
    """Manages video processing queue with concurrent execution.
    
    Attributes:
        max_workers: Maximum number of concurrent processing threads
        jobs: Dictionary of all jobs by ID
        job_queue: Queue for pending jobs
        executor: Thread pool executor for concurrent processing
        running: Whether queue is actively processing
        paused: Whether queue processing is paused
        active_jobs: Set of currently processing job IDs
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize processing queue.
        
        Args:
            max_workers: Maximum concurrent workers (defaults to CPU count)
        """
        self.max_workers = max_workers or min(DEFAULT_MAX_WORKERS, psutil.cpu_count() or 2)
        self.jobs: Dict[str, ProcessingJob] = {}
        self.job_queue: Queue[str] = Queue(maxsize=MAX_QUEUE_SIZE)
        self.executor: Optional[ThreadPoolExecutor] = None
        self.running = False
        self.paused = False
        self.active_jobs: Set[str] = set()
        self._lock = threading.RLock()
        
        # Callbacks with proper type hints
        self.on_job_started: Optional[Callable[[ProcessingJob], None]] = None
        self.on_job_completed: Optional[Callable[[ProcessingJob], None]] = None
        self.on_job_failed: Optional[Callable[[ProcessingJob, str], None]] = None
        self.on_job_progress: Optional[Callable[[ProcessingJob, float], None]] = None
        self.on_queue_empty: Optional[Callable[[], None]] = None
        
        # Processing engines registry
        self.engines: Dict[str, Any] = {}
        
    def register_engine(self, name: str, engine_instance: Any) -> bool:
        """Register a processing engine.
        
        Args:
            name: Engine name identifier
            engine_instance: Engine instance with trim_video method
            
        Returns:
            bool: True if registered successfully
        """
        if not name or engine_instance is None:
            logger.error(f"Invalid engine registration: {name}")
            return False
            
        if not hasattr(engine_instance, 'trim_video'):
            logger.error(f"Engine {name} missing required 'trim_video' method")
            return False
        
        with self._lock:
            self.engines[name] = engine_instance
            logger.debug(f"Registered processing engine: {name}")
            return True
        
    def add_job(self, job: ProcessingJob) -> str:
        """Add job to queue."""
        self.jobs[job.id] = job
        self.job_queue.put(job)
        logger.info(f"Added job {job.id} to queue")
        return job.id
    
    def create_and_add_job(self, input_path: str, output_path: str, 
                          trim_duration: float, from_start: bool = True,
                          engine: str = "ffmpeg", priority: int = 0,
                          **settings) -> str:
        """Create and add a new job to the queue."""
        job = ProcessingJob(
            input_path=input_path,
            output_path=output_path,
            trim_start=trim_duration if from_start else 0,
            trim_end=trim_duration if not from_start else 0,
            from_start=from_start,
            engine=engine,
            priority=priority,
            settings=settings
        )
        return self.add_job(job)
    
    def remove_job(self, job_id: str) -> bool:
        """Remove job from queue (if not started)."""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                logger.info(f"Cancelled job {job_id}")
                return True
            elif job.status == JobStatus.PROCESSING:
                # Can't cancel running jobs easily - would need more complex implementation
                logger.warning(f"Cannot cancel running job {job_id}")
                return False
        return False
    
    def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def get_jobs_by_status(self, status: JobStatus) -> List[ProcessingJob]:
        """Get all jobs with specific status."""
        return [job for job in self.jobs.values() if job.status == status]
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        stats = {status.value: 0 for status in JobStatus}
        for job in self.jobs.values():
            stats[job.status.value] += 1
        return stats
    
    def start_processing(self):
        """Start processing jobs from queue."""
        if self.running:
            return
        
        # Create executor if not exists
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        self.running = True
        self.paused = False
        logger.info("Started processing queue")
        
        # Submit initial jobs
        for _ in range(self.max_workers):
            self.executor.submit(self._worker_thread)
    
    def pause_processing(self):
        """Pause processing (finish current jobs but don't start new ones)."""
        self.paused = True
        logger.info("Paused processing queue")
    
    def resume_processing(self):
        """Resume processing."""
        if self.running and self.paused:
            self.paused = False
            logger.info("Resumed processing queue")
            # Restart worker threads
            for _ in range(self.max_workers):
                self.executor.submit(self._worker_thread)
    
    def stop_processing(self):
        """Stop processing and shutdown."""
        self.running = False
        self.paused = False
        if self.executor is not None:
            self.executor.shutdown(wait=False)
            self.executor = None
        logger.info("Stopped processing queue")
    
    def _worker_thread(self):
        """Worker thread that processes jobs from queue."""
        while self.running and not self.paused:
            try:
                # Get next job with timeout
                job = self.job_queue.get(timeout=1.0)
                
                if job.status == JobStatus.CANCELLED:
                    continue
                
                # Process the job
                self._process_job(job)
                
                self.job_queue.task_done()
                
            except Empty:
                # Timeout - check if we should continue
                if self.job_queue.empty() and self.on_queue_empty:
                    self.on_queue_empty()
                continue
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
    
    def _process_job(self, job: ProcessingJob):
        """Process a single job."""
        try:
            job.status = JobStatus.PROCESSING
            job.start_time = time.time()
            job.progress = 0.0
            
            logger.info(f"Starting job {job.id}: {job.input_path}")
            
            if self.on_job_started:
                self.on_job_started(job)
            
            # Get the appropriate engine
            engine = self.engines.get(job.engine)
            if not engine:
                raise Exception(f"Unknown engine: {job.engine}")
            
            # Create progress callback
            def progress_callback(progress: float):
                job.progress = progress
                if self.on_job_progress:
                    self.on_job_progress(job, progress)
            
            # Execute the job based on engine type
            if hasattr(engine, 'trim_video_advanced'):
                # FFmpeg engine
                duration = job.trim_start if job.from_start else job.trim_end
                engine.trim_video_advanced(
                    job.input_path, 
                    job.output_path, 
                    duration, 
                    job.from_start,
                    verbose=job.settings.get('verbose', False)
                )
            else:
                # MoviePy or other engine
                self._process_with_moviepy(job, progress_callback)
            
            # Job completed successfully
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.end_time = time.time()
            
            logger.info(f"Completed job {job.id} in {job.duration:.2f}s")
            
            if self.on_job_completed:
                self.on_job_completed(job)
                
        except Exception as e:
            # Job failed
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.end_time = time.time()
            
            logger.error(f"Job {job.id} failed: {e}")
            
            if self.on_job_failed:
                self.on_job_failed(job, str(e))
    
    def _process_with_moviepy(self, job: ProcessingJob, progress_callback: Callable):
        """Process job using MoviePy with progress tracking."""
        from moviepy import VideoFileClip
        
        # Load video
        video = VideoFileClip(job.input_path)
        total_duration = video.duration
        
        # Calculate trim parameters
        if job.from_start:
            start_time = job.trim_start
            end_time = total_duration
        else:
            start_time = 0
            end_time = total_duration - job.trim_end
        
        # Validate trim parameters
        if end_time <= start_time:
            video.close()
            raise ValueError(f"Invalid trim parameters: start={start_time}, end={end_time}")
        
        # Progress callback for MoviePy
        def moviepy_progress(progress):
            progress_callback(progress * 100)
        
        # Trim video
        trimmed_video = video.subclipped(start_time, end_time)
        
        # Write output with progress tracking
        trimmed_video.write_videofile(
            job.output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            progress_bar=False,  # We'll handle progress ourselves
            logger=None  # Disable MoviePy logging
        )
        
        # Cleanup
        trimmed_video.close()
        video.close()
    
    def clear_completed_jobs(self):
        """Remove completed and failed jobs from memory."""
        completed_jobs = [
            job_id for job_id, job in self.jobs.items() 
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        ]
        
        for job_id in completed_jobs:
            del self.jobs[job_id]
        
        logger.info(f"Cleared {len(completed_jobs)} completed jobs")
    
    def estimate_remaining_time(self) -> Optional[float]:
        """Estimate remaining processing time."""
        pending_jobs = self.get_jobs_by_status(JobStatus.PENDING)
        processing_jobs = self.get_jobs_by_status(JobStatus.PROCESSING)
        
        if not pending_jobs and not processing_jobs:
            return 0
        
        # Calculate average processing time from completed jobs
        completed_jobs = self.get_jobs_by_status(JobStatus.COMPLETED)
        if completed_jobs:
            avg_time = sum(job.duration for job in completed_jobs if job.duration) / len(completed_jobs)
        else:
            avg_time = 60  # Default estimate
        
        # Estimate time for pending jobs
        pending_time = len(pending_jobs) * avg_time
        
        # Add remaining time for current jobs
        processing_time = 0
        for job in processing_jobs:
            if job.elapsed_time and job.progress > 0:
                estimated_total = job.elapsed_time * (100 / job.progress)
                processing_time += max(0, estimated_total - job.elapsed_time)
            else:
                processing_time += avg_time
        
        return pending_time + processing_time
    
    def get_overall_progress(self) -> float:
        """Get overall queue progress percentage."""
        if not self.jobs:
            return 100.0
        
        total_progress = sum(
            100 if job.status == JobStatus.COMPLETED else
            0 if job.status in [JobStatus.PENDING, JobStatus.FAILED, JobStatus.CANCELLED] else
            job.progress
            for job in self.jobs.values()
        )
        
        return total_progress / len(self.jobs)
    
    def export_queue_report(self) -> Dict[str, Any]:
        """Export detailed queue report."""
        stats = self.get_queue_stats()
        completed_jobs = self.get_jobs_by_status(JobStatus.COMPLETED)
        failed_jobs = self.get_jobs_by_status(JobStatus.FAILED)
        
        total_processing_time = sum(
            job.duration for job in completed_jobs if job.duration
        )
        
        return {
            'stats': stats,
            'total_jobs': len(self.jobs),
            'total_processing_time': total_processing_time,
            'average_processing_time': total_processing_time / len(completed_jobs) if completed_jobs else 0,
            'failed_jobs': [
                {'id': job.id, 'input': job.input_path, 'error': job.error_message}
                for job in failed_jobs
            ],
            'queue_start_time': min(job.created_time for job in self.jobs.values()) if self.jobs else None,
            'estimated_remaining_time': self.estimate_remaining_time(),
            'overall_progress': self.get_overall_progress()
        }