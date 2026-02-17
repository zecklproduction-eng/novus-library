
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, Play, Square, Settings2, Trash2, BookOpen, AlertCircle, Headphones, Download, PlayCircle, RotateCcw, Loader2 } from 'lucide-react';
import { VOICES, MAX_TEXT_LENGTH } from './constants';
import { VoiceName } from './types';
import { generateSpeech } from './services/geminiService';
import { decode, decodeAudioData, createWavBlob } from './utils/audioUtils';

const App: React.FC = () => {
  const [text, setText] = useState<string>('');
  const [selectedVoice, setSelectedVoice] = useState<VoiceName>(VoiceName.Zephyr);
  const [pitch, setPitch] = useState<number>(0);
  const [apiKey, setApiKey] = useState<string>('');
  const [model, setModel] = useState<string>('gemini-2.5-flash-preview-tts');
  const [showApiSettings, setShowApiSettings] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [previewingVoiceId, setPreviewingVoiceId] = useState<VoiceName | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastGeneratedAudio, setLastGeneratedAudio] = useState<string | null>(null);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [playbackProgress, setPlaybackProgress] = useState(0);

  const audioContextRef = useRef<AudioContext | null>(null);
  const audioSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const progressIntervalRef = useRef<number | null>(null);
  const playbackRequestRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);
  const durationRef = useRef<number>(0);

  // Initialize Settings from localStorage
  useEffect(() => {
    const savedKey = localStorage.getItem('gemini_voice_reader_api_key');
    const savedModel = localStorage.getItem('gemini_voice_reader_model');

    if (savedKey) setApiKey(savedKey);
    else setShowApiSettings(true); // Show settings if key is missing

    if (savedModel) setModel(savedModel);
  }, []);

  const saveApiKey = (key: string) => {
    setApiKey(key);
    localStorage.setItem('gemini_voice_reader_api_key', key);
  };

  const saveModel = (m: string) => {
    setModel(m);
    localStorage.setItem('gemini_voice_reader_model', m);
  };

  // Generation Progress Simulator
  useEffect(() => {
    if (isGenerating) {
      setGenerationProgress(0);
      progressIntervalRef.current = window.setInterval(() => {
        setGenerationProgress((prev) => (prev < 90 ? prev + Math.random() * 10 : prev));
      }, 200);
    } else {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      setGenerationProgress(0);
    }
    return () => { if (progressIntervalRef.current) clearInterval(progressIntervalRef.current); };
  }, [isGenerating]);

  // Playback Progress Monitor
  const updatePlaybackProgress = useCallback(() => {
    if (!audioContextRef.current || !isSpeaking) return;
    const elapsed = audioContextRef.current.currentTime - startTimeRef.current;
    const progress = Math.min((elapsed / durationRef.current) * 100, 100);
    setPlaybackProgress(progress);
    if (progress < 100) {
      playbackRequestRef.current = requestAnimationFrame(updatePlaybackProgress);
    }
  }, [isSpeaking]);

  useEffect(() => {
    if (isSpeaking) {
      playbackRequestRef.current = requestAnimationFrame(updatePlaybackProgress);
    } else {
      if (playbackRequestRef.current) cancelAnimationFrame(playbackRequestRef.current);
      setPlaybackProgress(0);
    }
    return () => { if (playbackRequestRef.current) cancelAnimationFrame(playbackRequestRef.current); };
  }, [isSpeaking, updatePlaybackProgress]);

  const extractPdfText = async (arrayBuffer: ArrayBuffer): Promise<string> => {
    // @ts-ignore
    const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let fullText = '';
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      const strings = content.items.map((item: any) => item.str);
      fullText += strings.join(' ') + '\n';
    }
    return fullText;
  };

  const readFileAsText = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(new Error("Failed to read text file."));
      reader.readAsText(file);
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setError(null);
    setIsParsing(true);

    try {
      let content = '';
      if (file.type === 'text/plain') {
        content = await readFileAsText(file);
      } else if (file.type === 'application/pdf') {
        const arrayBuffer = await file.arrayBuffer();
        content = await extractPdfText(arrayBuffer);
      } else {
        throw new Error("Unsupported file format. Please use .txt or .pdf");
      }
      setText(content.substring(0, MAX_TEXT_LENGTH));
    } catch (err: any) {
      setError(err.message || "Failed to parse file.");
    } finally {
      setIsParsing(false);
      e.target.value = ''; // Reset input
    }
  };

  const stopAudio = useCallback(() => {
    if (audioSourceRef.current) {
      try { audioSourceRef.current.stop(); } catch (e) { }
      audioSourceRef.current = null;
    }
    setIsSpeaking(false);
    setPreviewingVoiceId(null);
  }, []);

  const playInternal = async (content: string, voice: VoiceName, isPreview: boolean = false) => {
    if (!apiKey) {
      setError("Please provide a Gemini API Key in Settings.");
      setShowApiSettings(true);
      return;
    }

    if (isSpeaking) {
      const wasPreviewingThis = previewingVoiceId === voice;
      stopAudio();
      if (isPreview && wasPreviewingThis) return;
    }

    if (!isPreview) {
      setIsGenerating(true);
      setLastGeneratedAudio(null);
    } else {
      setPreviewingVoiceId(voice);
    }

    setError(null);
    try {
      const base64Audio = await generateSpeech(content, voice, pitch, apiKey, model);
      if (!base64Audio) throw new Error("No audio data received.");

      if (!isPreview) {
        setGenerationProgress(100);
        setLastGeneratedAudio(base64Audio);
      }

      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      }

      const decodedBytes = decode(base64Audio);
      const audioBuffer = await decodeAudioData(decodedBytes, audioContextRef.current, 24000, 1);

      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.onended = () => {
        setIsSpeaking(false);
        setPreviewingVoiceId(null);
        audioSourceRef.current = null;
      };

      durationRef.current = audioBuffer.duration;
      startTimeRef.current = audioContextRef.current.currentTime;
      audioSourceRef.current = source;
      source.start();
      setIsSpeaking(true);
    } catch (err: any) {
      setError(err.message || "Speech synthesis failed. Check your API key or connection.");
      setPreviewingVoiceId(null);
    } finally {
      if (!isPreview) setTimeout(() => setIsGenerating(false), 200);
    }
  };

  const playSpeech = () => {
    if (!text.trim()) { setError("Text area is empty."); return; }
    playInternal(text.substring(0, MAX_TEXT_LENGTH), selectedVoice);
  };

  const handleDownload = () => {
    if (!lastGeneratedAudio) return;
    const decodedBytes = decode(lastGeneratedAudio);
    const blob = createWavBlob(decodedBytes, 24000);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voice-reader-${selectedVoice.toLowerCase()}.wav`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col items-center p-4 md:p-8">
      {/* Header */}
      <header className="w-full max-w-5xl flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="bg-indigo-600 p-3 rounded-2xl text-white shadow-xl shadow-indigo-100 ring-4 ring-white">
            <Headphones size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Gemini Voice Reader</h1>
            <p className="text-sm font-medium text-slate-500">Natural AI Text-to-Speech</p>
          </div>
        </div>
        <div className="flex gap-2">
          {lastGeneratedAudio && (
            <button onClick={handleDownload} className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-indigo-600 font-semibold text-sm hover:bg-indigo-50 transition-all shadow-sm">
              <Download size={18} />
              <span className="hidden sm:inline">Save Audio</span>
            </button>
          )}
          <button onClick={() => setShowApiSettings(!showApiSettings)} className={`p-2 transition-colors border rounded-xl shadow-sm ${showApiSettings ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-400 border-slate-200 hover:text-indigo-600'}`}>
            <Settings2 size={20} />
          </button>
          <button onClick={() => { setText(''); setFileName(null); stopAudio(); setLastGeneratedAudio(null); }} className="p-2 text-slate-400 hover:text-red-500 transition-colors bg-white border border-slate-200 rounded-xl shadow-sm">
            <Trash2 size={20} />
          </button>
        </div>
      </header>

      <main className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Editor Section */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 flex flex-col min-h-[550px] relative overflow-hidden ring-1 ring-slate-100">
            {/* Progress Bar (at the very top) */}
            <div className="h-[2px] w-full bg-slate-50 overflow-hidden pointer-events-none">
              {isGenerating && (
                <div className="h-full bg-indigo-500 transition-all duration-300" style={{ width: `${generationProgress}%` }} />
              )}
              {isSpeaking && !previewingVoiceId && (
                <div className="h-full bg-rose-500 transition-all duration-100" style={{ width: `${playbackProgress}%` }} />
              )}
            </div>

            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 truncate max-w-[70%]">
                <BookOpen size={18} className="text-indigo-500 shrink-0" />
                <span className="truncate">{fileName || 'Untitled Document'}</span>
              </div>
              <div className={`text-[11px] font-bold px-2 py-1 rounded-md transition-colors ${text.length > MAX_TEXT_LENGTH ? 'bg-red-100 text-red-600' : 'bg-slate-200 text-slate-600'}`}>
                {text.length.toLocaleString()} / {MAX_TEXT_LENGTH.toLocaleString()}
              </div>
            </div>

            <div className="flex-1 flex flex-col relative group">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Start typing here or drag and drop a .txt or .pdf file..."
                className="flex-1 w-full p-8 resize-none focus:outline-none text-slate-800 leading-relaxed custom-scrollbar text-xl font-medium placeholder:text-slate-300 transition-colors"
                spellCheck={false}
              />
            </div>

            <div className="p-5 bg-slate-50/80 border-t border-slate-100 flex items-center justify-between gap-4">
              <label className="flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 rounded-2xl cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-all text-sm font-bold text-slate-700 shadow-sm active:scale-95 disabled:opacity-50">
                {isParsing ? <Loader2 size={18} className="animate-spin text-indigo-600" /> : <Upload size={18} className="text-indigo-600" />}
                <span>{isParsing ? 'Processing...' : 'Upload Document'}</span>
                <input type="file" accept=".txt,.pdf" className="hidden" onChange={handleFileUpload} disabled={isParsing} />
              </label>

              <div className="flex items-center gap-3">
                {isSpeaking && !previewingVoiceId && (
                  <div className="flex items-center gap-2 text-xs font-bold text-rose-600 uppercase tracking-widest animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-rose-600"></span>
                    Now Reading
                  </div>
                )}
                {isGenerating && (
                  <div className="text-xs font-bold text-indigo-600 uppercase tracking-widest animate-pulse flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin" />
                    Generating Speech
                  </div>
                )}
              </div>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-3 p-4 bg-red-50 text-red-700 rounded-2xl border border-red-100 animate-in fade-in slide-in-from-top-2">
              <AlertCircle size={20} className="shrink-0" />
              <p className="text-sm font-bold">{error}</p>
            </div>
          )}
        </div>

        {/* Sidebar Settings */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-8 flex flex-col ring-1 ring-slate-100">
            {showApiSettings ? (
              <div className="animate-in fade-in slide-in-from-right-4">
                <div className="flex items-center gap-2 mb-4 text-slate-800 font-bold">
                  <Settings2 size={22} className="text-indigo-600" />
                  <h2 className="text-lg">API Settings</h2>
                </div>
                <p className="text-xs text-slate-500 mb-6 font-medium leading-relaxed">
                  Enter your Gemini API key to enable speech synthesis. Your key is stored locally in your browser.
                </p>
                <div className="space-y-4">
                  <div>
                    <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2 block">API Key</label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => saveApiKey(e.target.value)}
                      placeholder="Enter your API Key..."
                      className="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-indigo-50 focus:border-indigo-400 transition-all font-mono text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2 block">AI Model</label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {['gemini-2.5-flash-preview-tts', 'gemini-3-flash', 'gemini-2.0-flash', 'gemini-1.5-flash-8b'].map(m => (
                        <button
                          key={m}
                          onClick={() => saveModel(m)}
                          className={`px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all border ${model === m ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-500 border-slate-100 hover:border-indigo-200'}`}
                        >
                          {m === 'gemini-2.5-flash-preview-tts' ? '2.5 Flash TTS' : m}
                        </button>
                      ))}
                    </div>
                    <input
                      type="text"
                      value={model}
                      onChange={(e) => saveModel(e.target.value)}
                      placeholder="Custom Model Name..."
                      className="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-indigo-50 focus:border-indigo-400 transition-all font-mono text-sm"
                    />
                  </div>
                  <button
                    onClick={() => setShowApiSettings(false)}
                    className="w-full py-3 bg-indigo-600 text-white rounded-2xl font-bold text-sm shadow-lg shadow-indigo-100 active:scale-95 transition-all"
                  >
                    Save & Close
                  </button>
                  <p className="text-center">
                    <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-[10px] text-indigo-500 font-black hover:underline uppercase tracking-widest">
                      Get a free key here →
                    </a>
                  </p>
                </div>
              </div>
            ) : (
              <div className="animate-in fade-in slide-in-from-left-4">
                <div className="flex items-center gap-2 mb-8 text-slate-800 font-bold">
                  <Headphones size={22} className="text-indigo-600" />
                  <h2 className="text-lg">Voice Engine</h2>
                </div>

                <div className="space-y-3 mb-10">
                  {VOICES.map((voice) => (
                    <div key={voice.id} className="relative group">
                      <button
                        onClick={() => setSelectedVoice(voice.id)}
                        className={`w-full text-left p-4 rounded-2xl border-2 transition-all flex items-center justify-between gap-3 ${selectedVoice === voice.id
                          ? 'border-indigo-600 bg-indigo-50 ring-4 ring-indigo-50/50'
                          : 'border-slate-50 hover:border-indigo-200 bg-slate-50/50'
                          }`}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className={`font-bold text-sm truncate ${selectedVoice === voice.id ? 'text-indigo-800' : 'text-slate-900'}`}>{voice.label}</span>
                            <span className="text-[10px] font-black text-slate-400 px-1.5 py-0.5 bg-white border border-slate-100 rounded-lg">{voice.gender}</span>
                          </div>
                          <p className="text-[11px] font-medium text-slate-500 leading-tight line-clamp-1">{voice.description}</p>
                        </div>
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); playInternal(`I am the ${voice.label} voice.`, voice.id, true); }}
                        className={`absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-xl transition-all ${previewingVoiceId === voice.id
                          ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
                          : 'text-slate-400 hover:text-indigo-600 hover:bg-white bg-transparent'
                          }`}
                        title="Preview Voice"
                      >
                        {previewingVoiceId === voice.id ? <Square size={16} fill="currentColor" /> : <PlayCircle size={20} />}
                      </button>
                    </div>
                  ))}
                </div>

                <div className="pt-8 border-t border-slate-100">
                  <div className="flex items-center justify-between mb-6">
                    <label className="text-sm font-bold text-slate-700 flex items-center gap-2">
                      Vocal Tone
                      <span className="text-[10px] text-slate-400 uppercase tracking-tighter">(Experimental)</span>
                    </label>
                    <button onClick={() => setPitch(0)} className="text-slate-400 hover:text-indigo-600 transition-colors p-1" title="Reset Tone">
                      <RotateCcw size={16} />
                    </button>
                  </div>
                  <div className="flex gap-2 mb-6">
                    {[
                      { label: 'Deep', val: -0.5 },
                      { label: 'Normal', val: 0 },
                      { label: 'Bright', val: 0.5 }
                    ].map((p) => (
                      <button
                        key={p.label}
                        onClick={() => setPitch(p.val)}
                        className={`flex-1 py-2 rounded-xl text-[11px] font-black transition-all border-2 ${pitch === p.val ? 'bg-indigo-600 text-white border-indigo-600 shadow-lg' : 'bg-white text-slate-600 border-slate-50 hover:border-slate-200'
                          }`}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                  <input
                    type="range" min="-1.0" max="1.0" step="0.1" value={pitch}
                    onChange={(e) => setPitch(parseFloat(e.target.value))}
                    className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                </div>
              </div>
            )}
          </div>

          <button
            onClick={playSpeech}
            disabled={isGenerating || isParsing || !text.trim()}
            className={`w-full py-8 rounded-3xl flex flex-col items-center justify-center gap-4 transition-all transform active:scale-[0.97] disabled:grayscale disabled:opacity-50 ${isSpeaking && !previewingVoiceId ? 'bg-rose-600 text-white shadow-2xl shadow-rose-200' : 'bg-indigo-600 text-white shadow-2xl shadow-indigo-200'
              }`}
          >
            <div className="bg-white/10 p-4 rounded-2xl ring-2 ring-white/20">
              {isGenerating ? <Loader2 size={36} className="animate-spin" /> : (isSpeaking && !previewingVoiceId) ? <Square size={36} fill="currentColor" /> : <Play size={36} fill="currentColor" className="ml-1" />}
            </div>
            <span className="font-black text-xl tracking-wide uppercase">
              {isGenerating ? 'Synthesizing...' : (isSpeaking && !previewingVoiceId) ? 'Stop Reading' : 'Start Reading'}
            </span>
          </button>
        </div>
      </main>

      <footer className="mt-12 text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em]">
        Built with Gemini AI & PDF.js
      </footer>
    </div>
  );
};

export default App;
