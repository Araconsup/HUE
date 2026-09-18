"""
HUE AI Gateway Management & Image Preprocessing
Handles image resizing, compression, base64 encoding, and request payload preparation.
"""

import io
import base64
import logging
from typing import Tuple, Optional, Dict, Any
from django.conf import settings
from PIL import Image, ImageStat

logger = logging.getLogger('hue.ai.gateway')


class GatewayConfig:
    """Snapshot of AI Gateway configuration from Django settings."""

    @classmethod
    def get_url(cls) -> str:
        return getattr(settings, 'AI_GATEWAY_URL', '').rstrip('/')

    @classmethod
    def get_api_key(cls) -> str:
        return getattr(settings, 'AI_GATEWAY_API_KEY', '')

    @classmethod
    def get_vision_model(cls) -> str:
        return getattr(settings, 'AI_VISION_MODEL', 'gpt-4o')

    @classmethod
    def get_text_model(cls) -> str:
        return getattr(settings, 'AI_TEXT_MODEL', 'gpt-4o-mini')

    @classmethod
    def get_timeout(cls) -> int:
        return int(getattr(settings, 'AI_REQUEST_TIMEOUT', 45))

    @classmethod
    def get_max_image_size(cls) -> int:
        return int(getattr(settings, 'AI_MAX_IMAGE_SIZE', 10 * 1024 * 1024))

    @classmethod
    def is_live_gateway_configured(cls) -> bool:
        """Returns True if a live gateway URL and API key are configured."""
        return bool(cls.get_url() and cls.get_api_key())


class ImageProcessor:
    """Prepares and validates image data before submission to AI models."""

    @staticmethod
    def process_image(image_bytes: bytes, max_dimension: int = 1536) -> Tuple[bool, Optional[str], Optional[bytes], Dict[str, Any]]:
        """
        Validates, resizes, and compresses image.
        Returns: (success, base64_data_uri, compressed_bytes, metadata)
        """
        if not image_bytes:
            return False, None, None, {"error": "Empty image data"}

        if len(image_bytes) > GatewayConfig.get_max_image_size():
            return False, None, None, {"error": "Image file exceeds maximum allowable size of 10MB"}

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Convert RGBA/P/other to RGB for JPEG encoding
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            width, height = image.size

            # Fast local pre-checks
            stats = ImageStat.Stat(image.convert('L'))
            mean_brightness = stats.mean[0]  # 0 (black) to 255 (white)
            variance = stats.var[0] if stats.var else 100.0  # low variance indicates flat or very blurry image

            # Downscale if exceeding max_dimension
            if max(width, height) > max_dimension:
                scale = max_dimension / float(max(width, height))
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                width, height = image.size

            # Compress to JPEG
            out_buf = io.BytesIO()
            image.save(out_buf, format='JPEG', quality=85, optimize=True)
            compressed_bytes = out_buf.getvalue()

            b64_str = base64.b64encode(compressed_bytes).decode('ascii')
            data_uri = f"data:image/jpeg;base64,{b64_str}"

            metadata = {
                "width": width,
                "height": height,
                "mean_brightness": round(mean_brightness, 1),
                "variance": round(variance, 1),
                "is_too_dark": mean_brightness < 25,
                "is_too_bright": mean_brightness > 245,
                "is_likely_flat": variance < 15,
                "size_bytes": len(compressed_bytes),
            }

            return True, data_uri, compressed_bytes, metadata

        except Exception as e:
            logger.exception("Failed to process image")
            return False, None, None, {"error": f"Invalid or corrupt image format: {str(e)}"}
