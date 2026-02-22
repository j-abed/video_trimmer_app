#!/usr/bin/env python3
"""
Enhanced FFmpeg Trimmer with Advanced Features
Extended version with hardware acceleration, quality presets, and advanced filtering.
"""

import subprocess
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union, Set
from loguru import logger
import psutil
import shutil

# Constants
DEFAULT_FFMPEG_TIMEOUT = 300  # 5 minutes
MAX_PROBE_RETRIES = 3
SUPPORTED_CODECS = {
    'video': ['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc'],
    'audio': ['aac', 'mp3', 'ac3', 'libopus']
}
HARDWARE_ENCODERS = {
    'nvidia': ['h264_nvenc', 'hevc_nvenc'],
    'intel': ['h264_qsv', 'hevc_qsv'],
    'amd': ['h264_amf', 'hevc_amf']
}
QUALITY_PRESETS = {
    'original': {},  # No re-encoding (stream copy)
    'high': {
        'video_codec': 'libx264',
        'video_bitrate': '8000k',
        'audio_codec': 'aac',
        'audio_bitrate': '192k',
        'preset': 'slow',
        'crf': '18'
    },
    'medium': {
        'video_codec': 'libx264',
        'video_bitrate': '4000k',
        'audio_codec': 'aac',
        'audio_bitrate': '128k',
        'preset': 'medium',
        'crf': '23'
    },
    'low': {
        'video_codec': 'libx264',
        'video_bitrate': '1500k',
        'audio_codec': 'aac',
        'audio_bitrate': '96k',
        'preset': 'fast',
        'crf': '28'
    }
}


