
import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Search, Globe, X, History, TrendingUp, Clock, Trash2, Book, Layers, ChevronRight, Loader2 } from 'lucide-react';
import { MOCK_DATA } from '../mockData';
import { ContentType, RankingItem } from '../types';

interface NavbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onTypeChange?: (type: ContentType) => void;
}

const Navbar: React.FC<NavbarProps> = ({ searchQuery, onSearchChange, onTypeChange }) => {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const loadingTimeoutRef = useRef<number | null>(null);
  
  const navItems = ['Updates', 'Featured', 'Ranking', 'Manga List', 'Creators', 'Favorite', 'About Us'];

  // Load recent searches on mount
  useEffect(() => {
    const saved = localStorage.getItem('manga_plus_recent_searches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  // Effect to simulate loading state when search query changes
  useEffect(() => {
    if (searchQuery.trim()) {
      setIsLoading(true);
      if (loadingTimeoutRef.current) window.clearTimeout(loadingTimeoutRef.current);
      
      loadingTimeoutRef.current = window.setTimeout(() => {
        setIsLoading(false);
      }, 400); // Subtle delay to show "thinking" process
    } else {
      setIsLoading(false);
    }
    
    return () => {
      if (loadingTimeoutRef.current) window.clearTimeout(loadingTimeoutRef.current);
    };
  }, [searchQuery]);

  // Save search to history when query is committed
  const addToHistory = (query: string) => {
    if (!query.trim()) return;
    const updated = [
      query.trim(),
      ...recentSearches.filter(s => s !== query.trim())
    ].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('manga_plus_recent_searches', JSON.stringify(updated));
  };

  const clearHistory = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Clear all recent search history?')) {
      setRecentSearches([]);
      localStorage.removeItem('manga_plus_recent_searches');
    }
  };

  const removeHistoryItem = (e: React.MouseEvent, item: string) => {
    e.stopPropagation();
    const updated = recentSearches.filter(s => s !== item);
    setRecentSearches(updated);
    localStorage.setItem('manga_plus_recent_searches', JSON.stringify(updated));
  };

  // Filter suggestions based on current MOCK_DATA
  const suggestions = useMemo(() => {
    if (!searchQuery.trim()) return [];
    return MOCK_DATA
      .filter(item => 
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.author.toLowerCase().includes(searchQuery.toLowerCase())
      )
      .slice(0, 6);
  }, [searchQuery]);

  useEffect(() => {
    if (isSearchOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isSearchOpen]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) && 
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      addToHistory(searchQuery);
      setIsFocused(false);
    }
  };

  const handleSelectSuggestion = (item: RankingItem) => {
    onSearchChange(item.title);
    addToHistory(item.title);
    if (onTypeChange) {
      onTypeChange(item.type);
    }
    setIsFocused(false);
    setIsSearchOpen(false); // Collapse mobile search view
  };

  const handleSelectHistory = (query: string) => {
    onSearchChange(query);
    addToHistory(query);
    setIsFocused(false);
  };

  return (
    <nav className="flex items-center justify-between px-6 py-4 bg-[#121212] sticky top-0 z-50 border-b border-gray-800 h-[72px]">
      <div className="flex items-center space-x-8 flex-1">
        <div className="flex items-center gap-1 cursor-pointer shrink-0" onClick={() => window.location.reload()}>
          <div className="bg-red-600 text-white font-black px-2 py-0.5 rounded italic text-lg uppercase tracking-tighter">
            Manga
          </div>
          <span className="text-white font-bold text-lg uppercase">Plus</span>
        </div>
        
        {!isSearchOpen && (
          <div className="hidden lg:flex items-center space-x-6">
            {navItems.map((item) => (
              <a
                key={item}
                href="#"
                className={`text-sm font-medium hover:text-white transition-colors ${
                  item === 'Ranking' ? 'text-white underline decoration-red-600 decoration-2 underline-offset-4' : 'text-gray-400'
                }`}
              >
                {item}
              </a>
            ))}
          </div>
        )}

        {isSearchOpen && (
          <div className="flex-1 max-w-xl relative animate-in fade-in slide-in-from-left-4 duration-200">
            <div className="relative group">
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onFocus={() => setIsFocused(true)}
                onChange={(e) => onSearchChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search manga, authors, or books..."
                className="w-full bg-gray-900 border border-gray-700 rounded-full py-2.5 pl-11 pr-12 text-sm text-white focus:outline-none focus:border-red-500/50 focus:ring-2 focus:ring-red-500/10 transition-all shadow-2xl"
              />
              <Search className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors ${isFocused ? 'text-red-500' : 'text-gray-500'}`} size={16} />
              
              <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                {isLoading && (
                  <Loader2 size={16} className="text-red-500 animate-spin" />
                )}
                {searchQuery && !isLoading && (
                  <button 
                    onClick={() => {
                      onSearchChange('');
                      inputRef.current?.focus();
                    }}
                    className="text-gray-500 hover:text-white p-1 hover:bg-white/5 rounded-full transition-colors"
                  >
                    <X size={16} />
                  </button>
                )}
                {!searchQuery && !isLoading && (
                  <button 
                    onClick={() => {
                      setIsSearchOpen(false);
                      setIsFocused(false);
                    }}
                    className="text-gray-500 hover:text-white p-1 hover:bg-white/5 rounded-full"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            </div>

            {/* Suggestions & History Dropdown */}
            {isFocused && (searchQuery.trim() !== '' || recentSearches.length > 0) && (
              <div 
                ref={dropdownRef}
                className="absolute top-full left-0 right-0 mt-3 bg-[#1c1c1c] border border-gray-800 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[80vh]"
              >
                {/* Auto Suggestions Section */}
                {searchQuery.trim() !== '' && (
                  <div className="flex-shrink-0">
                    <div className="px-4 py-3 flex items-center gap-2 text-[10px] font-black uppercase text-gray-500 tracking-widest border-b border-gray-800/50">
                      <TrendingUp size={12} className="text-red-500" />
                      Suggested Results
                    </div>
                    
                    <div className="overflow-y-auto max-h-[400px] custom-scrollbar">
                      {suggestions.length > 0 ? (
                        suggestions.map((item) => (
                          <button
                            key={item.id}
                            onMouseDown={() => handleSelectSuggestion(item)}
                            className="w-full px-4 py-3 flex items-center gap-4 hover:bg-white/[0.04] transition-all text-left group border-b border-gray-800/30 last:border-0 relative overflow-hidden"
                          >
                            <div className="w-10 h-14 rounded bg-gray-800 overflow-hidden flex-shrink-0 border border-gray-700 group-hover:border-red-500/40 transition-colors shadow-lg">
                              <img src={item.imageUrl} alt="" className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                            </div>
                            <div className="flex-1 min-w-0 py-0.5">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`text-[8px] font-black px-1.5 py-0.5 rounded border-2 uppercase flex items-center gap-1 leading-none tracking-wider ${
                                  item.type === 'Manga' 
                                    ? 'bg-red-500/10 text-red-500 border-red-500/20' 
                                    : 'bg-blue-500/10 text-blue-500 border-blue-500/20'
                                }`}>
                                  {item.type === 'Manga' ? <Layers size={8} /> : <Book size={8} />}
                                  {item.type}
                                </span>
                                <span className="text-[10px] text-gray-600 font-black tracking-tighter">RANK #{item.rank}</span>
                              </div>
                              <p className="text-sm font-black text-white truncate group-hover:text-red-500 transition-colors tracking-tight">{item.title}</p>
                              <p className="text-[11px] text-gray-500 font-bold truncate tracking-wide">{item.author}</p>
                            </div>
                            <ChevronRight size={16} className="text-gray-800 group-hover:text-red-500 group-hover:translate-x-1 transition-all" />
                          </button>
                        ))
                      ) : (
                        <div className="px-4 py-12 text-center">
                          <p className="text-sm text-gray-500 font-black italic uppercase tracking-widest opacity-50">No matches found</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Separator */}
                {searchQuery.trim() !== '' && recentSearches.length > 0 && (
                  <div className="h-[2px] bg-gray-800/50" />
                )}

                {/* Recent History Section */}
                {recentSearches.length > 0 && (
                  <div className="flex-shrink-0 bg-black/10">
                    <div className="px-4 py-3 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-gray-500">
                      <div className="flex items-center gap-2">
                        <Clock size={12} />
                        Recent History
                      </div>
                      <button 
                        onMouseDown={clearHistory}
                        className="flex items-center gap-1.5 px-2 py-1 rounded bg-gray-800/30 hover:bg-red-500/10 hover:text-red-500 transition-all border border-gray-700/50 group"
                      >
                        <Trash2 size={10} className="group-hover:animate-pulse" />
                        <span>Clear All</span>
                      </button>
                    </div>
                    <div className="py-1">
                      {recentSearches.map((search, idx) => (
                        <div
                          key={`${search}-${idx}`}
                          className="group flex items-center hover:bg-white/[0.03] transition-colors"
                        >
                          <button
                            onMouseDown={() => handleSelectHistory(search)}
                            className="flex-1 px-4 py-2.5 flex items-center gap-3 text-left"
                          >
                            <History size={14} className="text-gray-600 group-hover:text-red-400" />
                            <span className="text-sm font-medium text-gray-400 group-hover:text-white transition-colors">{search}</span>
                          </button>
                          <button 
                            onMouseDown={(e) => removeHistoryItem(e, search)}
                            className="px-4 py-2.5 text-gray-700 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                            title="Remove from history"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center space-x-6 ml-4">
        {!isSearchOpen && (
          <button 
            onClick={() => setIsSearchOpen(true)}
            className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-gray-800 rounded-full"
            aria-label="Open search"
          >
            <Search size={20} />
          </button>
        )}
        <button className="flex items-center space-x-2 bg-gray-800/50 hover:bg-gray-800 px-3 py-1.5 rounded-md border border-gray-700 transition-all">
          <span className="text-xs text-gray-400">Language</span>
          <span className="text-xs font-bold text-white uppercase flex items-center gap-1">
            EN <Globe size={12} className="text-gray-500" />
          </span>
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
