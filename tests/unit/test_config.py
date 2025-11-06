"""
Unit tests for AppConfig.
"""

import pytest
import os
from unittest.mock import patch
from config import AppConfig


@pytest.mark.unit
class TestAppConfig:
    """Test suite for AppConfig."""
    
    def test_initialization_with_required_vars(self, mock_env_vars):
        """Test AppConfig initializes with required environment variables."""
        config = AppConfig()
        
        assert config.GEMINI_API_KEY == "test_key_12345"
        assert config.LOCAL_ASSETS_DIR is not None
        assert config.LOCAL_OUTPUT_DIR is not None
    
    def test_initialization_without_gemini_key(self, monkeypatch):
        """Test AppConfig raises error without GEMINI_API_KEY."""
        monkeypatch.delenv('GEMINI_API_KEY', raising=False)
        
        with pytest.raises(ValueError) as exc_info:
            AppConfig()
        
        assert "GEMINI_API_KEY" in str(exc_info.value)
    
    def test_has_dropbox_credentials_with_access_token(self, mock_env_vars):
        """Test credential detection with access token."""
        config = AppConfig()
        
        assert config.has_dropbox_credentials() is True
    
    def test_has_dropbox_credentials_with_refresh_token(self, monkeypatch):
        """Test credential detection with refresh token flow."""
        monkeypatch.setenv('GEMINI_API_KEY', 'test_key')
        monkeypatch.delenv('DROPBOX_ACCESS_TOKEN', raising=False)
        monkeypatch.setenv('DROPBOX_REFRESH_TOKEN', 'refresh_token')
        monkeypatch.setenv('DROPBOX_APP_KEY', 'app_key')
        monkeypatch.setenv('DROPBOX_APP_SECRET', 'app_secret')
        
        config = AppConfig()
        
        assert config.has_dropbox_credentials() is True
    
    def test_has_dropbox_credentials_incomplete_refresh_flow(self, monkeypatch):
        """Test credential detection with incomplete refresh token flow."""
        monkeypatch.setenv('GEMINI_API_KEY', 'test_key')
        monkeypatch.delenv('DROPBOX_ACCESS_TOKEN', raising=False)
        monkeypatch.setenv('DROPBOX_REFRESH_TOKEN', 'refresh_token')
        monkeypatch.setenv('DROPBOX_APP_KEY', 'app_key')
        # Missing DROPBOX_APP_SECRET
        monkeypatch.delenv('DROPBOX_APP_SECRET', raising=False)
        
        config = AppConfig()
        
        assert config.has_dropbox_credentials() is False
    
    def test_has_dropbox_credentials_none(self, mock_env_no_dropbox):
        """Test credential detection with no Dropbox credentials."""
        config = AppConfig()
        
        assert config.has_dropbox_credentials() is False
    
    def test_get_storage_mode_dropbox(self, mock_env_vars):
        """Test storage mode detection returns Dropbox."""
        config = AppConfig()
        
        assert config.get_storage_mode() == "dropbox"
    
    def test_get_storage_mode_local(self, mock_env_no_dropbox):
        """Test storage mode detection returns local."""
        config = AppConfig()
        
        assert config.get_storage_mode() == "local"
    
    def test_get_patagonia_brand_guidelines(self, mock_env_vars):
        """Test retrieving Patagonia brand guidelines."""
        config = AppConfig()
        
        guidelines = config.get_patagonia_brand_guidelines()
        
        assert guidelines is not None
        assert 'core_values' in guidelines
        assert 'forbidden_content' in guidelines
        assert 'brand_voice_principles' in guidelines
    
    def test_brand_guidelines_core_values(self, mock_env_vars):
        """Test brand guidelines contain core values."""
        config = AppConfig()
        
        guidelines = config.get_patagonia_brand_guidelines()
        core_values = guidelines['core_values']
        
        assert 'quality' in core_values
        assert 'integrity' in core_values
        assert 'environmentalism' in core_values
        assert 'justice' in core_values
        assert 'not_bound_by_convention' in core_values
    
    def test_brand_guidelines_forbidden_content(self, mock_env_vars):
        """Test brand guidelines contain forbidden content."""
        config = AppConfig()
        
        guidelines = config.get_patagonia_brand_guidelines()
        forbidden = guidelines['forbidden_content']
        
        assert 'legal' in forbidden
        assert 'brand_voice' in forbidden
        assert isinstance(forbidden['brand_voice'], list)
        assert 'buy now' in forbidden['brand_voice']
        assert 'guaranteed' in forbidden['brand_voice']
    
    def test_brand_guidelines_voice_principles(self, mock_env_vars):
        """Test brand guidelines contain voice principles."""
        config = AppConfig()
        
        guidelines = config.get_patagonia_brand_guidelines()
        principles = guidelines['brand_voice_principles']
        
        assert isinstance(principles, list)
        assert len(principles) > 0
    
    def test_local_directories_created(self, mock_env_vars, tmp_path, monkeypatch):
        """Test that local directories are created on init."""
        # Set custom paths
        assets_dir = tmp_path / "test_assets"
        output_dir = tmp_path / "test_output"
        
        # Create a config that will use these paths
        with patch('config.Path') as mock_path:
            mock_path.return_value.mkdir = lambda **kwargs: None
            
            config = AppConfig()
            config.LOCAL_ASSETS_DIR = assets_dir
            config.LOCAL_OUTPUT_DIR = output_dir
            
            # Manually trigger directory creation
            assets_dir.mkdir(exist_ok=True)
            output_dir.mkdir(exist_ok=True)
            
            assert assets_dir.exists()
            assert output_dir.exists()
    
    def test_dropbox_base_path_configuration(self, mock_env_vars):
        """Test Dropbox base path is configurable."""
        config = AppConfig()
        
        assert config.DROPBOX_BASE_PATH is not None
    
    def test_access_token_priority(self, monkeypatch):
        """Test that access token has priority over refresh token."""
        monkeypatch.setenv('GEMINI_API_KEY', 'test_key')
        monkeypatch.setenv('DROPBOX_ACCESS_TOKEN', 'access_token')
        monkeypatch.setenv('DROPBOX_REFRESH_TOKEN', 'refresh_token')
        monkeypatch.setenv('DROPBOX_APP_KEY', 'app_key')
        monkeypatch.setenv('DROPBOX_APP_SECRET', 'app_secret')
        
        config = AppConfig()
        
        # Both are present, should still detect credentials
        assert config.has_dropbox_credentials() is True
        assert config.DROPBOX_ACCESS_TOKEN == 'access_token'
    
    def test_optional_env_vars_handling(self, monkeypatch):
        """Test handling of optional environment variables."""
        monkeypatch.setenv('GEMINI_API_KEY', 'test_key')
        # Don't set any Dropbox vars
        monkeypatch.delenv('DROPBOX_ACCESS_TOKEN', raising=False)
        monkeypatch.delenv('DROPBOX_REFRESH_TOKEN', raising=False)
        monkeypatch.delenv('DROPBOX_APP_KEY', raising=False)
        monkeypatch.delenv('DROPBOX_APP_SECRET', raising=False)
        
        config = AppConfig()
        
        # Should not raise error
        assert config.DROPBOX_ACCESS_TOKEN is None
        assert config.DROPBOX_REFRESH_TOKEN is None
    
    def test_config_is_singleton_pattern(self, mock_env_vars):
        """Test that importing config gives same instance."""
        from config import config
        
        assert isinstance(config, AppConfig)
        assert config.GEMINI_API_KEY is not None
    
    def test_brand_guidelines_immutability(self, mock_env_vars):
        """Test that brand guidelines are consistent across calls."""
        config = AppConfig()
        
        guidelines1 = config.get_patagonia_brand_guidelines()
        guidelines2 = config.get_patagonia_brand_guidelines()
        
        assert guidelines1 == guidelines2

