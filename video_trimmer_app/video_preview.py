#!/usr/bin/env python3
"""
Video Preview and Thumbnail Generator
Handles video preview, thumbnail generation, and basic video analysis.
"""

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    # Don't set cv2 to None to avoid type annotation issues

import numpy as np
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    # Don't set Image/ImageTk to None to avoid type annotation issues

import threading
from pathlib import Path
from typing import Optional, Callable, Tuple, List, Dict, Any, Union
from loguru import logger
import tempfile
import os
import warnings

# Suppress OpenCV H.264 warnings
warnings.filterwarnings('ignore', category=UserWarning, module='cv2')

# Constants
DEFAULT_THUMBNAIL_SIZE = (100, 60)
MAX_CACHE_SIZE = 50
DEFAULT_TIMELINE_THUMBNAILS = 10
MAX_TIMELINE_THUMBNAILS = 20
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.ts']
MAX_VIDEO_SIZE_MB = 1000  # Maximum video size for processing


class VideoPreview:
    """Handles video preview and thumbnail generation."""
    
    def __init__(self):
        """Initialize video preview handler."""
        self.current_video = None
        self.video_path: Optional[str] = None
        self.frame_cache: Dict[float, np.ndarray] = {}
        self.thumbnail_cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        self._video_lock = threading.Lock() # Lock for thread-safe video access
        self._moviepy_clip = None
        
        # Supported video formats
        self.supported_formats = {
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.ts',
            '.m4v', '.3gp', '.3g2', '.mpg', '.mpeg', '.m2v'
        }
        
    def _is_supported_format(self, video_path: str) -> bool:
        """Check if video format is supported."""
        file_ext = Path(video_path).suffix.lower()
        return file_ext in self.supported_formats
        
    def _clear_caches(self) -> None:
        """Thread-safe cache clearing."""
        with self._cache_lock:
            self.frame_cache.clear()
            self.thumbnail_cache.clear()
            
    def _release_current_video(self) -> None:
        """Safely release current video capture."""
        if self.current_video is not None:
            try:
                self.current_video.release()
            except Exception as e:
                logger.warning(f"Error releasing video capture: {e}")
            finally:
                self.current_video = None
        
        if self._moviepy_clip is not None:
            try:
                self._moviepy_clip.close()
            except Exception as e:
                logger.warning(f"Error releasing MoviePy clip: {e}")
            finally:
                self._moviepy_clip = None
                
    def release_video(self) -> None:
        """Public method to release current video."""
        self._release_current_video()
        self._clear_caches()
        self.video_path = None
        
    def load_video(self, video_path: str) -> bool:
        """Load video for preview.
        
        Args:
            video_path: Path to video file
            
        Returns:
            bool: True if video loaded successfully
        """
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Video file does not exist: {video_path}")
            return False
            
        if not self._is_supported_format(video_path):
            logger.error(f"Unsupported video format: {video_path}")
            return False
            
        try:
            # Release previous video
            self._release_current_video()
            
            if CV2_AVAILABLE:
                # Try OpenCV first
                self.current_video = cv2.VideoCapture(video_path)
                self.video_path = video_path
                
                if not self.current_video.isOpened():
                    logger.error(f"Failed to open video with OpenCV: {video_path}")
                    return self._load_video_with_moviepy(video_path)
                
                # Clear caches with thread safety
                self._clear_caches()
                logger.debug(f"Video loaded successfully with OpenCV: {video_path}")
                return True
            else:
                # Fallback to MoviePy
                return self._load_video_with_moviepy(video_path)
            
        except Exception as e:
            logger.error(f"Error loading video: {e}")
            return self._load_video_with_moviepy(video_path)
    
    def _load_video_with_moviepy(self, video_path: str) -> bool:
        """Fallback method to load video using MoviePy."""
        try:
            from moviepy.editor import VideoFileClip  # type: ignore
            
            # Store basic info for moviepy
            self.current_video = None  # Not using OpenCV
            self.video_path = video_path
            self._moviepy_clip = VideoFileClip(video_path)
            
            logger.debug(f"Video loaded successfully with MoviePy: {video_path}")
            return True
            
        except ImportError:
            logger.error("MoviePy not available - cannot load video")
            return False
        except Exception as e:
            logger.error(f"Failed to load video with MoviePy: {e}")
            return False
    
    def get_video_info(self) -> Optional[dict]:
        """Get detailed video information."""
        with self._video_lock:
            try:
                if self.current_video and CV2_AVAILABLE and self.current_video.isOpened():
                    # Use OpenCV
                    info = {
                        'frame_count': int(self.current_video.get(cv2.CAP_PROP_FRAME_COUNT)),
                        'fps': self.current_video.get(cv2.CAP_PROP_FPS),
                        'width': int(self.current_video.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        'height': int(self.current_video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                        'codec': None,  # OpenCV doesn't provide easy codec info
                    }
                    
                    # Calculate duration
                    if info['fps'] > 0:
                        info['duration'] = info['frame_count'] / info['fps']
                    else:
                        info['duration'] = 0
                        
                elif self._moviepy_clip:
                    # Use MoviePy
                    info = {
                        'frame_count': int(self._moviepy_clip.fps * self._moviepy_clip.duration) if self._moviepy_clip.fps else 0,
                        'fps': self._moviepy_clip.fps or 30.0,  # Default to 30 if not available
                        'width': self._moviepy_clip.size[0] if self._moviepy_clip.size else 0,
                        'height': self._moviepy_clip.size[1] if self._moviepy_clip.size else 0,
                        'duration': self._moviepy_clip.duration or 0,
                        'codec': None,
                    }
                else:
                    logger.error("No video loaded for getting info")
                    return None
                
                # Calculate bitrate (rough estimate)
                if self.video_path and os.path.exists(self.video_path):
                    file_size = os.path.getsize(self.video_path)
                    if info['duration'] > 0:
                        info['bitrate'] = (file_size * 8) / (info['duration'] * 1024)  # kbps
                    else:
                        info['bitrate'] = 0
                else:
                    info['bitrate'] = 0
                
                return info
            except Exception as e:
                logger.error(f"Error getting video info: {e}")
                return None
    
    def get_frame_at_time(self, time_seconds: float, size: Optional[Tuple[int, int]] = None) -> Optional[np.ndarray]:
        """Get frame at specific time."""
        # Validate time bounds
        if time_seconds < 0:
            time_seconds = 0
            
        # Check if we have video info to validate max time
        try:
            info = self.get_video_info()
            if info and info['duration'] > 0:
                max_time = info['duration'] - 0.1  # Leave small buffer
                if time_seconds > max_time:
                    time_seconds = max_time
                    logger.warning(f"Requested time {time_seconds:.2f}s exceeds video duration, clamping to {max_time:.2f}s")
        except Exception:
            pass  # Continue with original time if we can't get info
        
        # Check cache first
        cache_key = f"{time_seconds}_{size}"
        with self._cache_lock:
            if cache_key in self.frame_cache:
                return self.frame_cache[cache_key]
        
        with self._video_lock:
            # Try OpenCV method first
            if self.current_video and CV2_AVAILABLE and self.current_video.isOpened():
                try:
                    fps = self.current_video.get(cv2.CAP_PROP_FPS)
                    frame_number = int(time_seconds * fps)
                    
                    # Set video position
                    self.current_video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                    
                    # Read frame
                    ret, frame = self.current_video.read()
                    if ret and frame is not None:
                        # Convert BGR to RGB
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Resize if needed
                        if size:
                            frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
                        
                        # Cache the frame
                        with self._cache_lock:
                            self.frame_cache[cache_key] = frame
                        return frame
                        
                except Exception as e:
                    logger.debug(f"OpenCV frame extraction failed: {e}")
            
            # Fallback to MoviePy if available
            if self._moviepy_clip:
                try:
                    from moviepy.editor import VideoFileClip  # type: ignore
                    
                    # Get frame from MoviePy
                    frame_array = self._moviepy_clip.get_frame(time_seconds)
                    
                    # Resize if needed
                    if size:
                        if CV2_AVAILABLE:
                            frame_array = cv2.resize(frame_array, size, interpolation=cv2.INTER_AREA)
                        elif PIL_AVAILABLE:
                            # Use PIL for resizing as fallback
                            pil_image = Image.fromarray(frame_array.astype('uint8'))
                            pil_image = pil_image.resize(size, Image.LANCZOS)
                            frame_array = np.array(pil_image)
                        # If neither available, return original size
                    
                    # Cache the frame
                    with self._cache_lock:
                        self.frame_cache[cache_key] = frame_array
                    return frame_array
                    
                except ImportError:
                    logger.error("MoviePy not available for frame extraction")
                except Exception as e:
                    logger.debug(f"MoviePy frame extraction failed: {e}")
        
        logger.error(f"Failed to get frame at time {time_seconds}s")
        return None
    
    def get_thumbnail(self, time_seconds: float, size: Tuple[int, int] = (160, 90), as_pil: bool = False):
        """Get thumbnail as PhotoImage for Tkinter or PIL Image."""
        if not PIL_AVAILABLE:
            logger.warning("PIL not available for thumbnail generation")
            return None
            
        try:
            cache_key = f"thumb_{time_seconds}_{size}"
            with self._cache_lock:
                if cache_key in self.thumbnail_cache:
                    cached_item = self.thumbnail_cache[cache_key]
                    # If the request is for a PIL image and we have one, return it
                    if as_pil and PIL_AVAILABLE and hasattr(cached_item, 'size'):  # PIL Image check
                        return cached_item
                    # If the request is for a PhotoImage and we have one, return it
                    if not as_pil and PIL_AVAILABLE and hasattr(cached_item, 'width'):  # PhotoImage check
                        return cached_item
            
            frame = self.get_frame_at_time(time_seconds, size)
            if frame is None:
                return None
            
            # Convert to PIL Image
            if PIL_AVAILABLE:
                pil_image = Image.fromarray(frame)
            else:
                return None
            
            if as_pil:
                with self._cache_lock:
                    self.thumbnail_cache[cache_key] = pil_image
                return pil_image

            # Check if Tkinter root exists before creating PhotoImage
            import tkinter as tk
            try:
                # Try to get the default root
                root = tk._default_root
                if root is None:
                    # Create a hidden root if none exists
                    root = tk.Tk()
                    root.withdraw()  # Hide the window
                    
                # Convert to PhotoImage
                if PIL_AVAILABLE:
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # Cache the thumbnail
                    with self._cache_lock:
                        self.thumbnail_cache[cache_key] = photo
                    
                    return photo
                else:
                    return pil_image
                
            except (tk.TclError, RuntimeError) as te:
                logger.warning(f"Tkinter not available for PhotoImage: {te}. Returning PIL image.")
                # Cache and return PIL image as fallback
                with self._cache_lock:
                    self.thumbnail_cache[cache_key] = pil_image
                return pil_image
                
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None
            
    def get_frame_as_pil(self, time_seconds: float, size: Tuple[int, int] = (160, 90)):
        """Get frame as PIL Image without Tkinter dependency."""
        return self.get_thumbnail(time_seconds, size, as_pil=True)
    
    def generate_timeline_thumbnails(self, count: int = 10, size: Tuple[int, int] = (80, 45), 
                                   as_pil: bool = False,
                                   callback: Optional[Callable] = None):
        """Generate thumbnails for timeline view."""
        thumbnails = []
        
        # Check if we have any video loaded
        if not ((self.current_video and self.current_video.isOpened()) or self._moviepy_clip):
            logger.warning("No video loaded for timeline thumbnail generation")
            return thumbnails
        
        try:
            info = self.get_video_info()
            if not info or info['duration'] <= 0:
                logger.warning("Invalid video duration for timeline thumbnails")
                return thumbnails
            
            duration = info['duration']
            time_interval = duration / (count + 1)  # +1 to avoid first and last frame
            
            logger.debug(f"Generating {count} thumbnails for {duration}s video")
            
            for i in range(count):
                time_pos = time_interval * (i + 1)
                thumbnail = self.get_thumbnail(time_pos, size, as_pil=as_pil)
                
                if thumbnail:
                    thumbnails.append(thumbnail)
                else:
                    logger.debug(f"Failed to generate thumbnail at {time_pos}s")
                
                # Call progress callback if provided
                if callback:
                    callback(i + 1, count)
            
            logger.debug(f"Generated {len(thumbnails)} timeline thumbnails")
            return thumbnails
            
        except Exception as e:
            logger.error(f"Error generating timeline thumbnails: {e}")
            return thumbnails
    
    def extract_audio_waveform(self, output_path: str = None) -> Optional[str]:
        """Extract audio waveform data for visualization."""
        if not self.video_path:
            return None
        
        try:
            import librosa
            import soundfile as sf
            
            # Extract audio
            audio_data, sample_rate = librosa.load(self.video_path)
            
            # Generate output path if not provided
            if not output_path:
                output_path = tempfile.mktemp(suffix='.wav')
            
            # Save audio file
            sf.write(output_path, audio_data, sample_rate)
            
            return output_path
        except ImportError:
            logger.warning("librosa not available for audio waveform extraction")
            return None
        except Exception as e:
            logger.error(f"Error extracting audio waveform: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.current_video:
                self.current_video.release()
            
            self.frame_cache.clear()
            self.thumbnail_cache.clear()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


class AsyncVideoLoader:
    """Asynchronous video loader for better UI responsiveness."""
    
    def __init__(self, preview_handler: VideoPreview):
        """Initialize async loader."""
        self.preview_handler = preview_handler
        self.loading_thread = None
        self.cancel_loading = False
    
    def load_video_async(self, video_path: str, callback: Callable[[bool, Optional[dict]], None]):
        """Load video asynchronously."""
        self.cancel_loading = False
        self.loading_thread = threading.Thread(
            target=self._load_video_worker,
            args=(video_path, callback)
        )
        self.loading_thread.daemon = True
        self.loading_thread.start()
    
    def _load_video_worker(self, video_path: str, callback: Callable[[bool, Optional[dict]], None]):
        """Worker thread for loading video."""
        try:
            if self.cancel_loading:
                return
            
            # Load video
            success = self.preview_handler.load_video(video_path)
            
            if self.cancel_loading:
                return
            
            # Get video info
            video_info = None
            if success:
                video_info = self.preview_handler.get_video_info()
            
            # Call callback
            callback(success, video_info)
        except Exception as e:
            logger.error(f"Error in async video loader: {e}")
            callback(False, None)
    
    def cancel(self):
        """Cancel current loading operation."""
        self.cancel_loading = True
        
        if self.loading_thread and self.loading_thread.is_alive():
            self.loading_thread.join(timeout=1.0)
    
    # Helper methods for VideoPreview class
    def _is_supported_format(self, file_path: str) -> bool:
        """Check if video format is supported.
        
        Args:
            file_path: Path to video file
            
        Returns:
            bool: True if format is supported
        """
        if not file_path:
            return False
            
        file_ext = Path(file_path).suffix.lower()
        return file_ext in SUPPORTED_FORMATS
            
    def _manage_cache_size(self) -> None:
        """Ensure cache doesn't exceed maximum size."""
        with self._cache_lock:
            if len(self.frame_cache) > MAX_CACHE_SIZE:
                # Remove oldest entries (simple FIFO)
                excess_count = len(self.frame_cache) - MAX_CACHE_SIZE + 10
                keys_to_remove = list(self.frame_cache.keys())[:excess_count]
                for key in keys_to_remove:
                    del self.frame_cache[key]
                    
            if len(self.thumbnail_cache) > MAX_CACHE_SIZE:
                excess_count = len(self.thumbnail_cache) - MAX_CACHE_SIZE + 10
                keys_to_remove = list(self.thumbnail_cache.keys())[:excess_count]
                for key in keys_to_remove:
                    del self.thumbnail_cache[key]