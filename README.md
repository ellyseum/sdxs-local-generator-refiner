# SDXS Generator & Refiner

A powerful web application for generating and refining images locally using Stable Diffusion XS models from HuggingFace.

## Features

- 🚀 Download and load SD-XS models directly from HuggingFace
- 🎨 Generate images locally using PyTorch + Diffusers
- ✨ **NEW:** Refine generated images with img2img pipelines
- 🔄 **NEW:** Multiple refiner model options (SDXS, Small SD V0)
- 💾 Save generated and refined images to local storage
- 🖥️ Clean, intuitive web interface with conditional workflows
- ⚡ Fast inference with optimized settings

## Tech Stack

- **Backend**: FastAPI (Python) with PyTorch + Diffusers
- **Frontend**: React with Tailwind CSS + shadcn/ui components
- **Inference**: PyTorch with diffusers library
- **Storage**: Local file system

## How It Works

### 1. Model Loading

When you click "Fetch & Load Model":

1. The app parses the HuggingFace model URL to extract the repo ID
2. Downloads the model files using `huggingface_hub.snapshot_download()`
3. Loads the model into memory using the `diffusers` library
4. Caches the pipeline for fast subsequent generations
5. **Automatically links to refiner service** for SDXS refinement

### 2. Image Generation

When you click "Generate":

1. Takes your text prompt
2. Runs the SD-XS diffusion pipeline (default: 8 steps, 512x512)
3. Saves the generated PNG to `./data/images/`
4. Displays the image in the UI
5. **Reveals the refiner section** below the generated image

### 3. Image Refinement (NEW)

After image generation, you can refine your images:

1. **Select refiner model:**
   - **SDXS (Already Loaded)** - Uses the existing SD-XS model (instant, no download)
   - **Small Stable Diffusion V0** - Lightweight 0.76B parameter model (requires download)

2. **For Small SD V0:** Click "Fetch & Load Refiner Model" (one-time setup)

3. **Enter refinement prompt:**
   - Describe modifications: "make it more vibrant and colorful"
   - Add details: "add dramatic lighting"
   - Change style: "make it look like an oil painting"

4. **Click "Refine Image"**:
   - Runs img2img diffusion (strength=0.75, 20 steps)
   - Saves refined image to `./data/images/refined/`
   - Displays the refined result below

## Supported Models

The app works with SD-XS (Stable Diffusion XS) models that are compatible with the `diffusers` library.

### Tested Models

- **IDKiro/sdxs-512-0.9** - SD-XS 512x512 model (recommended for testing)

## API Endpoints

### `POST /api/model/prepare`
Loads a model from HuggingFace.

### `POST /api/generate`
Generates an image from a text prompt.

### `GET /api/images/{filename}`
Serves a generated image file.

## Configuration

### Generation Parameters

- **size**: Image dimensions (default: `512x512`)
- **steps**: Number of inference steps (default: `8`)
- **guidance**: Guidance scale (default: `4.0`)
- **seed**: Random seed for reproducibility (optional)

### Performance

- **CPU Mode**: Works but slower (~30-60s per image)
- **GPU Mode**: Much faster (~2-5s per image) if CUDA is available

The app automatically detects and uses GPU if available.

## Notes

- All inference is local - no cloud API calls except initial HuggingFace download
- Generated images are saved permanently in `./data/images/`
- Models are cached in `./models/` directory