class AdvancedFFmpegTrimmer:
    """Advanced FFmpeg-based video trimmer with enhanced features.
    
    Provides hardware acceleration, quality presets, progress tracking,
    and advanced video processing capabilities.
    
    Attributes:
        ffmpeg_path: Path to FFmpeg executable
        ffprobe_path: Path to FFprobe executable
        hardware_info: Detected hardware capabilities
        quality_presets: Available quality presets
    """
    
    def __init__(self):
        """Initialize advanced FFmpeg trimmer with hardware detection."""
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()
        self.hardware_info = self._detect_hardware()
        self.quality_presets = QUALITY_PRESETS.copy()
        
        # Validate FFmpeg installation
        if not self.ffmpeg_path or not self.ffprobe_path:
            logger.warning("FFmpeg not found - some features may be limited")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable."""
        possible_paths = [
            'ffmpeg',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            'C:\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        return None
    
    def _find_ffprobe(self) -> Optional[str]:
        """Find FFprobe executable."""
        if not self.ffmpeg_path:
            return None
        
        # Try to find ffprobe in the same directory as ffmpeg
        ffmpeg_dir = Path(self.ffmpeg_path).parent
        ffprobe_name = 'ffprobe.exe' if os.name == 'nt' else 'ffprobe'
        ffprobe_path = ffmpeg_dir / ffprobe_name
        
        if ffprobe_path.exists():
            return str(ffprobe_path)
        
        # Try standalone ffprobe
        try:
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'ffprobe'
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return None
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """Detect available hardware acceleration."""
        hardware_info = {
            'cuda': False,
            'videotoolbox': False,  # macOS
            'vaapi': False,  # Linux
            'dxva2': False,  # Windows
            'cpu_cores': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3))
        }
        
        if not self.ffmpeg_path:
            return hardware_info
        
        try:
            # Get FFmpeg encoders and decoders
            result = subprocess.run([self.ffmpeg_path, '-encoders'], 
                                  capture_output=True, text=True, timeout=10)
            encoders = result.stdout
            
            result = subprocess.run([self.ffmpeg_path, '-decoders'], 
                                  capture_output=True, text=True, timeout=10)
            decoders = result.stdout
            
            # Check for hardware acceleration support
            if 'h264_nvenc' in encoders or 'h264_cuda' in decoders:
                hardware_info['cuda'] = True
            
            if 'videotoolbox' in encoders or 'videotoolbox' in decoders:
                hardware_info['videotoolbox'] = True
            
            if 'vaapi' in encoders or 'vaapi' in decoders:
                hardware_info['vaapi'] = True
                
            if 'dxva2' in decoders:
                hardware_info['dxva2'] = True
            
        except Exception as e:
            logger.warning(f"Failed to detect hardware acceleration: {e}")
        
        return hardware_info
    
    def get_detailed_video_info(self, input_path: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive video information using ffprobe."""
        if not self.ffprobe_path or not os.path.exists(input_path):
            return None
        
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"FFprobe failed: {result.stderr}")
                return None
            
            probe_data = json.loads(result.stdout)
            
            # Extract relevant information
            format_info = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)
            audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), None)
            
            if not video_stream:
                return None
            
            info = {
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', ''),
                'video': {
                    'codec': video_stream.get('codec_name', ''),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')),
                    'bitrate': int(video_stream.get('bit_rate', 0)),
                    'pixel_format': video_stream.get('pix_fmt', ''),
                    'color_space': video_stream.get('color_space', ''),
                },
                'audio': None
            }
            
            if audio_stream:
                info['audio'] = {
                    'codec': audio_stream.get('codec_name', ''),
                    'sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'channels': int(audio_stream.get('channels', 0)),
                    'bitrate': int(audio_stream.get('bit_rate', 0)),
                }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    def _parse_fps(self, fps_string: str) -> float:
        """Parse FPS from fraction string."""
        try:
            if '/' in fps_string:
                num, den = fps_string.split('/')
                return float(num) / float(den)
            return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def trim_video_advanced(self, input_path: str, output_path: str, 
                           trim_duration: float, from_start: bool = True,
                           quality: str = 'original', 
                           hardware_accel: bool = True,
                           filters: Optional[List[str]] = None,
                           custom_options: Optional[Dict[str, str]] = None,
                           progress_callback: Optional[callable] = None) -> bool:
        """Advanced video trimming with quality control and hardware acceleration."""
        
        if not self.ffmpeg_path or not os.path.exists(input_path):
            return False
        
        try:
            # Get video info for validation
            video_info = self.get_detailed_video_info(input_path)
            if not video_info:
                logger.error("Failed to analyze input video")
                return False
            
            total_duration = video_info['duration']
            
            # Calculate trim parameters
            if from_start:
                start_time = trim_duration
                end_duration = total_duration - trim_duration
            else:
                start_time = 0
                end_duration = total_duration - trim_duration
            
            if end_duration <= 0:
                logger.error("Invalid trim duration: resulting video would be empty")
                return False
            
            # Build FFmpeg command
            cmd = [self.ffmpeg_path]
            
            # Add hardware acceleration if available and requested
            if hardware_accel and quality != 'original':
                if self.hardware_info.get('cuda'):
                    cmd.extend(['-hwaccel', 'cuda'])
                elif self.hardware_info.get('videotoolbox'):
                    cmd.extend(['-hwaccel', 'videotoolbox'])
                elif self.hardware_info.get('vaapi'):
                    cmd.extend(['-hwaccel', 'vaapi'])
            
            # Add input
            cmd.extend(['-i', input_path])
            
            # Add seek (trim start)
            if start_time > 0:
                cmd.extend(['-ss', str(start_time)])
            
            # Add duration limit
            cmd.extend(['-t', str(end_duration)])
            
            # Apply quality settings
            quality_settings = self.quality_presets.get(quality, {})
            
            if quality == 'original':
                # Stream copy - no re-encoding
                cmd.extend(['-c', 'copy'])
            else:
                # Re-encode with quality settings
                if 'video_codec' in quality_settings:
                    cmd.extend(['-c:v', quality_settings['video_codec']])
                
                if 'audio_codec' in quality_settings:
                    cmd.extend(['-c:a', quality_settings['audio_codec']])
                
                if 'video_bitrate' in quality_settings:
                    cmd.extend(['-b:v', quality_settings['video_bitrate']])
                
                if 'audio_bitrate' in quality_settings:
                    cmd.extend(['-b:a', quality_settings['audio_bitrate']])
                
                if 'preset' in quality_settings:
                    cmd.extend(['-preset', quality_settings['preset']])
                
                if 'crf' in quality_settings:
                    cmd.extend(['-crf', quality_settings['crf']])
            
            # Add video filters if specified
            if filters:
                filter_string = ','.join(filters)
                cmd.extend(['-vf', filter_string])
            
            # Add custom options
            if custom_options:
                for key, value in custom_options.items():
                    cmd.extend([f'-{key}', value])
            
            # Output settings
            cmd.extend(['-y'])  # Overwrite output file
            cmd.append(output_path)
            
            # Execute command
            logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")
            
            if progress_callback:
                return self._run_with_progress(cmd, total_duration, progress_callback)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg error: {result.stderr}")
                    return False
                
                logger.info(f"Successfully trimmed video: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error in advanced trim: {e}")
            return False
    
    def _run_with_progress(self, cmd: List[str], total_duration: float, 
                          progress_callback: callable) -> bool:
        """Run FFmpeg command with progress tracking."""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read stderr for progress information
            progress_pattern = re.compile(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
            
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    # Parse progress
                    match = progress_pattern.search(output)
                    if match:
                        hours, minutes, seconds, centiseconds = match.groups()
                        current_time = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
                        
                        if total_duration > 0:
                            progress = min((current_time / total_duration) * 100, 100)
                            progress_callback(progress)
            
            # Wait for completion
            process.wait()
            
            if process.returncode != 0:
                error_output = process.stderr.read()
                logger.error(f"FFmpeg error: {error_output}")
                return False
            
            # Final progress update
            progress_callback(100.0)
            return True
            
        except Exception as e:
            logger.error(f"Error running FFmpeg with progress: {e}")
            return False
    
    def apply_video_filters(self, input_path: str, output_path: str, 
                           filters: List[str], quality: str = 'medium') -> bool:
        """Apply video filters to input video."""
        if not self.ffmpeg_path or not os.path.exists(input_path):
            return False
        
        try:
            cmd = [self.ffmpeg_path, '-i', input_path]
            
            # Add quality settings
            quality_settings = self.quality_presets.get(quality, {})
            for key, value in quality_settings.items():
                if key == 'video_codec':
                    cmd.extend(['-c:v', value])
                elif key == 'audio_codec':
                    cmd.extend(['-c:a', value])
                elif key == 'video_bitrate':
                    cmd.extend(['-b:v', value])
                elif key == 'audio_bitrate':
                    cmd.extend(['-b:a', value])
                elif key in ['preset', 'crf']:
                    cmd.extend([f'-{key}', value])
            
            # Add filters
            filter_string = ','.join(filters)
            cmd.extend(['-vf', filter_string])
            
            cmd.extend(['-y', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode != 0:
                logger.error(f"Filter application failed: {result.stderr}")
                return False
            
            logger.info(f"Successfully applied filters to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return False
    
    def extract_audio(self, input_path: str, output_path: str, 
                     format: str = 'mp3', quality: str = 'medium') -> bool:
        """Extract audio from video."""
        if not self.ffmpeg_path or not os.path.exists(input_path):
            return False
        
        try:
            cmd = [self.ffmpeg_path, '-i', input_path]
            
            # Audio-only extraction
            cmd.extend(['-vn'])  # No video
            
            # Set audio format and quality
            if format == 'mp3':
                cmd.extend(['-acodec', 'mp3'])
                if quality == 'high':
                    cmd.extend(['-ab', '320k'])
                elif quality == 'medium':
                    cmd.extend(['-ab', '192k'])
                else:
                    cmd.extend(['-ab', '128k'])
            elif format == 'wav':
                cmd.extend(['-acodec', 'pcm_s16le'])
            elif format == 'aac':
                cmd.extend(['-acodec', 'aac'])
                cmd.extend(['-ab', '192k' if quality == 'medium' else '128k'])
            
            cmd.extend(['-y', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode != 0:
                logger.error(f"Audio extraction failed: {result.stderr}")
                return False
            
            logger.info(f"Successfully extracted audio to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return False
    
    def create_thumbnail_grid(self, input_path: str, output_path: str, 
                             grid_size: Tuple[int, int] = (4, 3), 
                             thumbnail_size: Tuple[int, int] = (160, 90)) -> bool:
        """Create thumbnail grid from video."""
        if not self.ffmpeg_path or not os.path.exists(input_path):
            return False
        
        try:
            cols, rows = grid_size
            thumb_width, thumb_height = thumbnail_size
            total_thumbs = cols * rows
            
            # Get video duration
            video_info = self.get_detailed_video_info(input_path)
            if not video_info:
                return False
            
            duration = video_info['duration']
            
            # Generate thumbnail timestamps
            timestamps = []
            for i in range(total_thumbs):
                time_pos = (i + 1) * duration / (total_thumbs + 1)
                timestamps.append(time_pos)
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', f'fps=1/{duration/total_thumbs},scale={thumb_width}:{thumb_height},tile={cols}x{rows}',
                '-frames:v', '1',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"Thumbnail grid creation failed: {result.stderr}")
                return False
            
            logger.info(f"Successfully created thumbnail grid: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating thumbnail grid: {e}")
            return False
    
    def check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available."""
        return self.ffmpeg_path is not None
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported input formats."""
        if not self.ffmpeg_path:
            return []
        
        try:
            result = subprocess.run([self.ffmpeg_path, '-formats'], 
                                  capture_output=True, text=True, timeout=10)
            
            formats = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                if 'DE' in line[:10]:  # Demuxer and encoder support
                    parts = line.split()
                    if len(parts) >= 2:
                        format_name = parts[1]
                        formats.append(format_name)
            
            return formats
            
        except Exception as e:
            logger.error(f"Error getting supported formats: {e}")
            return []
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get detected hardware information."""
        return self.hardware_info.copy()
    
    # Helper methods
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable in system PATH.
        
        Returns:
            str: Path to FFmpeg executable or None if not found
        """
        ffmpeg_names = ['ffmpeg', 'ffmpeg.exe']
        
        for name in ffmpeg_names:
            path = shutil.which(name)
            if path:
                logger.debug(f"Found FFmpeg at: {path}")
                return path
        
        # Try common installation paths
        common_paths = [
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            '/usr/bin/ffmpeg',
            'C:\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.debug(f"Found FFmpeg at: {path}")
                return path
        
        logger.warning("FFmpeg not found in system PATH or common locations")
        return None
    
    def _find_ffprobe(self) -> Optional[str]:
        """Find FFprobe executable in system PATH.
        
        Returns:
            str: Path to FFprobe executable or None if not found
        """
        ffprobe_names = ['ffprobe', 'ffprobe.exe']
        
        for name in ffprobe_names:
            path = shutil.which(name)
            if path:
                logger.debug(f"Found FFprobe at: {path}")
                return path
        
        # Try common installation paths
        common_paths = [
            '/usr/local/bin/ffprobe',
            '/opt/homebrew/bin/ffprobe',
            '/usr/bin/ffprobe',
            'C:\\ffmpeg\\bin\\ffprobe.exe',
            'C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.debug(f"Found FFprobe at: {path}")
                return path
        
        logger.warning("FFprobe not found in system PATH or common locations")
        return None
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """Detect available hardware acceleration.
        
        Returns:
            Dict containing hardware capabilities
        """
        hardware_info = {
            'nvidia_available': False,
            'intel_qsv_available': False,
            'amd_available': False,
            'supported_encoders': [],
            'gpu_memory': None
        }
        
        if not self.ffmpeg_path:
            return hardware_info
        
        try:
            # Check available encoders
            result = subprocess.run(
                [self.ffmpeg_path, '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            encoder_output = result.stdout.lower()
            
            # Check for NVIDIA encoders
            nvidia_encoders = ['h264_nvenc', 'hevc_nvenc']
            for encoder in nvidia_encoders:
                if encoder in encoder_output:
                    hardware_info['nvidia_available'] = True
                    hardware_info['supported_encoders'].append(encoder)
            
            # Check for Intel QSV encoders
            intel_encoders = ['h264_qsv', 'hevc_qsv']
            for encoder in intel_encoders:
                if encoder in encoder_output:
                    hardware_info['intel_qsv_available'] = True
                    hardware_info['supported_encoders'].append(encoder)
            
            # Check for AMD encoders
            amd_encoders = ['h264_amf', 'hevc_amf']
            for encoder in amd_encoders:
                if encoder in encoder_output:
                    hardware_info['amd_available'] = True
                    hardware_info['supported_encoders'].append(encoder)
            
            logger.debug(f"Hardware detection completed: {hardware_info}")
            
        except (subprocess.SubprocessError, OSError) as e:
            logger.error(f"Error detecting hardware: {e}")
        
        return hardware_info
    
    def _validate_input_file(self, input_path: str) -> bool:
        """Validate input video file.
        
        Args:
            input_path: Path to input video file
            
        Returns:
            bool: True if file is valid
        """
        if not input_path:
            logger.error("Input path is empty")
            return False
        
        path = Path(input_path)
        if not path.exists():
            logger.error(f"Input file does not exist: {input_path}")
            return False
        
        if not path.is_file():
            logger.error(f"Input path is not a file: {input_path}")
            return False
        
        # Check file extension
        supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.ts']
        if path.suffix.lower() not in supported_extensions:
            logger.warning(f"Potentially unsupported file format: {path.suffix}")
        
        return True
    
    def _prepare_output_directory(self, output_path: str) -> bool:
        """Ensure output directory exists.
        
        Args:
            output_path: Path to output file
            
        Returns:
            bool: True if directory is ready
        """
        output_dir = Path(output_path).parent
        
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            return True
        except OSError as e:
            logger.error(f"Error creating output directory: {e}")
            return False