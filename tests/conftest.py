"""
Shared fixtures for pytest test suite.
"""

import os
import io
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
import yaml

# Mock environment variables for testing
os.environ['GEMINI_API_KEY'] = 'test_key_12345'


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv('GEMINI_API_KEY', 'test_key_12345')
    monkeypatch.setenv('DROPBOX_ACCESS_TOKEN', 'test_token_12345')
    monkeypatch.setenv('DROPBOX_BASE_PATH', '/test')
    return {
        'GEMINI_API_KEY': 'test_key_12345',
        'DROPBOX_ACCESS_TOKEN': 'test_token_12345',
        'DROPBOX_BASE_PATH': '/test'
    }


@pytest.fixture
def mock_env_no_dropbox(monkeypatch):
    """Set up test environment without Dropbox credentials."""
    monkeypatch.setenv('GEMINI_API_KEY', 'test_key_12345')
    monkeypatch.delenv('DROPBOX_ACCESS_TOKEN', raising=False)
    monkeypatch.delenv('DROPBOX_REFRESH_TOKEN', raising=False)
    monkeypatch.delenv('DROPBOX_APP_KEY', raising=False)
    monkeypatch.delenv('DROPBOX_APP_SECRET', raising=False)
    return {'GEMINI_API_KEY': 'test_key_12345'}


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directories."""
    assets_dir = tmp_path / "assets"
    output_dir = tmp_path / "output"
    assets_dir.mkdir()
    output_dir.mkdir()
    
    return {
        'root': tmp_path,
        'assets': assets_dir,
        'output': output_dir
    }


@pytest.fixture
def sample_image():
    """Create a simple test image."""
    img = Image.new('RGB', (1080, 1080), color=(70, 130, 180))
    return img


@pytest.fixture
def sample_image_portrait():
    """Create a portrait test image."""
    img = Image.new('RGB', (1080, 1920), color=(100, 150, 100))
    return img


@pytest.fixture
def sample_image_landscape():
    """Create a landscape test image."""
    img = Image.new('RGB', (1920, 1080), color=(180, 100, 100))
    return img


@pytest.fixture
def test_images_path():
    """Return path to test images directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_brief():
    """Load valid sample campaign brief."""
    brief_path = Path(__file__).parent / "test_data" / "sample_brief.yaml"
    with open(brief_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_brief_invalid():
    """Load invalid sample campaign brief."""
    brief_path = Path(__file__).parent / "test_data" / "sample_brief_invalid.yaml"
    with open(brief_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_brief_noncompliant():
    """Load non-compliant sample campaign brief."""
    brief_path = Path(__file__).parent / "test_data" / "sample_brief_noncompliant.yaml"
    with open(brief_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def mock_config(temp_storage, monkeypatch):
    """Create a mock AppConfig for testing."""
    monkeypatch.setenv('GEMINI_API_KEY', 'test_key_12345')
    
    # Import after setting env vars
    from config import AppConfig
    
    config = AppConfig()
    config.LOCAL_ASSETS_DIR = temp_storage['assets']
    config.LOCAL_OUTPUT_DIR = temp_storage['output']
    
    return config


@pytest.fixture
def mock_config_with_dropbox(temp_storage, monkeypatch):
    """Create a mock AppConfig with Dropbox credentials."""
    monkeypatch.setenv('GEMINI_API_KEY', 'test_key_12345')
    monkeypatch.setenv('DROPBOX_ACCESS_TOKEN', 'test_token_12345')
    monkeypatch.setenv('DROPBOX_BASE_PATH', '/test')
    
    from config import AppConfig
    
    config = AppConfig()
    config.LOCAL_ASSETS_DIR = temp_storage['assets']
    config.LOCAL_OUTPUT_DIR = temp_storage['output']
    
    return config


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    mock_client = MagicMock()
    
    # Mock text generation response
    def mock_generate_text(*args, **kwargs):
        """Mock text generation stream."""
        mock_chunk = MagicMock()
        mock_chunk.text = '{"compliant": true, "reason": "Test passed"}'
        yield mock_chunk
    
    mock_client.models.generate_content_stream = mock_generate_text
    
    return mock_client


@pytest.fixture
def mock_gemini_image_response(sample_image):
    """Create a mock Gemini image generation response."""
    def create_mock_stream(*args, **kwargs):
        """Mock image generation stream."""
        # Convert PIL image to bytes
        buffer = io.BytesIO()
        sample_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        # Create mock response with proper inline_data
        mock_chunk = MagicMock()
        mock_chunk.candidates = [MagicMock()]
        mock_chunk.candidates[0].content = MagicMock()
        mock_chunk.candidates[0].content.parts = [MagicMock()]
        
        # Create a proper mock for inline_data with data attribute
        mock_inline_data = MagicMock()
        mock_inline_data.data = image_bytes
        mock_chunk.candidates[0].content.parts[0].inline_data = mock_inline_data
        
        yield mock_chunk
    
    return create_mock_stream


@pytest.fixture
def mock_dropbox_client():
    """Create a mock Dropbox client."""
    mock_dbx = MagicMock()
    
    # Mock account info
    mock_account = MagicMock()
    mock_account.email = 'test@example.com'
    mock_dbx.users_get_current_account.return_value = mock_account
    
    # Mock file operations
    mock_dbx.files_get_metadata.return_value = MagicMock()
    mock_dbx.files_create_folder_v2.return_value = MagicMock()
    mock_dbx.files_upload.return_value = MagicMock()
    mock_dbx.files_list_folder.return_value = MagicMock(entries=[])
    
    return mock_dbx


@pytest.fixture
def compliance_agent(mock_config):
    """Create a ComplianceAgent instance with mocked Gemini API."""
    with patch('modules.compliance_agent.genai.Client') as mock_client_class:
        mock_client = mock_gemini_client()
        mock_client_class.return_value = mock_client
        
        from modules.compliance_agent import ComplianceAgent
        agent = ComplianceAgent(mock_config)
        agent.client = mock_client
        
        return agent


@pytest.fixture
def image_generator(mock_config, mock_gemini_image_response):
    """Create an ImageGenerator instance with mocked Gemini API."""
    with patch('modules.image_generator.genai.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client.models.generate_content_stream = mock_gemini_image_response
        mock_client_class.return_value = mock_client
        
        from modules.image_generator import ImageGenerator
        generator = ImageGenerator(mock_config)
        generator.client = mock_client
        
        return generator


@pytest.fixture
def creative_engine():
    """Create a CreativeEngine instance."""
    from modules.creative_engine import CreativeEngine
    return CreativeEngine()


@pytest.fixture
def storage_manager_local(mock_config):
    """Create a StorageManager in local mode."""
    from modules.storage_manager import StorageManager
    manager = StorageManager(mock_config)
    return manager


@pytest.fixture
def storage_manager_dropbox(mock_config_with_dropbox, mock_dropbox_client):
    """Create a StorageManager in Dropbox mode."""
    with patch('modules.storage_manager.dropbox.Dropbox') as mock_dropbox_class:
        mock_dropbox_class.return_value = mock_dropbox_client
        
        from modules.storage_manager import StorageManager
        manager = StorageManager(mock_config_with_dropbox)
        manager.dbx = mock_dropbox_client
        manager.mode = "dropbox"
        
        return manager


@pytest.fixture
def orchestrator(mock_config):
    """Create a CampaignOrchestrator instance with mocked components."""
    with patch('modules.image_generator.genai.Client'), \
         patch('modules.compliance_agent.genai.Client'):
        
        from modules.orchestrator import CampaignOrchestrator
        orch = CampaignOrchestrator(mock_config)
        
        return orch


@pytest.fixture
def fastapi_test_client():
    """Create a FastAPI test client."""
    from fastapi.testclient import TestClient
    from app import app
    
    return TestClient(app)


@pytest.fixture
def log_callback():
    """Create a mock log callback function."""
    logs = []
    
    def callback(message: str):
        logs.append(message)
    
    callback.logs = logs
    return callback


@pytest.fixture(autouse=True)
def suppress_print_statements(monkeypatch):
    """Suppress print statements during tests unless explicitly needed."""
    import builtins
    
    original_print = builtins.print
    
    def mock_print(*args, **kwargs):
        # Only print if PYTEST_VERBOSE is set
        if os.environ.get('PYTEST_VERBOSE'):
            original_print(*args, **kwargs)
    
    # Comment out to enable print suppression
    # monkeypatch.setattr(builtins, 'print', mock_print)

