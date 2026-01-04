
import React, { useState, useEffect, useRef } from 'react';
import { Flame, BookOpen, Share2, Heart, CheckCircle2 } from 'lucide-react';
import { RankingItem } from '../types';

interface RankingCardProps {
  item: RankingItem;
}

const RankingCard: React.FC<RankingCardProps> = ({ item }) => {
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  // Persistence for Favorite status
  const [isFavorite, setIsFavorite] = useState(() => {
    try {
      const saved = localStorage.getItem('manga_plus_favorites');
      const favorites = saved ? JSON.parse(saved) : [];
      return favorites.includes(item.id);
    } catch {
      return false;
    }
  });

  // Handle cases where image might be cached and load instantly
  useEffect(() => {
    if (imgRef.current?.complete) {
      setIsImageLoaded(true);
    }
  }, []);

  const handleReadNow = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isReading) return;

    setIsReading(true);
    // Simulate a brief loading period for a "premium" feel
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setIsReading(false);
    alert(`Redirecting to read: ${item.title}`);
  };

  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isSharing) return;

    setIsSharing(true);
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    setIsSharing(false);
    alert(`Share link for "${item.title}" copied to clipboard!`);
  };

  const toggleFavorite = (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const saved = localStorage.getItem('manga_plus_favorites');
      let favorites = saved ? JSON.parse(saved) : [];
      
      if (isFavorite) {
        favorites = favorites.filter((id: string) => id !== item.id);
      } else {
        favorites = [...favorites, item.id];
      }
      
      localStorage.setItem('manga_plus_favorites', JSON.stringify(favorites));
      setIsFavorite(!isFavorite);
    } catch (err) {
      console.error("Failed to update favorites:", err);
    }
  };

  return (
    <div 
      className="flex flex-col group cursor-pointer transition-all duration-500 cubic-bezier(0.34, 1.56, 0.64, 1) hover:scale-[1.03] hover:shadow-[0_30px_70px_-15px_rgba(0,0,0,0.7),0_0_20px_rgba(239,68,68,0.05)] p-3 -m-3 rounded-2xl hover:bg-white/[0.04] border border-transparent hover:border-white/10 active:scale-[0.98]"
      onClick={() => console.log(`Card clicked: ${item.title}`)}
    >
      {/* Cover Image Container */}
      <div className="relative aspect-[2/3] overflow-hidden rounded-lg bg-[#1a1a1a] transition-all duration-500 group-hover:shadow-2xl group-hover:shadow-red-900/30">
        
        {/* Advanced Shimmering Skeleton Loader */}
        {!isImageLoaded && (
          <div className="absolute inset-0 z-10 overflow-hidden bg-[#1f1f1f]">
            {/* Shimmer Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full animate-sweep" />
            
            {/* Abstract Placeholder Content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center p-4 opacity-30">
              <div className="w-1/2 h-1/2 bg-gray-800 rounded-md mb-4 rotate-3" />
              <div className="w-3/4 h-3 bg-gray-800 rounded-full mb-2" />
              <div className="w-1/2 h-3 bg-gray-800 rounded-full" />
            </div>
          </div>
        )}

        {/* Optimized Main Image with Blur-In Transition */}
        <img
          ref={imgRef}
          src={item.imageUrl}
          alt={item.title}
          onLoad={() => setIsImageLoaded(true)}
          decoding="async"
          loading="lazy"
          className={`w-full h-full object-cover transition-all duration-1000 cubic-bezier(0.4, 0, 0.2, 1) ${
            isImageLoaded 
              ? 'opacity-100 scale-100 blur-0' 
              : 'opacity-0 scale-110 blur-xl'
          } group-hover:scale-110`}
        />

        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        
        {/* Status Badge overlay for Completed */}
        {item.category === 'Completed' && (
          <div className="absolute top-2 left-2 z-20">
            <div className="bg-emerald-600/90 backdrop-blur-sm px-2 py-0.5 rounded-md flex items-center gap-1 shadow-lg border border-emerald-400/30">
              <CheckCircle2 size={10} className="text-white" />
              <span className="text-[9px] font-black uppercase text-white tracking-widest leading-none">Completed</span>
            </div>
          </div>
        )}

        {/* Favorite indicator overlay */}
        {isFavorite && (
          <div className="absolute top-2 right-2 z-20 animate-in zoom-in duration-300">
            <div className="bg-red-600 p-1.5 rounded-full shadow-lg border border-red-500/50">
              <Heart size={10} fill="white" className="text-white" />
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="mt-4 flex flex-col space-y-1">
        <div className="flex items-end justify-between">
          <span className="text-4xl font-black text-white italic leading-none transition-all group-hover:translate-x-1 group-hover:text-red-500 duration-300">
            {item.rank}
          </span>
          <div className="flex items-center space-x-1 text-orange-500 transition-all duration-300 group-hover:scale-110">
            <Flame size={14} fill="currentColor" />
            <span className="text-sm font-bold">{item.views.toLocaleString()}</span>
          </div>
        </div>

        {/* Title */}
        <div className="relative group/tooltip-title">
          <h3 className="text-lg font-bold text-white line-clamp-1 group-hover:text-red-500 transition-colors duration-300">
            {item.title}
          </h3>
          <div className="absolute bottom-full left-0 mb-2 opacity-0 group-hover/tooltip-title:opacity-100 transition-all duration-200 translate-y-1 group-hover/tooltip-title:translate-y-0 z-50 pointer-events-none w-max max-w-[240px]">
            <div className="bg-[#1f1f1f] text-white text-[11px] py-2 px-3 rounded-lg border border-gray-700 shadow-2xl font-bold">
              {item.title}
              <div className="absolute top-full left-4 -mt-1.5 border-[6px] border-transparent border-t-[#1f1f1f]" />
            </div>
          </div>
        </div>
        
        {/* Author */}
        <p className="text-sm text-gray-400 font-semibold truncate group-hover:text-gray-200 transition-colors duration-300">
          {item.author}
        </p>

        {/* Description */}
        <p className="text-xs text-gray-500 font-medium line-clamp-2 leading-relaxed mt-1 group-hover:text-gray-400 transition-colors duration-300">
          {item.description}
        </p>

        {/* Language & Status Badges */}
        <div className="flex flex-wrap gap-1.5 mt-3 transition-transform duration-300 group-hover:translate-y-[-2px]">
          {item.category === 'Completed' && (
            <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 uppercase tracking-tighter">
              Completed
            </span>
          )}
          {item.languages.map((lang) => (
            <span key={lang} className="text-[10px] font-black px-1.5 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-700 uppercase group-hover:border-red-500/30 group-hover:text-white transition-all">
              {lang}
            </span>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="mt-4 flex flex-col gap-2 transition-all duration-500 opacity-60 group-hover:opacity-100">
          {/* Read Now Button */}
          <button
            onClick={handleReadNow}
            disabled={isReading}
            className={`relative overflow-hidden w-full flex items-center justify-center gap-2 font-black uppercase text-[10px] tracking-[0.15em] py-2.5 rounded-lg transition-all transform border border-red-500/20 shadow-lg shadow-red-900/20 ${
              isReading 
                ? 'bg-red-800 text-white/70 cursor-not-allowed' 
                : 'bg-red-600 hover:bg-red-500 active:bg-red-700 text-white hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            {isReading && (
              <>
                <div className="absolute inset-0 bg-white/20 animate-sweep" />
                <div className="absolute inset-0 bg-red-400/10 animate-pulse" />
              </>
            )}
            <BookOpen size={14} strokeWidth={3} className={isReading ? 'animate-bounce' : ''} />
            <span className="relative z-10">{isReading ? 'Initializing...' : 'Read Now'}</span>
          </button>

          {/* Add to Favorites Button */}
          <button
            onClick={toggleFavorite}
            className={`w-full flex items-center justify-center gap-2 font-black uppercase text-[10px] tracking-[0.15em] py-2.5 rounded-lg transition-all border transform active:scale-95 ${
              isFavorite
                ? 'bg-red-600/10 border-red-500/40 text-red-500 hover:bg-red-600/20'
                : 'bg-transparent border-gray-800 text-gray-400 hover:text-white hover:border-gray-600 hover:bg-white/10'
            }`}
          >
            <Heart size={14} fill={isFavorite ? "currentColor" : "none"} className={isFavorite ? 'animate-in zoom-in duration-300' : ''} />
            <span>{isFavorite ? 'Favorited' : 'Add to Favorites'}</span>
          </button>

          {/* Share Button */}
          <div className="relative group/share-tooltip">
            <button
              onClick={handleShare}
              disabled={isSharing}
              className={`relative overflow-hidden w-full flex items-center justify-center gap-2 font-black uppercase text-[10px] tracking-[0.15em] py-2.5 rounded-lg transition-all border ${
                isSharing
                  ? 'bg-gray-800 text-white/50 border-gray-700 cursor-not-allowed'
                  : 'bg-transparent hover:bg-white/5 text-gray-400 hover:text-white border-gray-800 hover:border-gray-600'
              }`}
            >
              {isSharing && (
                <div className="absolute inset-0 flex items-center justify-center">
                   <div className="w-4 h-4 rounded-full bg-white/30 animate-expand-ring" />
                   <div className="w-4 h-4 rounded-full bg-white/20 animate-expand-ring delay-300" />
                </div>
              )}
              <Share2 size={14} strokeWidth={2} className={`relative z-10 ${isSharing ? 'animate-pulse' : ''}`} />
              <span className="relative z-10">{isSharing ? 'Syncing...' : 'Share'}</span>
            </button>
            
            {/* Share Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover/share-tooltip:opacity-100 transition-all duration-200 translate-y-1 group-hover/share-tooltip:translate-y-0 z-50 pointer-events-none w-max">
              <div className="bg-[#1f1f1f] text-white text-[11px] py-1.5 px-3 rounded-lg border border-gray-700 shadow-2xl font-bold whitespace-nowrap">
                Share this item
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1.5 border-[6px] border-transparent border-t-[#1f1f1f]" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RankingCard;
