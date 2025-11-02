import { useState } from 'react';
import '@/App.css';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [modelUrl, setModelUrl] = useState('https://huggingface.co/IDKiro/sdxs-512-0.9');
  const [prompt, setPrompt] = useState('');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [generatedImageFilename, setGeneratedImageFilename] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  
  // Refiner states
  const [selectedRefiner, setSelectedRefiner] = useState('sdxs');
  const [refinerLoaded, setRefinerLoaded] = useState({ sdxs: false, 'small-sd-v0': false });
  const [isLoadingRefiner, setIsLoadingRefiner] = useState(false);
  const [refinementPrompt, setRefinementPrompt] = useState('');
  const [isRefining, setIsRefining] = useState(false);
  const [refinedImage, setRefinedImage] = useState(null);
  const [refinerStatusMessage, setRefinerStatusMessage] = useState('');

  const handleFetchModel = async () => {
    if (!modelUrl.trim()) {
      toast.error('Please enter a model URL');
      return;
    }

    setIsLoading(true);
    setStatusMessage('Downloading model from HuggingFace...');
    
    try {
      const response = await axios.post(`${API}/model/prepare`, {
        modelCardUrl: modelUrl
      });

      if (response.data.ok) {
        setModelLoaded(true);
        setStatusMessage(`✓ ${response.data.message}`);
        toast.success('Model loaded successfully!');
      }
    } catch (error) {
      console.error('Error loading model:', error);
      const errorMsg = error.response?.data?.detail || error.message;
      setStatusMessage(`✗ Error: ${errorMsg}`);
      toast.error(`Failed to load model: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setIsGenerating(true);
    setStatusMessage('Generating image... (this may take 30-60 seconds)');
    
    try {
      const response = await axios.post(`${API}/generate`, {
        prompt: prompt,
        size: '512x512',
        steps: 8,
        guidance: 4.0
      }, {
        timeout: 120000 // 2 minute timeout
      });

      if (response.data.ok) {
        const imageUrl = `${BACKEND_URL}${response.data.imagePath}`;
        setGeneratedImage(imageUrl);
        setStatusMessage(`✓ Image generated: ${response.data.filename}`);
        toast.success('Image generated successfully!');
      }
    } catch (error) {
      console.error('Error generating image:', error);
      const errorMsg = error.response?.data?.detail || error.message;
      setStatusMessage(`✗ Error: ${errorMsg}`);
      toast.error(`Failed to generate image: ${errorMsg}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="app-container">
      <div className="content-wrapper">
        <header className="app-header">
          <h1 className="app-title">SD-XS Local Generator</h1>
          <p className="app-subtitle">Generate images locally using Stable Diffusion XS</p>
        </header>

        <div className="cards-container">
          <Card className="control-card" data-testid="model-card">
            <CardHeader>
              <CardTitle>Model Setup</CardTitle>
              <CardDescription>Load a Stable Diffusion XS model from HuggingFace</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="model-url">Model Card URL</Label>
                <Input
                  id="model-url"
                  data-testid="model-url-input"
                  type="text"
                  placeholder="https://huggingface.co/..."
                  value={modelUrl}
                  onChange={(e) => setModelUrl(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <Button
                data-testid="fetch-convert-button"
                onClick={handleFetchModel}
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading Model...
                  </>
                ) : (
                  'Fetch & Load Model'
                )}
              </Button>
            </CardContent>
          </Card>

          <Card className="control-card" data-testid="generate-card">
            <CardHeader>
              <CardTitle>Generate Image</CardTitle>
              <CardDescription>Enter a prompt to generate an image</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="prompt">Prompt</Label>
                <Input
                  id="prompt"
                  data-testid="prompt-input"
                  type="text"
                  placeholder="A beautiful sunset over mountains..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={!modelLoaded || isGenerating}
                />
              </div>
              <Button
                data-testid="generate-button"
                onClick={handleGenerate}
                disabled={!modelLoaded || isGenerating}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  'Generate'
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {statusMessage && (
          <div className="status-message" data-testid="status-message">
            {statusMessage}
          </div>
        )}

        {generatedImage && (
          <Card className="result-card" data-testid="result-card">
            <CardHeader>
              <CardTitle>Generated Image</CardTitle>
            </CardHeader>
            <CardContent>
              <img
                data-testid="generated-image"
                src={generatedImage}
                alt="Generated"
                className="generated-image"
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default App;
