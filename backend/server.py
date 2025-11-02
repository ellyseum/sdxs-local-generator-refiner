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
