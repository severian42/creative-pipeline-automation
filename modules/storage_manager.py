"""
Storage manager for handling file operations with Dropbox or local storage.
"""

import io
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from PIL import Image
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError


class StorageManager:
    """
    Abstracts file system operations, routing to Dropbox or local storage.
    """
    
    def __init__(self, config):
        """
        Initialize storage manager with configuration.
        
        Args:
            config: AppConfig instance with storage credentials
        """
        self.config = config
        self.dbx = None
        self.dropbox_base_path = config.DROPBOX_BASE_PATH
        
        # Determine storage mode
        if config.has_dropbox_credentials():
            try:
                # Priority 1: Use simple access token (easiest for development)
                if config.DROPBOX_ACCESS_TOKEN:
                    print("  Using Dropbox access token...")
                    self.dbx = dropbox.Dropbox(
                        oauth2_access_token=config.DROPBOX_ACCESS_TOKEN
                    )
                # Priority 2: Use refresh token flow (for production)
                elif config.DROPBOX_REFRESH_TOKEN and config.DROPBOX_APP_KEY and config.DROPBOX_APP_SECRET:
                    print("  Using Dropbox refresh token flow...")
                    self.dbx = dropbox.Dropbox(
                        oauth2_refresh_token=config.DROPBOX_REFRESH_TOKEN,
                        app_key=config.DROPBOX_APP_KEY,
                        app_secret=config.DROPBOX_APP_SECRET
                    )
                else:
                    raise ValueError("Invalid Dropbox credentials configuration")
                # Test connection
                account = self.dbx.users_get_current_account()
                print(f"✓ Connected to Dropbox account: {account.email}")
                
                # Verify and create base folder structure
                self._verify_dropbox_structure()
                
                self.mode = "dropbox"
                print(f"✓ StorageManager initialized in DROPBOX mode")
                print(f"  Base path: {self.dropbox_base_path if self.dropbox_base_path else '/ (root)'}")
                
            except Exception as e:
                print(f"⚠ Dropbox initialization failed: {e}")
                print(f"  Error details: {type(e).__name__}")
                print("  Falling back to LOCAL mode")
                self.mode = "local"
                self.dbx = None
        else:
            self.mode = "local"
            self.dbx = None
            print("⚠ StorageManager initialized in LOCAL mode (Dropbox credentials not found)")
    
    def _verify_dropbox_structure(self):
        """Verify and create required Dropbox folder structure."""
        if not self.dbx:
            return
        
        try:
            # Create base folders
            required_folders = ["assets", "output"]
            
            for folder_name in required_folders:
                folder_path = f"{self.dropbox_base_path}/{folder_name}" if self.dropbox_base_path else f"/{folder_name}"
                folder_path = self._normalize_dropbox_path(folder_path)
                
                try:
                    self.dbx.files_get_metadata(folder_path)
                    print(f"  ✓ Folder verified: {folder_path}")
                except ApiError:
                    # Folder doesn't exist, create it
                    try:
                        self.dbx.files_create_folder_v2(folder_path)
                        print(f"  ✓ Created folder: {folder_path}")
                    except ApiError as create_error:
                        # Ignore if already exists
                        if "conflict" not in str(create_error).lower():
                            print(f"  ⚠ Could not create {folder_path}: {create_error}")
        except Exception as e:
            print(f"  ⚠ Error verifying folder structure: {e}")
    
    def _normalize_dropbox_path(self, path: str) -> str:
        """Normalize Dropbox path format."""
        if not path:
            return ""
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path
        # Remove duplicate slashes
        while "//" in path:
            path = path.replace("//", "/")
        # Remove trailing slash (except for root)
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]
        return path
    
    def _ensure_dropbox_folder(self, folder_path: str):
        """Ensure a folder exists in Dropbox."""
        if not self.dbx:
            return
        
        try:
            folder_path = self._normalize_dropbox_path(folder_path)
            self.dbx.files_get_metadata(folder_path)
        except ApiError as e:
            if isinstance(e.error, dropbox.files.GetMetadataError) and e.error.is_path():
                # Folder doesn't exist, create it
                try:
                    self.dbx.files_create_folder_v2(folder_path)
                    print(f"  Created Dropbox folder: {folder_path}")
                except ApiError as create_error:
                    # Ignore if folder already exists
                    if not (hasattr(create_error.error, 'is_path') and 
                           hasattr(create_error.error.get_path(), 'is_conflict')):
                        raise
    
    def find_asset(self, asset_filename: str, log_callback=None) -> Optional[Image.Image]:
        """
        Find and load an asset image by filename.
        
        Args:
            asset_filename: Clean filename without extension (e.g., "patagonia_better_sweater")
        
        Returns:
            PIL Image object if found, None otherwise
        """
        if self.mode == "dropbox" and self.dbx:
            return self._find_asset_dropbox(asset_filename, log_callback)
        else:
            return self._find_asset_local(asset_filename, log_callback)
    
    def _find_asset_dropbox(self, asset_filename: str, log_callback=None) -> Optional[Image.Image]:
        """Search for asset in Dropbox."""
        try:
            # Search in assets folder
            search_path = f"{self.dropbox_base_path}/assets/{asset_filename}" if self.dropbox_base_path else f"/assets/{asset_filename}"
            search_path = self._normalize_dropbox_path(search_path)
            
            # List files in the folder
            result = self.dbx.files_list_folder(search_path)
            
            # Look for image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    ext = Path(entry.name).suffix.lower()
                    if ext in image_extensions:
                        # Download and return first match
                        _, response = self.dbx.files_download(entry.path_display)
                        image = Image.open(io.BytesIO(response.content)).convert("RGB")
                        msg = f"  ✓ Asset found in Dropbox: {entry.path_display}"
                        print(msg)
                        if log_callback:
                            log_callback(msg)
                        return image
            
            msg = f"  ✗ Asset not found in Dropbox: {asset_filename}"
            print(msg)
            if log_callback:
                log_callback(msg)
            return None
            
        except ApiError as e:
            msg = f"  ✗ Asset not found in Dropbox: {asset_filename} (folder doesn't exist)"
            print(msg)
            if log_callback:
                log_callback(msg)
            return None
        except Exception as e:
            msg = f"  ✗ Error finding asset in Dropbox: {e}"
            print(msg)
            if log_callback:
                log_callback(msg)
            return None
    
    def _find_asset_local(self, asset_filename: str, log_callback=None) -> Optional[Image.Image]:
        """Search for asset in local storage."""
        try:
            # Search in local assets folder
            asset_folder = self.config.LOCAL_ASSETS_DIR / asset_filename
            
            if not asset_folder.exists():
                msg = f"  ✗ Asset folder not found: {asset_folder}"
                print(msg)
                if log_callback:
                    log_callback(msg)
                return None
            
            # Look for image files
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
            for pattern in image_extensions:
                matches = list(asset_folder.glob(pattern))
                if matches:
                    # Return first match
                    image = Image.open(matches[0]).convert("RGB")
                    msg = f"  ✓ Asset found locally: {matches[0]}"
                    print(msg)
                    if log_callback:
                        log_callback(msg)
                    return image
            
            msg = f"  ✗ No image files found in: {asset_folder}"
            print(msg)
            if log_callback:
                log_callback(msg)
            return None
            
        except Exception as e:
            msg = f"  ✗ Error finding asset locally: {e}"
            print(msg)
            if log_callback:
                log_callback(msg)
            return None
    
    def upload_creative(self, campaign_id: str, product_name: str, 
                       aspect_ratio: str, image: Image.Image, log_callback=None) -> str:
        """
        Upload a final creative image.
        
        Args:
            campaign_id: Campaign identifier
            product_name: Product name
            aspect_ratio: Aspect ratio (e.g., "1:1", "9:16", "16:9")
            image: PIL Image to upload
        
        Returns:
            str: Path where the image was saved
        """
        # Clean product name for path
        clean_product_name = product_name.lower().replace(" ", "_")
        
        # Generate filename
        aspect_ratio_filename = aspect_ratio.replace(":", "x")
        filename = f"{aspect_ratio_filename}.jpg"
        
        if self.mode == "dropbox" and self.dbx:
            return self._upload_creative_dropbox(
                campaign_id, clean_product_name, filename, image, log_callback
            )
        else:
            return self._upload_creative_local(
                campaign_id, clean_product_name, filename, image, log_callback
            )
    
    def _upload_creative_dropbox(self, campaign_id: str, product_name: str, 
                                 filename: str, image: Image.Image, log_callback=None) -> str:
        """Upload creative to Dropbox."""
        try:
            # Construct path
            folder_path = f"{self.dropbox_base_path}/output/{campaign_id}/{product_name}" if self.dropbox_base_path else f"/output/{campaign_id}/{product_name}"
            file_path = f"{folder_path}/{filename}"
            
            # Ensure folder exists
            self._ensure_dropbox_folder(folder_path)
            
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=95)
            buffer.seek(0)
            
            # Upload
            file_path = self._normalize_dropbox_path(file_path)
            self.dbx.files_upload(
                buffer.read(),
                file_path,
                mode=WriteMode.overwrite
            )
            
            msg = f"  ✓ Creative uploaded to Dropbox: {file_path}"
            print(msg)
            if log_callback:
                log_callback(msg)
            return file_path
            
        except Exception as e:
            msg = f"  ✗ Error uploading to Dropbox: {e}"
            print(msg)
            if log_callback:
                log_callback(msg)
            raise
    
    def _upload_creative_local(self, campaign_id: str, product_name: str, 
                               filename: str, image: Image.Image, log_callback=None) -> str:
        """Upload creative to local storage."""
        try:
            # Construct path
            output_folder = self.config.LOCAL_OUTPUT_DIR / campaign_id / product_name
            output_folder.mkdir(parents=True, exist_ok=True)
            
            file_path = output_folder / filename
            
            # Save image
            image.save(file_path, format='JPEG', quality=95)
            
            msg = f"  ✓ Creative saved locally: {file_path}"
            print(msg)
            if log_callback:
                log_callback(msg)
            return str(file_path)
            
        except Exception as e:
            msg = f"  ✗ Error saving locally: {e}"
            print(msg)
            if log_callback:
                log_callback(msg)
            raise
    
    def upload_user_assets(self, image_files: List) -> Dict:
        """
        Upload user-provided asset images.
        
        Args:
            image_files: List of file paths from Gradio upload
        
        Returns:
            dict: Upload results with count and file list
        """
        uploaded_files = []
        
        for file_path in image_files:
            try:
                # Get filename
                filename = Path(file_path).name
                stem = Path(file_path).stem
                
                # Determine destination folder (use stem as folder name)
                if self.mode == "dropbox" and self.dbx:
                    dest_path = f"{self.dropbox_base_path}/assets/{stem}/{filename}" if self.dropbox_base_path else f"/assets/{stem}/{filename}"
                    dest_path = self._normalize_dropbox_path(dest_path)
                    
                    # Ensure folder exists
                    folder_path = f"{self.dropbox_base_path}/assets/{stem}" if self.dropbox_base_path else f"/assets/{stem}"
                    self._ensure_dropbox_folder(folder_path)
                    
                    # Upload
                    with open(file_path, 'rb') as f:
                        self.dbx.files_upload(
                            f.read(),
                            dest_path,
                            mode=WriteMode.overwrite
                        )
                    
                    uploaded_files.append(dest_path)
                    print(f"  ✓ Uploaded to Dropbox: {dest_path}")
                else:
                    # Local storage
                    dest_folder = self.config.LOCAL_ASSETS_DIR / stem
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    dest_path = dest_folder / filename
                    
                    shutil.copy2(file_path, dest_path)
                    uploaded_files.append(str(dest_path))
                    print(f"  ✓ Copied to local storage: {dest_path}")
                    
            except Exception as e:
                print(f"  ✗ Error uploading {file_path}: {e}")
        
        return {
            "uploaded_count": len(uploaded_files),
            "files": uploaded_files
        }
    
    def list_campaign_outputs(self, campaign_id: str) -> List[str]:
        """
        List all output files for a campaign.
        
        Args:
            campaign_id: Campaign identifier
        
        Returns:
            List of file paths
        """
        if self.mode == "dropbox" and self.dbx:
            return self._list_campaign_outputs_dropbox(campaign_id)
        else:
            return self._list_campaign_outputs_local(campaign_id)
    
    def _list_campaign_outputs_dropbox(self, campaign_id: str) -> List[str]:
        """List campaign outputs from Dropbox."""
        try:
            folder_path = f"{self.dropbox_base_path}/output/{campaign_id}" if self.dropbox_base_path else f"/output/{campaign_id}"
            folder_path = self._normalize_dropbox_path(folder_path)
            
            result = self.dbx.files_list_folder(folder_path, recursive=True)
            
            files = []
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    files.append(entry.path_display)
            
            return files
            
        except ApiError:
            return []
    
    def _list_campaign_outputs_local(self, campaign_id: str) -> List[str]:
        """List campaign outputs from local storage."""
        output_folder = self.config.LOCAL_OUTPUT_DIR / campaign_id
        
        if not output_folder.exists():
            return []
        
        files = []
        for file_path in output_folder.rglob("*.jpg"):
            files.append(str(file_path))
        
        return files

