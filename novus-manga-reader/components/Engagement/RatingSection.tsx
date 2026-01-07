
import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Share2, MoreHorizontal } from 'lucide-react';

export const RatingSection = () => {
  const [likes, setLikes] = useState(12400);
  const [userVote, setUserVote] = useState<'like' | 'dislike' | null>(null);

  const handleLike = () => {
    if (userVote === 'like') {
      setLikes(l => l - 1);
      setUserVote(null);
    } else {
      setLikes(l => l + (userVote === 'dislike' ? 2 : 1));
      setUserVote('like');
    }
  };

  const handleDislike = () => {
    if (userVote === 'dislike') {
      setUserVote(null);
    } else {
      if (userVote === 'like') setLikes(l => l - 1);
      setUserVote('dislike');
    }
  };

  return (
    <div className="flex items-center justify-between py-6 px-4 bg-slate-900/50 rounded-xl border border-slate-800">
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-bold">Chapter 1 Rating</h3>
        <p className="text-xs text-slate-500">How would you rate this chapter?</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center bg-slate-800 rounded-full h-10 overflow-hidden ring-1 ring-slate-700">
          <button 
            onClick={handleLike}
            className={`flex items-center gap-2 px-4 h-full hover:bg-slate-700 transition-colors ${userVote === 'like' ? 'text-sky-400' : 'text-white'}`}
          >
            <ThumbsUp size={18} />
            <span className="text-sm font-bold">{(likes / 1000).toFixed(1)}K</span>
          </button>
          <div className="w-px h-6 bg-slate-700" />
          <button 
            onClick={handleDislike}
            className={`flex items-center justify-center px-4 h-full hover:bg-slate-700 transition-colors ${userVote === 'dislike' ? 'text-sky-400' : 'text-white'}`}
          >
            <ThumbsDown size={18} />
          </button>
        </div>

        <button className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 px-4 h-10 rounded-full text-sm font-bold transition-colors ring-1 ring-slate-700">
          <Share2 size={18} />
          Share
        </button>

        <button className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400">
          <MoreHorizontal size={20} />
        </button>
      </div>
    </div>
  );
};
