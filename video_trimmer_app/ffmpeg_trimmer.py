#!/usr/bin/env python3
"""
FFmpeg-based Video Trimmer
Efficient video trimming using FFmpeg with stream copy (no re-encoding).
This is much faster than MoviePy's re-encoding approach for simple trimming operations.
"""

import subprocess
import os
import sys
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from loguru import logger
import shutil

# Constants
DEFAULT_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 2
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.ts']
FFMPEG_COMMON_PATHS = [
    'ffmpeg',
    '/usr/bin/ffmpeg',
    '/usr/local/bin/ffmpeg',
    '/opt/homebrew/bin/ffmpeg',  # macOS with Homebrew
    'C:\\ffmpeg\\bin\\ffmpeg.exe',  # Windows
    'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',  # Windows
]


class FFmpegTrimmer:
    """FFmpeg-based video trimmer for efficient trimming without re-encoding.
    
    Provides fast video trimming using FFmpeg's stream copy feature,
    avoiding re-encoding for significant performance improvements.
    
    Attributes:
        ffmpeg_path: Path to FFmpeg executable
    """
    
    def __init__(self):
        """Initialize FFmpeg trimmer with automatic path detection."""
        self.ffmpeg_path = self._find_ffmpeg()
        
        if not self.ffmpeg_path:
            logger.warning(
                "FFmpeg not found. Video trimming will be limited. "
                "Please install FFmpeg for better performance."
            )
        
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable path.
        
        Returns:
            Optional[str]: Path to FFmpeg executable or None if not found
        """
        # Try shutil.which first (most reliable)
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            logger.debug(f"Found FFmpeg via shutil.which: {ffmpeg_path}")
            return ffmpeg_path
        
        # Try common installation paths
        for path in FFMPEG_COMMON_PATHS:
            try:
                # Test if ffmpeg is available at this path
                result = subprocess.run(
                    [path, '-version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    logger.debug(f"Found FFmpeg at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        logger.warning("FFmpeg not found in system PATH or common locations")        
        return None
    
    def check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available on the system.
        
        Returns:
            bool: True if FFmpeg is available
        """
        return self.ffmpeg_path is not None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename safe for filesystem
        """
        if not filename:
            return "unnamed_file"
            
        # Remove or replace invalid characters for filesystem
        sanitized = re.sub(INVALID_FILENAME_CHARS, '_', filename)
        
        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip(' .')
        
        return sanitized if sanitized else "unnamed_file"
        # Remove or replace invalid characters for filesystem
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename)
        return sanitized
    
    def get_video_info(self, input_path):
        """
        Get video information using ffprobe.
        
        Returns:
            dict: Video information including duration, codec, etc.
        """
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
            
        try:
            # Use ffprobe to get video information
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to get video info: {result.stderr}")
                
            import json
            info = json.loads(result.stdout)
            
            # Extract duration
            duration = float(info['format']['duration'])
            
            # Find video stream
            video_stream = None
            for stream in info['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
                    
            return {
                'duration': duration,
                'codec': video_stream['codec_name'] if video_stream else 'unknown',
                'format': info['format']['format_name'],
                'size': int(info['format']['size']) if 'size' in info['format'] else 0
            }
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout while getting video info")
        except json.JSONDecodeError:
            raise RuntimeError("Failed to parse video info")
        except Exception as e:
            raise RuntimeError(f"Error getting video info: {str(e)}")
    
    def trim_video(self, input_path, output_path, duration, from_start=True, 
                   use_stream_copy=True, verbose=False):
        """
        Trim video using FFmpeg.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to output video file
            duration (float): Duration to trim in seconds
            from_start (bool): If True, trim from start; if False, trim from end
            use_stream_copy (bool): If True, use stream copy (no re-encoding)
            verbose (bool): If True, show FFmpeg output
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
            
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        try:
            # Get video info to validate duration
            video_info = self.get_video_info(input_path)
            total_duration = video_info['duration']
            
            if verbose:
                print(f"Original duration: {total_duration:.2f} seconds")
                print(f"Codec: {video_info['codec']}")
            
            # Calculate trim parameters
            if from_start:
                start_time = duration
                end_time = total_duration
                trim_info = f"Trimming {duration} seconds from START"
            else:
                start_time = 0
                end_time = total_duration - duration
                trim_info = f"Trimming {duration} seconds from END"
                
            if end_time <= start_time:
                raise ValueError(f"Cannot trim {duration} seconds from {'start' if from_start else 'end'}. "
                               f"Video is only {total_duration:.2f} seconds long.")
            
            if verbose:
                print(f"{trim_info}")
                print(f"Resulting duration: {end_time - start_time:.2f} seconds")
                print(f"Time range: {start_time:.2f}s to {end_time:.2f}s")
            
            # Build FFmpeg command
            cmd = [self.ffmpeg_path]
            
            # Input seeking (more accurate than output seeking for stream copy)
            cmd.extend(['-ss', str(start_time)])
            cmd.extend(['-i', input_path])
            
            # Output settings
            if use_stream_copy:
                # Stream copy (no re-encoding) - much faster
                cmd.extend(['-c', 'copy'])
                
                # For stream copy, we need to specify duration differently
                # We can't use -t with stream copy easily, so we'll use a different approach
                if not from_start:  # Trimming from end
                    # For trimming from end, we can use -t with the calculated duration
                    cmd.extend(['-t', str(end_time - start_time)])
            else:
                # Re-encoding (slower but more flexible)
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
                cmd.extend(['-t', str(end_time - start_time)])
            
            # Output file
            cmd.append(output_path)
            
            # Suppress output unless verbose
            if not verbose:
                cmd.extend(['-loglevel', 'error'])
            
            if verbose:
                print(f"Running command: {' '.join(cmd)}")
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                raise RuntimeError(f"FFmpeg failed: {error_msg}")
                
            # Verify output file was created and has reasonable size
            if not os.path.exists(output_path):
                raise RuntimeError("Output file was not created")
                
            output_size = os.path.getsize(output_path)
            if output_size < 1024:  # Less than 1KB suggests an error
                raise RuntimeError("Output file is too small, operation may have failed")
                
            if verbose:
                print(f"Successfully saved to: {output_path}")
                print(f"Output file size: {output_size:,} bytes")
                
            return True
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg operation timed out")
        except Exception as e:
            # Clean up output file if it exists and is likely corrupted
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass
            raise e
    
    def trim_video_advanced(self, input_path, output_path, duration, from_start=True, 
                           verbose=False):
        """
        Advanced trimming with better stream copy support.
        This method handles keyframe boundaries better.
        """
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
            
        try:
            # Get video info
            video_info = self.get_video_info(input_path)
            total_duration = video_info['duration']
            
            # Calculate trim parameters
            if from_start:
                start_time = duration
                end_time = total_duration
            else:
                start_time = 0
                end_time = total_duration - duration
                
            if end_time <= start_time:
                raise ValueError(f"Cannot trim {duration} seconds from {'start' if from_start else 'end'}. "
                               f"Video is only {total_duration:.2f} seconds long.")
            
            # For trimming from start with stream copy, we need a two-pass approach
            if from_start and duration > 0:
                # First, create a temporary file with the trimmed portion
                # Sanitize the temp filename to avoid issues with special characters
                output_path_obj = Path(output_path)
                temp_filename = self._sanitize_filename(output_path_obj.stem + '_temp' + output_path_obj.suffix)
                temp_path = str(output_path_obj.parent / temp_filename)
                
                try:
                    # Extract the portion we want to keep
                    cmd = [
                        self.ffmpeg_path,
                        '-ss', str(start_time),
                        '-i', input_path,
                        '-c', 'copy',
                        '-avoid_negative_ts', 'make_zero',
                        temp_path
                    ]
                    
                    if not verbose:
                        cmd.extend(['-loglevel', 'error'])
                    
                    if verbose:
                        print(f"Extracting portion: {' '.join(cmd)}")
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode != 0:
                        raise RuntimeError(f"FFmpeg extraction failed: {result.stderr}")
                    
                    # Move temp file to final output
                    os.rename(temp_path, output_path)
                    
                except Exception:
                    # Clean up temp file on error
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise
                    
            else:
                # For trimming from end, we can use a simpler approach
                cmd = [
                    self.ffmpeg_path,
                    '-i', input_path,
                    '-c', 'copy',
                    '-t', str(end_time),
                    output_path
                ]
                
                if not verbose:
                    cmd.extend(['-loglevel', 'error'])
                
                if verbose:
                    print(f"Trimming from end: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    raise RuntimeError(f"FFmpeg trimming failed: {result.stderr}")
            
            # Verify output
            if not os.path.exists(output_path) or os.path.getsize(output_path) < 1024:
                raise RuntimeError("Output file is invalid or too small")
                
            return True
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg operation timed out")
        except Exception as e:
            # Clean up output file if it exists and is likely corrupted
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass
            raise e


def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS.ss format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.2f}"
    else:
        return f"{minutes:02d}:{secs:06.2f}"


# Example usage and testing
if __name__ == "__main__":
    trimmer = FFmpegTrimmer()
    
    if not trimmer.check_ffmpeg_available():
        print("ERROR: FFmpeg not found. Please install FFmpeg.")
        print("Visit https://ffmpeg.org/download.html for installation instructions.")
        sys.exit(1)
    
    print("FFmpeg-based Video Trimmer")
    print("=========================")
    print("This trimmer uses FFmpeg with stream copy for fast, lossless trimming.")
    print("It's much faster than re-encoding approaches for simple trimming operations.")
    print()
    print("Usage examples:")
    print("1. Trim 10 seconds from start:")
    print("   trimmer.trim_video('input.mp4', 'output.mp4', 10, from_start=True)")
    print()
    print("2. Trim 30 seconds from end:")
    print("   trimmer.trim_video('input.mp4', 'output.mp4', 30, from_start=False)")
    print()
    print("3. Get video info:")
    print("   info = trimmer.get_video_info('input.mp4')")
    print("   print(f'Duration: {format_duration(info[\"duration\"])}')")
