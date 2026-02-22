#!/usr/bin/env python3
"""
Launch Script for Enhanced Video Trimmer
Handles dependencies and launches the appropriate version.
"""

import sys
import os
import subprocess
from pathlib import Path
import importlib.util
from typing import List, Tuple, Optional
from loguru import logger

# Constants
MIN_PYTHON_VERSION = (3, 8)
REQUIRED_DEPENDENCIES = [
    'customtkinter',
    'tkinterdnd2', 
    'moviepy',
    'numpy',
    'loguru',
    'psutil'
]
OPTIONAL_DEPENDENCIES = [
    'cv2',  # opencv-python
    'PIL',  # Pillow
    'yaml',  # pyyaml
    'ffmpeg',  # ffmpeg-python
    'tqdm',
    'librosa',
    'soundfile'
]
# Mapping from import names to package names for installation
OPTIONAL_PACKAGE_MAPPING = {
    'cv2': 'opencv-python',
    'PIL': 'Pillow', 
    'yaml': 'pyyaml',
    'ffmpeg': 'ffmpeg-python',
    'tqdm': 'tqdm',
    'librosa': 'librosa',
    'soundfile': 'soundfile'
}
LOG_FILE = 'logs/launcher.log'


def check_python_version() -> bool:
    """Check if Python version is compatible.
    
    Returns:
        bool: True if Python version meets requirements
    """
    if sys.version_info < MIN_PYTHON_VERSION:
        min_version_str = '.'.join(map(str, MIN_PYTHON_VERSION))
        current_version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        print(f"❌ Error: Python {min_version_str} or higher is required.")
        print(f"📍 Current version: {current_version_str}")
        print(f"💡 Please upgrade your Python installation.")
        return False
    
    logger.debug(f"Python version check passed: {sys.version}")
    return True


def check_dependencies() -> Tuple[List[str], List[str]]:
    """Check for required and optional dependencies.
    
    Returns:
        Tuple[List[str], List[str]]: (missing_required, missing_optional)
    """
    missing_required = []
    missing_optional = []
    
    # Check required dependencies
    for dep in REQUIRED_DEPENDENCIES:
        if importlib.util.find_spec(dep) is None:
            missing_required.append(dep)
            logger.warning(f"Missing required dependency: {dep}")
    
    # Check optional dependencies
    for dep in OPTIONAL_DEPENDENCIES:
        if importlib.util.find_spec(dep) is None:
            missing_optional.append(dep)
            logger.debug(f"Missing optional dependency: {dep}")
    
    return missing_required, missing_optional
    
    for dep in optional_deps:
        if importlib.util.find_spec(dep) is None:
            missing_optional.append(dep)
    
    return missing_required, missing_optional


def install_dependencies(packages: List[str], optional: bool = False) -> bool:
    """Install missing dependencies."""
    if not packages:
        return True
    
    dep_type = "optional" if optional else "required"
    
    # Convert import names to package names for optional dependencies
    if optional:
        package_names = [OPTIONAL_PACKAGE_MAPPING.get(pkg, pkg) for pkg in packages]
        print(f"\nInstalling missing {dep_type} dependencies: {', '.join(package_names)}")
    else:
        package_names = packages
        print(f"\nInstalling missing {dep_type} dependencies: {', '.join(package_names)}")
    
    try:
        cmd = [sys.executable, '-m', 'pip', 'install'] + package_names
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Successfully installed {dep_type} dependencies.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {dep_type} dependencies:")
        print(e.stderr)
        return False


def launch_main_version():
    """Launch the main video trimmer."""
    try:
        # Try to import and launch main version
        try:
            from .video_trimmer import main as main_app
        except ImportError:
            # Fallback for direct script execution
            from video_trimmer import main as main_app
        print("Launching Video Trimmer...")
        main_app()
    except ImportError as e:
        print(f"Cannot launch main version: {e}")
        print("Falling back to basic version...")
        launch_basic_version()
    except Exception as e:
        print(f"Error launching enhanced version: {e}")
        print("Falling back to basic version...")
        launch_basic_version()


def launch_basic_version():
    """Launch the basic video trimmer as fallback."""
    try:
        try:
            from .video_trimmer_basic import main as basic_main
        except ImportError:
            # Fallback for direct script execution
            from video_trimmer_basic import main as basic_main
        print("Launching Basic Video Trimmer...")
        basic_main()
    except ImportError as e:
        print(f"Cannot launch basic version: {e}")
        print("Please install required dependencies and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching basic version: {e}")
        sys.exit(1)


def main():
    """Main launcher function."""
    print("Video Trimmer Application Launcher")
    print("==================================")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    missing_required, missing_optional = check_dependencies()
    
    # Handle missing required dependencies
    if missing_required:
        print(f"\nMissing required dependencies: {', '.join(missing_required)}")
        
        # Ask user if they want to install automatically
        response = input("Would you like to install them automatically? (y/n): ").lower()
        
        if response == 'y':
            if not install_dependencies(missing_required):
                print("Failed to install required dependencies. Please install manually.")
                print(f"Run: pip install {' '.join(missing_required)}")
                sys.exit(1)
        else:
            print("Please install the required dependencies manually:")
            print(f"pip install {' '.join(missing_required)}")
            sys.exit(1)
    
    # Handle missing optional dependencies
    if missing_optional:
        # Convert import names to package names for display
        missing_package_names = [OPTIONAL_PACKAGE_MAPPING.get(pkg, pkg) for pkg in missing_optional]
        print(f"\nMissing optional dependencies: {', '.join(missing_package_names)}")
        print("Optional features may not be available.")
        
        response = input("Would you like to install them for enhanced features? (y/n): ").lower()
        
        if response == 'y':
            install_dependencies(missing_optional, optional=True)
    
    # Determine which version to launch
    try:
        import customtkinter
        import tkinterdnd2
        
        # Enhanced version available
        enhanced_available = True
    except ImportError:
        enhanced_available = False
    
    if enhanced_available:
        launch_main_version()
    else:
        print("\nMain version dependencies not available.")
        print("Launching basic version...")
        launch_basic_version()
        launch_basic_version()


if __name__ == "__main__":
    main()