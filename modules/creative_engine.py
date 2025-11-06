"""
Creative engine for image processing and text overlay operations.
"""

from typing import Tuple
from PIL import Image, ImageDraw, ImageFont


class CreativeEngine:
    """
    Handles PIL/Pillow image operations including resize, crop, and text overlay.
    """
    
    def __init__(self):
        """Initialize creative engine with aspect ratio configurations."""
        # Define target sizes for each aspect ratio
        self.aspect_ratios = {
            "1:1": (1080, 1080),      # Square - Instagram posts
            "9:16": (1080, 1920),     # Portrait - Instagram stories, TikTok
            "16:9": (1920, 1080)      # Landscape - YouTube, Facebook
        }
        
        # Load fonts
        self._load_fonts()
        
        print("✓ CreativeEngine initialized")
    
    def _load_fonts(self):
        """Load fonts with fallback to default."""
        try:
            # Try to load system fonts
            self.heading_font = ImageFont.truetype("Arial.ttf", 60)
            self.message_font = ImageFont.truetype("Arial.ttf", 48)
            self.product_font = ImageFont.truetype("Arial.ttf", 36)
        except:
            try:
                # Try alternative font names
                self.heading_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
                self.message_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
                self.product_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                # Fall back to default
                self.heading_font = ImageFont.load_default()
                self.message_font = ImageFont.load_default()
                self.product_font = ImageFont.load_default()
    
    def _get_responsive_fonts(self, image_width: int, image_height: int):
        """Get fonts sized responsively based on image dimensions."""
        try:
            base_size = min(image_width, image_height)
            message_size = max(24, base_size // 25)
            product_size = max(18, base_size // 35)
            
            message_font = ImageFont.truetype("Arial.ttf", message_size)
            product_font = ImageFont.truetype("Arial.ttf", product_size)
            return message_font, product_font
        except:
            try:
                base_size = min(image_width, image_height)
                message_size = max(24, base_size // 25)
                product_size = max(18, base_size // 35)
                
                message_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", message_size)
                product_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", product_size)
                return message_font, product_font
            except:
                return ImageFont.load_default(), ImageFont.load_default()
    
    def resize_to_aspect_ratio(self, image: Image.Image, aspect_ratio: str) -> Image.Image:
        """
        Resize and crop image to target aspect ratio.
        
        Args:
            image: Source PIL Image
            aspect_ratio: Target aspect ratio ("1:1", "9:16", "16:9")
        
        Returns:
            PIL Image resized and cropped to target dimensions
        """
        if aspect_ratio not in self.aspect_ratios:
            raise ValueError(f"Invalid aspect ratio: {aspect_ratio}")
        
        target_size = self.aspect_ratios[aspect_ratio]
        target_width, target_height = target_size
        
        # Calculate aspect ratios
        source_ratio = image.width / image.height
        target_ratio = target_width / target_height
        
        # Determine resize dimensions to fill target while maintaining aspect ratio
        if source_ratio > target_ratio:
            # Image is wider than target - fit by height
            new_height = target_height
            new_width = int(new_height * source_ratio)
        else:
            # Image is taller than target - fit by width
            new_width = target_width
            new_height = int(new_width / source_ratio)
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate crop box to center the image
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        # Crop to exact target size
        cropped = resized.crop((left, top, right, bottom))
        
        return cropped
    
    def _draw_wrapped_text(self, draw: ImageDraw.Draw, text: str, 
                          x: int, y: int, max_width: int, 
                          font: ImageFont.FreeTypeFont, fill: str) -> int:
        """
        Draw text with word wrapping.
        
        Args:
            draw: ImageDraw object
            text: Text to draw
            x, y: Starting position
            max_width: Maximum width for text
            font: Font to use
            fill: Text color
        
        Returns:
            int: Total height of drawn text
        """
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add anyway
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate line height
        bbox = draw.textbbox((0, 0), "Ay", font=font)
        line_height = bbox[3] - bbox[1] + 10
        
        # Draw each line
        current_y = y
        for line in lines:
            draw.text((x, current_y), line, fill=fill, font=font)
            current_y += line_height
        
        return current_y - y
    
    def add_text_overlay(self, image: Image.Image, campaign_message: str, 
                        product_name: str) -> Image.Image:
        """
        Add campaign message and product name as text overlay.
        
        Args:
            image: Source PIL Image
            campaign_message: Campaign message text
            product_name: Product name text
        
        Returns:
            PIL Image with text overlay
        """
        # Create a copy to avoid modifying original
        img_with_text = image.copy()
        width, height = img_with_text.size
        
        # Get responsive fonts
        message_font, product_font = self._get_responsive_fonts(width, height)
        
        # Create semi-transparent overlay
        overlay = Image.new('RGBA', img_with_text.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Add slimmer dark overlay at bottom for campaign message (reduced from 1/3 to 1/6)
        overlay_height = height // 6
        overlay_draw.rectangle(
            [0, height - overlay_height, width, height],
            fill=(0, 0, 0, 180)
        )
        
        # Composite overlay onto image
        img_with_text = Image.alpha_composite(img_with_text.convert('RGBA'), overlay)
        img_with_text = img_with_text.convert('RGB')
        
        # Draw text on the composite image
        draw = ImageDraw.Draw(img_with_text)
        
        # Add campaign message at bottom with minimal padding
        message_y = height - overlay_height + 15
        padding = 30
        self._draw_wrapped_text(
            draw, 
            campaign_message, 
            padding, 
            message_y, 
            width - (padding * 2), 
            message_font, 
            "white"
        )
        
        # Add product name at top
        product_y = 30
        draw.text((padding, product_y), product_name.upper(), fill="black", font=product_font)
        
        return img_with_text
    
    def process_creative(self, base_image: Image.Image, aspect_ratio: str, 
                        campaign_message: str, product_name: str) -> Image.Image:
        """
        Process a complete creative: resize and add text overlay.
        
        Args:
            base_image: Source PIL Image
            aspect_ratio: Target aspect ratio
            campaign_message: Campaign message text
            product_name: Product name text
        
        Returns:
            PIL Image ready for output
        """
        # Resize to aspect ratio
        resized = self.resize_to_aspect_ratio(base_image, aspect_ratio)
        
        # Add text overlay
        final = self.add_text_overlay(resized, campaign_message, product_name)
        
        return final

