"""
Configuration management for Creative Automation Pipeline.
Loads environment variables and manages application settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AppConfig:
    """Application configuration with environment validation."""
    
    def __init__(self):
        """Initialize configuration and validate required settings."""
        # Required: Gemini API Key
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )
        
        # Optional: Dropbox credentials
        # Option 1: Use simple access token (easiest for development)
        self.DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
        
        # Option 2: Use refresh token flow (for production, long-lived)
        self.DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
        self.DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
        self.DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
        
        # Dropbox base path
        # For "App Folder" access: use empty string "" (app is automatically scoped to /Apps/<app_name>)
        # For "Full Dropbox" access: use full path like "/Creative Automation Pipeline 11-25"
        self.DROPBOX_BASE_PATH = "/"  # Empty for App Folder access
        
        # Local storage paths
        self.LOCAL_ASSETS_DIR = Path("./assets")
        self.LOCAL_OUTPUT_DIR = Path("./output")
        
        # Ensure local directories exist
        self._ensure_local_directories()
        
        # Patagonia brand guidelines
        self._patagonia_guidelines = {
            "core_values": {
                "quality": "Build the best product, provide the best service, and constantly improve everything we do. The best product is useful, versatile, long-lasting, repairable, and recyclable.",
                "integrity": "Examine our practices openly and honestly, learn from our mistakes, and meet our commitments.",
                "environmentalism": "Protect our home planet. We're all part of nature. We work to reduce our impact, share solutions, and embrace regenerative practices. Address the deep connections between environmental destruction and social justice.",
                "justice": "Be just, equitable, and antiracist as a company and in our community. We embrace the work necessary to create equity for historically marginalized people.",
                "not_bound_by_convention": "Do it our way. Our success lies in developing new ways to do things."
            },
            "forbidden_content": {
                "legal": [
                    "Discriminatory language (e.g., 'men only', 'whites only')",
                    "Harmful or violent terms",
                    "Hate speech or offensive content"
                ],
                "brand_voice": [
                    "get rich quick",
                    "guaranteed",
                    "miracle cure",
                    "100% effective",
                    "buy now",
                    "limited time only",
                    "act now",
                    "don't miss out",
                    "scam or false claims",
                    "overly aggressive sales language"
                ]
            },
            "brand_voice_principles": [
                "Focus on quality, durability, and environmental mission",
                "Authentic and transparent communication",
                "Avoid hyperbolic or exaggerated claims",
                "Emphasize repair, reuse, and responsibility",
                "Support social and environmental justice"
            ]
        }
    
    def _ensure_local_directories(self):
        """Create local storage directories if they don't exist."""
        self.LOCAL_ASSETS_DIR.mkdir(exist_ok=True)
        self.LOCAL_OUTPUT_DIR.mkdir(exist_ok=True)
    
    def has_dropbox_credentials(self) -> bool:
        """
        Check if Dropbox credentials are present.
        
        Returns:
            bool: True if access token OR refresh token credentials are set
        """
        # Check for simple access token (easiest)
        if self.DROPBOX_ACCESS_TOKEN:
            return True
        
        # Check for refresh token flow (requires all 3)
        if all([self.DROPBOX_REFRESH_TOKEN, self.DROPBOX_APP_KEY, self.DROPBOX_APP_SECRET]):
            return True
        
        return False
    
    def get_storage_mode(self) -> str:
        """
        Determine the storage mode based on credential availability.
        
        Returns:
            str: "dropbox" if credentials are available, "local" otherwise
        """
        return "dropbox" if self.has_dropbox_credentials() else "local"
    
    def get_patagonia_brand_guidelines(self) -> dict:
        """
        Get Patagonia brand guidelines for compliance checking.
        
        Returns:
            dict: Brand guidelines including values, forbidden content, and voice principles
        """
        return self._patagonia_guidelines


# Global configuration instance
config = AppConfig()

