# Video Trimmer Pro Package
# Professional video trimming application

__version__ = "2.0.0"
__author__ = "Video Trimmer Team"
__email__ = "contact@videotrimmer.dev"

# Import main components for easy access
try:
    from .video_trimmer import AdvancedVideoTrimmer
    from .ffmpeg_trimmer import FFmpegTrimmer
    from .config_manager import ConfigManager
    from .launch import main
except ImportError:
    # Handle relative import issues during development
    pass

__all__ = ['AdvancedVideoTrimmer', 'FFmpegTrimmer', 'ConfigManager', 'main']