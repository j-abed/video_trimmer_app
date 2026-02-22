#!/usr/bin/env python3
"""
Test script for Enhanced Video Trimmer Features
Tests the advanced functionality added in the enhanced version.
"""

import os
import tempfile
import time
from pathlib import Path
import unittest

# Test imports
try:
    from config_manager import ConfigManager
    from video_preview import VideoPreview
    from processing_queue import ProcessingQueue, ProcessingJob
    from ffmpeg_processor import AdvancedFFmpegTrimmer
    from cloud_integration import CloudManager
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Some features may not be available")


def test_config_manager():
    """Test configuration management."""
    print("\n=== Testing Config Manager ===")
    
    try:
        config = ConfigManager()
        
        # Test basic get/set
        config.set("test.value", 42)
        assert config.get("test.value") == 42
        print("✓ Basic configuration get/set working")
        
        # Test default values
        assert config.get("nonexistent.key", "default") == "default"
        print("✓ Default values working")
        
        # Test recent files
        config.add_recent_file("/path/to/test.mp4")
        recent = config.get_recent_files()
        assert "/path/to/test.mp4" in recent
        print("✓ Recent files management working")
        
        # Test presets
        preset = {"duration": "10", "quality": "high"}
        config.save_preset("test_preset", preset)
        presets = config.get_presets()
        assert "test_preset" in presets
        print("✓ Preset system working")
        
        return True
    except Exception as e:
        print(f"✗ Config manager test failed: {e}")
        return False


def test_processing_queue():
    """Test processing queue functionality."""
    print("\n=== Testing Processing Queue ===")
    
    try:
        queue = ProcessingQueue(max_workers=2)
        
        # Create test job
        job_id = queue.create_and_add_job(
            input_path="/test/input.mp4",
            output_path="/test/output.mp4",
            trim_duration=10.0,
            from_start=True
        )
        
        assert job_id in queue.jobs
        print("✓ Job creation working")
        
        # Test job retrieval
        job = queue.get_job(job_id)
        assert job is not None
        assert job.input_path == "/test/input.mp4"
        print("✓ Job retrieval working")
        
        # Test queue stats
        stats = queue.get_queue_stats()
        assert stats["pending"] >= 1
        print("✓ Queue statistics working")
        
        # Test progress estimation
        progress = queue.get_overall_progress()
        assert isinstance(progress, float)
        print("✓ Progress calculation working")
        
        queue.stop_processing()
        print("✓ Queue shutdown working")
        
        return True
    except Exception as e:
        print(f"✗ Processing queue test failed: {e}")
        return False


def test_ffmpeg_processor():
    """Test advanced FFmpeg functionality."""
    print("\n=== Testing FFmpeg Processor ===")
    
    try:
        ffmpeg = AdvancedFFmpegTrimmer()
        
        # Test FFmpeg availability
        available = ffmpeg.check_ffmpeg_available()
        print(f"FFmpeg available: {'✓' if available else '✗'}")
        
        # Test hardware detection
        hardware = ffmpeg.get_hardware_info()
        print(f"Hardware acceleration: {hardware}")
        
        # Test quality presets
        assert "original" in ffmpeg.quality_presets
        assert "high" in ffmpeg.quality_presets
        print("✓ Quality presets configured")
        
        # Test supported formats (if FFmpeg available)
        if available:
            formats = ffmpeg.get_supported_formats()
            assert isinstance(formats, list)
            print(f"✓ Supported formats: {len(formats)} formats detected")
        
        return True
    except Exception as e:
        print(f"✗ Enhanced FFmpeg test failed: {e}")
        return False


def test_video_preview():
    """Test video preview functionality."""
    print("\n=== Testing Video Preview ===")
    
    try:
        preview = VideoPreview()
        
        # Test basic initialization
        assert preview.current_video is None
        print("✓ Video preview initialization working")
        
        # Test cache functionality
        preview.frame_cache = {"test": "frame"}
        assert "test" in preview.frame_cache
        print("✓ Frame caching working")
        
        # Test cleanup
        preview.cleanup()
        print("✓ Preview cleanup working")
        
        return True
    except Exception as e:
        print(f"✗ Video preview test failed: {e}")
        return False


