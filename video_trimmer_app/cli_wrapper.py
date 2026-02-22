#!/usr/bin/env python3
"""
Entry point wrapper for video-trimmer CLI
"""

def main():
    """Main entry point for video-trimmer command"""
    try:
        try:
            from .launch import main as launch_main
        except ImportError:
            # Fallback for direct script execution
            from launch import main as launch_main
        launch_main()
    except ImportError:
        print("Error: Video Trimmer package not properly installed")
        print("Please run: pip install -e . from the project directory")
        return 1

if __name__ == "__main__":
    exit(main())