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

## Installation & Setup

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Node.js 16+** and **npm/yarn** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/downloads))
- **Optional but recommended:** CUDA-compatible GPU with drivers for faster inference

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd sdxs-generator-refiner
```

### Step 2: Backend Setup

#### Install Python Dependencies

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Backend Dependencies Include:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `torch` - PyTorch for model inference
- `diffusers` - HuggingFace diffusers library
- `transformers` - Model components
- `huggingface-hub` - Model downloading
- `Pillow` - Image processing

#### Create Environment File (Optional)

Create a `.env` file in the `backend` directory if you need custom configuration:

```bash
# backend/.env
CORS_ORIGINS=http://localhost:3000
```

### Step 3: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
# or with yarn:
yarn install
```

#### Frontend Dependencies Include:
- `react` - UI framework
- `axios` - HTTP client
- `tailwindcss` - Styling
- `shadcn/ui` - UI components

#### Create Environment File

Create a `.env` file in the `frontend` directory:

```bash
# frontend/.env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Step 4: Run the Application

You'll need two terminal windows/tabs:

#### Terminal 1: Start Backend

```bash
cd backend
# Activate virtual environment if not already activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

Backend will be available at `http://localhost:8001`

#### Terminal 2: Start Frontend

```bash
cd frontend

# Start development server
npm start
# or with yarn:
yarn start
```

Frontend will be available at `http://localhost:3000`

### Step 5: First Use

1. Open your browser and navigate to `http://localhost:3000`
2. Enter the SD-XS model URL: `https://huggingface.co/IDKiro/sdxs-512-0.9`
3. Click "Fetch & Load Model" (first download takes 1-2 minutes)
4. Enter a prompt and click "Generate"
5. Once image is generated, try the refiner feature below!

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

The app works with SD-XS (Stable Diffusion XS) models and lightweight Stable Diffusion models compatible with the `diffusers` library.

### Generation Models (SD-XS)

- **IDKiro/sdxs-512-0.9** - SD-XS 512x512 model (recommended, ~1-2GB)

### Refiner Models

- **SDXS (Built-in)** - Uses the loaded SD-XS model for refinement (no extra download)
- **OFA-Sys/small-stable-diffusion-v0** - Compact 0.76B parameter model (~2GB download)

## API Endpoints

### Generation Endpoints

#### `POST /api/model/prepare`
Loads a generation model from HuggingFace.

**Request:**
```json
{
  "modelCardUrl": "https://huggingface.co/IDKiro/sdxs-512-0.9"
}
```

#### `POST /api/generate`
Generates an image from a text prompt.

**Request:**
```json
{
  "prompt": "a beautiful sunset over mountains",
  "size": "512x512",
  "steps": 8,
  "guidance": 4.0,
  "seed": null
}
```

#### `GET /api/images/{filename}`
Serves a generated image file.

### Refiner Endpoints (NEW)

#### `POST /api/refiner/prepare`
Loads a refiner model (Small SD V0 only, SDXS auto-loaded).

**Request:**
```json
{
  "modelCardUrl": "https://huggingface.co/OFA-Sys/small-stable-diffusion-v0",
  "modelType": "small-sd-v0"
}
```

#### `POST /api/refiner/refine`
Refines an image using img2img pipeline.

**Request:**
```json
{
  "originalImageFilename": "image.png",
  "refinementPrompt": "make it more vibrant",
  "modelType": "sdxs",
  "strength": 0.75,
  "steps": 20,
  "guidance": 7.5
}
```

#### `GET /api/images/refined/{filename}`
Serves a refined image file.

## Configuration

### Generation Parameters

- **size**: Image dimensions (default: `512x512`)
- **steps**: Number of inference steps (default: `8` for generation)
- **guidance**: Guidance scale (default: `4.0` for generation)
- **seed**: Random seed for reproducibility (optional)

### Refinement Parameters (NEW)

- **strength**: How much to transform the image (default: `0.75`, range: 0.0-1.0)
  - Lower values = more faithful to original
  - Higher values = more creative changes
- **steps**: Number of refinement steps (default: `20`)
- **guidance**: Guidance scale for refinement (default: `7.5`)

### Performance

- **CPU Mode**: Works but slower
  - Generation: ~30-60s per image
  - Refinement: ~60-90s per image
- **GPU Mode**: Much faster if CUDA is available
  - Generation: ~2-5s per image
  - Refinement: ~5-10s per image

The app automatically detects and uses GPU if available.

## Project Structure

```
/app/
├── backend/
│   ├── server.py                    # Main FastAPI application
│   ├── services/
│   │   ├── hf_downloader.py        # HuggingFace model downloader
│   │   ├── model_loader.py         # Model loading service
│   │   ├── pipeline.py             # SD-XS generation pipeline
│   │   └── refiner.py              # Image refinement service (NEW)
│   ├── data/
│   │   └── images/
│   │       ├── *.png               # Generated images
│   │       └── refined/            # Refined images (NEW)
│   └── models/                     # Downloaded models cache
├── frontend/
│   └── src/
│       ├── App.js                  # Main React component
│       └── components/ui/          # shadcn/ui components
└── README.md
```

## Notes

- All inference is local - no cloud API calls except initial HuggingFace downloads
- Generated images are saved permanently in `./data/images/`
- Refined images are saved separately in `./data/images/refined/`
- Models are cached in `./models/` directory for reuse
- SDXS refiner uses the same model as generation (memory efficient)
- Small SD V0 refiner requires separate download but offers alternative results

## Tips for Best Results

### Generation
- Use descriptive prompts: "a serene mountain landscape at sunset with purple clouds"
- Keep prompts focused and specific
- Default 8 steps work well for SD-XS models

### Refinement
- Use refinement prompts to describe changes, not recreate the entire scene
- Examples:
  - ✅ "make colors more vibrant"
  - ✅ "add dramatic lighting"
  - ✅ "enhance details and sharpness"
  - ❌ "a completely different scene" (better to generate new)
- Adjust strength parameter:
  - 0.5-0.7: Subtle refinements
  - 0.7-0.8: Moderate changes (default: 0.75)
  - 0.8-1.0: Dramatic transformations
- Try both SDXS and Small SD V0 refiners for different results
