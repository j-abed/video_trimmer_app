#!/usr/bin/env python3
"""
Test script for Video Trimmer Application
Creates a simple test video and tests the trimming functionality.
"""

import os
import tempfile
from moviepy import VideoFileClip, ColorClip, CompositeVideoClip, TextClip
import time


def create_test_video(duration=30, output_path="test_video.mp4"):
    """Create a simple test video with colored background."""
    print(f"Creating test video: {output_path} (duration: {duration} seconds)")
    
    # Create a colored background
    video = ColorClip(size=(640, 480), color=(100, 150, 200), duration=duration)
    video.fps = 24
    
    # Write video file
    video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac'
    )
    
    video.close()
    print(f"Test video created successfully: {output_path}")
    return output_path


def test_trim_functionality():
    """Test the core trimming functionality."""
    print("Testing Video Trimmer functionality...")
    
    # Create test video
    test_video = create_test_video(duration=30)
    
    try:
        # Test 1: Trim from start
        print("\nTest 1: Trimming 10 seconds from start")
        from video_trimmer_cli import trim_video
        
        success = trim_video(
            test_video, 
            "test_trimmed_start.mp4", 
            duration=10, 
            from_start=True, 
            verbose=True
        )
        
        if success:
            print("✓ Test 1 passed: Trim from start successful")
        else:
            print("✗ Test 1 failed: Trim from start failed")
            
        # Test 2: Trim from end
        print("\nTest 2: Trimming 5 seconds from end")
        success = trim_video(
            test_video, 
            "test_trimmed_end.mp4", 
            duration=5, 
            from_start=False, 
            verbose=True
        )
        
        if success:
            print("✓ Test 2 passed: Trim from end successful")
        else:
            print("✗ Test 2 failed: Trim from end failed")
            
        # Test 3: Verify output files exist and have correct duration
        print("\nTest 3: Verifying output files")
        
        # Check trimmed from start
        if os.path.exists("test_trimmed_start.mp4"):
            video = VideoFileClip("test_trimmed_start.mp4")
            duration = video.duration
            video.close()
            expected_duration = 20  # 30 - 10
            if abs(duration - expected_duration) < 1:  # Allow 1 second tolerance
                print(f"✓ Trim from start: Duration {duration:.2f}s (expected ~{expected_duration}s)")
            else:
                print(f"✗ Trim from start: Duration {duration:.2f}s (expected ~{expected_duration}s)")
        else:
            print("✗ Trim from start: Output file not found")
            
        # Check trimmed from end
        if os.path.exists("test_trimmed_end.mp4"):
            video = VideoFileClip("test_trimmed_end.mp4")
            duration = video.duration
            video.close()
            expected_duration = 25  # 30 - 5
            if abs(duration - expected_duration) < 1:  # Allow 1 second tolerance
                print(f"✓ Trim from end: Duration {duration:.2f}s (expected ~{expected_duration}s)")
            else:
                print(f"✗ Trim from end: Duration {duration:.2f}s (expected ~{expected_duration}s)")
        else:
            print("✗ Trim from end: Output file not found")
            
        print("\nAll tests completed!")
        
    except Exception as e:
        print(f"✗ Test failed with error: {str(e)}")
        
    finally:
        # Clean up test files
        cleanup_files = [
            "test_video.mp4",
            "test_trimmed_start.mp4", 
            "test_trimmed_end.mp4"
        ]
        
        for file in cleanup_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"Cleaned up: {file}")


if __name__ == "__main__":
    test_trim_functionality()
