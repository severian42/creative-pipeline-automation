"""
Unit tests for StorageManager.
"""

import pytest
import io
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from PIL import Image
from modules.storage_manager import StorageManager
import dropbox
from dropbox.files import FileMetadata, FolderMetadata
from dropbox.exceptions import ApiError


@pytest.mark.unit
class TestStorageManagerLocal:
    """Test suite for StorageManager in local mode."""
    
    @pytest.mark.local
    def test_initialization_local_mode(self, mock_env_no_dropbox, temp_storage):
        """Test StorageManager initializes in local mode without Dropbox credentials."""
        with patch('config.AppConfig') as mock_config_class:
            mock_config = Mock()
            mock_config.has_dropbox_credentials.return_value = False
            mock_config.LOCAL_ASSETS_DIR = temp_storage['assets']
            mock_config.LOCAL_OUTPUT_DIR = temp_storage['output']
            mock_config_class.return_value = mock_config
            
            manager = StorageManager(mock_config)
            
            assert manager.mode == "local"
            assert manager.dbx is None
    
    @pytest.mark.local
    def test_find_asset_local_exists(self, storage_manager_local, sample_image, temp_storage):
        """Test finding an existing asset in local storage."""
        # Create test asset
        asset_folder = temp_storage['assets'] / "test_product"
        asset_folder.mkdir()
        asset_path = asset_folder / "image.jpg"
        sample_image.save(asset_path)
        
        # Find asset
        result = storage_manager_local.find_asset("test_product")
        
        assert result is not None
        assert isinstance(result, Image.Image)
    
    @pytest.mark.local
    def test_find_asset_local_not_found(self, storage_manager_local):
        """Test finding a non-existent asset in local storage."""
        result = storage_manager_local.find_asset("nonexistent_product")
        
        assert result is None
    
    @pytest.mark.local
    def test_upload_creative_local(self, storage_manager_local, sample_image, temp_storage):
        """Test uploading a creative to local storage."""
        output_path = storage_manager_local.upload_creative(
            "test-campaign",
            "Test Product",
            "1:1",
            sample_image
        )
        
        assert output_path is not None
        assert Path(output_path).exists()
        assert "test-campaign" in output_path
        assert "test_product" in output_path.lower()
        assert "1x1.jpg" in output_path
    
    @pytest.mark.local
    def test_list_campaign_outputs_local(self, storage_manager_local, sample_image, temp_storage):
        """Test listing campaign outputs in local storage."""
        # Upload some creatives
        storage_manager_local.upload_creative(
            "test-campaign",
            "Product One",
            "1:1",
            sample_image
        )
        storage_manager_local.upload_creative(
            "test-campaign",
            "Product Two",
            "9:16",
            sample_image
        )
        
        # List outputs
        outputs = storage_manager_local.list_campaign_outputs("test-campaign")
        
        assert len(outputs) == 2
        assert all("test-campaign" in path for path in outputs)
    
    @pytest.mark.local
    def test_list_campaign_outputs_empty(self, storage_manager_local):
        """Test listing outputs for non-existent campaign."""
        outputs = storage_manager_local.list_campaign_outputs("nonexistent")
        
        assert outputs == []


