#!/usr/bin/env python3
"""
Configuration Manager for Video Trimmer Application
Handles user preferences, settings persistence, and application configuration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from loguru import logger

# Constants
CONFIG_DIR_NAME = ".video_trimmer"
CONFIG_FILE_NAME = "config.json"
RECENT_FILES_NAME = "recent_files.json"
PRESETS_FILE_NAME = "presets.json"
MAX_RECENT_FILES = 10
DEFAULT_TEMP_DIR = "tmp/video_trimmer"


class ConfigManager:
    """Manages application configuration and user preferences.
    
    Provides persistent storage for settings, recent files, and user presets
    with automatic fallback to defaults and safe error handling.
    """
    
    def __init__(self) -> None:
        """Initialize configuration manager."""
        # Setup file paths
        self.config_dir = Path.home() / CONFIG_DIR_NAME
        self.config_file = self.config_dir / CONFIG_FILE_NAME
        self.recent_files_file = self.config_dir / RECENT_FILES_NAME
        self.presets_file = self.config_dir / PRESETS_FILE_NAME
        
        # Initialize configuration
        self._ensure_config_directory()
        self.default_config = self._get_default_config()
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def _ensure_config_directory(self) -> None:
        """Create configuration directory if it doesn't exist."""
        try:
            self.config_dir.mkdir(exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create config directory: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration dictionary."""
        return {
            "appearance": {
                "theme": "dark",
                "color_theme": "blue",
                "window_geometry": "900x700",
                "remember_window_state": True
            },
            "processing": {
                "default_engine": "ffmpeg",
                "hardware_acceleration": True,
                "concurrent_jobs": 2,
                "temp_directory": str(Path.home() / DEFAULT_TEMP_DIR),
                "auto_delete_temp": True
            },
            "ui": {
                "show_thumbnails": True,
                "preview_quality": "medium",
                "auto_preview": True,
                "drag_drop_enabled": True,
                "show_progress_details": True
            },
            "output": {
                "default_format": "mp4",
                "default_quality": "original",
                "auto_naming": True,
                "organize_outputs": False,
                "backup_originals": False
            },
            "advanced": {
                "verbose_logging": False,
                "keep_logs": 30,  # days
                "check_updates": True,
                "enable_gpu": True
            }
        }
        
    def load_config(self) -> None:
        """Load configuration from file with safe fallback to defaults."""
        try:
            if self.config_file.exists():
                loaded_config = self._read_json_file(self.config_file)
                self.config = self._merge_dict(self.default_config, loaded_config)
                logger.debug("Configuration loaded successfully")
            else:
                self.config = self.default_config.copy()
                self.save_config()
                logger.info("Created new configuration file with defaults")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading config, using defaults: {e}")
            self.config = self.default_config.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            self._write_json_file(self.config_file, self.config)
            logger.debug("Configuration saved successfully")
            return True
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'appearance.theme')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        if not key_path:
            return default
            
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'appearance.theme')
            value: Value to set
            
        Returns:
            bool: True if set and saved successfully
        """
        if not key_path:
            return False
            
        keys = key_path.split('.')
        config_ref = self.config
        
        # Navigate to parent dictionary
        try:
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]
            
            # Set the value
            config_ref[keys[-1]] = value
            return self.save_config()
            
        except (TypeError, AttributeError) as e:
            logger.error(f"Error setting config value '{key_path}': {e}")
            return False
    
    def get_recent_files(self) -> List[str]:
        """Get list of recent files, filtering out non-existent files.
        
        Returns:
            List of valid file paths
        """
        try:
            if not self.recent_files_file.exists():
                return []
                
            recent_files = self._read_json_file(self.recent_files_file, [])
            # Filter out files that no longer exist
            valid_files = [file for file in recent_files if os.path.exists(file)]
            
            # Update the file if we filtered out any files
            if len(valid_files) != len(recent_files):
                self._write_json_file(self.recent_files_file, valid_files)
                
            return valid_files
            
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading recent files: {e}")
            return []
    
    def add_recent_file(self, file_path: str) -> bool:
        """Add file to recent files list.
        
        Args:
            file_path: Path to the file to add
            
        Returns:
            bool: True if added successfully
        """
        if not file_path or not os.path.exists(file_path):
            return False
            
        try:
            recent = self.get_recent_files()
            
            # Remove if already exists (to move to top)
            if file_path in recent:
                recent.remove(file_path)
            
            # Add to beginning and limit to MAX_RECENT_FILES
            recent.insert(0, file_path)
            recent = recent[:MAX_RECENT_FILES]
            
            self._write_json_file(self.recent_files_file, recent)
            logger.debug(f"Added recent file: {file_path}")
            return True
            
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Error saving recent file: {e}")
            return False
    
    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get user-defined presets.
        
        Returns:
            Dictionary of preset name to preset configuration
        """
        try:
            return self._read_json_file(self.presets_file, {})
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading presets: {e}")
            return {}
    
    def save_preset(self, name: str, preset: Dict[str, Any]) -> bool:
        """Save a new preset.
        
        Args:
            name: Preset name
            preset: Preset configuration dictionary
            
        Returns:
            bool: True if saved successfully
        """
        if not name or not isinstance(preset, dict):
            return False
            
        try:
            presets = self.get_presets()
            presets[name] = preset
            
            self._write_json_file(self.presets_file, presets)
            logger.debug(f"Saved preset: {name}")
            return True
            
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Error saving preset: {e}")
            return False
    
    def delete_preset(self, name: str) -> bool:
        """Delete a preset.
        
        Args:
            name: Name of preset to delete
            
        Returns:
            bool: True if deleted successfully or didn't exist
        """
        if not name:
            return False
            
        try:
            presets = self.get_presets()
            if name not in presets:
                return True  # Already doesn't exist
                
            del presets[name]
            self._write_json_file(self.presets_file, presets)
            logger.debug(f"Deleted preset: {name}")
            return True
            
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Error deleting preset: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults.
        
        Returns:
            bool: True if reset successfully
        """
        self.config = self.default_config.copy()
        return self.save_config()
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to file.
        
        Args:
            file_path: Path to export configuration to
            
        Returns:
            bool: True if exported successfully
        """
        if not file_path:
            return False
            
        try:
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_json_file(export_path, self.config)
            logger.info(f"Configuration exported to: {file_path}")
            return True
            
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from file.
        
        Args:
            file_path: Path to import configuration from
            
        Returns:
            bool: True if imported successfully
        """
        if not file_path or not os.path.exists(file_path):
            return False
            
        try:
            imported_config = self._read_json_file(Path(file_path))
            # Merge with defaults to ensure completeness
            self.config = self._merge_dict(self.default_config, imported_config)
            
            if self.save_config():
                logger.info(f"Configuration imported from: {file_path}")
                return True
            return False
            
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error importing config: {e}")
            return False
    
    # Helper methods
    def _read_json_file(self, file_path: Path, default: Any = None) -> Any:
        """Safely read JSON file with fallback.
        
        Args:
            file_path: Path to JSON file
            default: Default value if file doesn't exist or is invalid
            
        Returns:
            Parsed JSON data or default value
        """
        try:
            if not file_path.exists():
                return default if default is not None else {}
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return default if default is not None else {}
    
    def _write_json_file(self, file_path: Path, data: Any) -> None:
        """Safely write JSON file.
        
        Args:
            file_path: Path to write JSON file
            data: Data to serialize to JSON
            
        Raises:
            OSError: If file cannot be written
            json.JSONEncodeError: If data cannot be serialized
        """
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _merge_dict(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with defaults.
        
        Args:
            default: Default configuration dictionary
            user: User configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        result = default.copy()
        
        for key, value in user.items():
            if (key in result 
                and isinstance(result[key], dict) 
                and isinstance(value, dict)):
                result[key] = self._merge_dict(result[key], value)
            else:
                result[key] = value
        
        return result