
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  BookOpen,
  FileText,
  Music,
  MessageSquare,
  Settings,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Download,
  Play,
  Pause,
  RotateCcw,
  Volume2,
  X,
  Info,
  Zap,
  Search,
  ChevronUp,
  ChevronDown,
  Bookmark,
  Layout,
  Highlighter,
  Trash2,
  StickyNote,
  Plus,
  PencilLine,
  Check,
  Calendar,
  List,
  Palette,
  SearchX,
  ArrowUpDown,
  SortAsc,
  SortDesc,
  Clock,
  Hash,
  Link as LinkIcon,
  ExternalLink,
  Globe,
  Filter,
  FilterX,
  CalendarDays,
  Keyboard,
  Command,
  Copy,
  CheckCircle2,
  VolumeX,
  Loader2,
  Timer,
  Sparkles,
  FileJson,
  FileCode,
  FileEdit,
  Link2
} from 'lucide-react';
import { GoogleGenAI, Modality } from "@google/genai";
import { MOCK_BOOK, MOCK_PAGES } from './constants';
import { SidebarTab, ChatMessage, Highlight, Note } from './types';
import { getGeminiResponse } from './services/gemini';

const PLAYBACK_SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];
const HIGHLIGHT_COLORS = [
  { name: 'Yellow', bg: 'bg-yellow-200', hex: '#fef08a' },
  { name: 'Green', bg: 'bg-green-200', hex: '#bbf7d0' },
  { name: 'Blue', bg: 'bg-blue-200', hex: '#bfdbfe' },
  { name: 'Pink', bg: 'bg-pink-200', hex: '#fbcfe8' },
];

const NOTE_COLORS = [
  { name: 'Indigo', bg: 'bg-indigo-500', hex: '#4f46e5' },
  { name: 'Amber', bg: 'bg-amber-500', hex: '#f59e0b' },
  { name: 'Emerald', bg: 'bg-emerald-500', hex: '#10b981' },
  { name: 'Rose', bg: 'bg-rose-500', hex: '#f43f5e' },
  { name: 'Violet', bg: 'bg-violet-500', hex: '#8b5cf6' },
  { name: 'Sky', bg: 'bg-sky-500', hex: '#0ea5e9' },
];

// Audio decoding helpers for raw PCM data from Gemini TTS
function decode(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

async function decodeAudioData(
  data: Uint8Array,
  ctx: AudioContext,
  sampleRate: number,
  numChannels: number,
): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) {
      channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
    }
  }
  return buffer;
}

// Declare pdfjsLib on window
declare global {
  interface Window {
    pdfjsLib?: any;
  }
}

type SortCriterion = 'date' | 'page' | 'color';

// PDF Canvas Page Component - renders PDF pages using PDF.js
const PDFCanvasPage: React.FC<{
  pdfDoc: any;
  pageNumber: number;
  zoom: number;
  onVisible: (pageNumber: number) => void;
}> = ({ pdfDoc, pageNumber, zoom, onVisible }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInView, setIsInView] = useState(false);
  const renderTaskRef = useRef<any>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting) {
          setIsInView(true);
          onVisible(pageNumber);
        } else {
          setIsInView(false);
        }
      },
      { threshold: 0.1, rootMargin: '200px' }
    );
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [pageNumber, onVisible]);

  useEffect(() => {
    const renderPage = async () => {
      if (!window.pdfjsLib || !canvasRef.current || !pdfDoc || !isInView) {
        return;
      }

      try {
        if (renderTaskRef.current) {
          renderTaskRef.current.cancel();
        }

        setIsLoading(true);
        const page = await pdfDoc.getPage(pageNumber);
        const scale = (zoom / 100) * 1.5;
        const viewport = page.getViewport({ scale });

        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');
        if (!context) return;

        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const renderContext = {
          canvasContext: context,
          viewport: viewport
        };

        renderTaskRef.current = page.render(renderContext);
        await renderTaskRef.current.promise;

        setIsLoading(false);
        setError(null);
      } catch (err: any) {
        if (err.name === 'RenderingCancelledException') return;
        console.error('PDF render error:', err);
        setError('Failed to render PDF page');
        setIsLoading(false);
      }
    };

    renderPage();
    return () => {
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
      }
    };
  }, [pdfDoc, pageNumber, zoom, isInView]);

  return (
    <div
      ref={containerRef}
      id={`page-${pageNumber}`}
      className="mb-8 relative"
    >
      <div
        className="bg-white rounded-xl shadow-2xl overflow-hidden"
        style={{
          boxShadow: '0 0 40px rgba(0, 212, 255, 0.1), 0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        }}
      >
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-100 rounded-xl">
            <div className="text-center">
              <Loader2 size={32} className="text-cyan-500 animate-spin mx-auto mb-2" />
              <p className="text-slate-500 text-sm">Loading page {pageNumber}...</p>
            </div>
          </div>
        )}
        {error && (
          <div className="p-8 flex items-center justify-center bg-slate-100 rounded-xl min-h-[400px]">
            <div className="text-center">
              <BookOpen size={48} className="text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500 text-sm">{error}</p>
            </div>
          </div>
        )}
        <canvas ref={canvasRef} className={isLoading ? 'opacity-0' : 'opacity-100'} />
      </div>
      <div className="text-center mt-2 text-slate-400 text-xs font-medium">
        Page {pageNumber}
      </div>
    </div>
  );
};

// Page Component
const PDFPage: React.FC<{
  page: typeof MOCK_PAGES[0];
  zoom: number;
  onVisible: (pageNumber: number) => void;
  searchQuery: string;
  highlights: Highlight[];
  notes: Note[];
  activeTranscriptText: string | null;
  onSelectText: (e: React.MouseEvent, pageNumber: number) => void;
  onRemoveHighlight: (id: string) => void;
}> = ({
  page,
  zoom,
  onVisible,
  searchQuery,
  highlights,
  notes,
  activeTranscriptText,
  onSelectText,
  onRemoveHighlight
}) => {
    const pageRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting && entry.intersectionRatio > 0.4) {
            onVisible(page.pageNumber);
          }
        },
        { threshold: [0, 0.1, 0.4, 0.8], rootMargin: '-10% 0px -10% 0px' }
      );

      if (pageRef.current) observer.observe(pageRef.current);
      return () => observer.disconnect();
    }, [page.pageNumber, onVisible]);

    const renderEnhancedText = (text: string) => {
      let segments: { text: string; search: boolean; reading: boolean; highlightColor?: string; id?: string }[] = [{ text, search: false, reading: false }];

      if (activeTranscriptText) {
        const newSegments: typeof segments = [];
        segments.forEach(seg => {
          if (seg.reading) {
            newSegments.push(seg);
            return;
          }
          const index = seg.text.toLowerCase().indexOf(activeTranscriptText.toLowerCase());
          if (index !== -1) {
            if (index > 0) newSegments.push({ text: seg.text.substring(0, index), search: false, reading: false });
            newSegments.push({
              text: seg.text.substring(index, index + activeTranscriptText.length),
              search: false,
              reading: true
            });
            const remaining = seg.text.substring(index + activeTranscriptText.length);
            if (remaining) newSegments.push({ text: remaining, search: false, reading: false });
          } else {
            newSegments.push(seg);
          }
        });
        segments = newSegments;
      }

      highlights.forEach(h => {
        const newSegments: typeof segments = [];
        segments.forEach(seg => {
          if (seg.highlightColor || seg.search || seg.reading) {
            newSegments.push(seg);
            return;
          }
          const index = seg.text.indexOf(h.text);
          if (index !== -1) {
            if (index > 0) newSegments.push({ text: seg.text.substring(0, index), search: false, reading: false });
            newSegments.push({ text: h.text, search: false, reading: false, highlightColor: h.color, id: h.id });
            const remaining = seg.text.substring(index + h.text.length);
            if (remaining) newSegments.push({ text: remaining, search: false, reading: false });
          } else {
            newSegments.push(seg);
          }
        });
        segments = newSegments;
      });

      if (searchQuery && searchQuery.length >= 2) {
        const searchLower = searchQuery.toLowerCase();
        const finalSegments: typeof segments = [];
        segments.forEach(seg => {
          if (seg.search) {
            finalSegments.push(seg);
            return;
          }
          const textLower = seg.text.toLowerCase();
          let lastIdx = 0;
          let matchIdx = textLower.indexOf(searchLower);

          while (matchIdx !== -1) {
            if (matchIdx > lastIdx) {
              finalSegments.push({ ...seg, text: seg.text.substring(lastIdx, matchIdx) });
            }
            finalSegments.push({
              text: seg.text.substring(matchIdx, matchIdx + searchQuery.length),
              search: true,
              reading: seg.reading,
              highlightColor: seg.highlightColor
            });
            lastIdx = matchIdx + searchQuery.length;
            matchIdx = textLower.indexOf(searchLower, lastIdx);
          }
          if (lastIdx < seg.text.length) {
            finalSegments.push({ ...seg, text: seg.text.substring(lastIdx) });
          }
        });
        segments = finalSegments;
      }

      return segments.map((seg, i) => {
        const style: React.CSSProperties = {};
        let className = "";
        if (seg.highlightColor) {
          style.backgroundColor = seg.highlightColor;
          className = "relative group/h";
        }
        if (seg.reading) {
          className += " reading-highlight";
        }
        if (seg.search) {
          className += " ring-1 ring-orange-400 bg-orange-100/80 rounded-sm";
        }
        return (
          <span key={i} className={className} style={style}>
            {seg.text}
            {seg.id && !seg.search && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onRemoveHighlight(seg.id!);
                }}
                className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-rose-500 text-white w-4 h-4 rounded-full shadow-lg opacity-0 group-hover/h:opacity-100 transition-all hover:scale-125 hover:bg-rose-600 active:scale-95 z-20 flex items-center justify-center border border-white"
                title="Remove Highlight"
              >
                <X size={10} strokeWidth={3} />
              </button>
            )}
          </span>
        );
      });
    };

    return (
      <div
        ref={pageRef}
        onMouseUp={(e) => onSelectText(e, page.pageNumber)}
        className="bg-white shadow-xl rounded-sm flex flex-col p-12 transition-all duration-300 origin-top mb-8 relative border border-slate-200 select-text"
        id={`page-${page.pageNumber}`}
        style={{
          width: `${600 * (zoom / 100)}px`,
          minHeight: `${848 * (zoom / 100)}px`,
          fontSize: `${1 * (zoom / 100)}rem`
        }}
      >
        <div className="absolute top-4 right-6 text-[10px] font-bold text-slate-300 uppercase select-none flex items-center gap-2">
          {notes.length > 0 && <StickyNote size={12} className="text-indigo-400" />}
          Page {page.pageNumber}
        </div>
        <div className="border-b border-slate-100 pb-4 mb-6 select-none">
          <h3 className="font-bold text-slate-900" style={{ fontSize: `${1.2 * (zoom / 100)}rem` }}>
            {renderEnhancedText(page.title)}
          </h3>
        </div>
        <div className="text-slate-700 leading-relaxed text-justify space-y-4">
          <p>{renderEnhancedText(page.content)}</p>
          <p>{renderEnhancedText(page.content)}</p>
          <p>{renderEnhancedText(page.content)}</p>
        </div>
      </div>
    );
  };

