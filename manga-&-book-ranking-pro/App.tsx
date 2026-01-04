
import React, { useState, useMemo, useEffect } from 'react';
import { ChevronDown, ArrowUpDown, ArrowUp } from 'lucide-react';
import Navbar from './components/Navbar';
import RankingCard from './components/RankingCard';
import Tabs from './components/Tabs';
import { MOCK_DATA } from './mockData';
import { ContentType, FilterType, SortBy, SortOrder } from './types';

const FILTER_DESCRIPTIONS: Record<FilterType, string> = {
  'Hottest': 'The most popular titles right now based on recent activity.',
  'Trending': 'Titles quickly rising in popularity this week.',
  'Most Viewed': 'Ranking based on total lifetime views.',
  'Most Popular': 'All-time fan favorites with the highest engagement.',
  'Ongoing': 'Currently releasing new chapters or volumes.',
  'Completed': 'Stories that have reached their conclusion.',
  'Fiction': 'Imaginative storytelling and prose.',
  'Non-Fiction': 'Informative content, guides, and real-world facts.'
};

const SORT_DESCRIPTIONS: Record<SortBy, string> = {
  'Rank': 'Order by official placement and popularity.',
  'Views': 'Sort based on total engagement metrics.',
  'Title': 'Organize alphabetically for easy browsing.'
};

const ORDER_DESCRIPTIONS: Record<SortOrder, string> = {
  'Asc': 'Display results from lowest to highest.',
  'Desc': 'Display results from highest to lowest.'
};

