
import React, { useState, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import { Book, Upload, Sparkles, Image as ImageIcon, Download, Loader2, RotateCcw, AlertCircle } from 'lucide-react';
import { GoogleGenAI, GenerateContentResponse } from "@google/genai";

// --- Types ---
interface GenerationState {
  status: 'idle' | 'processing' | 'analyzing' | 'generating' | 'completed' | 'error';
  progress: number;
  error?: string;
  coverUrl?: string;
  analysis?: string;
}

interface CoverOptions {
  style: string;
  mood: string;
  addTitle: boolean;
  aspectRatio: "1:1" | "3:4" | "4:3" | "9:16" | "16:9";
}

enum AppStyle {
  MANGA = 'Japanese Manga / Anime Style',
  REALISTIC = 'Realistic Cinematic',
  OIL_PAINTING = 'Classic Oil Painting',
  MINIMALIST = 'Modern Minimalist',
  DARK_FANTASY = 'Dark Fantasy Concept Art'
}

// --- PDF Service ---
// @ts-ignore
const pdfjsLib = window['pdfjs-dist/build/pdf'];
if (pdfjsLib) {
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

async function extractPagesAsImages(file: File, maxPages: number = 3): Promise<string[]> {
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const images: string[] = [];
  
  const numPages = Math.min(pdf.numPages, maxPages);
  
  for (let i = 1; i <= numPages; i++) {
    const page = await pdf.getPage(i);
    const viewport = page.getViewport({ scale: 1.5 });
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (!context) continue;
    
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    await page.render({
      canvasContext: context,
      viewport: viewport
    }).promise;
    
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    images.push(dataUrl.split(',')[1]); 
  }
  
  return images;
}

// --- Gemini Service ---
async function analyzeContent(base64Images: string[]): Promise<string> {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
  
  const imageParts = base64Images.map(data => ({
    inlineData: {
      mimeType: 'image/jpeg',
      data
    }
  }));

  const prompt = `Analyze these pages from a book/manga. Describe the core theme, the main characters shown (appearance, vibes), the setting, and the overall mood. Summarize this into a detailed creative description that could be used as a prompt for an illustrator to design a cover page. Focus on visual details.`;

  const response: GenerateContentResponse = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: [{
      parts: [...imageParts, { text: prompt }]
    }]
  });

  if (!response.candidates || response.candidates.length === 0) {
    throw new Error("The model failed to analyze the document. It might contain restricted content.");
  }

  return response.text || "A mysterious story waiting to be told.";
}

async function generateCoverImage(analysis: string, options: CoverOptions): Promise<string> {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
  
  const finalPrompt = `Professional book cover illustration. ${options.style}. Mood: ${options.mood}. Scene details: ${analysis}. Extremely high quality, vibrant colors, detailed textures, professional composition. No text or typography. Style: ${options.style}.`;

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: [{
      parts: [{ text: finalPrompt }]
    }],
    config: {
      imageConfig: {
        aspectRatio: options.aspectRatio
      }
    }
  });

  if (!response.candidates || response.candidates.length === 0) {
    throw new Error("The image generation was blocked or failed. Please try a different style or mood.");
  }

  // Use optional chaining for parts access to prevent undefined errors
  const parts = response.candidates[0].content?.parts || [];
  for (const part of parts) {
    if (part.inlineData) {
      return `data:image/png;base64,${part.inlineData.data}`;
    }
  }

  throw new Error("No image data was found in the model response.");
}

