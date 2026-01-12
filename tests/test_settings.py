"""
Unit tests for settings module
Author: Conrad Vaslin - xAI Finance Tutor
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.settings import Settings


class TestSettings:
    """Test settings management"""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
        yield config_path
        if config_path.exists():
            config_path.unlink()

    def test_default_settings_creation(self, temp_config):
        """Test that default settings are created"""
        settings = Settings(temp_config)
        assert settings.get('version') == '2.0.0'
        assert settings.get('developer') == 'Conrad Vaslin'
        assert settings.get('verbose_logging') == False
        assert settings.get('show_progress_bars') == True

    def test_load_existing_settings(self, temp_config):
        """Test loading existing settings"""
        # Create initial settings
        test_settings = {'test_key': 'test_value', 'version': '2.0.0'}
        with open(temp_config, 'w') as f:
            json.dump(test_settings, f)

        # Load settings
        settings = Settings(temp_config)
        assert settings.get('test_key') == 'test_value'

    def test_save_settings(self, temp_config):
        """Test saving settings"""
        settings = Settings(temp_config)
        settings.set('new_key', 'new_value')

        # Reload and verify
        settings2 = Settings(temp_config)
        assert settings2.get('new_key') == 'new_value'

    def test_nested_get(self, temp_config):
        """Test nested key access with dots"""
        settings = Settings(temp_config)
        value = settings.get('detection_thresholds.min_person_name_length')
        assert value == 5

    def test_nested_set(self, temp_config):
        """Test nested key setting with dots"""
        settings = Settings(temp_config)
        settings.set('detection_thresholds.min_person_name_length', 10)
        assert settings.get('detection_thresholds.min_person_name_length') == 10

    def test_reset_settings(self, temp_config):
        """Test resetting settings to defaults"""
        settings = Settings(temp_config)
        settings.set('test_key', 'test_value')
        settings.reset()

        # Verify reset
        assert settings.get('test_key') is None
        assert settings.get('version') == '2.0.0'

    def test_export_import(self, temp_config):
        """Test export and import functionality"""
        settings = Settings(temp_config)
        settings.set('custom_key', 'custom_value')

        # Export
        export_path = temp_config.with_suffix('.export.json')
        settings.export_settings(export_path)

        # Import to new instance
        settings2 = Settings(temp_config.with_suffix('.new.json'))
        settings2.import_settings(export_path)

        assert settings2.get('custom_key') == 'custom_value'

        # Cleanup
        export_path.unlink()
        temp_config.with_suffix('.new.json').unlink()

    def test_developer_info(self, temp_config):
        """Test that developer information is preserved"""
        settings = Settings(temp_config)
        assert settings.get('developer') == 'Conrad Vaslin'
        assert settings.get('developer_role') == 'xAI Finance Tutor'
        assert 'Conrad Vaslin' in settings.get('copyright')
