"""
Unit tests for ImageGenerator.
"""

import pytest
import io
from unittest.mock import MagicMock, patch
from PIL import Image
from modules.image_generator import ImageGenerator


@pytest.mark.unit
class TestImageGenerator:
    """Test suite for ImageGenerator."""
    
    def test_initialization(self, mock_config):
        """Test ImageGenerator initializes correctly."""
        with patch('modules.image_generator.genai.Client') as mock_client:
            generator = ImageGenerator(mock_config)
            
            assert generator.config == mock_config
            assert generator.model == "gemini-2.5-flash-image"
    
    def test_generate_product_image_1_1(self, mock_config, sample_image):
        """Test generating 1:1 aspect ratio image."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Convert sample image to bytes
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            # Mock response
            mock_chunk = MagicMock()
            mock_chunk.candidates = [MagicMock()]
            mock_chunk.candidates[0].content = MagicMock()
            mock_chunk.candidates[0].content.parts = [MagicMock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            result = generator.generate_product_image(
                "Test Product",
                "A quality test product",
                "1:1"
            )
            
            assert isinstance(result, Image.Image)
            assert result.mode == "RGB"
    
    def test_generate_product_image_9_16(self, mock_config, sample_image):
        """Test generating 9:16 aspect ratio image."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            mock_chunk = MagicMock()
            mock_chunk.candidates = [MagicMock()]
            mock_chunk.candidates[0].content = MagicMock()
            mock_chunk.candidates[0].content.parts = [MagicMock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            result = generator.generate_product_image(
                "Test Product",
                "A quality test product",
                "9:16"
            )
            
            assert isinstance(result, Image.Image)
    
    def test_generate_product_image_16_9(self, mock_config, sample_image):
        """Test generating 16:9 aspect ratio image."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            mock_chunk = MagicMock()
            mock_chunk.candidates = [MagicMock()]
            mock_chunk.candidates[0].content = MagicMock()
            mock_chunk.candidates[0].content.parts = [MagicMock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            result = generator.generate_product_image(
                "Test Product",
                "A quality test product",
                "16:9"
            )
            
            assert isinstance(result, Image.Image)
    
    def test_generate_with_locale(self, mock_config, sample_image):
        """Test image generation with locale parameter."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            mock_chunk = MagicMock()
            mock_chunk.candidates = [MagicMock()]
            mock_chunk.candidates[0].content = MagicMock()
            mock_chunk.candidates[0].content.parts = [MagicMock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def mock_stream(*args, **kwargs):
                # Verify locale is considered in prompt
                contents = kwargs.get('contents', args[1] if len(args) > 1 else [])
                if contents and len(contents) > 0:
                    prompt_text = str(contents[0])
                    # Should contain Spanish reference
                    assert 'Spanish' in prompt_text or 'es_ES' in str(kwargs)
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            result = generator.generate_product_image(
                "Producto de Prueba",
                "Un producto de calidad",
                "1:1",
                locale="es_ES"
            )
            
            assert isinstance(result, Image.Image)
    
    def test_generate_all_aspect_ratios(self, mock_config, sample_image):
        """Test generating all three aspect ratios."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            mock_chunk = MagicMock()
            mock_chunk.candidates = [MagicMock()]
            mock_chunk.candidates[0].content = MagicMock()
            mock_chunk.candidates[0].content.parts = [MagicMock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            results = generator.generate_all_aspect_ratios(
                "Test Product",
                "A quality test product"
            )
            
            assert len(results) == 3
            assert "1:1" in results
            assert "9:16" in results
            assert "16:9" in results
            assert all(isinstance(img, Image.Image) for img in results.values())
    
    def test_no_image_data_error(self, mock_config):
        """Test handling when no image data is returned."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock empty response
            mock_chunk = MagicMock()
            mock_chunk.candidates = []
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            with pytest.raises(Exception) as exc_info:
                generator.generate_product_image(
                    "Test Product",
                    "Description",
                    "1:1"
                )
            
            assert "No image data" in str(exc_info.value)
    
    def test_api_exception_handling(self, mock_config):
        """Test handling of API exceptions."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            def mock_stream(*args, **kwargs):
                raise Exception("API connection failed")
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            with pytest.raises(Exception) as exc_info:
                generator.generate_product_image(
                    "Test Product",
                    "Description",
                    "1:1"
                )
            
            assert "Failed to generate image" in str(exc_info.value)
    
    def test_generate_all_ratios_partial_failure(self, mock_config, sample_image):
        """Test that if one ratio fails, exception is raised."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            call_count = [0]
            
            def mock_stream(*args, **kwargs):
                call_count[0] += 1
                
                # First two calls succeed
                if call_count[0] <= 2:
                    buffer = io.BytesIO()
                    sample_image.save(buffer, format='JPEG')
                    image_bytes = buffer.getvalue()
                    
                    mock_chunk = MagicMock()
                    mock_chunk.candidates = [MagicMock()]
                    mock_chunk.candidates[0].content = MagicMock()
                    mock_chunk.candidates[0].content.parts = [MagicMock()]
                    mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
                    mock_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
                    
                    yield mock_chunk
                else:
                    # Third call fails
                    raise Exception("Generation failed")
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            with pytest.raises(Exception):
                generator.generate_all_aspect_ratios(
                    "Test Product",
                    "Description"
                )
    
    def test_log_callback(self, mock_config, sample_image, log_callback):
        """Test that log callback receives messages."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            mock_chunk = MagicMock()
            mock_chunk.candidates = [MagicMock()]
            mock_chunk.candidates[0].content = MagicMock()
            mock_chunk.candidates[0].content.parts = [MagicMock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            generator.generate_product_image(
                "Test Product",
                "Description",
                "1:1",
                log_callback=log_callback
            )
            
            assert len(log_callback.logs) > 0
            assert any("Generating" in log or "Generated" in log for log in log_callback.logs)
    
    def test_invalid_image_data(self, mock_config):
        """Test handling of invalid image data."""
        with patch('modules.image_generator.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock invalid image bytes
            mock_chunk = MagicMock()
            mock_chunk.candidates = [MagicMock()]
            mock_chunk.candidates[0].content = MagicMock()
            mock_chunk.candidates[0].content.parts = [MagicMock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = b'invalid image data'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            generator = ImageGenerator(mock_config)
            
            with pytest.raises(Exception):
                generator.generate_product_image(
                    "Test Product",
                    "Description",
                    "1:1"
                )