@pytest.mark.unit
class TestStorageManagerDropbox:
    """Test suite for StorageManager in Dropbox mode."""
    
    @pytest.mark.dropbox
    def test_initialization_dropbox_mode(self, mock_config_with_dropbox, mock_dropbox_client):
        """Test StorageManager initializes in Dropbox mode with credentials."""
        with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
            mock_dropbox_class.return_value = mock_dropbox_client
            
            manager = StorageManager(mock_config_with_dropbox)
            
            assert manager.mode == "dropbox"
            assert manager.dbx is not None
    
    @pytest.mark.dropbox
    def test_dropbox_connection_failure_fallback(self, mock_config_with_dropbox):
        """Test fallback to local mode when Dropbox connection fails."""
        with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
            mock_dropbox_class.side_effect = Exception("Connection failed")
            
            manager = StorageManager(mock_config_with_dropbox)
            
            assert manager.mode == "local"
            assert manager.dbx is None
    
    @pytest.mark.dropbox
    def test_find_asset_dropbox_exists(self, storage_manager_dropbox, sample_image):
        """Test finding an existing asset in Dropbox."""
        # Mock Dropbox response
        mock_file = Mock(spec=FileMetadata)
        mock_file.name = "image.jpg"
        mock_file.path_display = "/test/assets/test_product/image.jpg"
        
        mock_list_result = Mock()
        mock_list_result.entries = [mock_file]
        
        storage_manager_dropbox.dbx.files_list_folder.return_value = mock_list_result
        
        # Mock download
        buffer = io.BytesIO()
        sample_image.save(buffer, format='JPEG')
        mock_response = Mock()
        mock_response.content = buffer.getvalue()
        
        storage_manager_dropbox.dbx.files_download.return_value = (None, mock_response)
        
        # Find asset
        result = storage_manager_dropbox.find_asset("test_product")
        
        assert result is not None
        assert isinstance(result, Image.Image)
    
    @pytest.mark.dropbox
    def test_find_asset_dropbox_not_found(self, storage_manager_dropbox):
        """Test finding a non-existent asset in Dropbox."""
        # Mock ApiError for folder not found
        error = ApiError("", Mock(), "", "")
        storage_manager_dropbox.dbx.files_list_folder.side_effect = error
        
        result = storage_manager_dropbox.find_asset("nonexistent")
        
        assert result is None
    
    @pytest.mark.dropbox
    def test_upload_creative_dropbox(self, storage_manager_dropbox, sample_image):
        """Test uploading a creative to Dropbox."""
        output_path = storage_manager_dropbox.upload_creative(
            "test-campaign",
            "Test Product",
            "1:1",
            sample_image
        )
        
        assert output_path is not None
        assert "output/test-campaign" in output_path
        assert "test_product" in output_path.lower()
        assert "1x1.jpg" in output_path
        
        # Verify upload was called
        storage_manager_dropbox.dbx.files_upload.assert_called_once()
    
    @pytest.mark.dropbox
    def test_list_campaign_outputs_dropbox(self, storage_manager_dropbox):
        """Test listing campaign outputs in Dropbox."""
        # Mock Dropbox response
        mock_file1 = Mock(spec=FileMetadata)
        mock_file1.path_display = "/test/output/test-campaign/product1/1x1.jpg"
        
        mock_file2 = Mock(spec=FileMetadata)
        mock_file2.path_display = "/test/output/test-campaign/product2/9x16.jpg"
        
        mock_list_result = Mock()
        mock_list_result.entries = [mock_file1, mock_file2]
        
        storage_manager_dropbox.dbx.files_list_folder.return_value = mock_list_result
        
        outputs = storage_manager_dropbox.list_campaign_outputs("test-campaign")
        
        assert len(outputs) == 2
        assert all("test-campaign" in path for path in outputs)
    
    @pytest.mark.dropbox
    def test_normalize_dropbox_path(self, storage_manager_dropbox):
        """Test Dropbox path normalization."""
        assert storage_manager_dropbox._normalize_dropbox_path("test/path") == "/test/path"
        assert storage_manager_dropbox._normalize_dropbox_path("/test/path") == "/test/path"
        assert storage_manager_dropbox._normalize_dropbox_path("/test//path/") == "/test/path"
        assert storage_manager_dropbox._normalize_dropbox_path("") == ""
    
    @pytest.mark.dropbox
    def test_ensure_dropbox_folder_creates(self, storage_manager_dropbox):
        """Test that ensure_dropbox_folder creates missing folders."""
        # Reset the mock to clear any initialization calls
        storage_manager_dropbox.dbx.files_create_folder_v2.reset_mock()
        storage_manager_dropbox.dbx.files_get_metadata.reset_mock()
        
        # Create proper ApiError for path not found
        from dropbox.files import GetMetadataError, LookupError as DropboxLookupError
        path_error = DropboxLookupError('not_found', None)
        metadata_error = GetMetadataError('path', path_error)
        error = ApiError("", metadata_error, "", "")
        
        storage_manager_dropbox.dbx.files_get_metadata.side_effect = error
        
        storage_manager_dropbox._ensure_dropbox_folder("/test/new_folder")
        
        # Should call create_folder
        storage_manager_dropbox.dbx.files_create_folder_v2.assert_called_once()
    
    @pytest.mark.dropbox
    def test_ensure_dropbox_folder_exists(self, storage_manager_dropbox):
        """Test that ensure_dropbox_folder handles existing folders."""
        # Mock folder exists
        storage_manager_dropbox.dbx.files_get_metadata.return_value = Mock()
        
        storage_manager_dropbox._ensure_dropbox_folder("/test/existing_folder")
        
        # Should not call create_folder
        storage_manager_dropbox.dbx.files_create_folder_v2.assert_not_called()


