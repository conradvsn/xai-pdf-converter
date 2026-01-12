#!/usr/bin/env python3
"""
Persistent settings management for xAI PDF Converter
Handles loading, saving, and managing user preferences.

Author: Conrad Vaslin - xAI Finance Tutor
Copyright: © 2025 Conrad Vaslin - All Rights Reserved
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Settings:
    """
    Manages persistent user settings with JSON storage.
    """

    DEFAULT_SETTINGS = {
        # General settings
        "version": "2.0.0",
        "verbose_logging": False,
        "show_progress_bars": True,

        # Directory settings
        "pdf_directory": "pdf",
        "output_directory": "output",

        # Conversion settings
        "pages_per_chunk": 10,
        "auto_detect_scanned": True,
        "ocr_language": "en",
        "ocr_engine_preference": "paddleocr",  # paddleocr, easyocr, tesseract

        # Analysis settings
        "detection_thresholds": {
            "min_person_name_length": 5,
            "max_person_name_length": 40,
            "min_company_name_length": 2,
            "phone_number_validation": True,
            "email_validation": True,
        },
        "enable_anonymization": True,
        "enable_deduplication": True,
        "grouping_keywords": [],

        # Report settings
        "report_format": "excel",  # excel, csv, json
        "consolidated_reports": True,
        "include_images_in_report": True,

        # UI settings
        "theme": "default",  # default, minimal
        "show_file_sizes": True,

        # Developer settings
        "developer": "Conrad Vaslin",
        "developer_role": "xAI Finance Tutor",
        "copyright": "© 2025 Conrad Vaslin - All Rights Reserved"
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize settings manager.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            config_path = Path.cwd() / "config.json"

        self.config_path = Path(config_path)
        self.settings = self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load settings from file, or create default if not exists.

        Returns:
            Dict[str, Any]: Settings dictionary
        """
        if not self.config_path.exists():
            logger.info(f"Config file not found at {self.config_path}, creating default...")
            self.save(self.DEFAULT_SETTINGS)
            return self.DEFAULT_SETTINGS.copy()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)

            # Merge with defaults to ensure all keys exist
            settings = self.DEFAULT_SETTINGS.copy()
            settings.update(loaded_settings)

            logger.info(f"Settings loaded from {self.config_path}")
            return settings

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            logger.info("Using default settings")
            return self.DEFAULT_SETTINGS.copy()

    def save(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save settings to file.

        Args:
            settings: Settings to save. If None, saves current settings.

        Returns:
            bool: True if successful, False otherwise
        """
        if settings is None:
            settings = self.settings

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            self.settings = settings
            logger.info(f"Settings saved to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: Setting key (supports nested keys with dots, e.g., 'detection_thresholds.min_person_name_length')
            default: Default value if key not found

        Returns:
            Any: Setting value
        """
        keys = key.split('.')
        value = self.settings

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """
        Set a setting value.

        Args:
            key: Setting key (supports nested keys with dots)
            value: Value to set
            save: Whether to save to file immediately

        Returns:
            bool: True if successful, False otherwise
        """
        keys = key.split('.')
        current = self.settings

        # Navigate to the nested location
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value

        if save:
            return self.save()

        return True

    def reset(self) -> bool:
        """
        Reset all settings to defaults.

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Resetting settings to defaults")
        return self.save(self.DEFAULT_SETTINGS.copy())

    def export_settings(self, export_path: Path) -> bool:
        """
        Export current settings to a different file.

        Args:
            export_path: Path to export file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Settings exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return False

    def import_settings(self, import_path: Path) -> bool:
        """
        Import settings from a file.

        Args:
            import_path: Path to import file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)

            # Merge with defaults
            settings = self.DEFAULT_SETTINGS.copy()
            settings.update(imported_settings)

            logger.info(f"Settings imported from {import_path}")
            return self.save(settings)

        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return False


# Global settings instance
_settings_instance = None


def get_settings() -> Settings:
    """
    Get the global settings instance (singleton pattern).

    Returns:
        Settings: Global settings instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings():
    """Reload settings from file."""
    global _settings_instance
    if _settings_instance is not None:
        _settings_instance.settings = _settings_instance.load()
