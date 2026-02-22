#!/usr/bin/env python3
"""
Setup script for Enhanced Video Trimmer
Handles package installation and configuration.
"""

from setuptools import setup, find_packages
from pathlib import Path
from typing import List, Dict, Any

# Constants
PACKAGE_NAME = "enhanced-video-trimmer"
VERSION = "2.0.0"
AUTHOR = "Video Trimmer Team"
AUTHOR_EMAIL = "dev@videotrimmer.com"
DESCRIPTION = "Advanced video trimming application with modern GUI and batch processing"
URL = "https://github.com/videotrimmer/enhanced-video-trimmer"
LICENSE = "MIT"
PYTHON_REQUIRES = ">=3.8"

def read_file(filename: str) -> str:
    """Read content from a file.
    
    Args:
        filename: Name of the file to read
        
    Returns:
        str: File content or empty string if file doesn't exist
    """
    file_path = Path(__file__).parent / filename
    if file_path.exists():
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not read {filename}: {e}")
    return ""

def read_requirements(filename: str) -> List[str]:
    """Read requirements from a file.
    
    Args:
        filename: Name of requirements file
        
    Returns:
        List[str]: List of requirements
    """
    content = read_file(filename)
    if not content:
        return []
    
    requirements = []
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-r"):
            requirements.append(line)
    
    return requirements

# Core requirements
requirements = read_requirements("requirements.txt")

# Read long description from README
long_description = read_file("README.md")

# Optional dependencies
extras_require = {
    "dev": read_requirements("requirements-dev.txt"),
    "cloud": [
        "dropbox>=11.36.0",
        "google-cloud-storage>=2.10.0",
        "google-auth>=2.22.0",
        "google-auth-oauthlib>=1.0.0",
        "google-auth-httplib2>=0.1.1",
        "google-api-python-client>=2.97.0",
    ],
    "audio": [
        "librosa>=0.10.0",
        "soundfile>=0.12.0",
        "librosa[display]>=0.10.0",
    ],
    "advanced": [
        "opencv-python>=4.8.0",
        "scikit-image>=0.21.0",
        "scikit-video>=1.1.11",
        "imageio-ffmpeg>=0.4.8",
    ],
}

# All extras combined
extras_require["all"] = list(set(
    req for extra_reqs in extras_require.values() 
    for req in extra_reqs if isinstance(req, str)
))

setup(
    name="video-trimmer-pro",
    version="2.0.0",
    author="Video Trimmer Team",
    author_email="contact@videotrimmer.dev",
    description="Professional video trimming application with advanced features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/video-trimmer-pro",
    project_urls={
        "Bug Reports": "https://github.com/your-username/video-trimmer-pro/issues",
        "Source": "https://github.com/your-username/video-trimmer-pro",
        "Documentation": "https://video-trimmer-pro.readthedocs.io/",
    },
    packages=["video_trimmer_app"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Video :: Conversion",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "video-trimmer=video_trimmer_app.cli_wrapper:main",
            "video-trimmer-gui=video_trimmer_app.video_trimmer:main", 
            "video-trimmer-cli=video_trimmer_app.video_trimmer_cli:main",
            "video-trimmer-basic=video_trimmer_app.video_trimmer_basic:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    data_files=[
        ("", ["README.md", "LICENSE"]),
    ],
    keywords=[
        "video", "trimming", "editing", "ffmpeg", "moviepy", 
        "gui", "cli", "batch", "processing", "multimedia"
    ],
    zip_safe=False,
    platforms=["any"],
)