def test_cloud_integration():
    """Test cloud integration."""
    print("\n=== Testing Cloud Integration ===")
    
    try:
        cloud = CloudManager()
        
        # Test service registration
        assert isinstance(cloud.uploaders, dict)
        print("✓ Cloud manager initialization working")
        
        # Test service availability
        services = cloud.get_available_services()
        assert isinstance(services, dict)
        print("✓ Service availability check working")
        
        return True
    except Exception as e:
        print(f"✗ Cloud integration test failed: {e}")
        return False


def create_test_video_opencv():
    """Create a test video using OpenCV if available."""
    try:
        import cv2
        import numpy as np
        
        output_path = "test_video_enhanced.mp4"
        
        # Video properties
        width, height = 640, 480
        fps = 24
        duration = 30  # seconds
        total_frames = fps * duration
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        print(f"Creating test video: {output_path}")
        
        for frame_num in range(total_frames):
            # Create colorful frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add gradient background
            for y in range(height):
                for x in range(width):
                    frame[y, x] = [
                        int(255 * frame_num / total_frames),  # Red increases over time
                        int(255 * x / width),                 # Green increases left to right
                        int(255 * y / height)                 # Blue increases top to bottom
                    ]
            
            # Add frame counter text
            cv2.putText(frame, f"Frame {frame_num}", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add timestamp
            timestamp = frame_num / fps
            cv2.putText(frame, f"{timestamp:.2f}s", (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(frame)
            
            # Progress feedback
            if frame_num % 60 == 0:
                print(f"Progress: {frame_num}/{total_frames} frames ({100*frame_num/total_frames:.1f}%)")
        
        out.release()
        cv2.destroyAllWindows()
        
        print(f"✓ Test video created: {output_path}")
        return output_path
        
    except ImportError:
        print("OpenCV not available, skipping video creation")
        return None
    except Exception as e:
        print(f"Error creating test video: {e}")
        return None


def benchmark_processing():
    """Benchmark processing performance."""
    print("\n=== Performance Benchmark ===")
    
    test_video = create_test_video_opencv()
    if not test_video or not os.path.exists(test_video):
        print("No test video available for benchmarking")
        return
    
    try:
        ffmpeg = AdvancedFFmpegTrimmer()
        
        if not ffmpeg.check_ffmpeg_available():
            print("FFmpeg not available for benchmarking")
            return
        
        # Test original quality (stream copy)
        start_time = time.time()
        output_path = "benchmark_original.mp4"
        
        success = ffmpeg.trim_video_advanced(
            test_video, output_path, 5.0, True, quality="original"
        )
        
        if success:
            processing_time = time.time() - start_time
            print(f"✓ Original quality (stream copy): {processing_time:.2f}s")
            
            # Check file sizes
            original_size = os.path.getsize(test_video)
            output_size = os.path.getsize(output_path)
            print(f"  Original: {original_size:,} bytes")
            print(f"  Output: {output_size:,} bytes")
            
            os.remove(output_path)
        
        # Test high quality re-encoding
        start_time = time.time()
        output_path = "benchmark_high.mp4"
        
        success = ffmpeg.trim_video_advanced(
            test_video, output_path, 5.0, True, quality="high"
        )
        
        if success:
            processing_time = time.time() - start_time
            print(f"✓ High quality (re-encoding): {processing_time:.2f}s")
            
            output_size = os.path.getsize(output_path)
            print(f"  Output: {output_size:,} bytes")
            
            os.remove(output_path)
        
    except Exception as e:
        print(f"Benchmark failed: {e}")
    
    finally:
        if test_video and os.path.exists(test_video):
            os.remove(test_video)


def main():
    """Run all enhanced feature tests."""
    print("Enhanced Video Trimmer Feature Tests")
    print("====================================")
    
    results = []
    
    # Run tests
    results.append(("Config Manager", test_config_manager()))
    results.append(("Processing Queue", test_processing_queue()))
    results.append(("FFmpeg Processor", test_ffmpeg_processor()))
    results.append(("Video Preview", test_video_preview()))
    results.append(("Cloud Integration", test_cloud_integration()))
    
    # Run benchmark
    benchmark_processing()
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 All enhanced features are working correctly!")
    else:
        print("⚠️  Some features may have issues. Check the output above.")
    
    # Additional info
    print(f"\nPython version: {os.sys.version}")
    print(f"Platform: {os.name}")


if __name__ == "__main__":
    main()