@pytest.mark.unit
class TestStorageManagerUserAssets:
    """Test suite for user asset upload functionality."""
    
    @pytest.mark.local
    def test_upload_user_assets_local(self, storage_manager_local, temp_storage, sample_image):
        """Test uploading user assets to local storage."""
        # Create temporary files
        temp_file1 = temp_storage['root'] / "upload1.jpg"
        temp_file2 = temp_storage['root'] / "upload2.jpg"
        sample_image.save(temp_file1)
        sample_image.save(temp_file2)
        
        result = storage_manager_local.upload_user_assets([str(temp_file1), str(temp_file2)])
        
        assert result['uploaded_count'] == 2
        assert len(result['files']) == 2
    
    @pytest.mark.dropbox
    def test_upload_user_assets_dropbox(self, storage_manager_dropbox, temp_storage, sample_image):
        """Test uploading user assets to Dropbox."""
        # Create temporary file
        temp_file = temp_storage['root'] / "upload.jpg"
        sample_image.save(temp_file)
        
        result = storage_manager_dropbox.upload_user_assets([str(temp_file)])
        
        assert result['uploaded_count'] == 1
        assert len(result['files']) == 1
        
        # Verify upload was called
        storage_manager_dropbox.dbx.files_upload.assert_called()
    
    @pytest.mark.local
    def test_upload_user_assets_error_handling(self, storage_manager_local, temp_storage):
        """Test error handling in user asset upload."""
        # Try to upload non-existent file
        result = storage_manager_local.upload_user_assets(["/nonexistent/file.jpg"])
        
        # Should handle gracefully
        assert result['uploaded_count'] == 0


@pytest.mark.unit
class TestStorageManagerImageFormats:
    """Test suite for different image format handling."""
    
    @pytest.mark.local
    def test_find_asset_jpg_format(self, storage_manager_local, sample_image, temp_storage):
        """Test finding JPG format assets."""
        asset_folder = temp_storage['assets'] / "test_jpg"
        asset_folder.mkdir()
        sample_image.save(asset_folder / "image.jpg")
        
        result = storage_manager_local.find_asset("test_jpg")
        assert result is not None
    
    @pytest.mark.local
    def test_find_asset_png_format(self, storage_manager_local, sample_image, temp_storage):
        """Test finding PNG format assets."""
        asset_folder = temp_storage['assets'] / "test_png"
        asset_folder.mkdir()
        sample_image.save(asset_folder / "image.png")
        
        result = storage_manager_local.find_asset("test_png")
        assert result is not None
    
    @pytest.mark.local
    def test_find_asset_webp_format(self, storage_manager_local, sample_image, temp_storage):
        """Test finding WebP format assets."""
        asset_folder = temp_storage['assets'] / "test_webp"
        asset_folder.mkdir()
        sample_image.save(asset_folder / "image.webp", 'WEBP')
        
        result = storage_manager_local.find_asset("test_webp")
        assert result is not None


@pytest.mark.unit
class TestStorageManagerAspectRatios:
    """Test suite for aspect ratio filename handling."""
    
    @pytest.mark.local
    def test_aspect_ratio_filename_conversion(self, storage_manager_local, sample_image, temp_storage):
        """Test that aspect ratios are converted to filename format."""
        # 1:1 -> 1x1.jpg
        path = storage_manager_local.upload_creative(
            "test", "product", "1:1", sample_image
        )
        assert "1x1.jpg" in path
        
        # 9:16 -> 9x16.jpg
        path = storage_manager_local.upload_creative(
            "test", "product", "9:16", sample_image
        )
        assert "9x16.jpg" in path
        
        # 16:9 -> 16x9.jpg
        path = storage_manager_local.upload_creative(
            "test", "product", "16:9", sample_image
        )
        assert "16x9.jpg" in path

