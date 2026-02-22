#!/usr/bin/env python3
"""
Entry point wrapper for video-trimmer CLI
"""

def main():
    """Main entry point for video-trimmer command"""
    try:\n        try:\n            from .launch import main as launch_main\n        except ImportError:\n            # Fallback for direct script execution\n            from launch import main as launch_main\n        launch_main()\n    except ImportError:\n        print(\"Error: Video Trimmer package not properly installed\")\n        print(\"Please run: pip install -e . from the project directory\")\n        return 1

if __name__ == "__main__":
    exit(main())