import logging
from pathlib import Path
from typing import Optional, Literal
import uuid
import torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline, DiffusionPipeline

logger = logging.getLogger(__name__)

RefinerModelType = Literal["sdxs", "small-sd-v0"]

class RefinerService:
    """Service for image refinement using img2img pipelines."""
    
    def __init__(self, models_dir: Path, images_dir: Path, refined_images_dir: Path):
        self.models_dir = models_dir
        self.images_dir = images_dir
        self.refined_images_dir = refined_images_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Storage for loaded refiner models
        self.refiner_pipelines = {}
        self.sdxs_pipeline = None  # Will be set from main loader
        
        logger.info(f"RefinerService initialized with device: {self.device}")
    
    def set_sdxs_pipeline(self, pipeline):
        """Set the SDXS pipeline from the main model loader."""
        self.sdxs_pipeline = pipeline
        logger.info("SDXS pipeline linked to refiner service")
    
    async def load_refiner_model(self, model_type: RefinerModelType, repo_id: str, model_path: Path):
        """Load a refiner model (Small SD V0)."""
        try:
            if model_type == "sdxs":
                # SDXS uses the already loaded pipeline
                if self.sdxs_pipeline is None:
                    raise Exception("SDXS pipeline not loaded. Please load SDXS model first.")
                logger.info("Using existing SDXS pipeline for refinement")
                return
            
            elif model_type == "small-sd-v0":
                logger.info(f"Loading Small SD V0 refiner from {model_path}...")
                
                try:
                    # Try loading from local path first
                    pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                        str(model_path),
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        safety_checker=None,
                        use_safetensors=True
                    )
                    logger.info("Loaded Small SD V0 from local path")
                except Exception as e:
                    logger.warning(f"Could not load from local path: {e}")
                    logger.info("Loading Small SD V0 from HuggingFace directly...")
                    pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                        repo_id,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        safety_checker=None,
                        use_safetensors=True
                    )
                
                pipeline = pipeline.to(self.device)
                
                # Enable optimizations
                if self.device == "cuda":
                    try:
                        pipeline.enable_attention_slicing()
                    except:
                        pass
                
                self.refiner_pipelines[model_type] = pipeline
                logger.info(f"Small SD V0 refiner loaded successfully")
            
            else:
                raise ValueError(f"Unknown refiner model type: {model_type}")
                
        except Exception as e:
            logger.error(f"Error loading refiner model: {e}")
            raise Exception(f"Failed to load refiner model: {str(e)}")
    
    def is_refiner_loaded(self, model_type: RefinerModelType) -> bool:
        """Check if a refiner model is loaded."""
        if model_type == "sdxs":
            return self.sdxs_pipeline is not None
        return model_type in self.refiner_pipelines
    
    async def refine_image(
        self,
        original_image_filename: str,
        refinement_prompt: str,
        model_type: RefinerModelType,
        strength: float = 0.75,
        steps: int = 20,
        guidance: float = 7.5,
        seed: Optional[int] = None
    ) -> str:
        """Refine an image using img2img pipeline."""
        try:
            # Check if refiner is loaded
            if not self.is_refiner_loaded(model_type):
                raise Exception(f"Refiner model {model_type} not loaded")
            
            # Load original image
            original_image_path = self.images_dir / original_image_filename
            if not original_image_path.exists():
                raise Exception(f"Original image not found: {original_image_filename}")
            
            original_image = Image.open(original_image_path).convert("RGB")
            logger.info(f"Loaded original image: {original_image_path}")
            
            # Get the appropriate pipeline
            if model_type == "sdxs":
                # Convert SDXS text2img pipeline to img2img on the fly
                # We'll use the same pipeline but with an init image
                pipeline = self.sdxs_pipeline
                use_img2img = False
            else:
                pipeline = self.refiner_pipelines[model_type]
                use_img2img = True
            
            # Set seed for reproducibility
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
            else:
                generator = None
            
            logger.info(f"Refining with {model_type}: strength={strength}, steps={steps}, guidance={guidance}")
            
            # Prepare generation parameters
            if use_img2img or hasattr(pipeline, 'image'):
                # Proper img2img pipeline
                gen_params = {
                    "prompt": refinement_prompt,
                    "image": original_image,
                    "strength": strength,
                    "num_inference_steps": steps,
                    "guidance_scale": guidance,
                    "generator": generator
                }
            else:
                # Fallback for SDXS if it doesn't have img2img
                # We'll try to use it as img2img anyway
                try:
                    # Attempt to create img2img pipeline from existing components
                    from diffusers import StableDiffusionImg2ImgPipeline
                    img2img_pipeline = StableDiffusionImg2ImgPipeline(
                        vae=pipeline.vae,
                        text_encoder=pipeline.text_encoder,
                        tokenizer=pipeline.tokenizer,
                        unet=pipeline.unet,
                        scheduler=pipeline.scheduler,
                        safety_checker=None,
                        feature_extractor=pipeline.feature_extractor if hasattr(pipeline, 'feature_extractor') else None,
                    )
                    img2img_pipeline = img2img_pipeline.to(self.device)
                    
                    gen_params = {
                        "prompt": refinement_prompt,
                        "image": original_image,
                        "strength": strength,
                        "num_inference_steps": steps,
                        "guidance_scale": guidance,
                        "generator": generator
                    }
                    pipeline = img2img_pipeline
                except Exception as e:
                    logger.error(f"Could not create img2img pipeline from SDXS: {e}")
                    raise Exception("SDXS model does not support image refinement. Please use Small SD V0.")
            
            # Generate refined image
            with torch.inference_mode():
                result = pipeline(**gen_params)
            
            refined_image = result.images[0]
            
            # Save refined image
            filename = f"refined_{uuid.uuid4()}.png"
            refined_image_path = self.refined_images_dir / filename
            refined_image.save(refined_image_path)
            
            logger.info(f"Refined image saved to {refined_image_path}")
            return str(refined_image_path)
            
        except Exception as e:
            logger.error(f"Error refining image: {e}")
            raise Exception(f"Failed to refine image: {str(e)}")
