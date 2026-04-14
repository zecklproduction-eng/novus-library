
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { SummaryState, ProcessingStep, DetailLevel } from './types';
import { generateBookSummary } from './services/gemini';
import MarkdownRenderer from './components/MarkdownRenderer';

const App: React.FC = () => {
  const [state, setState] = useState<SummaryState>({
    isProcessing: false,
    content: null,
    error: null,
    fileName: null,
    detailLevel: 'balanced'
  });

  const [copySuccess, setCopySuccess] = useState(false);
  const [progress, setProgress] = useState(0);

  const [steps, setSteps] = useState<ProcessingStep[]>([
    { label: 'Reading PDF file', status: 'pending' },
    { label: 'Analyzing structure', status: 'pending' },
    { label: 'Generating summaries', status: 'pending' }
  ]);

  const updateStep = (index: number, status: ProcessingStep['status']) => {
    setSteps(prev => prev.map((step, i) => i === index ? { ...step, status } : step));
  };

  const resetSteps = () => {
    setSteps([
      { label: 'Reading PDF file', status: 'pending' },
      { label: 'Analyzing structure', status: 'pending' },
      { label: 'Generating summaries', status: 'pending' }
    ]);
    setProgress(0);
  };

  // Smooth progress animation
  useEffect(() => {
    let interval: number;
    if (state.isProcessing) {
      const activeStepIndex = steps.findIndex(s => s.status === 'active');
      const targetProgress = activeStepIndex === 0 ? 30 : activeStepIndex === 1 ? 60 : 95;
      
      interval = window.setInterval(() => {
        setProgress(prev => {
          if (prev < targetProgress) return prev + 1;
          return prev;
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [state.isProcessing, steps]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setState(prev => ({ ...prev, error: 'Please upload a valid PDF file.' }));
      return;
    }

    setState(prev => ({ ...prev, isProcessing: true, content: null, error: null, fileName: file.name }));
    resetSteps();

    try {
      updateStep(0, 'active');
      const reader = new FileReader();
      
      const base64Promise = new Promise<string>((resolve, reject) => {
        reader.onload = () => {
          const result = reader.result as string;
          const base64 = result.split(',')[1];
          resolve(base64);
        };
        reader.onerror = reject;
      });

      reader.readAsDataURL(file);
      const base64 = await base64Promise;
      updateStep(0, 'completed');
      setProgress(33);
      
      updateStep(1, 'active');
      await new Promise(r => setTimeout(r, 1200));
      updateStep(1, 'completed');
      setProgress(66);

      updateStep(2, 'active');
      const summary = await generateBookSummary(base64, state.detailLevel);
      
      setProgress(100);
      updateStep(2, 'completed');
      
      // Delay slightly to show 100% completion
      setTimeout(() => {
        setState(prev => ({ ...prev, content: summary, isProcessing: false }));
      }, 500);
      
    } catch (err) {
      console.error(err);
      setState(prev => ({ 
        ...prev, 
        isProcessing: false, 
        error: err instanceof Error ? err.message : 'An error occurred during processing.' 
      }));
      setSteps(prev => prev.map(s => s.status === 'active' ? { ...s, status: 'error' } : s));
    }
  };

  const handleCopy = useCallback(async () => {
    if (!state.content) return;
    try {
      await navigator.clipboard.writeText(state.content);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  }, [state.content]);

  const detailLevels: { value: DetailLevel; label: string; desc: string }[] = [
    { value: 'concise', label: 'Concise', desc: 'Core themes' },
    { value: 'balanced', label: 'Balanced', desc: 'Full overview' },
    { value: 'detailed', label: 'Detailed', desc: 'In-depth' },
  ];

  const headings = useMemo(() => {
    if (!state.content) return [];
    const lines = state.content.split('\n');
    const result: { text: string; level: number; id: string }[] = [];
    const idCounts: Record<string, number> = {};

    const generateId = (text: string) => {
      let baseId = text.toLowerCase().trim().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
      if (idCounts[baseId]) {
        idCounts[baseId]++;
        return `${baseId}-${idCounts[baseId]}`;
      }
      idCounts[baseId] = 1;
      return baseId;
    };

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('# ')) {
        const text = trimmed.replace('# ', '');
        result.push({ text, level: 1, id: generateId(text) });
      } else if (trimmed.startsWith('## ')) {
        const text = trimmed.replace('## ', '');
        result.push({ text, level: 2, id: generateId(text) });
      } else if (trimmed.startsWith('### ')) {
        const text = trimmed.replace('### ', '');
        result.push({ text, level: 3, id: generateId(text) });
      }
    });
    return result;
  }, [state.content]);

  const handleTocClick = (id: string) => {
    const target = document.getElementById(id);
    if (target) {
      let parent = target.closest('details');
      while (parent) {
        parent.open = true;
        parent = parent.parentElement?.closest('details') || null;
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900">
      <nav className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold">L</div>
            <span className="font-bold text-xl tracking-tight text-slate-800">Lumina Studio</span>
          </div>
          {state.fileName && (
            <div className="hidden md:flex items-center space-x-2 text-sm text-slate-500">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
              <span>{state.fileName}</span>
            </div>
          )}
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!state.content && !state.isProcessing && (
          <div className="text-center mb-16 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <h1 className="serif text-5xl md:text-6xl mb-6 text-slate-900">
              Your books, <br />
              <span className="text-indigo-600 italic">distilled.</span>
            </h1>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
              Upload any book in PDF format and receive a perfectly structured summary organized by chapters and sections.
            </p>
          </div>
        )}

        {!state.content && !state.isProcessing && (
          <div className="max-w-xl mx-auto space-y-8">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-4">Summary Detail Level</h3>
              <div className="grid grid-cols-3 gap-2">
                {detailLevels.map((lvl) => (
                  <button
                    key={lvl.value}
                    onClick={() => setState(prev => ({ ...prev, detailLevel: lvl.value }))}
                    className={`flex flex-col items-center justify-center p-3 rounded-xl border-2 transition-all ${
                      state.detailLevel === lvl.value
                        ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                        : 'border-slate-100 bg-white text-slate-500 hover:border-slate-200'
                    }`}
                  >
                    <span className="font-bold text-sm">{lvl.label}</span>
                    <span className="text-[10px] opacity-70">{lvl.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <label className="group relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-slate-300 rounded-2xl bg-white hover:bg-slate-50 hover:border-indigo-400 transition-all cursor-pointer shadow-sm">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                  </svg>
                </div>
                <p className="mb-2 text-lg font-semibold text-slate-700">Drop your book here</p>
                <p className="text-sm text-slate-500">PDF documents up to 20MB</p>
              </div>
              <input type="file" className="hidden" accept=".pdf" onChange={handleFileUpload} />
            </label>
            {state.error && (
              <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-100 flex items-center space-x-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"></path></svg>
                <span>{state.error}</span>
              </div>
            )}
          </div>
        )}

        {state.isProcessing && (
          <div className="max-w-2xl mx-auto py-20">
            <div className="text-center mb-12">
              <div className="relative inline-block mb-8">
                <div className="w-24 h-24 border-4 border-slate-100 border-t-indigo-600 rounded-full animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg className="w-8 h-8 text-indigo-600 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                  </svg>
                </div>
              </div>
              
              <h2 className="text-2xl font-bold mb-2 text-slate-800">Processing "{state.fileName}"</h2>
              <p className="text-slate-500 mb-8">Distilling complex content into clear insights.</p>
            </div>

            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-8">
              {/* Progress Bar Container */}
              <div className="space-y-2">
                <div className="flex justify-between items-end">
                  <span className="text-sm font-bold text-indigo-600 uppercase tracking-widest">Progress</span>
                  <span className="text-lg font-bold text-slate-700">{progress}%</span>
                </div>
                <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-indigo-600 transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Step Checklist */}
              <div className="space-y-4 pt-4">
                {steps.map((step, idx) => (
                  <div key={idx} className="flex items-center space-x-4">
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                      step.status === 'completed' ? 'bg-green-100 text-green-600' :
                      step.status === 'active' ? 'bg-indigo-600 text-white animate-pulse shadow-lg shadow-indigo-200' :
                      step.status === 'error' ? 'bg-red-100 text-red-600' :
                      'bg-slate-100 text-slate-400'
                    }`}>
                      {step.status === 'completed' ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>
                      ) : idx + 1}
                    </div>
                    <div className="flex flex-col">
                      <span className={`text-sm ${step.status === 'active' ? 'font-bold text-slate-900' : 'font-medium text-slate-500'}`}>
                        {step.label}
                      </span>
                      {step.status === 'active' && (
                        <span className="text-xs text-indigo-500 animate-pulse font-medium">Please wait...</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mt-12 text-center">
              <p className="text-slate-400 text-sm italic">
                Our AI is currently performing a deep reading of your document. <br />
                This process usually takes between 30 and 60 seconds.
              </p>
            </div>
          </div>
        )}

        {state.content && !state.isProcessing && (
          <div className="animate-in fade-in slide-in-from-bottom-8 duration-1000">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 sticky top-20 bg-[#f8fafc]/95 backdrop-blur-sm py-4 z-40 border-b border-slate-200">
              <div>
                <h2 className="serif text-3xl text-slate-900">Summary & Analysis</h2>
                <div className="flex items-center space-x-3 text-slate-500 text-sm mt-1">
                  <span>{state.fileName}</span>
                  <span>•</span>
                  <span className="capitalize text-indigo-600 font-medium">{state.detailLevel} Detail</span>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button 
                  onClick={handleCopy}
                  className={`px-4 py-2 text-sm font-medium border rounded-lg transition-all flex items-center space-x-2 ${
                    copySuccess 
                      ? 'bg-green-50 border-green-200 text-green-700' 
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {copySuccess ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                  )}
                  <span>{copySuccess ? 'Copied!' : 'Copy'}</span>
                </button>
                <button 
                  onClick={() => window.print()}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path></svg>
                  <span>Export</span>
                </button>
                <button 
                  onClick={() => setState(prev => ({ ...prev, isProcessing: false, content: null, error: null, fileName: null }))}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  New Book
                </button>
              </div>
            </div>

            {/* Table of Contents */}
            {headings.length > 0 && (
              <div className="mb-12 p-8 bg-white rounded-3xl border border-slate-200 shadow-sm">
                <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h7"></path>
                  </svg>
                  Summary Navigator
                </h3>
                <nav className="max-h-96 overflow-y-auto pr-4 scrollbar-thin">
                  <ul className="space-y-2">
                    {headings.map((h, i) => (
                      <li 
                        key={`${h.id}-${i}`} 
                        style={{ paddingLeft: `${(h.level - 1) * 1.5}rem` }}
                      >
                        <a 
                          href={`#${h.id}`} 
                          onClick={() => handleTocClick(h.id)}
                          className={`group flex items-center space-x-2 text-sm transition-all hover:text-indigo-600 ${
                            h.level === 1 ? 'font-bold text-slate-800' : 'text-slate-500 font-medium'
                          }`}
                        >
                          <span className={`w-1 h-1 rounded-full bg-slate-300 group-hover:bg-indigo-400 transition-colors ${h.level > 1 ? 'block' : 'hidden'}`}></span>
                          <span>{h.text}</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                </nav>
              </div>
            )}

            <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 p-8 md:p-12 border border-slate-100">
              <MarkdownRenderer content={state.content} />
            </div>

            <footer className="mt-12 py-12 border-t border-slate-200 text-center text-slate-400 text-sm">
              <p>&copy; 2024 Lumina Studio. Powered by Gemini AI.</p>
            </footer>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
