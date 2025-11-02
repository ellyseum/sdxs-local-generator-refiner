from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import uuid

from services.hf_downloader import HFDownloader
from services.model_loader import ModelLoader
from services.pipeline import SDXSPipeline
from services.refiner import RefinerService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create directories
MODELS_DIR = ROOT_DIR / 'models'
IMAGES_DIR = ROOT_DIR / 'data' / 'images'
REFINED_IMAGES_DIR = ROOT_DIR / 'data' / 'images' / 'refined'
MODELS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
REFINED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Initialize services
hf_downloader = HFDownloader(MODELS_DIR)
model_loader = ModelLoader()
sdxs_pipeline = SDXSPipeline(model_loader, IMAGES_DIR)
refiner_service = RefinerService(MODELS_DIR, IMAGES_DIR, REFINED_IMAGES_DIR)

# Models
class ModelPrepareRequest(BaseModel):
    modelCardUrl: str

class ModelPrepareResponse(BaseModel):
    ok: bool
    repoId: str
    message: str

class GenerateRequest(BaseModel):
    prompt: str
    size: Optional[str] = '512x512'
    steps: Optional[int] = 8
    guidance: Optional[float] = 4.0
    seed: Optional[int] = None

class GenerateResponse(BaseModel):
    ok: bool
    imagePath: str
    filename: str

class RefinerPrepareRequest(BaseModel):
    modelCardUrl: str
    modelType: str  # "small-sd-v0"

class RefinerPrepareResponse(BaseModel):
    ok: bool
    modelType: str
    message: str

class RefineRequest(BaseModel):
    originalImageFilename: str
    refinementPrompt: str
    modelType: str  # "sdxs" or "small-sd-v0"
    strength: Optional[float] = 0.75
    steps: Optional[int] = 20
    guidance: Optional[float] = 7.5
    seed: Optional[int] = None

class RefineResponse(BaseModel):
    ok: bool
    refinedImagePath: str
    filename: str

# Routes
@api_router.get("/")
async def root():
    return {"message": "SD-XS Local Image Generation API"}

@api_router.post("/model/prepare", response_model=ModelPrepareResponse)
async def prepare_model(request: ModelPrepareRequest):
    try:
        logger.info(f"Preparing model from {request.modelCardUrl}")
        
        # Download model
        repo_id = hf_downloader.parse_repo_id(request.modelCardUrl)
        model_path = await hf_downloader.download_model(repo_id)
        
        # Load model into memory
        await model_loader.load_model(repo_id, model_path)
        
        return ModelPrepareResponse(
            ok=True,
            repoId=repo_id,
            message=f"Model {repo_id} loaded successfully"
        )
    except Exception as e:
        logger.error(f"Error preparing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate", response_model=GenerateResponse)
async def generate_image(request: GenerateRequest):
    try:
        logger.info(f"Generating image for prompt: {request.prompt}")
        
        # Check if model is loaded
        if not model_loader.is_loaded():
            raise HTTPException(status_code=400, detail="No model loaded. Please prepare a model first.")
        
        # Generate image
        image_path = await sdxs_pipeline.generate(
            prompt=request.prompt,
            size=request.size,
            steps=request.steps,
            guidance=request.guidance,
            seed=request.seed
        )
        
        filename = Path(image_path).name
        
        return GenerateResponse(
            ok=True,
            imagePath=f"/api/images/{filename}",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/images/{filename}")
async def get_image(filename: str):
    image_path = IMAGES_DIR / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)

@api_router.get("/images/refined/{filename}")
async def get_refined_image(filename: str):
    image_path = REFINED_IMAGES_DIR / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Refined image not found")
    return FileResponse(image_path)

@api_router.post("/refiner/prepare", response_model=RefinerPrepareResponse)
async def prepare_refiner(request: RefinerPrepareRequest):
    try:
        logger.info(f"Preparing refiner model: {request.modelType}")
        
        if request.modelType == "sdxs":
            # SDXS is already loaded, just link it to refiner
            if not model_loader.is_loaded():
                raise HTTPException(status_code=400, detail="SDXS model not loaded. Please load SDXS first.")
            
            refiner_service.set_sdxs_pipeline(model_loader.get_pipeline())
            return RefinerPrepareResponse(
                ok=True,
                modelType="sdxs",
                message="SDXS refiner ready (using existing model)"
            )
        
        elif request.modelType == "small-sd-v0":
            # Download and load Small SD V0
            repo_id = hf_downloader.parse_repo_id(request.modelCardUrl)
            model_path = await hf_downloader.download_model(repo_id)
            await refiner_service.load_refiner_model("small-sd-v0", repo_id, model_path)
            
            return RefinerPrepareResponse(
                ok=True,
                modelType="small-sd-v0",
                message=f"Small SD V0 refiner loaded successfully"
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model type: {request.modelType}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing refiner: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/refiner/refine", response_model=RefineResponse)
async def refine_image(request: RefineRequest):
    try:
        logger.info(f"Refining image with {request.modelType}: {request.originalImageFilename}")
        
        # Check if refiner is loaded
        if not refiner_service.is_refiner_loaded(request.modelType):
            raise HTTPException(status_code=400, detail=f"Refiner model {request.modelType} not loaded. Please prepare it first.")
        
        # Refine image
        refined_path = await refiner_service.refine_image(
            original_image_filename=request.originalImageFilename,
            refinement_prompt=request.refinementPrompt,
            model_type=request.modelType,
            strength=request.strength,
            steps=request.steps,
            guidance=request.guidance,
            seed=request.seed
        )
        
        filename = Path(refined_path).name
        
        return RefineResponse(
            ok=True,
            refinedImagePath=f"/api/images/refined/{filename}",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refining image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
