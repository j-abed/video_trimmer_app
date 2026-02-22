#!/usr/bin/env python3
"""
Test script to demonstrate the efficiency difference between FFmpeg and MoviePy trimming.
This script shows the time difference when trimming videos using different methods.
"""

import time
import os
from pathlib import Path
try:
    from .ffmpeg_trimmer import FFmpegTrimmer
except ImportError:
    # Fallback for direct script execution
    from ffmpeg_trimmer import FFmpegTrimmer
from moviepy import VideoFileClip


def test_trimming_efficiency(input_file, output_dir="test_outputs"):
    """
    Test trimming efficiency using both FFmpeg and MoviePy.
    """
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        return
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Test parameters
    duration = 10  # Trim 10 seconds from start
    from_start = True
    
    print(f"Testing trimming efficiency with file: {input_file}")
    print(f"Trimming {duration} seconds from {'start' if from_start else 'end'}")
    print("=" * 60)
    
    # Test FFmpeg (if available)
    ffmpeg_trimmer = FFmpegTrimmer()
    if ffmpeg_trimmer.check_ffmpeg_available():
        print("Testing FFmpeg (stream copy)...")
        start_time = time.time()
        
        try:
            ffmpeg_output = output_path / "ffmpeg_trimmed.mp4"
            ffmpeg_trimmer.trim_video_advanced(
                input_file, str(ffmpeg_output), duration, from_start, verbose=False
            )
            
            ffmpeg_time = time.time() - start_time
            ffmpeg_size = os.path.getsize(ffmpeg_output)
            
            print(f"✓ FFmpeg completed in {ffmpeg_time:.2f} seconds")
            print(f"  Output file size: {ffmpeg_size:,} bytes")
            
        except Exception as e:
            print(f"✗ FFmpeg failed: {str(e)}")
            ffmpeg_time = None
            ffmpeg_size = None
    else:
        print("✗ FFmpeg not available")
        ffmpeg_time = None
        ffmpeg_size = None
    
    print()
    
    # Test MoviePy
    print("Testing MoviePy (re-encoding)...")
    start_time = time.time()
    
    try:
        moviepy_output = output_path / "moviepy_trimmed.mp4"
        
        # Load video
        video = VideoFileClip(input_file)
        total_duration = video.duration
        
        # Calculate trim parameters
        if from_start:
            start_time_trim = duration
            end_time = total_duration
        else:
            start_time_trim = 0
            end_time = total_duration - duration
            
        # Trim video
        trimmed_video = video.subclipped(start_time_trim, end_time)
        
        # Write output
        trimmed_video.write_videofile(
            str(moviepy_output),
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # Clean up
        trimmed_video.close()
        video.close()
        
        moviepy_time = time.time() - start_time
        moviepy_size = os.path.getsize(moviepy_output)
        
        print(f"✓ MoviePy completed in {moviepy_time:.2f} seconds")
        print(f"  Output file size: {moviepy_size:,} bytes")
        
    except Exception as e:
        print(f"✗ MoviePy failed: {str(e)}")
        moviepy_time = None
        moviepy_size = None
    
    print()
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    if ffmpeg_time and moviepy_time:
        speedup = moviepy_time / ffmpeg_time
        print(f"FFmpeg time:     {ffmpeg_time:.2f} seconds")
        print(f"MoviePy time:    {moviepy_time:.2f} seconds")
        print(f"Speedup factor:  {speedup:.1f}x faster with FFmpeg")
        
        if ffmpeg_size and moviepy_size:
            size_diff = abs(ffmpeg_size - moviepy_size)
            size_diff_pct = (size_diff / max(ffmpeg_size, moviepy_size)) * 100
            print(f"Size difference: {size_diff:,} bytes ({size_diff_pct:.1f}%)")
            
    elif ffmpeg_time:
        print(f"FFmpeg time:     {ffmpeg_time:.2f} seconds")
        print("MoviePy:         Failed")
    elif moviepy_time:
        print("FFmpeg:          Not available")
        print(f"MoviePy time:    {moviepy_time:.2f} seconds")
    else:
        print("Both methods failed or unavailable")
    
    print()
    print("Note: FFmpeg uses stream copy (no re-encoding) which is much faster")
    print("      MoviePy re-encodes the entire video which is slower but more flexible")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python test_efficiency.py <input_video_file>")
        print("Example: python test_efficiency.py sample.mp4")
        sys.exit(1)
    
    input_file = sys.argv[1]
    test_trimming_efficiency(input_file)
