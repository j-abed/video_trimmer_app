#!/usr/bin/env python3
"""
Video Trimmer CLI
Command-line interface for trimming video files (.mp4, .ts, etc.) from start or end.
Supports batch processing of multiple files.
"""

import argparse
import os
import sys
import re
from pathlib import Path
from moviepy import VideoFileClip
import time
from typing import Optional, List, Tuple, Union
from loguru import logger
try:
    from .ffmpeg_trimmer import FFmpegTrimmer
except ImportError:
    # Fallback for direct script execution
    from ffmpeg_trimmer import FFmpegTrimmer

# Constants
SUPPORTED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.ts', '.webm', '.flv']
DEFAULT_OUTPUT_SUFFIX = '_trimmed'
MAX_BATCH_SIZE = 100
MIN_DURATION = 0.1  # 100ms minimum
MAX_FILENAME_LENGTH = 200
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'


def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS.ss format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 0:
        return "00:00.00"
        
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.2f}"
    else:
        return f"{minutes:02d}:{secs:06.2f}"


def sanitize_filename(filename: str) -> str:
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
    
    # Limit length
    if len(sanitized) > MAX_FILENAME_LENGTH:
        name_part = sanitized[:MAX_FILENAME_LENGTH-10]
        ext_part = Path(sanitized).suffix
        sanitized = f"{name_part}...{ext_part}"
    
    return sanitized


def trim_video(
    input_path: str, 
    output_path: str, 
    duration: float, 
    from_start: bool = True, 
    verbose: bool = False, 
    use_ffmpeg: bool = True
) -> Tuple[bool, str]:
    """Trim a video file using either FFmpeg or MoviePy.
    
    Args:
        input_path: Path to input video file
        output_path: Path to output video file
        duration: Duration to trim in seconds
        from_start: If True, trim from start; if False, trim from end
        verbose: If True, print detailed information
        use_ffmpeg: If True, try to use FFmpeg first, fallback to MoviePy
        
    Returns:
        Tuple[bool, str]: (Success status, Error message or success info)
        bool: True if successful, False otherwise
    """
    try:
        if verbose:
            print(f"Loading video: {input_path}")
        
        # Sanitize output path to avoid filesystem issues
        output_path_obj = Path(output_path)
        sanitized_stem = sanitize_filename(output_path_obj.stem)
        output_path_sanitized = str(output_path_obj.parent / f"{sanitized_stem}{output_path_obj.suffix}")
        
        # Try FFmpeg first if requested and available
        if use_ffmpeg:
            ffmpeg_trimmer = FFmpegTrimmer()
            if ffmpeg_trimmer.check_ffmpeg_available():
                if verbose:
                    print("Using FFmpeg (stream copy - faster)")
                
                # Get video info first
                video_info = ffmpeg_trimmer.get_video_info(input_path)
                total_duration = video_info['duration']
                
                if verbose:
                    print(f"Original duration: {format_duration(total_duration)} ({total_duration:.2f} seconds)")
                    print(f"Codec: {video_info['codec']}")
                    
                    # Calculate trim parameters for preview
                    if from_start:
                        trim_info = f"Trimming {duration} seconds from START"
                    else:
                        trim_info = f"Trimming {duration} seconds from END"
                    print(f"{trim_info}")
                
                # Use FFmpeg for trimming
                ffmpeg_trimmer.trim_video_advanced(
                    input_path, output_path_sanitized, duration, from_start, verbose=verbose
                )
                
                if verbose:
                    print(f"Successfully saved to: {output_path_sanitized}")
                return True
            elif verbose:
                print("FFmpeg not available, falling back to MoviePy")
        
        # Fallback to MoviePy
        if verbose:
            print("Using MoviePy (re-encoding - slower)")
            
        # Load video
        video = VideoFileClip(input_path)
        total_duration = video.duration
        
        if verbose:
            print(f"Original duration: {format_duration(total_duration)} ({total_duration:.2f} seconds)")
            
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
            print(f"ERROR: Cannot trim {duration} seconds from {'start' if from_start else 'end'}.")
            print(f"Video duration is only {total_duration:.2f} seconds.")
            video.close()
            return False
            
        if verbose:
            print(f"{trim_info}")
            print(f"Resulting duration: {format_duration(end_time - start_time)} ({(end_time - start_time):.2f} seconds)")
            print(f"Time range: {format_duration(start_time)} to {format_duration(end_time)}")
            print(f"Processing...")
            
        # Trim video
        trimmed_video = video.subclipped(start_time, end_time)
        
        # Write output
        trimmed_video.write_videofile(
            output_path_sanitized,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Clean up
        trimmed_video.close()
        video.close()
        
        if verbose:
            print(f"Successfully saved to: {output_path_sanitized}")
            
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to trim video: {str(e)}")
        return False


def process_single_file(input_path, output_path, duration, from_start, verbose, use_ffmpeg=True):
    """Process a single video file."""
    if not os.path.exists(input_path):
        print(f"ERROR: Input file does not exist: {input_path}")
        return False
        
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    return trim_video(input_path, output_path, duration, from_start, verbose, use_ffmpeg)


def process_batch(input_dir, output_dir, duration, from_start, pattern, verbose, use_ffmpeg=True):
    """Process multiple video files in a directory."""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"ERROR: Input directory does not exist: {input_dir}")
        return False
        
    # Find video files
    video_extensions = ['.mp4', '.ts', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    video_files = []
    
    for ext in video_extensions:
        if pattern:
            video_files.extend(input_path.glob(f"*{pattern}*{ext}"))
        else:
            video_files.extend(input_path.glob(f"*{ext}"))
            
    if not video_files:
        print(f"ERROR: No video files found in {input_dir}")
        return False
        
    print(f"Found {len(video_files)} video file(s) to process")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_count = len(video_files)
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{total_count}] Processing: {video_file.name}")
        
        # Generate output filename (sanitize to avoid special characters)
        sanitized_stem = sanitize_filename(video_file.stem)
        output_filename = f"{sanitized_stem}_trimmed{video_file.suffix}"
        output_file_path = output_path / output_filename
        
        if process_single_file(str(video_file), str(output_file_path), duration, from_start, verbose, use_ffmpeg):
            success_count += 1
        else:
            print(f"Failed to process: {video_file.name}")
            
    print(f"\nBatch processing complete: {success_count}/{total_count} files processed successfully")
    return success_count == total_count