const ShortcutHelp: React.FC<{ onClose: () => void }> = ({ onClose }) => (
  <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[200] flex items-center justify-center p-6 animate-in fade-in duration-300">
    <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Keyboard className="text-indigo-600" size={24} />
          <h2 className="text-xl font-bold text-slate-800">Keyboard Shortcuts</h2>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-400 hover:text-slate-600">
          <X size={20} />
        </button>
      </div>
      <div className="p-6 grid grid-cols-1 gap-4 max-h-[70vh] overflow-y-auto">
        <ShortcutItem keys={["Space"]} label="Play / Pause Audio" />
        <ShortcutItem keys={["←", "→"]} label="Seek Backward / Forward (5s)" />
        <ShortcutItem keys={["+", "-"]} label="Zoom In / Out" />
        <ShortcutItem keys={["[", "]"]} label="Previous / Next Page" />
        <ShortcutItem keys={["B"]} label="Toggle Sidebar Panel" />
        <ShortcutItem keys={["S"]} label="Toggle Search Focus" />
        <ShortcutItem keys={["Esc"]} label="Clear Selection / Close Menu" />
        <ShortcutItem keys={["Alt", "1-6"]} label="Switch Sidebar Tabs" />
      </div>
      <div className="p-4 bg-slate-50 text-center text-xs text-slate-500 font-medium">
        Press any key to continue
      </div>
    </div>
  </div>
);

const ShortcutItem: React.FC<{ keys: string[]; label: string }> = ({ keys, label }) => (
  <div className="flex items-center justify-between py-1 border-b border-slate-50 last:border-0">
    <span className="text-sm text-slate-600 font-medium">{label}</span>
    <div className="flex items-center gap-1">
      {keys.map((k, i) => (
        <React.Fragment key={i}>
          <kbd className="px-2 py-1 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-700 shadow-sm min-w-[30px] text-center">
            {k}
          </kbd>
          {i < keys.length - 1 && <span className="text-slate-300 mx-0.5">/</span>}
        </React.Fragment>
      ))}
    </div>
  </div>
);

