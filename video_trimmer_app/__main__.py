#!/usr/bin/env python3
"""
Video Trimmer App - Module Entry Point
Allows the package to be executed with: python -m video_trimmer_app
"""

import sys
import os

def main():
    """Main entry point for module execution."""
    try:
        # Import and run the main application
        from .video_trimmer import main as app_main
        app_main()
    except ImportError as e:
        print(f"Error importing video trimmer: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting video trimmer: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()