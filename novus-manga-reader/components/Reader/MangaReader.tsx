import React, { useState, useRef, useEffect } from 'react';
import { 
  ChevronLeft, 
  Brain, 
  Maximize2, 
  Settings, 
  Menu, 
  ChevronRight, 
  Layout,
  Square,
  X,
  Sun,
  Type,
  Zap,
  ArrowRightCircle,
  Target
} from 'lucide-react';
import { Chapter } from '../../types';

interface MangaReaderProps {
  chapter: Chapter;
  onAIInsightsClick: () => void;
  isLoadingAI: boolean;
  onNextChapter?: () => void;
  hasNextChapter?: boolean;
}

interface ReaderSettings {
  animation: 'none' | 'fade' | 'slide';
  brightness: number;
  textScale: number;
}

export const MangaReader: React.FC<MangaReaderProps> = ({ 
  chapter, 
  onAIInsightsClick, 
  isLoadingAI,
  onNextChapter,
  hasNextChapter = false
}) => {
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [viewMode, setViewMode] = useState<'scroll' | 'single'>('scroll');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isJumpOpen, setIsJumpOpen] = useState(false);
  const [jumpInputValue, setJumpInputValue] = useState('');
  const [settings, setSettings] = useState<ReaderSettings>({
    animation: 'fade',
    brightness: 100,
    textScale: 100,
  });

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<(HTMLDivElement | null)[]>([]);
  const jumpInputRef = useRef<HTMLInputElement>(null);

  const isAtLastPage = currentPageIndex === chapter.pages.length - 1;
  const canGoToNextChapter = hasNextChapter && isAtLastPage;

  // Reset page index when chapter changes
  useEffect(() => {
    setCurrentPageIndex(0);
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [chapter.id]);

  useEffect(() => {
    if (isJumpOpen && jumpInputRef.current) {
      jumpInputRef.current.focus();
    }
  }, [isJumpOpen]);

  const goToPage = (index: number) => {
    if (index >= 0 && index < chapter.pages.length) {
      setCurrentPageIndex(index);
      if (viewMode === 'scroll') {
        pageRefs.current[index]?.scrollIntoView({ behavior: 'smooth' });
      }
      setIsJumpOpen(false);
      setJumpInputValue('');
    }
  };

  const goToNextPage = () => {
    if (currentPageIndex < chapter.pages.length - 1) {
      goToPage(currentPageIndex + 1);
    }
  };

  const goToPrevPage = () => {
    if (currentPageIndex > 0) {
      goToPage(currentPageIndex - 1);
    }
  };

  const handleJumpSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const pageNum = parseInt(jumpInputValue);
    if (!isNaN(pageNum)) {
      goToPage(pageNum - 1);
    }
  };

  const handleScroll = () => {
    if (viewMode !== 'scroll' || !scrollContainerRef.current) return;
    
    const container = scrollContainerRef.current;
    const scrollPos = container.scrollTop + container.clientHeight / 3;
    
    let activeIndex = 0;
    for (let i = 0; i < pageRefs.current.length; i++) {
      const el = pageRefs.current[i];
      if (el && el.offsetTop <= scrollPos) {
        activeIndex = i;
      }
    }
    if (activeIndex !== currentPageIndex) {
      setCurrentPageIndex(activeIndex);
    }
  };

  const getAnimationClass = () => {
    if (settings.animation === 'none') return '';
    if (settings.animation === 'fade') return 'animate-in fade-in duration-500';
    if (settings.animation === 'slide') return 'animate-in slide-in-from-right-4 duration-500';
    return '';
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
      {/* Reader Toolbar */}
      <div className="h-14 flex items-center justify-between px-6 bg-[#0f172a]/80 backdrop-blur-xl sticky top-0 z-20 border-b border-slate-800/50">
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
            <ChevronLeft size={20} />
          </button>
          <div className="flex items-center gap-2">
            <FolderOpenIcon className="text-sky-400" size={18} />
            <h2 className="text-sm font-semibold text-slate-200">
              Ch. {chapter.number}: {chapter.title}
            </h2>
          </div>
        </div>

        {/* Page Navigation Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-900/80 rounded-full px-2 py-1 border border-slate-800 ring-1 ring-white/5">
            <button 
              onClick={goToPrevPage}
              disabled={currentPageIndex === 0}
              className="p-1.5 hover:bg-slate-800 rounded-full disabled:opacity-30 disabled:cursor-not-allowed text-slate-400 hover:text-white transition-all"
            >
              <ChevronLeft size={18} />
            </button>
            
            <div className="px-4 flex items-center gap-1.5 relative">
              {isJumpOpen ? (
                <form onSubmit={handleJumpSubmit} className="absolute inset-0 z-30 flex items-center justify-center">
                  <input 
                    ref={jumpInputRef}
                    type="text"
                    value={jumpInputValue}
                    onChange={(e) => setJumpInputValue(e.target.value)}
                    onBlur={() => !jumpInputValue && setIsJumpOpen(false)}
                    placeholder="#"
                    className="w-12 bg-slate-800 text-sky-400 text-xs font-black text-center rounded-md border border-sky-500/50 outline-none animate-in zoom-in-75 duration-200"
                  />
                </form>
              ) : (
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-black text-sky-400 w-4 text-center">{currentPageIndex + 1}</span>
                  <span className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">/</span>
                  <span className="text-xs font-bold text-slate-400 w-4 text-center">{chapter.pages.length}</span>
                </div>
              )}
            </div>

            <button 
              onClick={goToNextPage}
              disabled={currentPageIndex === chapter.pages.length - 1}
              className="p-1.5 hover:bg-slate-800 rounded-full disabled:opacity-30 disabled:cursor-not-allowed text-slate-400 hover:text-white transition-all"
            >
              <ChevronRight size={18} />
            </button>
          </div>
          
          <button 
            onClick={() => setIsJumpOpen(!isJumpOpen)}
            className={`p-2 rounded-lg transition-all ${isJumpOpen ? 'bg-sky-500 text-black shadow-lg shadow-sky-500/20' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
            title="Quick Jump to Page"
          >
            <Target size={18} />
          </button>
        </div>

        <div className="flex items-center gap-3">
          {/* Next Chapter Button */}
          <button 
            onClick={onNextChapter}
            disabled={!canGoToNextChapter}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-black transition-all shadow-lg ${canGoToNextChapter ? 'bg-indigo-500 hover:bg-indigo-400 text-white shadow-indigo-500/20' : 'bg-slate-800 text-slate-600 cursor-not-allowed opacity-50'}`}
            title={!hasNextChapter ? 'No more chapters' : isAtLastPage ? 'Go to next chapter' : 'Finish current chapter first'}
          >
            <ArrowRightCircle size={16} />
            NEXT CHAPTER
          </button>

          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-800/50 rounded-lg p-1 border border-slate-700">
            <button 
              onClick={() => setViewMode('scroll')}
              className={`p-1.5 rounded-md transition-all ${viewMode === 'scroll' ? 'bg-sky-500 text-black shadow-lg shadow-sky-500/20' : 'text-slate-400 hover:text-white'}`}
              title="Continuous Scroll"
            >
              <Layout size={16} />
            </button>
            <button 
              onClick={() => setViewMode('single')}
              className={`p-1.5 rounded-md transition-all ${viewMode === 'single' ? 'bg-sky-500 text-black shadow-lg shadow-sky-500/20' : 'text-slate-400 hover:text-white'}`}
              title="Single Page"
            >
              <Square size={16} />
            </button>
          </div>

          <button 
            onClick={onAIInsightsClick}
            disabled={isLoadingAI}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-black transition-all shadow-lg ${isLoadingAI ? 'bg-slate-700 animate-pulse' : 'bg-sky-500 hover:bg-sky-400 text-black shadow-sky-500/20'}`}
          >
            <Brain size={16} />
            {isLoadingAI ? 'ANALYZING...' : 'AI INSIGHTS'}
          </button>
          <div className="w-px h-6 bg-slate-800 mx-2" />
          <div className="flex items-center gap-4 text-slate-400">
            <button className="hover:text-white transition-colors"><Maximize2 size={18} /></button>
            <button 
              onClick={() => setIsSettingsOpen(true)}
              className={`transition-colors ${isSettingsOpen ? 'text-sky-400' : 'hover:text-white'}`}
            >
              <Settings size={18} />
            </button>
            <button className="hover:text-white transition-colors"><Menu size={18} /></button>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-sm bg-[#1e293b] rounded-3xl border border-slate-700 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-6 border-b border-slate-800">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <Settings size={18} className="text-sky-400" />
                Reader Settings
              </h3>
              <button 
                onClick={() => setIsSettingsOpen(false)}
                className="p-2 hover:bg-slate-800 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-8">
              {/* Animation Mode */}
              <div className="space-y-3">
                <label className="text-xs font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                  <Zap size={14} /> Page Turn Animation
                </label>
                <div className="flex p-1 bg-slate-900/50 rounded-xl border border-slate-800">
                  {(['none', 'fade', 'slide'] as const).map((anim) => (
                    <button
                      key={anim}
                      onClick={() => setSettings({ ...settings, animation: anim })}
                      className={`flex-1 py-2 text-xs font-bold rounded-lg capitalize transition-all ${settings.animation === anim ? 'bg-sky-500 text-black' : 'text-slate-400 hover:text-white'}`}
                    >
                      {anim}
                    </button>
                  ))}
                </div>
              </div>

              {/* Brightness */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                    <Sun size={14} /> Reader Brightness
                  </label>
                  <span className="text-xs font-bold text-sky-400">{settings.brightness}%</span>
                </div>
                <input 
                  type="range"
                  min="20"
                  max="100"
                  value={settings.brightness}
                  onChange={(e) => setSettings({ ...settings, brightness: parseInt(e.target.value) })}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
                />
              </div>

              {/* Text Scaling */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                    <Type size={14} /> Overlay Text Scale
                  </label>
                  <span className="text-xs font-bold text-sky-400">{settings.textScale}%</span>
                </div>
                <input 
                  type="range"
                  min="50"
                  max="200"
                  value={settings.textScale}
                  onChange={(e) => setSettings({ ...settings, textScale: parseInt(e.target.value) })}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
                />
              </div>
            </div>

            <div className="p-6 bg-slate-900/30 border-t border-slate-800 flex justify-end">
              <button 
                onClick={() => setIsSettingsOpen(false)}
                className="px-6 py-2.5 bg-sky-500 hover:bg-sky-400 text-black text-xs font-black rounded-xl transition-all shadow-lg shadow-sky-500/20 uppercase tracking-widest"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manga Pages View */}
      <div 
        ref={scrollContainerRef}
        onScroll={handleScroll}
        style={{ filter: `brightness(${settings.brightness}%)` }}
        className={`flex-1 overflow-y-auto bg-[#05070a] flex flex-col items-center gap-8 transition-all duration-300 ${viewMode === 'single' ? 'justify-center p-4' : 'p-8'}`}
      >
        {viewMode === 'scroll' ? (
          chapter.pages.map((page, index) => (
            <div 
              key={page.pageNumber} 
              ref={el => pageRefs.current[index] = el}
              className={`relative group max-w-4xl w-full shadow-2xl transition-transform duration-500 ${currentPageIndex === index ? getAnimationClass() : ''}`}
            >
              <img 
                src={page.url} 
                alt={`Page ${page.pageNumber}`} 
                className={`w-full h-auto rounded-sm ring-1 transition-all duration-300 ${currentPageIndex === index ? 'ring-sky-500/50 scale-[1.01]' : 'ring-slate-800'}`}
                loading="lazy"
              />
              <div 
                style={{ fontSize: `${(settings.textScale / 100) * 10}px` }}
                className="absolute bottom-4 right-4 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10 text-white font-black tracking-widest opacity-0 group-hover:opacity-100 transition-opacity uppercase"
              >
                PAGE {page.pageNumber} / {chapter.pages.length}
              </div>
            </div>
          ))
        ) : (
          <div className={`relative group max-w-4xl w-full h-full flex items-center justify-center ${getAnimationClass()}`}>
            <img 
              src={chapter.pages[currentPageIndex].url} 
              alt={`Page ${currentPageIndex + 1}`} 
              className="max-w-full max-h-full object-contain rounded-sm shadow-2xl ring-1 ring-slate-800"
            />
            
            {/* Overlay Navigation for Single Page */}
            <div 
              className="absolute left-0 top-0 w-1/4 h-full cursor-w-resize" 
              onClick={goToPrevPage}
            />
            <div 
              className="absolute right-0 top-0 w-1/4 h-full cursor-e-resize" 
              onClick={goToNextPage}
            />

            <div 
              style={{ fontSize: `${(settings.textScale / 100) * 12}px` }}
              className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur-md px-4 py-2 rounded-full border border-white/10 text-white font-black tracking-widest shadow-2xl uppercase"
            >
              PAGE {currentPageIndex + 1} / {chapter.pages.length}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const FolderOpenIcon = ({ className, size }: { className?: string, size?: number }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size || 24} 
    height={size || 24} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.69.9H20a2 2 0 0 1 2 2v2" />
  </svg>
);
