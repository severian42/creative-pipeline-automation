"""
Image generator using Gemini 2.5 Flash Image API.
"""

import io
import mimetypes
from typing import Dict
from PIL import Image
from google import genai
from google.genai import types


class ImageGenerator:
    """
    Wrapper for Gemini 2.5 Flash Image API to generate product images.
    """
    
    def __init__(self, config):
        """
        Initialize image generator with Gemini API.
        
        Args:
            config: AppConfig instance with API key
        """
        self.config = config
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = "gemini-2.5-flash-image"
        
        print(f"✓ ImageGenerator initialized with model: {self.model}")
    
    def generate_product_image(self, product_name: str, product_description: str, 
                               aspect_ratio: str, locale: str = None, log_callback=None) -> Image.Image:
        """
        Generate a product image for a specific aspect ratio.
        
        Args:
            product_name: Name of the product
            product_description: Detailed product description
            aspect_ratio: Target aspect ratio ("1:1", "9:16", or "16:9")
            locale: Optional locale code (e.g., "en_US", "es_ES") for language context
        
        Returns:
            PIL Image object
        
        Raises:
            Exception: If image generation fails
        """
        # Determine language context for the prompt
        language_context = ""
        if locale:
            language_code = locale.split("_")[0].lower()
            language_names = {
                "en": "English",
                "es": "Spanish",
                "fr": "French",
                "de": "German",
                "it": "Italian",
                "pt": "Portuguese",
                "ja": "Japanese",
                "zh": "Chinese",
                "ko": "Korean",
                "ar": "Arabic"
            }
            language = language_names.get(language_code, "")
            if language:
                language_context = f"Marketing materials for {language}-speaking audience. "
        
        # Construct prompt for professional product photography
        prompt = (
            f"Professional product photography of {product_name}. "
            f"{product_description}. "
            f"{language_context}"
            f"High-quality commercial advertising style. Clean background. "
            f"Studio lighting. Photorealistic. Professional composition."
        )
        
        msg = f"  Generating image for {product_name} at {aspect_ratio}..."
        print(msg)
        if log_callback:
            log_callback(msg)
        
        try:
            # Create content for the request
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            
            # Configure generation
            generate_content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio
                ),
            )
            
            # Generate image
            image_data = None
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                # Check for image data in chunk
                if (chunk.candidates and 
                    chunk.candidates[0].content and 
                    chunk.candidates[0].content.parts):
                    
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        image_data = part.inline_data.data
                        break
            
            if not image_data:
                raise Exception("No image data received from Gemini API")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            
            msg = f"  ✓ Generated image for {product_name} at {aspect_ratio}"
            print(msg)
            if log_callback:
                log_callback(msg)
            return image
            
        except Exception as e:
            error_msg = f"Failed to generate image for {product_name}: {str(e)}"
            msg = f"  ✗ {error_msg}"
            print(msg)
            if log_callback:
                log_callback(msg)
            raise Exception(error_msg)
    
    def generate_all_aspect_ratios(self, product_name: str, 
                                   product_description: str,
                                   locale: str = None,
                                   log_callback=None) -> Dict[str, Image.Image]:
        """
        Generate product images for all required aspect ratios.
        
        Args:
            product_name: Name of the product
            product_description: Detailed product description
            locale: Optional locale code (e.g., "en_US", "es_ES") for language context
        
        Returns:
            dict: Mapping of aspect ratio to PIL Image
                  {"1:1": Image, "9:16": Image, "16:9": Image}
        """
        aspect_ratios = ["1:1", "9:16", "16:9"]
        results = {}
        
        for ratio in aspect_ratios:
            try:
                image = self.generate_product_image(product_name, product_description, ratio, locale, log_callback)
                results[ratio] = image
            except Exception as e:
                msg = f"  ✗ Failed to generate {ratio} for {product_name}: {e}"
                print(msg)
                if log_callback:
                    log_callback(msg)
                # Continue with other ratios even if one fails
                raise
        
        return results