def main():
    """Main function for CLI."""
    parser = argparse.ArgumentParser(
        description="Trim video files from start or end",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Trim 10 seconds from start of a single file (uses FFmpeg if available)
  python video_trimmer_cli.py input.mp4 output.mp4 --duration 10 --from-start
  
  # Trim 30 seconds from end of a single file
  python video_trimmer_cli.py input.mp4 output.mp4 --duration 30 --from-end
  
  # Force use of MoviePy instead of FFmpeg
  python video_trimmer_cli.py input.mp4 output.mp4 --duration 10 --from-start --no-ffmpeg
  
  # Batch process all MP4 files in a directory
  python video_trimmer_cli.py --batch input_dir/ output_dir/ --duration 15 --from-start
  
  # Batch process with pattern matching and verbose output
  python video_trimmer_cli.py --batch input_dir/ output_dir/ --duration 20 --from-end --pattern "episode" --verbose
        """
    )
    
    # Input/Output arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('input_file', nargs='?', help='Input video file (for single file mode)')
    group.add_argument('--batch', nargs=2, metavar=('INPUT_DIR', 'OUTPUT_DIR'),
                      help='Batch process all videos in INPUT_DIR and save to OUTPUT_DIR')
    
    parser.add_argument('output_file', nargs='?', help='Output video file (for single file mode)')
    
    # Trim options
    parser.add_argument('--duration', '-d', type=float, required=True,
                       help='Duration to trim in seconds')
    parser.add_argument('--from-start', action='store_true', default=True,
                       help='Trim from start of video (default)')
    parser.add_argument('--from-end', action='store_true',
                       help='Trim from end of video')
    
    # Batch options
    parser.add_argument('--pattern', '-p', help='Pattern to match in filenames (for batch mode)')
    
    # General options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--no-ffmpeg', action='store_true',
                       help='Force use of MoviePy instead of FFmpeg')
    
    args = parser.parse_args()
    
    # Determine trim direction and engine
    from_start = args.from_start and not args.from_end
    use_ffmpeg = not args.no_ffmpeg
    
    if args.batch:
        # Batch processing mode
        input_dir, output_dir = args.batch
        success = process_batch(input_dir, output_dir, args.duration, from_start, 
                              args.pattern, args.verbose, use_ffmpeg)
        sys.exit(0 if success else 1)
    else:
        # Single file mode
        if not args.output_file:
            print("ERROR: Output file is required for single file mode")
            sys.exit(1)
            
        success = process_single_file(args.input_file, args.output_file, 
                                    args.duration, from_start, args.verbose, use_ffmpeg)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