// --- Main App Component ---
const App: React.FC = () => {
  const [state, setState] = useState<GenerationState>({
    status: 'idle',
    progress: 0
  });

  const [options, setOptions] = useState<CoverOptions>({
    style: AppStyle.MANGA,
    mood: 'Epic and Dynamic',
    addTitle: false,
    aspectRatio: '3:4'
  });

  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const startGeneration = async () => {
    if (!file) return;

    try {
      setState({ status: 'processing', progress: 10 });
      const images = await extractPagesAsImages(file);
      
      setState({ status: 'analyzing', progress: 40 });
      const analysis = await analyzeContent(images);
      
      setState({ status: 'generating', progress: 70, analysis });
      const coverUrl = await generateCoverImage(analysis, options);
      
      setState({ status: 'completed', progress: 100, coverUrl, analysis });
    } catch (err: any) {
      console.error("Generation error:", err);
      setState({ 
        status: 'error', 
        progress: 0, 
        error: err.message || "An unexpected error occurred. Please try again." 
      });
    }
  };

  const reset = () => {
    setFile(null);
    setState({ status: 'idle', progress: 0 });
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-12 min-h-screen flex flex-col">
      <header className="text-center mb-12">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="bg-indigo-600 p-3 rounded-2xl shadow-lg shadow-indigo-500/20">
            <Book className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">
            MangaCover<span className="text-indigo-500">AI</span>
          </h1>
        </div>
        <p className="text-zinc-400 text-lg max-w-xl mx-auto">
          Upload your manuscript and let artificial intelligence design the perfect cover art for your story.
        </p>
      </header>

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-5 space-y-6">
          <section className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-xl">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <Upload className="w-5 h-5 text-indigo-400" />
              Upload Manuscript
            </h2>
            
            <div 
              onClick={() => !state.status.includes('ing') && fileInputRef.current?.click()}
              className={`
                relative border-2 border-dashed rounded-2xl p-8 transition-all cursor-pointer text-center
                ${file ? 'border-indigo-500 bg-indigo-500/5' : 'border-zinc-700 hover:border-zinc-500 bg-zinc-800/50'}
                ${state.status !== 'idle' && state.status !== 'error' && state.status !== 'completed' ? 'opacity-50 pointer-events-none' : ''}
              `}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept="application/pdf"
                onChange={handleFileChange}
              />
              <div className="flex flex-col items-center">
                <Upload className={`w-12 h-12 mb-4 ${file ? 'text-indigo-400' : 'text-zinc-500'}`} />
                <p className="font-medium text-zinc-200">
                  {file ? file.name : "Select your PDF file"}
                </p>
                <p className="text-xs text-zinc-500 mt-2">PDF up to 20MB</p>
              </div>
            </div>

            {file && (
              <div className="mt-8 space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="space-y-4">
                  <label className="block text-sm font-semibold text-zinc-400 uppercase tracking-wider">Cover Style</label>
                  <div className="grid grid-cols-1 gap-2">
                    {Object.values(AppStyle).map((style) => (
                      <button
                        key={style}
                        onClick={() => setOptions(prev => ({ ...prev, style }))}
                        className={`
                          px-4 py-3 rounded-xl text-sm font-medium transition-all text-left border
                          ${options.style === style 
                            ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/20' 
                            : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:bg-zinc-750'}
                        `}
                      >
                        {style}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <label className="block text-sm font-semibold text-zinc-400 uppercase tracking-wider">Mood / Atmosphere</label>
                  <input 
                    type="text"
                    value={options.mood}
                    onChange={(e) => setOptions(prev => ({ ...prev, mood: e.target.value }))}
                    placeholder="e.g. Melancholic, Action-packed, Whimsical"
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                  />
                </div>

                <div className="space-y-4">
                  <label className="block text-sm font-semibold text-zinc-400 uppercase tracking-wider">Dimensions</label>
                  <div className="flex gap-2">
                    {["3:4", "1:1", "9:16"].map((ratio) => (
                      <button
                        key={ratio}
                        onClick={() => setOptions(prev => ({ ...prev, aspectRatio: ratio as any }))}
                        className={`
                          flex-1 py-2 rounded-lg text-xs font-bold border transition-all
                          ${options.aspectRatio === ratio 
                            ? 'bg-zinc-200 border-white text-black' 
                            : 'bg-zinc-800 border-zinc-700 text-zinc-400'}
                        `}
                      >
                        {ratio}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  disabled={state.status.includes('ing')}
                  onClick={startGeneration}
                  className="w-full bg-white text-black font-black py-4 rounded-2xl flex items-center justify-center gap-2 hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-xl"
                >
                  {state.status.includes('ing') ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Sparkles className="w-5 h-5" />
                  )}
                  {state.status === 'idle' ? 'GENERATE COVER' : 
                   state.status === 'completed' ? 'RE-GENERATE' : 
                   'PROCESSING...'}
                </button>
              </div>
            )}
          </section>

          {state.status === 'error' && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 flex gap-3 text-red-400 items-start">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Generation Failed</p>
                <p className="text-sm opacity-80">{state.error}</p>
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-7 h-full">
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-4 md:p-8 h-full min-h-[500px] flex flex-col items-center justify-center relative overflow-hidden">
            {state.status === 'idle' && (
              <div className="text-center space-y-4 max-w-xs">
                <div className="w-20 h-20 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-6">
                  <ImageIcon className="w-8 h-8 text-zinc-600" />
                </div>
                <h3 className="text-xl font-bold text-zinc-300">Live Preview</h3>
                <p className="text-zinc-500 text-sm">Your generated cover will appear here after we analyze your manuscript.</p>
              </div>
            )}

            {(state.status.includes('ing')) && (
              <div className="flex flex-col items-center space-y-6 w-full max-w-sm">
                <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div 
                    className="bg-indigo-500 h-full transition-all duration-500 ease-out shadow-[0_0_15px_rgba(99,102,241,0.5)]" 
                    style={{ width: `${state.progress}%` }}
                  ></div>
                </div>
                <div className="text-center">
                  <h3 className="text-xl font-bold text-white flex items-center gap-2 justify-center mb-2">
                    <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
                    {state.status === 'processing' && 'Reading PDF...'}
                    {state.status === 'analyzing' && 'Analyzing Story Themes...'}
                    {state.status === 'generating' && 'Illustrating Cover...'}
                  </h3>
                  <p className="text-zinc-500 text-sm italic">
                    {state.status === 'processing' && 'Extracting key visual references from your pages.'}
                    {state.status === 'analyzing' && 'Understanding the plot, characters, and setting.'}
                    {state.status === 'generating' && 'Our AI artists are handcrafting your unique cover art.'}
                  </p>
                </div>
              </div>
            )}

            {state.status === 'completed' && state.coverUrl && (
              <div className="w-full flex flex-col items-center space-y-6 animate-in zoom-in-95 duration-700">
                <div className="relative group">
                  <div className="absolute -inset-4 bg-indigo-500/20 rounded-[2.5rem] blur-2xl group-hover:bg-indigo-500/30 transition-all"></div>
                  <img 
                    src={state.coverUrl} 
                    alt="Generated Cover" 
                    className="relative rounded-2xl shadow-2xl max-h-[70vh] w-auto border border-white/10"
                  />
                  
                  <div className="absolute top-4 right-4 flex gap-2">
                    <a 
                      href={state.coverUrl} 
                      download="manga-cover.png"
                      className="bg-white/90 hover:bg-white text-black p-3 rounded-full shadow-lg transition-transform hover:scale-110 active:scale-95"
                    >
                      <Download className="w-5 h-5" />
                    </a>
                  </div>
                </div>

                <div className="bg-zinc-800/80 border border-zinc-700 p-6 rounded-2xl w-full max-w-xl">
                  <h4 className="text-sm font-bold text-zinc-500 uppercase mb-3 flex items-center gap-2">
                    <Sparkles className="w-4 h-4" /> Story Analysis
                  </h4>
                  <p className="text-zinc-300 text-sm leading-relaxed italic">
                    "{state.analysis}"
                  </p>
                </div>

                <button 
                  onClick={reset}
                  className="flex items-center gap-2 text-zinc-500 hover:text-white transition-colors text-sm font-medium"
                >
                  <RotateCcw className="w-4 h-4" /> Start Over
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="mt-12 text-center text-zinc-600 text-sm py-8 border-t border-zinc-900">
        &copy; {new Date().getFullYear()} MangaCover AI. Powered by Google Gemini 2.5 Flash.
      </footer>
    </div>
  );
};

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
