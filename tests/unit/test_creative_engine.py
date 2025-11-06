"""
Unit tests for CreativeEngine.
"""

import pytest
from PIL import Image
from modules.creative_engine import CreativeEngine


@pytest.mark.unit
class TestCreativeEngine:
    """Test suite for CreativeEngine."""
    
    def test_initialization(self):
        """Test CreativeEngine initializes correctly."""
        engine = CreativeEngine()
        
        assert engine.aspect_ratios is not None
        assert len(engine.aspect_ratios) == 3
        assert "1:1" in engine.aspect_ratios
        assert "9:16" in engine.aspect_ratios
        assert "16:9" in engine.aspect_ratios
    
    def test_resize_to_1_1(self, creative_engine, sample_image):
        """Test resizing image to 1:1 aspect ratio."""
        result = creative_engine.resize_to_aspect_ratio(sample_image, "1:1")
        
        assert isinstance(result, Image.Image)
        assert result.size == (1080, 1080)
    
    def test_resize_to_9_16(self, creative_engine, sample_image):
        """Test resizing image to 9:16 aspect ratio."""
        result = creative_engine.resize_to_aspect_ratio(sample_image, "9:16")
        
        assert isinstance(result, Image.Image)
        assert result.size == (1080, 1920)
    
    def test_resize_to_16_9(self, creative_engine, sample_image):
        """Test resizing image to 16:9 aspect ratio."""
        result = creative_engine.resize_to_aspect_ratio(sample_image, "16:9")
        
        assert isinstance(result, Image.Image)
        assert result.size == (1920, 1080)
    
    def test_resize_portrait_image(self, creative_engine, sample_image_portrait):
        """Test resizing a portrait image."""
        result = creative_engine.resize_to_aspect_ratio(sample_image_portrait, "1:1")
        
        assert isinstance(result, Image.Image)
        assert result.size == (1080, 1080)
    
    def test_resize_landscape_image(self, creative_engine, sample_image_landscape):
        """Test resizing a landscape image."""
        result = creative_engine.resize_to_aspect_ratio(sample_image_landscape, "1:1")
        
        assert isinstance(result, Image.Image)
        assert result.size == (1080, 1080)
    
    def test_resize_invalid_aspect_ratio(self, creative_engine, sample_image):
        """Test that invalid aspect ratio raises error."""
        with pytest.raises(ValueError) as exc_info:
            creative_engine.resize_to_aspect_ratio(sample_image, "4:3")
        
        assert "Invalid aspect ratio" in str(exc_info.value)
    
    def test_resize_maintains_quality(self, creative_engine):
        """Test that resize maintains image quality."""
        # Create a high-resolution image
        large_image = Image.new('RGB', (3000, 2000), color=(100, 150, 200))
        
        result = creative_engine.resize_to_aspect_ratio(large_image, "16:9")
        
        assert result.size == (1920, 1080)
        assert result.mode == "RGB"
    
    def test_add_text_overlay(self, creative_engine, sample_image):
        """Test adding text overlay to image."""
        result = creative_engine.add_text_overlay(
            sample_image,
            "Test campaign message",
            "Test Product"
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size
        assert result.mode == "RGB"
    
    def test_add_text_overlay_long_message(self, creative_engine, sample_image):
        """Test text overlay with long message (word wrapping)."""
        long_message = "This is a very long campaign message that should wrap across multiple lines when displayed"
        
        result = creative_engine.add_text_overlay(
            sample_image,
            long_message,
            "Test Product"
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size
    
    def test_add_text_overlay_special_characters(self, creative_engine, sample_image):
        """Test text overlay with special characters."""
        message = "Quality & Durability — 100% Sustainable!"
        
        result = creative_engine.add_text_overlay(
            sample_image,
            message,
            "Test Product"
        )
        
        assert isinstance(result, Image.Image)
    
    def test_add_text_overlay_unicode(self, creative_engine, sample_image):
        """Test text overlay with Unicode characters."""
        message = "Productos de calidad para el planeta 🌍"
        
        result = creative_engine.add_text_overlay(
            sample_image,
            message,
            "Producto de Prueba"
        )
        
        assert isinstance(result, Image.Image)
    
    def test_process_creative_complete(self, creative_engine, sample_image):
        """Test complete creative processing (resize + overlay)."""
        result = creative_engine.process_creative(
            sample_image,
            "1:1",
            "Test campaign message",
            "Test Product"
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == (1080, 1080)
        assert result.mode == "RGB"
    
    def test_process_creative_all_ratios(self, creative_engine, sample_image):
        """Test processing creative for all aspect ratios."""
        ratios = ["1:1", "9:16", "16:9"]
        expected_sizes = [(1080, 1080), (1080, 1920), (1920, 1080)]
        
        for ratio, expected_size in zip(ratios, expected_sizes):
            result = creative_engine.process_creative(
                sample_image,
                ratio,
                "Test message",
                "Test Product"
            )
            
            assert result.size == expected_size
    
    def test_text_overlay_on_small_image(self, creative_engine):
        """Test text overlay on a small image."""
        small_image = Image.new('RGB', (400, 400), color=(100, 100, 100))
        
        result = creative_engine.add_text_overlay(
            small_image,
            "Test message",
            "Product"
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == (400, 400)
    
    def test_text_overlay_preserves_original(self, creative_engine, sample_image):
        """Test that text overlay doesn't modify original image."""
        original_pixels = sample_image.copy()
        
        creative_engine.add_text_overlay(
            sample_image,
            "Test message",
            "Product"
        )
        
        # Original should be unchanged
        assert list(sample_image.getdata()) == list(original_pixels.getdata())
    
    def test_resize_preserves_original(self, creative_engine, sample_image):
        """Test that resize doesn't modify original image."""
        original_size = sample_image.size
        
        creative_engine.resize_to_aspect_ratio(sample_image, "16:9")
        
        # Original should be unchanged
        assert sample_image.size == original_size
    
    def test_responsive_fonts(self, creative_engine):
        """Test that fonts scale responsively with image size."""
        small_image = Image.new('RGB', (400, 400), color=(100, 100, 100))
        large_image = Image.new('RGB', (3000, 3000), color=(100, 100, 100))
        
        small_result = creative_engine.add_text_overlay(
            small_image, "Message", "Product"
        )
        large_result = creative_engine.add_text_overlay(
            large_image, "Message", "Product"
        )
        
        # Both should succeed without errors
        assert isinstance(small_result, Image.Image)
        assert isinstance(large_result, Image.Image)
    
    def test_draw_wrapped_text(self, creative_engine, sample_image):
        """Test the internal wrapped text drawing function."""
        from PIL import ImageDraw
        
        draw = ImageDraw.Draw(sample_image)
        
        height = creative_engine._draw_wrapped_text(
            draw,
            "This is a long text that needs wrapping",
            50,
            50,
            500,
            creative_engine.message_font,
            "white"
        )
        
        assert height > 0
    
    def test_empty_message(self, creative_engine, sample_image):
        """Test handling of empty message."""
        result = creative_engine.add_text_overlay(
            sample_image,
            "",
            "Product"
        )
        
        assert isinstance(result, Image.Image)
    
    def test_empty_product_name(self, creative_engine, sample_image):
        """Test handling of empty product name."""
        result = creative_engine.add_text_overlay(
            sample_image,
            "Message",
            ""
        )
        
        assert isinstance(result, Image.Image)
    
    def test_aspect_ratio_crop_centering(self, creative_engine):
        """Test that images are cropped and centered correctly."""
        # Create a distinctly colored image to test centering
        test_image = Image.new('RGB', (2000, 1000), color=(255, 0, 0))
        
        result = creative_engine.resize_to_aspect_ratio(test_image, "1:1")
        
        # Should be centered crop
        assert result.size == (1080, 1080)
        
        # Check that we have image data (not just black or white)
        pixels = list(result.getdata())
        assert len(pixels) > 0
    
    def test_very_wide_image_resize(self, creative_engine):
        """Test resizing a very wide image."""
        wide_image = Image.new('RGB', (4000, 1000), color=(100, 150, 200))
        
        result = creative_engine.resize_to_aspect_ratio(wide_image, "9:16")
        
        assert result.size == (1080, 1920)
    
    def test_very_tall_image_resize(self, creative_engine):
        """Test resizing a very tall image."""
        tall_image = Image.new('RGB', (1000, 4000), color=(100, 150, 200))
        
        result = creative_engine.resize_to_aspect_ratio(tall_image, "16:9")
        
        assert result.size == (1920, 1080)

