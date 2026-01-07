import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Users, List, Sparkles, Star, MessageSquareQuote, ChevronRight, MessageSquare, Search, Hash, ArrowUp, Play } from 'lucide-react';
import { MangaSeries, Chapter } from '../../types';
import { MOCK_REVIEWS, MOCK_COMMENTS } from '../../constants';

interface RightPanelProps {
  series: MangaSeries;
  activeChapter: Chapter;
  aiInsights: string | null;
  onChapterSelect: (chapter: Chapter) => void;
}

const RatingBar = ({ stars, percentage }: { stars: number, percentage: number }) => (
  <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500">
    <span className="w-2">{stars}</span>
    <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
      <div className="h-full bg-sky-500" style={{ width: `${percentage}%` }} />
    </div>
    <span className="w-6 text-right">{percentage}%</span>
  </div>
);

export const RightPanel: React.FC<RightPanelProps> = ({ series, activeChapter, aiInsights, onChapterSelect }) => {
  const [chaptersOpen, setChaptersOpen] = useState(true);
  const [reviewsOpen, setReviewsOpen] = useState(true);
  const [commentsOpen, setCommentsOpen] = useState(true);
  const [expandedCharacters, setExpandedCharacters] = useState<string[]>([]);
  const [jumpValue, setJumpValue] = useState('');
  const [showScrollTop, setShowScrollTop] = useState(false);
  
  const containerRef = useRef<HTMLDivElement>(null);

  const toggleChar = (id: string) => {
    setExpandedCharacters(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleJumpToChapter = (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseFloat(jumpValue);
    if (isNaN(num)) return;
    
    const targetChapter = series.chapters.find(ch => ch.number === num);
    if (targetChapter) {
      onChapterSelect(targetChapter);
      setJumpValue('');
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = e.currentTarget.scrollTop;
    setShowScrollTop(scrollTop > 400);
  };

  const scrollToTop = () => {
    containerRef.current?.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  return (
    <div 
      ref={containerRef}
      onScroll={handleScroll}
      className="w-96 bg-[#0f172a] border-l border-slate-800 flex flex-col gap-6 p-6 overflow-y-auto shrink-0 hidden lg:flex h-screen pb-20 relative"
    >
      {/* Scroll to Top Button */}
      <button 
        onClick={scrollToTop}
        className={`fixed bottom-24 right-8 z-50 p-3 bg-sky-500 text-black rounded-full shadow-2xl shadow-sky-500/40 transition-all duration-300 transform hover:scale-110 hover:bg-sky-400 active:scale-95 ${showScrollTop ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0 pointer-events-none'}`}
        aria-label="Scroll to top"
      >
        <ArrowUp size={20} strokeWidth={3} />
      </button>

      {/* Series Overall Rating Card */}
      <div className="bg-[#1e293b] rounded-2xl p-6 border border-slate-800 ring-1 ring-slate-700/50 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col">
            <span className="text-3xl font-black text-white">4.9</span>
            <div className="flex items-center gap-0.5 text-sky-500">
              <Star size={12} fill="currentColor" />
              <Star size={12} fill="currentColor" />
              <Star size={12} fill="currentColor" />
              <Star size={12} fill="currentColor" />
              <Star size={12} fill="currentColor" />
            </div>
            <span className="text-[10px] text-slate-500 mt-1 uppercase font-bold tracking-widest">32.4k ratings</span>
          </div>
          <button className="bg-sky-500 hover:bg-sky-400 text-black text-[10px] font-black px-4 py-2 rounded-lg transition-all shadow-lg shadow-sky-500/10 uppercase tracking-widest">
            Rate Series
          </button>
        </div>
        <div className="flex flex-col gap-1.5">
          <RatingBar stars={5} percentage={92} />
          <RatingBar stars={4} percentage={6} />
          <RatingBar stars={3} percentage={1} />
          <RatingBar stars={2} percentage={0.5} />
          <RatingBar stars={1} percentage={0.5} />
        </div>
      </div>

      {/* AI Insights Card */}
      <div className="bg-[#1e293b] rounded-2xl p-6 border border-sky-900/30 shadow-xl ring-1 ring-sky-500/10">
        <div className="flex items-center gap-2 mb-4 text-sky-400">
          <Sparkles size={20} />
          <h3 className="font-bold tracking-tight">Smart Summary (Ch. {activeChapter.number})</h3>
        </div>
        <div className="text-sm leading-relaxed text-slate-300 space-y-3">
          {aiInsights ? (
            <div className="prose prose-invert prose-sm">
              {aiInsights.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 italic">Generate AI insights in the reader to see key plot points and character motivations here.</p>
          )}
        </div>
        
        <div className="mt-6 flex flex-col gap-3">
          <button 
            onClick={() => alert(`Rate Ch. ${activeChapter.number} feature coming soon!`)}
            className="w-full bg-sky-500 hover:bg-sky-400 text-black py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all shadow-lg shadow-sky-500/20 flex items-center justify-center gap-2"
          >
            <Star size={14} fill="currentColor" />
            Rate this chapter
          </button>
          <button className="w-full bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-sky-500/20 transition-all">
            View Full Analysis
          </button>
        </div>
      </div>

      {/* Chapters Navigation */}
      <div className="bg-[#1e293b] rounded-2xl overflow-hidden border border-slate-800 ring-1 ring-slate-700/50">
        <button 
          onClick={() => setChaptersOpen(!chaptersOpen)}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-800/50 transition-colors"
        >
          <div className="flex items-center gap-3 font-bold text-slate-200">
            <List size={20} className="text-sky-400" />
            <span>Chapters</span>
          </div>
          <ChevronDown size={18} className={`text-slate-500 transition-transform ${chaptersOpen ? 'rotate-180' : ''}`} />
        </button>
        {chaptersOpen && (
          <div className="p-2 border-t border-slate-800 flex flex-col gap-1">
            <div className="px-2 pt-2 pb-1">
              <form onSubmit={handleJumpToChapter} className="relative group">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-sky-400 transition-colors">
                  <Hash size={14} />
                </div>
                <input 
                  type="text" 
                  value={jumpValue}
                  onChange={(e) => setJumpValue(e.target.value)}
                  placeholder="Jump to chapter #..."
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-lg py-2 pl-9 pr-4 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/50 transition-all"
                />
                <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-500 hover:text-white">
                  <Search size={14} />
                </button>
              </form>
            </div>

            <div className="max-h-60 overflow-y-auto mt-1 flex flex-col gap-1 px-1">
              {series.chapters.map(ch => {
                const isActive = ch.id === activeChapter.id;
                return (
                  <div 
                    key={ch.id}
                    onClick={() => onChapterSelect(ch)}
                    className={`group flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium cursor-pointer transition-all duration-200 transform hover:scale-[1.02] ${isActive ? 'bg-sky-500 text-black shadow-lg shadow-sky-500/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white hover:shadow-md'}`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      {isActive && <Play size={12} fill="currentColor" className="shrink-0 animate-in zoom-in duration-300" />}
                      <span className="truncate">Ch. {ch.number} - {ch.title}</span>
                    </div>
                    <div className="flex items-center shrink-0">
                      {isActive ? (
                        <span className="text-[10px] font-black uppercase tracking-tighter animate-pulse px-1.5 py-0.5 bg-black/10 rounded">Now</span>
                      ) : (
                        <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-all translate-x-1 group-hover:translate-x-0 text-slate-500" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Top Reviews Preview */}
      <div className="bg-[#1e293b] rounded-2xl overflow-hidden border border-slate-800 ring-1 ring-slate-700/50">
        <button 
          onClick={() => setReviewsOpen(!reviewsOpen)}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-800/50 transition-colors"
        >
          <div className="flex items-center gap-3 font-bold text-slate-200">
            <MessageSquareQuote size={20} className="text-sky-400" />
            <span>Top Reviews</span>
          </div>
          <ChevronDown size={18} className={`text-slate-500 transition-transform ${reviewsOpen ? 'rotate-180' : ''}`} />
        </button>
        {reviewsOpen && (
          <div className="p-4 border-t border-slate-800 flex flex-col gap-4">
            {MOCK_REVIEWS.map(review => (
              <div key={review.id} className="bg-slate-900/40 p-3 rounded-xl border border-slate-800/50">
                <div className="flex items-center gap-2 mb-2">
                  <img src={review.authorAvatar} alt={review.author} className="w-6 h-6 rounded-full" />
                  <span className="text-[11px] font-bold text-slate-300">@{review.author}</span>
                  <div className="ml-auto flex items-center gap-0.5 text-sky-500">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} size={8} fill={i < review.rating ? 'currentColor' : 'none'} className={i < review.rating ? '' : 'text-slate-700'} />
                    ))}
                  </div>
                </div>
                <p className="text-[11px] text-slate-400 italic line-clamp-2 leading-relaxed">"{review.text}"</p>
              </div>
            ))}
            <button className="text-center text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors flex items-center justify-center gap-1 py-1">
              Read all reviews <ChevronRight size={12} />
            </button>
          </div>
        )}
      </div>

      {/* Recent Comments Preview */}
      <div className="bg-[#1e293b] rounded-2xl overflow-hidden border border-slate-800 ring-1 ring-slate-700/50">
        <button 
          onClick={() => setCommentsOpen(!commentsOpen)}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-800/50 transition-colors"
        >
          <div className="flex items-center gap-3 font-bold text-slate-200">
            <MessageSquare size={20} className="text-sky-400" />
            <span>Recent Comments</span>
          </div>
          <ChevronDown size={18} className={`text-slate-500 transition-transform ${commentsOpen ? 'rotate-180' : ''}`} />
        </button>
        {commentsOpen && (
          <div className="p-4 border-t border-slate-800 flex flex-col gap-4">
            {MOCK_COMMENTS.slice(0, 3).map(comment => (
              <div key={comment.id} className="flex gap-3 bg-slate-900/40 p-3 rounded-xl border border-slate-800/50">
                <img src={comment.authorAvatar} className="w-8 h-8 rounded-full shrink-0" alt={comment.author} />
                <div className="flex-1 min-w-0">
                   <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-bold text-white truncate">@{comment.author}</span>
                    <span className="text-[9px] text-slate-500 shrink-0">{comment.timestamp}</span>
                  </div>
                  <p className="text-[11px] text-slate-300 line-clamp-2">{comment.text}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Characters Profile Section */}
      <div className="bg-[#1e293b] rounded-2xl p-6 border border-slate-800 ring-1 ring-slate-700/50 mb-8">
        <div className="flex items-center gap-3 mb-6 text-slate-200 font-bold">
          <Users size={20} className="text-sky-400" />
          <span>Character Profiles</span>
        </div>
        <div className="flex flex-col gap-6">
          {series.characters.map(char => (
            <div key={char.id} className="flex gap-4 group cursor-default">
              <div className="relative shrink-0">
                <img 
                  src={char.image} 
                  className="w-12 h-12 rounded-full border-2 border-slate-700 shadow-md ring-2 ring-sky-500/0 group-hover:ring-sky-500/40 group-hover:scale-110 group-hover:border-sky-500/50 group-hover:shadow-[0_0_15px_rgba(56,189,248,0.3)] transition-all duration-300" 
                  alt={char.name} 
                />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-bold text-white group-hover:text-sky-400 transition-colors">{char.name}</h4>
                <p className="text-[10px] text-slate-500 uppercase font-black tracking-wider mb-2">{char.role}</p>
                <button 
                  onClick={() => toggleChar(char.id)}
                  className="flex items-center gap-1 text-[11px] font-bold text-sky-400 hover:text-sky-300 transition-colors uppercase"
                >
                  Description {expandedCharacters.includes(char.id) ? '▲' : '▼'}
                </button>
                {expandedCharacters.includes(char.id) && (
                  <p className="mt-2 text-xs text-slate-400 leading-relaxed bg-slate-900/30 p-2 rounded animate-in fade-in slide-in-from-top-1 duration-200">
                    {char.description}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};