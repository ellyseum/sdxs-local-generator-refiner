import logging
from pathlib import Path
from typing import Optional
import uuid
import torch
from PIL import Image

from services.model_loader import ModelLoader

logger = logging.getLogger(__name__)

class SDXSPipeline:
    def __init__(self, model_loader: ModelLoader, images_dir: Path):
        self.model_loader = model_loader
        self.images_dir = images_dir
    
    async def generate(
        self,
        prompt: str,
        size: str = '512x512',
        steps: int = 8,
        guidance: float = 4.0,
        seed: Optional[int] = None
    ) -> str:
        """Generate an image using SD-XS pipeline."""
        try:
            # Parse size
            width, height = map(int, size.split('x'))
            
            # Get pipeline
            pipeline = self.model_loader.get_pipeline()
            
            # Set seed for reproducibility
            if seed is not None:
                generator = torch.Generator(device=self.model_loader.device).manual_seed(seed)
            else:
                generator = None
            
            logger.info(f"Generating image: {width}x{height}, steps={steps}, guidance={guidance}")
            
            # Prepare generation parameters
            gen_params = {
                "prompt": prompt,
                "num_inference_steps": steps,
                "width": width,
                "height": height,
                "generator": generator
            }
            
            # Add guidance scale only if supported
            try:
                gen_params["guidance_scale"] = guidance
            except:
                logger.warning("Guidance scale not supported for this model")
            
            # Generate image
            with torch.inference_mode():
                result = pipeline(**gen_params)
            
            image = result.images[0]
            
            # Save image
            filename = f"{uuid.uuid4()}.png"
            image_path = self.images_dir / filename
            image.save(image_path)
            
            logger.info(f"Image saved to {image_path}")
            return str(image_path)
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise Exception(f"Failed to generate image: {str(e)}")