const App: React.FC = () => {
  const [contentType, setContentType] = useState<ContentType>('Manga');
  const [filterType, setFilterType] = useState<FilterType>('Hottest');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortBy>('Rank');
  const [sortOrder, setSortOrder] = useState<SortOrder>('Asc');
  
  // Dynamic update time tracking
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date>(new Date());
  const [timeAgo, setTimeAgo] = useState<string>('Just now');

  // Scroll to top state
  const [showScrollTop, setShowScrollTop] = useState(false);

  const contentTypes: ContentType[] = ['Manga', 'Book'];

  const filterMap: Record<ContentType, FilterType[]> = {
    Manga: ['Hottest', 'Trending', 'Most Popular', 'Most Viewed', 'Ongoing', 'Completed'],
    Book: ['Hottest', 'Trending', 'Most Popular', 'Most Viewed', 'Fiction', 'Non-Fiction']
  };

  const currentFilters = filterMap[contentType];

  // Helper to format "time ago"
  const formatTimeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 30) return 'Just now';
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  // Update "time ago" text every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeAgo(formatTimeAgo(lastUpdatedAt));
    }, 15000); 
    return () => clearInterval(interval);
  }, [lastUpdatedAt]);

  // Handle scroll to show/hide "Go to Top" button
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 400) {
        setShowScrollTop(true);
      } else {
        setShowScrollTop(false);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    if (!currentFilters.includes(filterType)) {
      setFilterType(currentFilters[0]);
    }
  }, [contentType, currentFilters, filterType]);

  // Content refresh triggers an update to the timestamp
  useEffect(() => {
    setLastUpdatedAt(new Date());
    setTimeAgo('Just now');
  }, [contentType, filterType, searchQuery, sortBy, sortOrder]);

  const filteredData = useMemo(() => {
    const data = MOCK_DATA.filter((item) => {
      const matchesType = item.type === contentType;
      const matchesCategory = item.category === filterType;
      const matchesSearch = !searchQuery || item.title.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesCategory && matchesSearch;
    });

    return data.sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'Rank') {
        comparison = a.rank - b.rank;
      } else if (sortBy === 'Views') {
        comparison = a.views - b.views;
      } else if (sortBy === 'Title') {
        comparison = a.title.localeCompare(b.title);
      }

      return sortOrder === 'Asc' ? comparison : -comparison;
    });
  }, [contentType, filterType, searchQuery, sortBy, sortOrder]);

  const resetFilters = () => {
    setSearchQuery('');
    setFilterType(currentFilters[0]);
    setSortBy('Rank');
    setSortOrder('Asc');
  };

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  const containerKey = `${contentType}-${filterType}-${sortBy}-${sortOrder}-${searchQuery}`;

  return (
    <div className="min-h-screen flex flex-col bg-[#121212] text-white selection:bg-red-500/30">
      <Navbar 
        searchQuery={searchQuery} 
        onSearchChange={setSearchQuery} 
        onTypeChange={setContentType}
      />

      <main className="flex-grow max-w-[1440px] mx-auto w-full px-6 py-8">
        <header className="mb-10">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-8">
            <div>
              <h1 className="text-5xl font-black italic tracking-tighter mb-6 uppercase text-white/95">
                Ranking
              </h1>
              <Tabs 
                activeType={contentType} 
                types={contentTypes} 
                onChange={setContentType} 
              />
            </div>
            
            <div className="flex flex-col items-start md:items-end gap-3">
              <div className="text-right hidden md:block">
                <p className="text-[10px] font-black text-gray-600 uppercase tracking-[0.2em] mb-1">
                  Database Sync
                </p>
                <p className="text-sm font-bold text-gray-300 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                  Updated {timeAgo}
                </p>
              </div>
              
              <div className="flex items-center gap-2 bg-gray-900/50 p-1 rounded-lg border border-gray-800">
                <div className="relative group/sort-by">
                  <div className="relative">
                    <select 
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value as SortBy)}
                      className="appearance-none bg-transparent pl-3 pr-8 py-1.5 text-xs font-bold text-gray-300 focus:outline-none cursor-pointer hover:text-white transition-colors"
                    >
                      <option value="Rank">Rank</option>
                      <option value="Views">Views</option>
                      <option value="Title">Title</option>
                    </select>
                    <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
                  </div>
                  <div className="absolute bottom-full right-0 mb-3 opacity-0 group-hover/sort-by:opacity-100 transition-all duration-200 translate-y-1 group-hover/sort-by:translate-y-0 z-50 pointer-events-none w-max">
                    <div className="bg-[#1f1f1f] text-white text-[11px] py-2 px-3 rounded-lg border border-gray-700 shadow-2xl font-bold max-w-[180px] text-center leading-snug">
                      {SORT_DESCRIPTIONS[sortBy]}
                      <div className="absolute top-full right-4 -mt-1.5 border-[6px] border-transparent border-t-[#1f1f1f]" />
                    </div>
                  </div>
                </div>

                <div className="w-px h-4 bg-gray-800" />

                <div className="relative group/sort-order">
                  <button 
                    onClick={() => setSortOrder(prev => prev === 'Asc' ? 'Desc' : 'Asc')}
                    className="px-2 py-1.5 hover:bg-white/5 rounded transition-colors text-gray-400 hover:text-white flex items-center gap-1.5"
                  >
                    <ArrowUpDown size={14} className={sortOrder === 'Desc' ? 'rotate-180 transition-transform' : 'transition-transform'} />
                    <span className="text-[10px] font-black uppercase tracking-wider">{sortOrder}</span>
                  </button>
                  <div className="absolute bottom-full right-0 mb-3 opacity-0 group-hover/sort-order:opacity-100 transition-all duration-200 translate-y-1 group-hover/sort-order:translate-y-0 z-50 pointer-events-none w-max">
                    <div className="bg-[#1f1f1f] text-white text-[11px] py-2 px-3 rounded-lg border border-gray-700 shadow-2xl font-bold max-w-[180px] text-center leading-snug">
                      {ORDER_DESCRIPTIONS[sortOrder]}
                      <div className="absolute top-full right-4 -mt-1.5 border-[6px] border-transparent border-t-[#1f1f1f]" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="flex items-center space-x-8 border-b border-gray-800 overflow-x-auto no-scrollbar scroll-smooth">
              {currentFilters.map((filter) => (
                <div key={filter} className="relative group/filter-tab">
                  <button
                    onClick={() => setFilterType(filter)}
                    className={`pb-4 px-2 text-lg font-black transition-all relative whitespace-nowrap ${
                      filterType === filter 
                        ? 'text-white translate-y-[-2px]' 
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {filter}
                    <div 
                      className={`absolute bottom-0 left-0 right-0 h-[3px] bg-red-600 rounded-t-full transition-all duration-500 ease-out transform ${
                        filterType === filter ? 'scale-x-100 opacity-100' : 'scale-x-0 opacity-0'
                      }`} 
                    />
                  </button>

                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 opacity-0 group-hover/filter-tab:opacity-100 transition-all duration-200 translate-y-1 group-hover/filter-tab:translate-y-0 z-50 pointer-events-none w-max max-w-[200px]">
                    <div className="bg-[#1f1f1f] text-white text-[11px] py-2 px-3 rounded-lg border border-gray-700 shadow-2xl text-center leading-snug font-bold">
                      {FILTER_DESCRIPTIONS[filter]}
                      <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-[6px] border-transparent border-t-[#1f1f1f]" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </header>

        {filteredData.length > 0 ? (
          <div 
            key={containerKey}
            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-x-8 gap-y-16"
          >
            {filteredData.map((item, index) => (
              <div 
                key={item.id}
                className="animate-in fade-in slide-in-from-bottom-6 duration-700 fill-mode-both"
                style={{ 
                  animationDelay: `${index * 60}ms`,
                  animationFillMode: 'both' 
                }}
              >
                <RankingCard item={item} />
              </div>
            ))}
          </div>
        ) : (
          <section className="flex flex-col items-center justify-center py-40 text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="relative mb-8">
              <div className="w-32 h-32 bg-gray-900/30 rounded-full flex items-center justify-center border border-gray-800">
                <span className="text-6xl text-gray-800 font-black">!</span>
              </div>
              <div className="absolute -bottom-2 -right-2 w-12 h-12 bg-red-600/10 rounded-full blur-xl" />
            </div>
            <h2 className="text-3xl font-black text-gray-300 mb-3 tracking-tight">Empty Rankings</h2>
            <p className="text-gray-500 max-w-sm mx-auto leading-relaxed mb-10">
              No results found for <span className="text-red-500 font-bold">"{searchQuery || filterType}"</span> in {contentType}s. 
              Try a different filter or search term.
            </p>
            <button 
              onClick={resetFilters}
              className="bg-white/5 hover:bg-white/10 text-white px-8 py-3 rounded-full text-sm font-bold border border-white/10 transition-all hover:scale-105 active:scale-95"
            >
              Reset Filters
            </button>
          </section>
        )}
      </main>

      <footer className="border-t border-gray-900 bg-black/40 py-20 px-6 mt-20">
        <div className="max-w-[1440px] mx-auto grid grid-cols-1 md:grid-cols-12 gap-16">
          <div className="md:col-span-5 flex flex-col gap-6">
            <div className="flex items-center gap-1 group cursor-pointer" onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})}>
              <div className="bg-red-600 text-white font-black px-2 py-0.5 rounded italic text-xl uppercase tracking-tighter group-hover:scale-105 transition-transform">
                Manga
              </div>
              <span className="text-white font-bold text-xl uppercase">Plus</span>
            </div>
            <p className="text-base text-gray-500 max-w-md leading-relaxed">
              Experience the world's most popular manga and literature platform. 
              Always official, always supportive of the original creators.
            </p>
          </div>
          
          <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-12">
            <div className="flex flex-col gap-4">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em]">Platform</h4>
              <nav className="flex flex-col gap-3">
                <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Mobile App</a>
                <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Creators Console</a>
                <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Submissions</a>
              </nav>
            </div>
            <div className="flex flex-col gap-4">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em]">Company</h4>
              <nav className="flex flex-col gap-3">
                <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">About Us</a>
                <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Press</a>
                <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Careers</a>
              </nav>
            </div>
            <div className="flex flex-col gap-4">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em]">Follow</h4>
              <nav className="flex flex-col gap-3">
                <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">X (Twitter)</a>
                <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Discord</a>
              </nav>
            </div>
          </div>
        </div>
        
        <div className="max-w-[1440px] mx-auto mt-20 pt-10 border-t border-gray-900 flex flex-col sm:flex-row justify-between items-center gap-6">
          <span className="text-[10px] text-gray-600 font-black uppercase tracking-[0.3em]">
            © 2024 Shueisha Inc. Global Edition
          </span>
          <div className="flex items-center gap-8 opacity-40 hover:opacity-100 transition-opacity">
             <div className="w-8 h-8 bg-gray-700 rounded-sm" />
             <div className="w-8 h-8 bg-gray-700 rounded-sm" />
             <div className="w-8 h-8 bg-gray-700 rounded-sm" />
          </div>
        </div>
      </footer>

      {/* Go to Top Button */}
      <button
        onClick={scrollToTop}
        className={`fixed bottom-8 right-8 z-[60] p-4 bg-red-600 text-white rounded-full shadow-[0_0_25px_rgba(220,38,38,0.5)] border border-red-500/20 transition-all duration-500 transform hover:scale-110 active:scale-90 flex items-center justify-center ${
          showScrollTop 
            ? 'opacity-100 translate-y-0 pointer-events-auto' 
            : 'opacity-0 translate-y-12 pointer-events-none'
        }`}
        aria-label="Scroll to top"
      >
        <ArrowUp size={24} strokeWidth={3} />
        {/* Glow effect on hover */}
        <div className="absolute inset-0 rounded-full bg-red-400/20 blur-md scale-0 group-hover:scale-150 transition-transform duration-500 -z-10" />
      </button>
    </div>
  );
};

export default App;
