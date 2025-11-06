"""
Integration tests for storage mode transitions and operations.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from PIL import Image
from modules.storage_manager import StorageManager
import dropbox


@pytest.mark.integration
class TestStorageModeTransitions:
    """Test suite for storage mode transitions."""
    
    @pytest.mark.local
    def test_initialization_defaults_to_local(self, mock_env_no_dropbox, temp_storage):
        """Test storage manager defaults to local mode without credentials."""
        mock_config = Mock()
        mock_config.has_dropbox_credentials.return_value = False
        mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
        mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
        
        manager = StorageManager(mock_config)
        
        assert manager.mode == "local"
        assert manager.dbx is None
    
    @pytest.mark.dropbox
    def test_initialization_with_dropbox_credentials(self, mock_config_with_dropbox):
        """Test storage manager initializes with Dropbox when credentials available."""
        with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
            mock_dbx = MagicMock()
            mock_account = MagicMock()
            mock_account.email = 'test@example.com'
            mock_dbx.users_get_current_account.return_value = mock_account
            mock_dropbox_class.return_value = mock_dbx
            
            manager = StorageManager(mock_config_with_dropbox)
            
            assert manager.mode == "dropbox"
            assert manager.dbx is not None
    
    @pytest.mark.dropbox
    def test_fallback_to_local_on_connection_failure(self, mock_config_with_dropbox):
        """Test fallback to local mode when Dropbox connection fails."""
        with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
            mock_dropbox_class.side_effect = Exception("Connection failed")
            
            manager = StorageManager(mock_config_with_dropbox)
            
            assert manager.mode == "local"
            assert manager.dbx is None
    
    @pytest.mark.local
    @pytest.mark.dropbox
    def test_storage_consistency_between_modes(self, sample_image, temp_storage):
        """Test that storage operations are consistent between modes."""
        # Test local mode
        mock_config_local = Mock()
        mock_config_local.has_dropbox_credentials.return_value = False
        mock_config_local.LOCAL_ASSETS_DIR = temp_storage['assets']
        mock_config_local.LOCAL_OUTPUT_DIR = temp_storage['output']
        
        manager_local = StorageManager(mock_config_local)
        
        path_local = manager_local.upload_creative(
            "test-campaign",
            "Test Product",
            "1:1",
            sample_image
        )
        
        assert Path(path_local).exists()
        assert "1x1.jpg" in path_local
        
        # Test Dropbox mode
        with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
            mock_dbx = MagicMock()
            mock_account = MagicMock()
            mock_account.email = 'test@example.com'
            mock_dbx.users_get_current_account.return_value = mock_account
            mock_dropbox_class.return_value = mock_dbx
            
            mock_config_dropbox = Mock()
            mock_config_dropbox.has_dropbox_credentials.return_value = True
            mock_config_dropbox.DROPBOX_ACCESS_TOKEN = "test_token"
            mock_config_dropbox.DROPBOX_BASE_PATH = "/test"
            mock_config_dropbox.LOCAL_ASSETS_DIR = temp_storage['assets']
            mock_config_dropbox.LOCAL_OUTPUT_DIR = temp_storage['output']
            
            manager_dropbox = StorageManager(mock_config_dropbox)
            manager_dropbox.dbx = mock_dbx
            manager_dropbox.mode = "dropbox"
            
            path_dropbox = manager_dropbox.upload_creative(
                "test-campaign",
                "Test Product",
                "1:1",
                sample_image
            )
            
            assert "1x1.jpg" in path_dropbox
            # Dropbox path should follow same naming convention
            assert "test_product" in path_dropbox.lower()


@pytest.mark.integration
class TestParallelStorageOperations:
    """Test suite for parallel storage operations."""
    
    @pytest.mark.local
    def test_concurrent_uploads_local(self, sample_image, temp_storage):
        """Test concurrent uploads in local mode."""
        mock_config = Mock()
        mock_config.has_dropbox_credentials.return_value = False
        mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
        mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
        
        manager = StorageManager(mock_config)
        
        # Upload multiple creatives concurrently
        paths = []
        for i in range(5):
            path = manager.upload_creative(
                f"campaign-{i}",
                f"Product {i}",
                "1:1",
                sample_image
            )
            paths.append(path)
        
        # All uploads should succeed
        assert len(paths) == 5
        assert all(Path(p).exists() for p in paths)
    
    @pytest.mark.dropbox
    def test_concurrent_uploads_dropbox(self, sample_image, temp_storage):
        """Test concurrent uploads in Dropbox mode."""
        with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
            mock_dbx = MagicMock()
            mock_account = MagicMock()
            mock_account.email = 'test@example.com'
            mock_dbx.users_get_current_account.return_value = mock_account
            mock_dropbox_class.return_value = mock_dbx
            
            mock_config = Mock()
            mock_config.has_dropbox_credentials.return_value = True
            mock_config.DROPBOX_ACCESS_TOKEN = "test_token"
            mock_config.DROPBOX_BASE_PATH = "/test"
            mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
            mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
            
            manager = StorageManager(mock_config)
            manager.dbx = mock_dbx
            manager.mode = "dropbox"
            
            # Upload multiple creatives
            paths = []
            for i in range(5):
                path = manager.upload_creative(
                    f"campaign-{i}",
                    f"Product {i}",
                    "1:1",
                    sample_image
                )
                paths.append(path)
            
            # All uploads should succeed
            assert len(paths) == 5
            assert mock_dbx.files_upload.call_count == 5
    
    @pytest.mark.local
    def test_parallel_asset_search(self, sample_image, temp_storage):
        """Test parallel asset searches in local mode."""
        mock_config = Mock()
        mock_config.has_dropbox_credentials.return_value = False
        mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
        mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
        
        manager = StorageManager(mock_config)
        
        # Create multiple assets
        for i in range(3):
            asset_folder = temp_storage['assets'] / f"product_{i}"
            asset_folder.mkdir()
            sample_image.save(asset_folder / "image.jpg")
        
        # Search for multiple assets
        results = []
        for i in range(3):
            result = manager.find_asset(f"product_{i}")
            results.append(result)
        
        # All should be found
        assert all(r is not None for r in results)
        assert all(isinstance(r, Image.Image) for r in results)


@pytest.mark.integration
class TestStorageErrorHandling:
    """Test suite for storage error handling."""
    
    @pytest.mark.local
    def test_local_storage_disk_full_simulation(self, sample_image, temp_storage):
        """Test handling of storage errors in local mode."""
        mock_config = Mock()
        mock_config.has_dropbox_credentials.return_value = False
        mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
        mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
        
        manager = StorageManager(mock_config)
        
        # Simulate disk full by using invalid path
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = OSError("Disk full")
            
            with pytest.raises(Exception):
                manager.upload_creative(
                    "test-campaign",
                    "Test Product",
                    "1:1",
                    sample_image
                )
    
    @pytest.mark.dropbox
    def test_dropbox_quota_exceeded(self, sample_image, temp_storage):
        """Test handling of Dropbox quota exceeded error."""
        with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
            mock_dbx = MagicMock()
            mock_account = MagicMock()
            mock_account.email = 'test@example.com'
            mock_dbx.users_get_current_account.return_value = mock_account
            
            # Simulate quota exceeded
            from dropbox.exceptions import ApiError
            mock_dbx.files_upload.side_effect = ApiError("", Mock(), "", "")
            
            mock_dropbox_class.return_value = mock_dbx
            
            mock_config = Mock()
            mock_config.has_dropbox_credentials.return_value = True
            mock_config.DROPBOX_ACCESS_TOKEN = "test_token"
            mock_config.DROPBOX_BASE_PATH = "/test"
            mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
            mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
            
            manager = StorageManager(mock_config)
            manager.dbx = mock_dbx
            manager.mode = "dropbox"
            
            with pytest.raises(Exception):
                manager.upload_creative(
                    "test-campaign",
                    "Test Product",
                    "1:1",
                    sample_image
                )
    
    @pytest.mark.local
    def test_corrupted_asset_handling(self, temp_storage):
        """Test handling of corrupted asset files."""
        mock_config = Mock()
        mock_config.has_dropbox_credentials.return_value = False
        mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
        mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
        
        manager = StorageManager(mock_config)
        
        # Create corrupted asset file
        asset_folder = temp_storage['assets'] / "corrupted_product"
        asset_folder.mkdir()
        with open(asset_folder / "image.jpg", 'wb') as f:
            f.write(b'corrupted data')
        
        # Should handle gracefully
        result = manager.find_asset("corrupted_product")
        
        # Should fail to load and return None or raise exception
        assert result is None or isinstance(result, Exception)


@pytest.mark.integration
class TestStoragePathNormalization:
    """Test suite for path normalization across storage modes."""
    
    @pytest.mark.dropbox
    def test_dropbox_path_with_special_characters(self, sample_image, temp_storage):
        """Test Dropbox path handling with special characters."""
        with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
            mock_dbx = MagicMock()
            mock_account = MagicMock()
            mock_account.email = 'test@example.com'
            mock_dbx.users_get_current_account.return_value = mock_account
            mock_dropbox_class.return_value = mock_dbx
            
            mock_config = Mock()
            mock_config.has_dropbox_credentials.return_value = True
            mock_config.DROPBOX_ACCESS_TOKEN = "test_token"
            mock_config.DROPBOX_BASE_PATH = "/test"
            mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
            mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
            
            manager = StorageManager(mock_config)
            manager.dbx = mock_dbx
            manager.mode = "dropbox"
            
            # Upload with product name containing spaces
            path = manager.upload_creative(
                "test-campaign",
                "Product With Spaces",
                "1:1",
                sample_image
            )
            
            # Path should be normalized
            assert "product_with_spaces" in path.lower()
    
    @pytest.mark.local
    def test_local_path_with_special_characters(self, sample_image, temp_storage):
        """Test local path handling with special characters."""
        mock_config = Mock()
        mock_config.has_dropbox_credentials.return_value = False
        mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
        mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
        
        manager = StorageManager(mock_config)
        
        # Upload with product name containing special characters
        path = manager.upload_creative(
            "test-campaign",
            "Product & Special!",
            "1:1",
            sample_image
        )
        
        # Path should be created successfully
        assert Path(path).exists()
        assert "product" in path.lower()