const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<SidebarTab>(SidebarTab.Info);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [zoom, setZoom] = useState(100);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [readingProgress, setReadingProgress] = useState(0);
  const [showResumeToast, setShowResumeToast] = useState(false);
  const [activePageNumber, setActivePageNumber] = useState(1);
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [isCopied, setIsCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [totalReadingTime, setTotalReadingTime] = useState(0);
  const [queryScope, setQueryScope] = useState<'book' | 'general'>('book');
  const [viewMode, setViewMode] = useState<'summary' | 'pdf'>('summary');

  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showShortcutHelp, setShowShortcutHelp] = useState(false);
  const [pdfNumPages, setPdfNumPages] = useState<number>(0);
  const [pdfDoc, setPdfDoc] = useState<any>(null);

  // PDF.js loading
  useEffect(() => {
    if (MOCK_BOOK.pdfUrl && viewMode === 'pdf') {
      const loadPdf = async () => {
        try {
          const pdfjsLib = window.pdfjsLib;
          if (!pdfjsLib) {
            console.warn("PDF.js not yet loaded for page count");
            return;
          }
          if (!pdfDoc) {
            const loadingTask = pdfjsLib.getDocument(MOCK_BOOK.pdfUrl);
            const pdf = await loadingTask.promise;
            setPdfDoc(pdf);
            setPdfNumPages(pdf.numPages);
          }
        } catch (error) {
          console.error("Error loading PDF for page count:", error);
          setPdfNumPages(25); // fallback
        }
      };
      loadPdf();
    }
  }, [MOCK_BOOK.pdfUrl, viewMode, pdfDoc]);

  const totalPages = viewMode === 'summary' ? MOCK_PAGES.length : (pdfNumPages || 25);
  const [sortCriterion, setSortCriterion] = useState<SortCriterion>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [filterPage, setFilterPage] = useState<string>('');
  const [filterStartDate, setFilterStartDate] = useState<string>('');
  const [filterEndDate, setFilterEndDate] = useState<string>('');

  const [selection, setSelection] = useState<{ text: string, pageNumber: number, x: number, y: number } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchActive, setIsSearchActive] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const transcriptRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const ttsAudioContextRef = useRef<AudioContext | null>(null);
  const ttsSourceRef = useRef<AudioBufferSourceNode | null>(null);

  // Keyboard Shortcut Implementation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isInputActive = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;

      if (e.key === 'Escape') {
        if (showShortcutHelp) setShowShortcutHelp(false);
        if (showExportDialog) setShowExportDialog(false);
        if (isSearchActive) setIsSearchActive(false);
        if (selection) setSelection(null);
        return;
      }

      if (isInputActive) return;

      switch (e.key.toLowerCase()) {
        case ' ':
          e.preventDefault();
          togglePlay();
          break;
        case 'arrowright':
          if (audioRef.current) audioRef.current.currentTime = Math.min(duration, audioRef.current.currentTime + 5);
          break;
        case 'arrowleft':
          if (audioRef.current) audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 5);
          break;
        case '+':
        case '=':
          setZoom(prev => Math.min(300, prev + 10));
          break;
        case '-':
        case '_':
          setZoom(prev => Math.max(25, prev - 10));
          break;
        case '[':
          scrollToPage(Math.max(1, activePageNumber - 1));
          break;
        case ']':
          scrollToPage(Math.min(MOCK_PAGES.length, activePageNumber + 1));
          break;
        case 'b':
          setShowSidebar(prev => !prev);
          break;
        case 's':
          setIsSearchActive(true);
          setTimeout(() => searchInputRef.current?.focus(), 50);
          break;
        case 'k':
          setShowShortcutHelp(prev => !prev);
          break;
      }

      if (e.altKey && !isNaN(parseInt(e.key)) && parseInt(e.key) >= 1 && parseInt(e.key) <= 6) {
        const tabs = Object.values(SidebarTab);
        const index = parseInt(e.key) - 1;
        if (tabs[index]) {
          setCurrentTab(tabs[index]);
          if (!showSidebar) setShowSidebar(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPlaying, duration, activePageNumber, showSidebar, showShortcutHelp, showExportDialog, isSearchActive, selection]);

  // Load Persistence
  useEffect(() => {
    const savedPos = localStorage.getItem(`lumina_pos_${MOCK_BOOK.id}`);
    if (savedPos && scrollContainerRef.current) {
      setTimeout(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTop = parseFloat(savedPos);
          setShowResumeToast(true);
          setTimeout(() => setShowResumeToast(false), 3000);
        }
      }, 150);
    }
    const savedHighlights = localStorage.getItem(`lumina_highlights_${MOCK_BOOK.id}`);
    if (savedHighlights) setHighlights(JSON.parse(savedHighlights));

    const savedNotes = localStorage.getItem(`lumina_notes_${MOCK_BOOK.id}`);
    if (savedNotes) setNotes(JSON.parse(savedNotes));

    const savedTime = localStorage.getItem(`lumina_time_${MOCK_BOOK.id}`);
    if (savedTime) setTotalReadingTime(parseInt(savedTime, 10));
  }, []);

  // Timer logic - tracks active focus time
  useEffect(() => {
    const interval = setInterval(() => {
      if (document.hasFocus()) {
        setTotalReadingTime(prev => {
          const next = prev + 1;
          // Persist every 10 seconds to storage
          if (next % 10 === 0) {
            localStorage.setItem(`lumina_time_${MOCK_BOOK.id}`, next.toString());
          }
          return next;
        });
      }
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    localStorage.setItem(`lumina_highlights_${MOCK_BOOK.id}`, JSON.stringify(highlights));
  }, [highlights]);

  useEffect(() => {
    localStorage.setItem(`lumina_notes_${MOCK_BOOK.id}`, JSON.stringify(notes));
  }, [notes]);

  const handleScroll = useCallback(() => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      const progress = Math.min(100, Math.round((scrollTop / (scrollHeight - clientHeight)) * 100));
      setReadingProgress(progress);
      localStorage.setItem(`lumina_pos_${MOCK_BOOK.id}`, scrollTop.toString());
    }
  }, []);

  const handleTextSelection = (e: React.MouseEvent, pageNumber: number) => {
    const sel = window.getSelection();
    if (sel && sel.toString().trim().length > 0) {
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      setSelection({
        text: sel.toString(),
        pageNumber,
        x: rect.left + rect.width / 2,
        y: rect.top - 12
      });
    } else {
      setSelection(null);
      setIsCopied(false);
    }
  };

  const addHighlight = (colorHex: string) => {
    if (!selection) return;
    const newHighlight: Highlight = {
      id: Math.random().toString(36).substr(2, 9),
      pageNumber: selection.pageNumber,
      text: selection.text,
      color: colorHex,
      timestamp: Date.now()
    };
    setHighlights(prev => [...prev, newHighlight]);
    setSelection(null);
    window.getSelection()?.removeAllRanges();
  };

  const copyToClipboard = async () => {
    if (!selection) return;
    try {
      await navigator.clipboard.writeText(selection.text);
      setIsCopied(true);
      setTimeout(() => {
        setSelection(null);
        setIsCopied(false);
        window.getSelection()?.removeAllRanges();
      }, 800);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const speakSelection = async () => {
    if (!selection || isSpeaking) return;

    // Stop any existing TTS
    if (ttsSourceRef.current) {
      ttsSourceRef.current.stop();
    }

    setIsSpeaking(true);
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash-preview-tts",
        contents: [{ parts: [{ text: `Read this academic text clearly: ${selection.text}` }] }],
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: { voiceName: 'Kore' },
            },
          },
        },
      });

      const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
      if (base64Audio) {
        if (!ttsAudioContextRef.current) {
          ttsAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
        }

        const audioBuffer = await decodeAudioData(
          decode(base64Audio),
          ttsAudioContextRef.current,
          24000,
          1
        );

        const source = ttsAudioContextRef.current.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(ttsAudioContextRef.current.destination);
        source.onended = () => setIsSpeaking(false);
        ttsSourceRef.current = source;
        source.start();
      } else {
        setIsSpeaking(false);
      }
    } catch (error) {
      console.error("TTS Error:", error);
      setIsSpeaking(false);
    }
  };

  const stopSpeaking = () => {
    if (ttsSourceRef.current) {
      ttsSourceRef.current.stop();
      setIsSpeaking(false);
    }
  };

  const createNoteFromSelection = () => {
    if (!selection) return;

    // Check if there's an existing highlight that matches this selection exactly
    const linkedHighlight = highlights.find(h =>
      h.pageNumber === selection.pageNumber && h.text === selection.text
    );

    const newNote: Note = {
      id: Math.random().toString(36).substr(2, 9),
      pageNumber: selection.pageNumber,
      content: '',
      referenceText: selection.text,
      highlightId: linkedHighlight?.id,
      timestamp: Date.now(),
      color: linkedHighlight ? linkedHighlight.color : NOTE_COLORS[0].hex
    };

    setNotes(prev => [...prev, newNote]);
    setEditingNoteId(newNote.id);
    setCurrentTab(SidebarTab.Notes);
    setSelection(null);
    window.getSelection()?.removeAllRanges();
  };

  const addEmptyNote = () => {
    const newNote: Note = {
      id: Math.random().toString(36).substr(2, 9),
      pageNumber: activePageNumber,
      content: '',
      timestamp: Date.now(),
      color: NOTE_COLORS[0].hex
    };
    setNotes(prev => [newNote, ...prev]);
    setEditingNoteId(newNote.id);
    setCurrentTab(SidebarTab.Notes);
  };

  const updateNoteContent = (id: string, content: string) => {
    setNotes(prev => prev.map(n => n.id === id ? { ...n, content } : n));
  };

  const updateNoteColor = (id: string, color: string) => {
    setNotes(prev => prev.map(n => n.id === id ? { ...n, color } : n));
  };

  const deleteNote = (id: string) => {
    setNotes(prev => prev.filter(n => n.id !== id));
  };

  const clearFilters = () => {
    setFilterPage('');
    setFilterStartDate('');
    setFilterEndDate('');
  };

  const scrollToPage = (pageNumber: number) => {
    const element = document.getElementById(`page-${pageNumber}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) audioRef.current.pause();
      else audioRef.current.play();
      setIsPlaying(!isPlaying);
    }
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) audioRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const onTimeUpdate = () => {
    if (audioRef.current) setCurrentTime(audioRef.current.currentTime);
  };

  const onLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
      audioRef.current.playbackRate = playbackSpeed;
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!inputText.trim() && !urlInput.trim()) || isAiLoading) return;

    const prompt = urlInput.trim()
      ? `Summarize this URL: ${urlInput}${inputText ? `. Also consider my question: ${inputText}` : ''}`
      : inputText;

    const userMsg: ChatMessage = { role: 'user', content: prompt };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    const currentUrl = urlInput.trim();
    const currentScope = queryScope; // Capture scope at send time
    setUrlInput('');
    setShowUrlInput(false);
    setIsAiLoading(true);

    const { text, sources } = await getGeminiResponse(
      [...messages, userMsg],
      MOCK_BOOK.preUploadedSummary,
      currentUrl || undefined,
      currentScope
    );
    setMessages(prev => [...prev, { role: 'assistant', content: text, sources }]);
    setIsAiLoading(false);
  };

  const activeTranscriptItem = useMemo(() => {
    if (typeof MOCK_BOOK.transcript === 'string') return null;
    return MOCK_BOOK.transcript.find(
      item => currentTime >= item.startTime && currentTime <= item.endTime
    );
  }, [currentTime]);

  const activeTranscriptId = useMemo(() => {
    if (typeof MOCK_BOOK.transcript === 'string') return null;
    if (isPlaying && activeTranscriptItem) return activeTranscriptItem.id;
    const pageBased = MOCK_BOOK.transcript.find(
      item => item.pageNumber === activePageNumber
    );
    return activeTranscriptItem?.id || pageBased?.id;
  }, [activeTranscriptItem, activePageNumber, isPlaying]);

  const currentReadingText = isPlaying && activeTranscriptItem ? activeTranscriptItem.text : null;

  const totalMatches = useMemo(() => {
    if (!searchQuery || searchQuery.length < 2) return 0;
    const query = searchQuery.toLowerCase();
    let count = 0;
    MOCK_PAGES.forEach(page => {
      const content = page.content.toLowerCase();
      let pos = content.indexOf(query);
      while (pos !== -1) {
        count++;
        pos = content.indexOf(query, pos + 1);
      }
      const title = page.title.toLowerCase();
      let tPos = title.indexOf(query);
      while (tPos !== -1) {
        count++;
        tPos = title.indexOf(query, tPos + 1);
      }
    });
    return count;
  }, [searchQuery]);

  const filteredAndSortedNotes = useMemo(() => {
    let result = [...notes];
    if (filterPage) {
      const pageNum = parseInt(filterPage);
      if (!isNaN(pageNum)) result = result.filter(n => n.pageNumber === pageNum);
    }
    if (filterStartDate) {
      const start = new Date(filterStartDate).getTime();
      result = result.filter(n => n.timestamp >= start);
    }
    if (filterEndDate) {
      const end = new Date(filterEndDate).getTime() + 86399999;
      result = result.filter(n => n.timestamp <= end);
    }
    return result.sort((a, b) => {
      let comparison = 0;
      if (sortCriterion === 'date') comparison = a.timestamp - b.timestamp;
      else if (sortCriterion === 'page') comparison = a.pageNumber - b.pageNumber;
      else if (sortCriterion === 'color') comparison = a.color.localeCompare(b.color);
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [notes, sortCriterion, sortOrder, filterPage, filterStartDate, filterEndDate]);

  const isFiltered = !!(filterPage || filterStartDate || filterEndDate);

  const formatReadingTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const activeTocId = useMemo(() => {
    if (typeof MOCK_BOOK.toc === 'string') return null;
    const currentP = isPlaying && activeTranscriptItem ? activeTranscriptItem.pageNumber : activePageNumber;
    const toc = [...MOCK_BOOK.toc].sort((a, b) => b.pageNumber - a.pageNumber);
    return toc.find(item => item.pageNumber <= (currentP || 1))?.id;
  }, [activeTranscriptItem, activePageNumber, isPlaying]);

  const handleExport = (format: 'json' | 'md' | 'txt') => {
    const groupedContent: { [key: number]: { highlights: Highlight[], notes: Note[] } } = {};

    highlights.forEach(h => {
      if (!groupedContent[h.pageNumber]) groupedContent[h.pageNumber] = { highlights: [], notes: [] };
      groupedContent[h.pageNumber].highlights.push(h);
    });

    notes.forEach(n => {
      if (!groupedContent[n.pageNumber]) groupedContent[n.pageNumber] = { highlights: [], notes: [] };
      groupedContent[n.pageNumber].notes.push(n);
    });

    const pages = Object.keys(groupedContent).map(Number).sort((a, b) => a - b);
    let content = "";
    let mimeType = "text/plain";
    let extension = format;

    if (format === 'json') {
      content = JSON.stringify({
        book: MOCK_BOOK.title,
        exportedAt: new Date().toISOString(),
        highlights,
        notes
      }, null, 2);
      mimeType = "application/json";
    } else if (format === 'md' || format === 'txt') {
      content = `# Research Report: ${MOCK_BOOK.title}\n`;
      content += `Author: ${MOCK_BOOK.author}\n`;
      content += `Date: ${new Date().toLocaleDateString()}\n\n`;
      content += `---\n\n`;

      pages.forEach(p => {
        content += `## Page ${p}\n\n`;
        const items = groupedContent[p];

        if (items.highlights.length > 0) {
          content += `### Highlights\n`;
          items.highlights.forEach(h => {
            content += `> ${h.text}\n\n`;
          });
        }

        if (items.notes.length > 0) {
          content += `### Notes\n`;
          items.notes.forEach(n => {
            if (n.referenceText) content += `*Ref: "${n.referenceText}"*\n`;
            if (n.highlightId) content += `*Linked to Highlight: ${n.highlightId}*\n`;
            content += `${n.content || '_No content_'}\n\n`;
          });
        }
        content += `---\n\n`;
      });
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Lumina_Research_${MOCK_BOOK.title.replace(/\s+/g, '_')}.${extension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setShowExportDialog(false);
  };

  useEffect(() => {
    if (activeTranscriptId && transcriptRefs.current[activeTranscriptId] && currentTab === SidebarTab.Transcript) {
      transcriptRefs.current[activeTranscriptId]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [activeTranscriptId, currentTab]);

  useEffect(() => {
    if (isPlaying && activeTranscriptItem?.pageNumber) {
      const pageEl = document.getElementById(`page-${activeTranscriptItem.pageNumber}`);
      if (pageEl && scrollContainerRef.current) {
        const rect = pageEl.getBoundingClientRect();
        const containerRect = scrollContainerRef.current.getBoundingClientRect();
        if (rect.top < containerRect.top || rect.bottom > containerRect.bottom) {
          pageEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    }
  }, [activeTranscriptItem?.id, isPlaying]);

  return (
    <div className="flex h-full w-full bg-gradient-to-br from-slate-900 via-gray-900 to-slate-900 overflow-hidden relative" onClick={() => selection && setSelection(null)}>
      {showShortcutHelp && <ShortcutHelp onClose={() => setShowShortcutHelp(false)} />}

      {showExportDialog && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[300] flex items-center justify-center p-6 animate-in fade-in duration-300">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Download className="text-indigo-600" size={24} />
                <h2 className="text-xl font-bold text-slate-800">Export Research</h2>
              </div>
              <button onClick={() => setShowExportDialog(false)} className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-slate-500 mb-4">Choose a format to save your captured highlights and notes for this book.</p>

              <button
                onClick={() => handleExport('md')}
                className="w-full p-4 flex items-center gap-4 bg-slate-50 border border-slate-100 rounded-2xl hover:bg-indigo-50 hover:border-indigo-100 transition-all group"
              >
                <div className="p-3 bg-white rounded-xl shadow-sm text-indigo-600 group-hover:scale-110 transition-transform"><FileEdit size={24} /></div>
                <div className="text-left">
                  <div className="text-sm font-bold text-slate-700">Markdown Report (.md)</div>
                  <div className="text-xs text-slate-400">Perfect for Obsidian or Notion</div>
                </div>
              </button>

              <button
                onClick={() => handleExport('json')}
                className="w-full p-4 flex items-center gap-4 bg-slate-50 border border-slate-100 rounded-2xl hover:bg-amber-50 hover:border-amber-100 transition-all group"
              >
                <div className="p-3 bg-white rounded-xl shadow-sm text-amber-600 group-hover:scale-110 transition-transform"><FileJson size={24} /></div>
                <div className="text-left">
                  <div className="text-sm font-bold text-slate-700">Raw Data (.json)</div>
                  <div className="text-xs text-slate-400">Complete dataset for developers</div>
                </div>
              </button>

              <button
                onClick={() => handleExport('txt')}
                className="w-full p-4 flex items-center gap-4 bg-slate-50 border border-slate-100 rounded-2xl hover:bg-emerald-50 hover:border-emerald-100 transition-all group"
              >
                <div className="p-3 bg-white rounded-xl shadow-sm text-emerald-600 group-hover:scale-110 transition-transform"><FileCode size={24} /></div>
                <div className="text-left">
                  <div className="text-sm font-bold text-slate-700">Plain Text (.txt)</div>
                  <div className="text-xs text-slate-400">Simple, readable document</div>
                </div>
              </button>
            </div>
            <div className="p-6 bg-slate-50 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{highlights.length + notes.length} Items Captured</span>
              <button onClick={() => setShowExportDialog(false)} className="text-sm font-bold text-slate-500 hover:text-slate-800 transition-colors">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {selection && (
        <div
          className="fixed z-[100] -translate-x-1/2 -translate-y-full flex items-center gap-1.5 bg-white p-2 rounded-xl shadow-2xl border border-slate-200 animate-in zoom-in-95 slide-in-from-bottom-3 fade-in duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
          style={{ left: selection.x, top: selection.y }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-b border-r border-slate-200 rotate-45" />
          <div className="flex items-center gap-1.5 pr-1.5 border-r border-slate-100">
            {HIGHLIGHT_COLORS.map(color => (
              <button
                key={color.name}
                onClick={() => addHighlight(color.hex)}
                className={`w-6 h-6 rounded-full ${color.bg} border-2 border-white hover:scale-110 transition-transform shadow-sm active:scale-95`}
                title={`Highlight in ${color.name}`}
              />
            ))}
          </div>
          <div className="flex items-center gap-1 px-1">
            <button
              onClick={isSpeaking ? stopSpeaking : speakSelection}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold text-xs transition-all active:scale-95 group ${isSpeaking ? 'bg-amber-50 text-amber-600' : 'hover:bg-indigo-50 text-indigo-600'}`}
              title={isSpeaking ? "Stop Reading" : "Read Aloud"}
            >
              {isSpeaking ? (
                <div className="flex items-center gap-1.5 animate-pulse">
                  <Loader2 size={14} className="animate-spin" />
                  <span>Reading...</span>
                </div>
              ) : (
                <>
                  <Volume2 size={14} className="group-hover:scale-110 transition-transform" />
                  <span>Speak</span>
                </>
              )}
            </button>
            <button
              onClick={createNoteFromSelection}
              className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-indigo-50 rounded-lg text-indigo-600 font-bold text-xs transition-all active:scale-95 group"
              title="Create Linked Note"
            >
              <PencilLine size={14} className="group-hover:rotate-12 transition-transform" />
              <span>Note</span>
            </button>
            <button
              onClick={copyToClipboard}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold text-xs transition-all active:scale-95 group ${isCopied ? 'bg-green-50 text-green-600' : 'hover:bg-slate-50 text-slate-600'}`}
              title="Copy to Clipboard"
            >
              {isCopied ? <CheckCircle2 size={14} className="animate-in zoom-in duration-200" /> : <Copy size={14} className="group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />}
              <span>{isCopied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <button
            className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-colors"
            onClick={() => setSelection(null)}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {showResumeToast && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-[60]">
          <div className="bg-slate-800 text-white px-4 py-2 rounded-full shadow-lg flex items-center gap-2 text-sm font-medium animate-in fade-in slide-in-from-top-4">
            <Bookmark size={16} className="text-indigo-400" />
            Resumed from your last position
          </div>
        </div>
      )}

      {/* Sidebar Nav - Dark Theme */}
      <div className="w-16 bg-slate-900/90 border-r border-slate-700/50 flex flex-col items-center py-6 gap-6 shadow-xl z-20 backdrop-blur-sm">
        <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl text-white mb-4 shadow-lg cursor-pointer" style={{ boxShadow: '0 0 20px rgba(0, 212, 255, 0.3)' }} onClick={() => setShowSidebar(!showSidebar)}>
          <BookOpen size={24} />
        </div>

        <SidebarButton active={currentTab === SidebarTab.Info && showSidebar} onClick={() => { setCurrentTab(SidebarTab.Info); setShowSidebar(true); }} icon={<Info size={22} />} label="Info (Alt+1)" />
        <SidebarButton active={currentTab === SidebarTab.Contents && showSidebar} onClick={() => { setCurrentTab(SidebarTab.Contents); setShowSidebar(true); }} icon={<List size={22} />} label="Contents (Alt+2)" />
        <SidebarButton active={currentTab === SidebarTab.Summary && showSidebar} onClick={() => { setCurrentTab(SidebarTab.Summary); setShowSidebar(true); }} icon={<FileText size={22} />} label="Summary (Alt+3)" />
        <SidebarButton active={currentTab === SidebarTab.Notes && showSidebar} onClick={() => { setCurrentTab(SidebarTab.Notes); setShowSidebar(true); }} icon={<StickyNote size={22} />} label="Notes (Alt+4)" />
        <SidebarButton active={currentTab === SidebarTab.Transcript && showSidebar} onClick={() => { setCurrentTab(SidebarTab.Transcript); setShowSidebar(true); }} icon={<Music size={22} />} label="Transcript (Alt+5)" />
        <SidebarButton active={currentTab === SidebarTab.Assistant && showSidebar} onClick={() => { setCurrentTab(SidebarTab.Assistant); setShowSidebar(true); }} icon={<MessageSquare size={22} />} label="AI Tutor (Alt+6)" />

        <div className="mt-auto">
          <SidebarButton active={showShortcutHelp} onClick={() => setShowShortcutHelp(true)} icon={<Keyboard size={22} />} label="Shortcuts (K)" />
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="h-14 bg-slate-900/80 border-b border-slate-700/50 flex items-center justify-between px-6 z-10 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-4 min-w-0 flex-1">
            <h1 className="font-semibold text-slate-100 truncate max-w-[200px]">{MOCK_BOOK.title}</h1>

            {/* View Mode Tabs - Hidden when search is active */}
            {!isSearchActive && (
              <div className="flex items-center bg-slate-800/60 p-1 rounded-lg border border-slate-700/50">
                <button
                  onClick={() => setViewMode('summary')}
                  className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${viewMode === 'summary'
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg'
                    : 'text-slate-400 hover:text-slate-200'
                    }`}
                  style={viewMode === 'summary' ? { boxShadow: '0 0 15px rgba(0, 212, 255, 0.3)' } : {}}
                >
                  <FileText size={14} className="inline mr-1.5" />
                  Summary
                </button>
                <button
                  onClick={() => setViewMode('pdf')}
                  className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${viewMode === 'pdf'
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg'
                    : 'text-slate-400 hover:text-slate-200'
                    }`}
                  style={viewMode === 'pdf' ? { boxShadow: '0 0 15px rgba(0, 212, 255, 0.3)' } : {}}
                >
                  <BookOpen size={14} className="inline mr-1.5" />
                  PDF
                </button>
              </div>
            )}

            <div className={`flex items-center transition-all duration-300 ${isSearchActive ? 'flex-1 max-w-lg' : 'w-10'}`}>

              {!isSearchActive ? (
                <button onClick={() => setIsSearchActive(true)} className="p-2 text-slate-400 hover:text-cyan-400 hover:bg-slate-800/50 rounded-lg transition-colors" title="Search (S)">
                  <Search size={20} />
                </button>
              ) : (
                <div className="flex items-center flex-1 bg-slate-800/60 rounded-lg px-2 py-1 gap-2 border border-slate-700/50">
                  <Search size={16} className="text-slate-400 flex-shrink-0" />
                  <input
                    ref={searchInputRef}
                    autoFocus
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search..."
                    className="bg-transparent border-none outline-none text-sm w-full text-slate-100 placeholder-slate-500"
                  />
                  {searchQuery.length >= 2 && (
                    <span className="text-[10px] font-bold text-cyan-400 bg-slate-700/60 px-1.5 py-0.5 rounded border border-slate-600/50 tabular-nums whitespace-nowrap animate-in fade-in zoom-in-95 duration-200">
                      {totalMatches} {totalMatches === 1 ? 'match' : 'matches'}
                    </span>
                  )}
                  <button onClick={() => { setIsSearchActive(false); setSearchQuery(''); }} className="p-1 text-slate-400 hover:text-slate-200">
                    <X size={16} />
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 bg-slate-800/60 border border-slate-700/50 px-3 py-1 rounded-full text-xs font-bold text-slate-400">
            <span className="text-cyan-400">PAGE {activePageNumber}</span> OF {totalPages}
          </div>

          <div className="flex items-center gap-2 bg-slate-800/60 p-1 rounded-lg ml-4 border border-slate-700/50">
            <ToolbarButton icon={<ZoomOut size={18} />} onClick={() => setZoom(prev => Math.max(25, prev - 10))} title="Zoom Out (-)" />
            <span className="px-3 text-xs font-medium text-slate-300 w-12 text-center tabular-nums">{zoom}%</span>
            <ToolbarButton icon={<ZoomIn size={18} />} onClick={() => setZoom(prev => Math.min(300, prev + 10))} title="Zoom In (+)" />
          </div>

          <div className="flex items-center gap-3 ml-4">
            <button
              onClick={() => setShowShortcutHelp(true)}
              className="p-2 text-slate-400 hover:text-cyan-400 hover:bg-slate-800/50 rounded-lg transition-colors hidden sm:block"
              title="View Shortcuts (K)"
            >
              <Command size={20} />
            </button>
            <div className="h-8 w-px bg-slate-700/50 mx-1" />
            <button
              onClick={addEmptyNote}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg text-xs font-bold hover:from-cyan-400 hover:to-blue-500 transition-colors shadow-lg"
              style={{ boxShadow: '0 0 15px rgba(0, 212, 255, 0.3)' }}
            >
              <Plus size={14} />
              <span>Note</span>
            </button>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden min-h-0">
          {viewMode === 'summary' ? (
            <div
              ref={scrollContainerRef}
              onScroll={handleScroll}
              className="flex-1 bg-slate-200/50 overflow-auto p-12 flex flex-col items-center custom-scrollbar scroll-smooth relative"
            >
              {isSearchActive && searchQuery.length >= 2 && totalMatches === 0 && (
                <div className="absolute inset-0 flex items-center justify-center z-30 bg-slate-200/40 animate-in fade-in duration-300">
                  <div className="bg-white p-8 rounded-3xl shadow-2xl border border-slate-200 text-center max-w-sm mx-4 transform animate-in zoom-in-95 slide-in-from-bottom-4">
                    <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
                      <SearchX size={40} className="text-slate-300" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-800 mb-2">No results found</h3>
                    <p className="text-slate-500 text-sm leading-relaxed mb-6">
                      We couldn't find any matches for <span className="text-indigo-600 font-bold">"{searchQuery}"</span>.
                      Try adjusting your search terms or checking for typos.
                    </p>
                    <button
                      onClick={() => setSearchQuery('')}
                      className="px-6 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-bold transition-all"
                    >
                      Clear Search
                    </button>
                  </div>
                </div>
              )}

              {MOCK_PAGES.map((page) => (
                <PDFPage
                  key={page.pageNumber}
                  page={page}
                  zoom={zoom}
                  activeTranscriptText={currentReadingText}
                  onVisible={(n) => setActivePageNumber(n)}
                  searchQuery={searchQuery}
                  highlights={highlights.filter(h => h.pageNumber === page.pageNumber)}
                  notes={notes.filter(n => n.pageNumber === page.pageNumber)}
                  onSelectText={handleTextSelection}
                  onRemoveHighlight={(id) => setHighlights(prev => prev.filter(h => h.id !== id))}
                />
              ))}
              <div className="h-24 w-full flex-shrink-0" />
            </div>
          ) : (
            <div
              ref={scrollContainerRef}
              onScroll={handleScroll}
              className="flex-1 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 overflow-auto p-8 flex flex-col items-center custom-scrollbar scroll-smooth"
            >
              {MOCK_BOOK.pdfUrl ? (
                <>
                  {/* PDF Pages rendered using PDF.js canvas */}
                  {Array.from({ length: pdfNumPages || 1 }, (_, i) => i + 1).map((pageNum) => (
                    <PDFCanvasPage
                      key={pageNum}
                      pdfDoc={pdfDoc}
                      pageNumber={pageNum}
                      zoom={zoom}
                      onVisible={setActivePageNumber}
                    />
                  ))}
                  <div className="h-24 w-full flex-shrink-0" />
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center min-h-full">
                  <div className="text-center p-12 bg-slate-800/50 rounded-3xl border border-slate-700/30 backdrop-blur-sm" style={{
                    boxShadow: '0 0 40px rgba(0, 212, 255, 0.1)'
                  }}>
                    <div className="w-24 h-24 bg-gradient-to-br from-slate-700 to-slate-800 rounded-full flex items-center justify-center mx-auto mb-6 border border-slate-600/30">
                      <BookOpen size={48} className="text-slate-400" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-200 mb-2">PDF Not Available</h3>
                    <p className="text-slate-400 mb-6">This book doesn't have a PDF file attached.</p>
                    <button
                      onClick={() => setViewMode('summary')}
                      className="px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl text-sm font-bold transition-all shadow-lg"
                      style={{ boxShadow: '0 0 20px rgba(0, 212, 255, 0.3)' }}
                    >
                      View Summary Instead
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {showSidebar && (
            <aside className="w-96 bg-white border-l border-slate-200 flex flex-col shadow-xl z-10 overflow-hidden animate-in slide-in-from-right duration-300">
              <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <h3 className="font-bold text-slate-800 flex items-center gap-2 uppercase text-xs tracking-widest">
                  {currentTab === SidebarTab.Info && <><Info size={16} /> Book Details</>}
                  {currentTab === SidebarTab.Contents && <><List size={16} /> Table of Contents</>}
                  {currentTab === SidebarTab.Summary && <><FileText size={16} /> Summary</>}
                  {currentTab === SidebarTab.Notes && <><StickyNote size={16} /> My Notes</>}
                  {currentTab === SidebarTab.Transcript && <><Music size={16} /> Transcript</>}
                  {currentTab === SidebarTab.Assistant && <><MessageSquare size={16} /> AI Assistant</>}
                </h3>
                <button className="text-slate-400 hover:text-slate-600 p-1 hover:bg-slate-100 rounded-lg transition-colors" onClick={() => setShowSidebar(false)} title="Close Sidebar (B)">
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto custom-scrollbar bg-slate-50/30">
                {currentTab === SidebarTab.Info && (
                  <div className="p-6 space-y-6">
                    <img src={MOCK_BOOK.coverUrl || "https://picsum.photos/seed/bookcover/400/600"} alt={MOCK_BOOK.title} className="w-full h-64 object-cover rounded-xl shadow-md border border-slate-200" />
                    <div>
                      <h4 className="font-bold text-xl text-slate-900">{MOCK_BOOK.title}</h4>
                      <p className="text-slate-500">by {MOCK_BOOK.author}</p>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100">
                        <div className="flex justify-between items-center mb-1">
                          <p className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Reading Progress</p>
                          <span className="text-xs font-bold text-indigo-600 tabular-nums">{readingProgress}%</span>
                        </div>
                        <div className="h-2 bg-indigo-200 rounded-full w-full overflow-hidden">
                          <div className="h-full bg-indigo-600 transition-all duration-300" style={{ width: `${readingProgress}%` }} />
                        </div>
                      </div>

                      <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-amber-50 rounded-lg text-amber-600">
                            <Clock size={18} />
                          </div>
                          <div>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Time Spent Reading</p>
                            <p className="text-sm font-bold text-slate-700 tabular-nums">{formatReadingTime(totalReadingTime)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {currentTab === SidebarTab.Contents && (
                  <div className="p-4 space-y-1">
                    {typeof MOCK_BOOK.toc === 'string' ? (
                      <div className="p-4 bg-white border border-slate-200 rounded-xl whitespace-pre-wrap text-sm text-slate-700 leading-relaxed shadow-sm">
                        {MOCK_BOOK.toc || "No table of contents available."}
                      </div>
                    ) : (
                      MOCK_BOOK.toc.map((item) => {
                        const isCurrent = activeTocId === item.id;
                        const hasPassed = !isCurrent && activePageNumber >= item.pageNumber;

                        return (
                          <button
                            key={item.id}
                            onClick={() => scrollToPage(item.pageNumber)}
                            className={`w-full text-left px-4 py-3 rounded-xl transition-all flex items-center justify-between group
                              ${item.level === 1 ? 'shadow-sm mb-2 mt-4 first:mt-0' : 'hover:bg-indigo-50/50'}
                              ${isCurrent ? 'bg-indigo-50/80 border border-indigo-200 shadow-indigo-100/50 ring-2 ring-indigo-500/10' : 'bg-white border border-transparent'}
                              ${isCurrent || hasPassed ? 'text-indigo-600' : 'text-slate-600'}
                            `}
                            style={{ paddingLeft: `${item.level * 1}rem` }}
                          >
                            <div className="flex items-center gap-3">
                              <span className={`text-xs font-bold transition-all ${isCurrent || hasPassed ? 'opacity-100' : 'opacity-0'}`}>
                                {isCurrent && isPlaying ? (
                                  <Volume2 size={14} className="text-indigo-600 animate-pulse" />
                                ) : (
                                  <ChevronRight size={14} className={isCurrent ? 'text-indigo-600' : 'text-indigo-400'} />
                                )}
                              </span>
                              <span className={`${item.level === 1 ? 'font-bold text-sm' : 'text-sm font-medium opacity-90'} ${isCurrent ? 'font-bold' : ''}`}>
                                {item.title}
                              </span>
                            </div>
                            <span className={`text-[10px] font-bold tabular-nums transition-colors ${isCurrent ? 'text-indigo-500' : 'text-slate-300 group-hover:text-indigo-400'}`}>
                              {item.pageNumber}
                            </span>
                          </button>
                        );
                      })
                    )}
                  </div>
                )}

                {currentTab === SidebarTab.Summary && (
                  <div className="p-6 prose prose-slate prose-sm italic text-slate-700 leading-relaxed border-l-4 border-indigo-100 pl-4 py-2 bg-white m-4 rounded-lg shadow-sm">
                    "{MOCK_BOOK.preUploadedSummary}"
                  </div>
                )}

                {currentTab === SidebarTab.Notes && (
                  <div className="h-full flex flex-col">
                    <div className="p-4 flex-1 space-y-4">
                      <div className="flex flex-col gap-3">
                        <button
                          onClick={addEmptyNote}
                          className="w-full py-3 border-2 border-dashed border-slate-200 rounded-xl flex items-center justify-center gap-2 text-slate-400 hover:text-indigo-600 hover:border-indigo-200 hover:bg-indigo-50/30 transition-all text-sm font-medium shadow-sm"
                        >
                          <Plus size={18} />
                          Create New Note
                        </button>

                        <div className="flex flex-col gap-2 bg-white/60 p-2 rounded-xl border border-slate-100 shadow-sm backdrop-blur-sm">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              <button onClick={() => setSortCriterion('date')} className={`p-2 rounded-lg transition-all ${sortCriterion === 'date' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-100'}`} title="Sort by Date"><Clock size={14} /></button>
                              <button onClick={() => setSortCriterion('page')} className={`p-2 rounded-lg transition-all ${sortCriterion === 'page' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-100'}`} title="Sort by Page"><Hash size={14} /></button>
                              <button onClick={() => setSortCriterion('color')} className={`p-2 rounded-lg transition-all ${sortCriterion === 'color' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-100'}`} title="Sort by Color"><Palette size={14} /></button>
                            </div>
                            <div className="flex items-center gap-1">
                              <button onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')} className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all" title={`Order: ${sortOrder}`}>{sortOrder === 'asc' ? <SortAsc size={16} /> : <SortDesc size={16} />}</button>
                              <button onClick={() => setShowFilters(!showFilters)} className={`p-2 rounded-lg transition-all ${showFilters || isFiltered ? 'bg-indigo-50 text-indigo-600' : 'text-slate-400 hover:bg-slate-100'}`} title="Toggle Filters">{isFiltered ? <Filter size={16} fill="currentColor" /> : <Filter size={16} />}</button>
                            </div>
                          </div>

                          {showFilters && (
                            <div className="pt-2 border-t border-slate-100 space-y-3 animate-in slide-in-from-top-2 fade-in duration-200">
                              <div className="grid grid-cols-2 gap-2">
                                <div className="space-y-1">
                                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Page #</label>
                                  <div className="relative">
                                    <input type="number" value={filterPage} onChange={(e) => setFilterPage(e.target.value)} placeholder="Any" className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-2 py-1.5 text-xs text-slate-900 outline-none focus:ring-1 focus:ring-indigo-500" />
                                    <Hash size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-300" />
                                  </div>
                                </div>
                                <div className="flex items-end pb-0.5">
                                  <button onClick={clearFilters} disabled={!isFiltered} className="w-full py-1.5 px-2 bg-slate-100 hover:bg-slate-200 disabled:opacity-30 disabled:hover:bg-slate-100 text-slate-500 rounded-lg text-[10px] font-bold uppercase tracking-tight flex items-center justify-center gap-1.5 transition-all"><FilterX size={12} /> Clear</button>
                                </div>
                              </div>
                              <div className="space-y-1">
                                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Date Range</label>
                                <div className="flex items-center gap-2">
                                  <input type="date" value={filterStartDate} onChange={(e) => setFilterStartDate(e.target.value)} className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-900 outline-none focus:ring-1 focus:ring-indigo-500" />
                                  <span className="text-slate-300 text-xs">—</span>
                                  <input type="date" value={filterEndDate} onChange={(e) => setFilterEndDate(e.target.value)} className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 text-xs text-slate-900 outline-none focus:ring-1 focus:ring-indigo-500" />
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {filteredAndSortedNotes.length === 0 ? (
                        <div className="text-center py-16 opacity-40 bg-white/40 rounded-3xl border border-dashed border-slate-200">
                          <div className="bg-slate-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                            {isFiltered ? <FilterX size={32} className="text-slate-300" /> : <StickyNote className="text-slate-300" size={32} />}
                          </div>
                          <p className="text-sm font-medium text-slate-500">{isFiltered ? 'No matches for these filters.' : 'Your thought garden is empty.'}</p>
                          {isFiltered && <button onClick={clearFilters} className="mt-3 text-xs font-bold text-indigo-600 hover:underline">Clear all filters</button>}
                        </div>
                      ) : (
                        filteredAndSortedNotes.map(note => (
                          <div
                            key={note.id}
                            className={`border ${editingNoteId === note.id ? 'border-indigo-400 ring-2 ring-indigo-50 z-10' : 'border-slate-200 shadow-sm'} rounded-2xl p-4 group hover:shadow-md transition-all relative overflow-hidden flex flex-col`}
                            style={{ backgroundColor: `${note.color}15` }}
                          >
                            <div className="absolute top-0 left-0 w-full h-1.5 opacity-90" style={{ backgroundColor: note.color }} />
                            <div className="flex justify-between items-start mb-3 pt-1">
                              <div className="flex gap-2">
                                <button onClick={() => scrollToPage(note.pageNumber)} className="flex items-center gap-1.5 px-2 py-0.5 bg-white/60 hover:bg-white text-slate-600 hover:text-indigo-600 rounded text-[10px] font-bold uppercase tracking-widest transition-colors shadow-xs"><Bookmark size={10} style={{ color: note.color }} /> Page {note.pageNumber}</button>
                                {note.highlightId && (
                                  <div className="flex items-center gap-1 px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded text-[10px] font-bold uppercase tracking-widest border border-indigo-100" title="Linked to Highlight">
                                    <Link2 size={10} />
                                    Linked
                                  </div>
                                )}
                              </div>
                              <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                {editingNoteId !== note.id && <button onClick={() => setEditingNoteId(note.id)} className="p-1.5 bg-white/60 hover:bg-white text-slate-400 hover:text-indigo-600 rounded-lg transition-colors shadow-xs"><PencilLine size={14} /></button>}
                                <button onClick={() => deleteNote(note.id)} className="p-1.5 bg-white/60 hover:bg-white text-slate-400 hover:text-red-600 rounded-lg transition-colors shadow-xs"><Trash2 size={14} /></button>
                              </div>
                            </div>
                            {note.referenceText && <div className="text-[11px] text-slate-500 italic mb-3 border-l-3 pl-3 py-1 line-clamp-3 bg-white/40 rounded-r-md" style={{ borderColor: `${note.color}40` }}>"{note.referenceText}"</div>}
                            {editingNoteId === note.id ? (
                              <div className="space-y-3 animate-in fade-in slide-in-from-top-1">
                                <div className="flex items-center gap-2 mb-2 p-1.5 bg-white/80 rounded-xl border border-white/40 shadow-xs">
                                  <Palette size={12} className="text-slate-400 ml-1" />
                                  <div className="flex gap-1.5">
                                    {NOTE_COLORS.map(color => (
                                      <button key={color.name} onClick={() => updateNoteColor(note.id, color.hex)} className={`w-4 h-4 rounded-full transition-all ring-offset-1 ${note.color === color.hex ? 'ring-2 ring-slate-400 scale-110' : 'hover:scale-110 opacity-70 hover:opacity-100'}`} style={{ backgroundColor: color.hex }} title={color.name} />
                                    ))}
                                  </div>
                                </div>
                                <textarea autoFocus value={note.content} onChange={(e) => updateNoteContent(note.id, e.target.value)} placeholder="Write your note here..." className="w-full text-sm text-slate-900 bg-white/80 border border-slate-200/50 rounded-xl p-4 focus:ring-2 focus:ring-indigo-500 outline-none h-40 resize-none shadow-inner" />
                                <div className="flex justify-end gap-2"><button onClick={() => setEditingNoteId(null)} className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold hover:bg-indigo-700 shadow-md flex items-center gap-1.5 transition-all"><Check size={14} />Save Changes</button></div>
                              </div>
                            ) : (
                              <div className="cursor-pointer group/content" onClick={() => setEditingNoteId(note.id)}>
                                <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed min-h-[1.5rem] group-hover/content:text-slate-900 transition-colors">{note.content || <span className="text-slate-400/60 italic">No content. Click to add your thoughts...</span>}</p>
                              </div>
                            )}
                            <div className="mt-4 pt-3 border-t border-black/5 flex items-center justify-between">
                              <div className="flex items-center gap-1.5 text-[9px] text-slate-500 font-bold uppercase tracking-tighter tabular-nums"><Calendar size={10} /> {new Date(note.timestamp).toLocaleDateString()}<span className="ml-2 w-2 h-2 rounded-full shadow-xs" style={{ backgroundColor: note.color }} /></div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                    {(highlights.length > 0 || notes.length > 0) && (
                      <div className="p-4 bg-white border-t border-slate-100 shadow-lg animate-in slide-in-from-bottom-4">
                        <button
                          onClick={() => setShowExportDialog(true)}
                          className="w-full py-3 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100 flex items-center justify-center gap-2 group"
                        >
                          <Download size={18} className="group-hover:translate-y-0.5 transition-transform" />
                          Export My Research
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {currentTab === SidebarTab.Transcript && (
                  <div className="p-6 space-y-4">
                    {typeof MOCK_BOOK.transcript === 'string' ? (
                      <div className="p-4 bg-white border border-slate-200 rounded-xl whitespace-pre-wrap text-sm text-slate-700 leading-relaxed shadow-sm">
                        {MOCK_BOOK.transcript || "No transcript available for this audio summary."}
                      </div>
                    ) : (
                      MOCK_BOOK.transcript.map(item => (
                        <div key={item.id} ref={el => transcriptRefs.current[item.id] = el} className={`p-3 rounded-lg transition-all cursor-pointer border flex flex-col gap-1 ${activeTranscriptId === item.id ? 'highlight-active border-yellow-400 scale-[1.02] bg-white ring-2 ring-yellow-50' : 'border-transparent hover:bg-slate-50'}`} onClick={() => { if (audioRef.current) audioRef.current.currentTime = item.startTime; if (!isPlaying) togglePlay(); if (item.pageNumber) scrollToPage(item.pageNumber); }}>
                          <div className="flex justify-between items-center"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter tabular-nums">{Math.floor(item.startTime / 60)}:{(item.startTime % 60).toString().padStart(2, '0')}</span>{item.pageNumber && <span className="text-[9px] font-bold text-indigo-500 opacity-60">PAGE {item.pageNumber}</span>}</div>
                          <p className={`text-sm leading-relaxed ${activeTranscriptId === item.id ? 'text-slate-900 font-medium' : 'text-slate-600'}`}>{item.text}</p>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {currentTab === SidebarTab.Assistant && (
                  <div className="h-full flex flex-col p-4 relative">
                    <div className="flex items-center bg-slate-100 p-1 rounded-xl mb-4 self-center shadow-inner">
                      <button
                        onClick={() => setQueryScope('book')}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${queryScope === 'book' ? 'bg-white text-indigo-600 shadow-sm ring-1 ring-slate-200' : 'text-slate-500 hover:text-slate-700'}`}
                      >
                        <BookOpen size={14} />
                        Current Book
                      </button>
                      <button
                        onClick={() => setQueryScope('general')}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${queryScope === 'general' ? 'bg-white text-indigo-600 shadow-sm ring-1 ring-slate-200' : 'text-slate-500 hover:text-slate-700'}`}
                      >
                        <Globe size={14} />
                        General Query
                      </button>
                    </div>

                    <div className="flex-1 space-y-4 mb-4 overflow-y-auto custom-scrollbar pr-2">
                      {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-4 opacity-60">
                          <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center">
                            <Sparkles className="w-8 h-8 text-indigo-400" />
                          </div>
                          <div className="space-y-2">
                            <p className="text-sm font-bold text-slate-700">How can I help you research today?</p>
                            <p className="text-xs text-slate-500 leading-relaxed max-w-[200px]">
                              Switch to <span className="font-bold">"Current Book"</span> to ask specific questions about the text, or <span className="font-bold">"General Query"</span> for broader research.
                            </p>
                          </div>
                        </div>
                      ) : (
                        messages.map((msg, i) => (
                          <div key={i} className={`flex flex-col gap-2 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                            <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none shadow-sm' : 'bg-slate-100 text-slate-800 rounded-tl-none border border-slate-200'}`}>{msg.content}</div>
                            {msg.sources && msg.sources.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 mt-1">
                                {msg.sources.map((source, si) => (
                                  <a key={si} href={source.uri} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 px-2 py-0.5 bg-white border border-slate-200 rounded-full text-[10px] font-bold text-slate-500 hover:text-indigo-600 hover:border-indigo-200 transition-all"><Globe size={10} className="text-indigo-400" /><span className="truncate max-w-[120px]">{source.title}</span><ExternalLink size={8} /></a>
                                ))}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                      {isAiLoading && (
                        <div className="flex flex-col items-start gap-2">
                          <div className="bg-slate-100 p-3 rounded-2xl rounded-tl-none border border-slate-200 flex gap-1 animate-pulse">{showUrlInput ? 'Analyzing external content...' : 'Generating response...'}</div>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-2">
                      {showUrlInput && (
                        <div className="bg-white border border-slate-200 p-3 rounded-xl shadow-lg animate-in slide-in-from-bottom-2 duration-200">
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Globe size={12} className="text-indigo-500" /> Web Content URL</label>
                            <button onClick={() => setShowUrlInput(false)} className="text-slate-400 hover:text-slate-600"><X size={14} /></button>
                          </div>
                          <div className="relative">
                            <input autoFocus type="url" value={urlInput} onChange={(e) => setUrlInput(e.target.value)} placeholder="https://example.com/research" className="w-full pl-3 pr-10 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 outline-none focus:ring-2 focus:ring-indigo-500" />
                            <div className="absolute right-2 top-2 text-slate-300"><LinkIcon size={14} /></div>
                          </div>
                        </div>
                      )}

                      <form onSubmit={handleSendMessage} className="relative flex items-center gap-2">
                        <div className="flex-1 relative">
                          <input type="text" value={inputText} onChange={(e) => setInputText(e.target.value)} placeholder={showUrlInput ? "Add a specific question (optional)..." : `Ask about ${queryScope === 'book' ? 'the book' : 'anything'}...`} className="w-full pl-4 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm text-slate-900 transition-all shadow-sm" />
                          <button type="button" onClick={() => setShowUrlInput(!showUrlInput)} className={`absolute right-3 top-2.5 p-1 rounded-lg transition-all ${showUrlInput || urlInput ? 'text-indigo-600 bg-indigo-50' : 'text-slate-400 hover:text-indigo-600 hover:bg-slate-100'}`} title="Analyze Web Link"><LinkIcon size={18} /></button>
                        </div>
                        <button type="submit" disabled={(!inputText.trim() && !urlInput.trim()) || isAiLoading} className="p-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:bg-slate-300 transition-all shadow-md active:scale-95"><ChevronRight size={20} /></button>
                      </form>
                    </div>
                  </div>
                )}
              </div>
            </aside>
          )}
        </div>

        <footer className="h-20 bg-slate-800 border-t border-slate-700 flex items-center px-8 z-[100] gap-8 shadow-[0_-4px_20px_rgba(0,0,0,0.5)] flex-shrink-0 mt-auto">
          <audio ref={audioRef} src={MOCK_BOOK.audioUrl} onTimeUpdate={onTimeUpdate} onLoadedMetadata={onLoadedMetadata} onEnded={() => setIsPlaying(false)} />
          <button onClick={togglePlay} className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-blue-500 text-white rounded-full flex items-center justify-center hover:from-cyan-300 hover:to-blue-400 transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(34,211,238,0.4)] border border-white/20" title="Play / Pause (Space)">
            {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-1" />}
          </button>
          <div className="flex-1 flex flex-col gap-1">
            <div className="flex justify-between text-[10px] font-bold text-slate-400 uppercase tracking-widest tabular-nums">
              <span>{Math.floor(currentTime / 60)}:{(Math.floor(currentTime % 60)).toString().padStart(2, '0')}</span>
              <span>{Math.floor(duration / 60)}:{(Math.floor(duration % 60)).toString().padStart(2, '0')}</span>
            </div>
            <div className="relative w-full h-1.5 group">
              <input type="range" min="0" max={duration || 0} value={currentTime} onChange={seek} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
              <div className="absolute inset-0 bg-slate-700 rounded-full" />
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full transition-all duration-100" style={{ width: `${(currentTime / duration) * 100}%` }} />
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="relative">
              <button onClick={() => setShowSpeedMenu(!showSpeedMenu)} className={`flex items-center gap-1.5 px-2 py-1 rounded-lg border transition-all text-xs font-bold uppercase tracking-tight ${showSpeedMenu ? 'border-cyan-500 bg-cyan-500/20 text-cyan-400' : 'border-slate-600 text-slate-400 hover:border-slate-500'}`}>
                <Zap size={14} fill={showSpeedMenu ? "currentColor" : "none"} />
                <span className="tabular-nums">{playbackSpeed}x</span>
              </button>
              {showSpeedMenu && (
                <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 bg-slate-800 border border-slate-700 shadow-xl rounded-xl py-2 min-w-[80px] z-50">
                  {PLAYBACK_SPEEDS.map(speed => (
                    <button key={speed} onClick={() => { setPlaybackSpeed(speed); setShowSpeedMenu(false); if (audioRef.current) audioRef.current.playbackRate = speed; }} className={`w-full px-4 py-1.5 text-left text-xs hover:bg-slate-700 ${playbackSpeed === speed ? 'text-cyan-400 font-bold bg-cyan-500/10' : 'text-slate-300'}`}>{speed}x</button>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center gap-3 w-32">
              <Volume2 size={20} className="text-slate-400" />
              <div className="flex-1 h-1.5 bg-slate-700 rounded-full relative overflow-hidden">
                <div className="absolute inset-0 bg-cyan-500 rounded-full w-3/4" />
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

const SidebarButton: React.FC<{ active: boolean; onClick: () => void; icon: React.ReactNode; label: string }> = ({ active, onClick, icon, label }) => (
  <button onClick={onClick} className={`relative group p-2.5 rounded-xl transition-all ${active ? 'bg-indigo-50 text-indigo-600 shadow-sm' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}>
    {icon}
    <div className="absolute left-full ml-4 px-2 py-1 bg-slate-800 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50 font-bold uppercase tracking-tight shadow-lg">{label}</div>
    {active && <div className="absolute -left-3 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-indigo-600 rounded-r-full" />}
  </button>
);

const ToolbarButton: React.FC<{ icon: React.ReactNode; onClick: () => void; title?: string }> = ({ icon, onClick, title }) => (
  <button onClick={onClick} className="p-1.5 hover:bg-white hover:shadow-sm rounded transition-all text-slate-500 hover:text-slate-800" title={title}>{icon}</button>
);

export default App;
