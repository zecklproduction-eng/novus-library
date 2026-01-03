
import React, { useState, useEffect, useRef } from 'react';
import { MediaType, MediaStatus, Media } from '../types';
import StarRating from './StarRating';
import { POPULAR_MEDIA } from '../services/mockData';

interface PostReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    title: string;
    type: MediaType;
    rating: number;
    status: MediaStatus;
    body: string;
    hasSpoilers: boolean;
    tags: string[];
  }) => Promise<void>;
}

const PostReviewModal: React.FC<PostReviewModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [title, setTitle] = useState('');
  const [type, setType] = useState<MediaType>(MediaType.MANGA);
  const [rating, setRating] = useState(0);
  const [status, setStatus] = useState<MediaStatus>(MediaStatus.READING);
  const [body, setBody] = useState('');
  const [hasSpoilers, setHasSpoilers] = useState(false);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Search / Selection State
  const [showResults, setShowResults] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Filter logic: show top 5 if empty, otherwise filter by title
  const filteredMedia = title.trim() === '' 
    ? POPULAR_MEDIA.slice(0, 5) 
    : POPULAR_MEDIA.filter(m => 
        m.title.toLowerCase().includes(title.toLowerCase())
      ).slice(0, 5);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (resultsRef.current && !resultsRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Draft persistence logic
  useEffect(() => {
    if (isOpen) {
      const draft = localStorage.getItem('mediahub_review_draft');
      if (draft) {
        try {
          const parsed = JSON.parse(draft);
          setTitle(parsed.title || '');
          setBody(parsed.body || '');
          setRating(parsed.rating || 0);
          setType(parsed.type || MediaType.MANGA);
          setStatus(parsed.status || MediaStatus.READING);
          setTags(parsed.tags || []);
          setHasSpoilers(parsed.hasSpoilers || false);
        } catch (e) {
          console.error("Failed to load draft");
        }
      }
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && (title || body || rating > 0)) {
      const draft = { title, body, rating, type, status, tags, hasSpoilers };
      localStorage.setItem('mediahub_review_draft', JSON.stringify(draft));
    }
  }, [title, body, rating, type, status, tags, hasSpoilers, isOpen]);

  if (!isOpen) return null;

  const handleSelectMedia = (media: Media) => {
    setTitle(media.title);
    setType(media.type);
    if (media.tags && media.tags.length > 0) {
      // Merge unique tags
      const newTags = Array.from(new Set([...tags, ...media.tags]));
      setTags(newTags);
    }
    setShowResults(false);
  };

  const handleAddTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const val = tagInput.trim().replace(/,/g, '');
      if (val && !tags.includes(val)) {
        setTags([...tags, val]);
        setTagInput('');
      }
    }
  };

  const removeTag = (t: string) => setTags(tags.filter(item => item !== t));

  const parseSpoilerSyntax = (text: string) => {
    return text.replace(/\|\|(.*?)\|\|/g, '<span class="spoiler">$1</span>');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !body.trim() || rating === 0) return;

    setIsSubmitting(true);
    try {
      const formattedBody = parseSpoilerSyntax(body);
      
      await onSubmit({ 
        title: title.trim(), 
        type, 
        rating, 
        status, 
        body: formattedBody, 
        hasSpoilers: hasSpoilers || formattedBody.includes('class="spoiler"'), 
        tags: tags.length > 0 ? tags : ['General'] 
      });
      
      localStorage.removeItem('mediahub_review_draft');
      setTitle('');
      setRating(0);
      setBody('');
      setHasSpoilers(false);
      setTags([]);
      onClose();
    } catch (error) {
      alert("Failed to post review. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isFormValid = title.trim() !== '' && body.trim() !== '' && rating > 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="absolute inset-0 bg-slate-900/70 backdrop-blur-md animate-in fade-in duration-300"
        onClick={() => {
          if (body.length > 50) {
            if (window.confirm("Close without finishing? Your draft is saved.")) onClose();
          } else {
            onClose();
          }
        }}
      />
      
      <div className="relative bg-white w-full max-w-2xl rounded-[2.5rem] shadow-2xl overflow-hidden animate-in zoom-in-95 fade-in duration-300 flex flex-col max-h-[90vh]">
        <div className="px-10 py-8 border-b border-slate-100 flex items-center justify-between bg-white relative z-10">
          <div>
            <h2 className="text-3xl font-black text-slate-900 tracking-tighter leading-none">Share Your Thoughts</h2>
            <div className="mt-2 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Public Feed Contribution</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-3 rounded-full hover:bg-slate-100 text-slate-400 transition-all hover:rotate-90"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-10 space-y-8 overflow-y-auto custom-scrollbar flex-grow">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-3 relative" ref={resultsRef}>
              <label className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Search Media</label>
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Type to search manga..."
                  className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-3xl text-base text-slate-900 font-bold focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:bg-white transition-all shadow-inner placeholder:text-slate-300"
                  value={title}
                  onFocus={() => setShowResults(true)}
                  onChange={(e) => {
                    setTitle(e.target.value);
                    setShowResults(true);
                  }}
                  required
                />
                
                {showResults && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-3xl shadow-[0_20px_60px_-15px_rgba(0,0,0,0.3)] z-50 overflow-hidden animate-in slide-in-from-top-2 duration-200">
                    {filteredMedia.length > 0 ? (
                      <div className="p-2">
                        <div className="px-4 py-2 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                          {title.trim() === '' ? 'Trending Now' : 'Matching Titles'}
                        </div>
                        {filteredMedia.map(m => (
                          <button
                            key={m.id}
                            type="button"
                            onClick={() => handleSelectMedia(m)}
                            className="w-full flex items-center gap-4 p-3 hover:bg-indigo-600 rounded-2xl transition-all text-left group"
                          >
                            <img src={m.coverUrl} className="w-10 h-14 object-cover rounded-lg shadow-sm border border-slate-100" alt="" />
                            <div>
                              {/* Explicit high-contrast text color for visibility */}
                              <div className="font-black text-sm text-slate-900 group-hover:text-white transition-colors">{m.title}</div>
                              <div className="text-[10px] font-bold uppercase text-indigo-600/80 group-hover:text-white/80 transition-colors">{m.type}</div>
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="p-6 text-center">
                        <p className="text-xs font-bold text-slate-400">Title not in our database? No problem!</p>
                        <button 
                          type="button"
                          onClick={() => setShowResults(false)}
                          className="mt-2 text-indigo-600 text-[10px] font-black uppercase underline hover:text-indigo-800 transition-colors"
                        >
                          Use "{title}" as Custom Title
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            
            <div className="space-y-3">
              <label className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Category</label>
              <div className="relative">
                <select 
                  className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-3xl text-sm text-slate-900 font-black focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all appearance-none cursor-pointer"
                  value={type}
                  onChange={(e) => setType(e.target.value as MediaType)}
                >
                  <option value={MediaType.MANGA}>Manga / Manhua</option>
                  <option value={MediaType.ANIME}>Anime / Series</option>
                  <option value={MediaType.BOOK}>Literature / Books</option>
                </select>
                <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-end">
            <div className="space-y-3">
              <label className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Your Rating</label>
              <div className="flex items-center justify-between bg-slate-50 px-6 py-4 rounded-3xl border border-slate-200 shadow-inner group transition-all focus-within:ring-4 focus-within:ring-indigo-500/10">
                <StarRating rating={rating} editable onChange={setRating} size="lg" />
                <span className={`text-xl font-black ${rating > 0 ? 'text-indigo-600' : 'text-slate-300'}`}>
                  {rating > 0 ? rating.toFixed(1) : '—'}
                </span>
              </div>
            </div>
            <div className="space-y-3">
              <label className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Current Status</label>
              <div className="relative">
                <select 
                  className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-3xl text-sm text-slate-900 font-black focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all appearance-none cursor-pointer"
                  value={status}
                  onChange={(e) => setStatus(e.target.value as MediaStatus)}
                >
                  <option value={MediaStatus.READING}>Active (Reading/Watching)</option>
                  <option value={MediaStatus.COMPLETED}>Completed</option>
                  <option value={MediaStatus.ON_HOLD}>On Hold / Sidelined</option>
                </select>
                <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Your Review</label>
            <div className="relative group">
              <textarea 
                placeholder="What made this special? Use ||text|| to hide spoilers."
                rows={8}
                className="w-full px-8 py-7 bg-slate-50 border border-slate-200 rounded-[2rem] text-base text-slate-900 font-medium leading-relaxed focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:bg-white transition-all shadow-inner placeholder:text-slate-300 custom-scrollbar"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                required
              />
              <div className="absolute bottom-4 right-6 text-[10px] font-black text-slate-400 uppercase tracking-widest pointer-events-none group-focus-within:opacity-0 transition-opacity">
                {body.length} Characters
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Community Tags</label>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-[1.5rem] focus-within:ring-4 focus-within:ring-indigo-500/10 focus-within:bg-white transition-all flex flex-wrap gap-2.5 items-center min-h-[64px]">
              {tags.map(t => (
                <span key={t} className="px-4 py-1.5 bg-indigo-50 text-indigo-700 text-[10px] font-black uppercase rounded-full border border-indigo-100 flex items-center group/tag hover:bg-indigo-600 hover:text-white transition-all shadow-sm">
                  {t}
                  <button type="button" onClick={() => removeTag(t)} className="ml-2 hover:scale-125 transition-transform">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              ))}
              <input 
                type="text" 
                placeholder={tags.length === 0 ? "Add tags like 'Masterpiece'..." : "Add more..."}
                className="flex-grow bg-transparent border-none focus:ring-0 text-sm text-slate-900 font-bold min-w-[150px] placeholder:text-slate-400"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleAddTag}
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-8 pt-10 border-t border-slate-50">
            <div className="flex items-center group cursor-pointer" onClick={() => setHasSpoilers(!hasSpoilers)}>
              <div className={`w-14 h-8 flex items-center rounded-full transition-all duration-500 p-1 ${hasSpoilers ? 'bg-red-500 shadow-lg shadow-red-100' : 'bg-slate-200 shadow-inner'}`}>
                <div className={`w-6 h-6 bg-white rounded-full transition-transform duration-500 shadow-sm ${hasSpoilers ? 'translate-x-6' : 'translate-x-0'}`} />
              </div>
              <div className="ml-4">
                <span className="block text-[11px] font-black text-slate-900 uppercase tracking-widest">Spoiler Shield</span>
                <span className="block text-[10px] font-bold text-slate-400">Blurred until user confirms</span>
              </div>
            </div>

            <div className="flex w-full sm:w-auto space-x-4">
              <button 
                type="button"
                onClick={onClose}
                className="flex-1 sm:flex-initial px-8 py-4 text-xs font-black text-slate-400 hover:text-slate-700 transition-colors uppercase tracking-[0.2em]"
              >
                Discard
              </button>
              <button 
                type="submit"
                disabled={isSubmitting || !isFormValid}
                className="flex-[2] sm:flex-initial px-12 py-4 bg-indigo-600 text-white text-xs font-black rounded-3xl hover:bg-indigo-700 hover:scale-[1.05] active:scale-[0.95] transition-all shadow-2xl shadow-indigo-100 disabled:opacity-40 disabled:shadow-none disabled:scale-100 uppercase tracking-[0.2em]"
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Publishing...
                  </span>
                ) : 'Publish Review'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PostReviewModal;
