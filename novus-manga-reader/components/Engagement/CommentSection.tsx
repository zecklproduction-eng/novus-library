
import React, { useState, useMemo } from 'react';
import { ThumbsUp, ThumbsDown, MessageSquare, Share2, Heart, ChevronDown, Check, Flag } from 'lucide-react';
import { Comment } from '../../types';

const MAX_COMMENT_LENGTH = 500;

type SortOption = 'newest' | 'oldest' | 'liked' | 'replied';

interface CommentItemProps {
  comment: Comment;
  isReply?: boolean;
  onAddReply: (parentId: string, text: string) => void;
}

const CommentItem: React.FC<CommentItemProps> = ({ comment, isReply, onAddReply }) => {
  const [isReplying, setIsReplying] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [isFavorited, setIsFavorited] = useState(false);
  
  // Local vote state
  const [likesCount, setLikesCount] = useState(comment.likes);
  const [userVote, setUserVote] = useState<'like' | 'dislike' | null>(null);

  const handleLike = () => {
    if (userVote === 'like') {
      setLikesCount(l => l - 1);
      setUserVote(null);
    } else {
      setLikesCount(l => l + (userVote === 'dislike' ? 2 : 1));
      setUserVote('like');
    }
  };

  const handleDislike = () => {
    if (userVote === 'dislike') {
      setUserVote(null);
    } else {
      if (userVote === 'like') setLikesCount(l => l - 1);
      setUserVote('dislike');
    }
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: 'Manga Comment',
        text: `Check out this comment by @${comment.author}: "${comment.text}"`,
        url: window.location.href,
      }).catch((error) => console.log('Error sharing', error));
    } else {
      alert(`Sharing comment by @${comment.author}: "${comment.text}"`);
    }
  };

  const handleReport = () => {
    alert(`Thank you for your feedback. Comment by @${comment.author} has been reported for review.`);
  };

  const submitReply = () => {
    if (!replyText.trim() || replyText.length > MAX_COMMENT_LENGTH) return;
    onAddReply(comment.id, replyText);
    setReplyText('');
    setIsReplying(false);
  };

  const toggleFavorite = () => {
    setIsFavorited(!isFavorited);
  };

  return (
    <div className={`flex gap-4 group ${isReply ? 'mt-4' : 'mt-6'}`}>
      <img src={comment.authorAvatar} className={`${isReply ? 'w-6 h-6' : 'w-10 h-10'} rounded-full shrink-0`} alt={comment.author} />
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-bold text-white hover:underline cursor-pointer">@{comment.author}</span>
          <span className="text-xs text-slate-500">{comment.timestamp}</span>
        </div>
        <p className="text-sm text-slate-300 mb-3 leading-relaxed">{comment.text}</p>
        
        <div className="flex items-center gap-4 text-slate-400 mb-2">
          <button 
            onClick={handleLike}
            className={`flex items-center gap-1 cursor-pointer transition-colors ${userVote === 'like' ? 'text-sky-400' : 'hover:text-white'}`}
          >
            <ThumbsUp size={14} fill={userVote === 'like' ? 'currentColor' : 'none'} />
            <span className="text-xs font-medium">{likesCount > 0 ? likesCount : ''}</span>
          </button>
          
          <button 
            onClick={handleDislike}
            className={`cursor-pointer transition-colors ${userVote === 'dislike' ? 'text-sky-400' : 'hover:text-white'}`}
          >
            <ThumbsDown size={14} fill={userVote === 'dislike' ? 'currentColor' : 'none'} />
          </button>

          <button 
            onClick={() => setIsReplying(!isReplying)}
            className="text-xs font-bold hover:text-white transition-colors"
          >
            Reply
          </button>
          
          <button 
            onClick={handleShare}
            className="text-xs font-bold hover:text-white transition-colors flex items-center gap-1"
          >
            <Share2 size={12} />
            Share
          </button>
          
          <button 
            onClick={toggleFavorite}
            className={`text-xs font-bold transition-colors flex items-center gap-1 ${isFavorited ? 'text-pink-500' : 'hover:text-white'}`}
          >
            <Heart size={12} fill={isFavorited ? 'currentColor' : 'none'} />
            {isFavorited ? 'Favorited' : 'Favorite'}
          </button>

          <button 
            onClick={handleReport}
            className="text-xs font-bold hover:text-red-400 transition-colors flex items-center gap-1"
          >
            <Flag size={12} />
            Report
          </button>
        </div>

        {isReplying && (
          <div className="flex gap-3 mt-4 mb-6">
            <img src="https://picsum.photos/seed/myuser/100/100" className="w-6 h-6 rounded-full shrink-0" alt="me" />
            <div className="flex-1">
              <div className="border-b border-slate-700 focus-within:border-white transition-colors mb-2">
                <input 
                  autoFocus
                  type="text" 
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Add a reply..." 
                  className="w-full bg-transparent border-none outline-none py-1 text-sm text-white placeholder:text-slate-500"
                  onKeyDown={(e) => e.key === 'Enter' && submitReply()}
                  maxLength={MAX_COMMENT_LENGTH}
                />
              </div>
              <div className="flex items-center justify-end gap-3">
                <span className={`text-[10px] font-medium ${replyText.length >= MAX_COMMENT_LENGTH ? 'text-red-500' : 'text-slate-500'}`}>
                  {replyText.length} / {MAX_COMMENT_LENGTH}
                </span>
                <button 
                  onClick={() => setIsReplying(false)}
                  className="px-3 py-1.5 text-xs font-bold text-white hover:bg-slate-800 rounded-full transition-colors"
                >
                  Cancel
                </button>
                <button 
                  disabled={!replyText.trim() || replyText.length > MAX_COMMENT_LENGTH}
                  onClick={submitReply}
                  className={`px-3 py-1.5 text-xs font-bold rounded-full transition-colors ${replyText.trim() && replyText.length <= MAX_COMMENT_LENGTH ? 'bg-sky-500 text-black hover:bg-sky-400' : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}
                >
                  Reply
                </button>
              </div>
            </div>
          </div>
        )}

        {comment.replies.length > 0 && (
          <div className="mt-2 border-l-2 border-slate-800 pl-4">
            {comment.replies.map(reply => (
              <CommentItem 
                key={reply.id} 
                comment={reply} 
                isReply 
                onAddReply={onAddReply}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export const CommentSection: React.FC<{ comments: Comment[] }> = ({ comments: initialComments }) => {
  const [localComments, setLocalComments] = useState<Comment[]>(initialComments);
  const [mainCommentText, setMainCommentText] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);

  const sortOptions: { value: SortOption; label: string }[] = [
    { value: 'newest', label: 'Newest' },
    { value: 'oldest', label: 'Oldest' },
    { value: 'liked', label: 'Most Liked' },
    { value: 'replied', label: 'Most Replied' },
  ];

  const sortedComments = useMemo(() => {
    return [...localComments].sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return b.id.localeCompare(a.id, undefined, { numeric: true, sensitivity: 'base' });
        case 'oldest':
          return a.id.localeCompare(b.id, undefined, { numeric: true, sensitivity: 'base' });
        case 'liked':
          return b.likes - a.likes;
        case 'replied':
          return b.replies.length - a.replies.length;
        default:
          return 0;
      }
    });
  }, [localComments, sortBy]);

  const addMainComment = () => {
    if (!mainCommentText.trim() || mainCommentText.length > MAX_COMMENT_LENGTH) return;
    const newComment: Comment = {
      id: Date.now().toString(),
      author: 'Reader_1',
      authorAvatar: 'https://picsum.photos/seed/myuser/100/100',
      text: mainCommentText,
      timestamp: 'Just now',
      likes: 0,
      replies: []
    };
    setLocalComments([newComment, ...localComments]);
    setMainCommentText('');
  };

  const handleAddReply = (parentId: string, text: string) => {
    const newReply: Comment = {
      id: Date.now().toString(),
      author: 'Reader_1',
      authorAvatar: 'https://picsum.photos/seed/myuser/100/100',
      text: text,
      timestamp: 'Just now',
      likes: 0,
      replies: []
    };

    const addReplyToNested = (list: Comment[]): Comment[] => {
      return list.map(c => {
        if (c.id === parentId) {
          return { ...c, replies: [...c.replies, newReply] };
        }
        if (c.replies.length > 0) {
          return { ...c, replies: addReplyToNested(c.replies) };
        }
        return c;
      });
    };

    setLocalComments(addReplyToNested(localComments));
  };

  return (
    <div className="mt-8 px-4">
      <div className="flex items-center gap-6 mb-8 relative">
        <h3 className="text-xl font-bold">{localComments.length} Comments</h3>
        
        <div className="relative">
          <button 
            onClick={() => setIsSortMenuOpen(!isSortMenuOpen)}
            className="flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-white transition-colors"
          >
            <MessageSquare size={18} />
            Sort by: <span className="text-white">{sortOptions.find(o => o.value === sortBy)?.label}</span>
            <ChevronDown size={14} className={`transition-transform ${isSortMenuOpen ? 'rotate-180' : ''}`} />
          </button>

          {isSortMenuOpen && (
            <>
              <div 
                className="fixed inset-0 z-20" 
                onClick={() => setIsSortMenuOpen(false)} 
              />
              <div className="absolute left-0 mt-2 w-48 bg-[#1e293b] border border-slate-700 rounded-xl shadow-2xl py-2 z-30 overflow-hidden ring-1 ring-white/5">
                {sortOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setSortBy(option.value);
                      setIsSortMenuOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-4 py-2 text-sm text-left transition-colors ${
                      sortBy === option.value ? 'bg-sky-500/10 text-sky-400' : 'text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    {option.label}
                    {sortBy === option.value && <Check size={14} />}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="flex gap-4 mb-8">
        <img src="https://picsum.photos/seed/myuser/100/100" className="w-10 h-10 rounded-full shrink-0" alt="me" />
        <div className="flex-1">
          <div className="border-b border-slate-700 focus-within:border-white transition-colors mb-2">
            <input 
              type="text" 
              value={mainCommentText}
              onChange={(e) => setMainCommentText(e.target.value)}
              placeholder="Add a comment..." 
              className="w-full bg-transparent border-none outline-none py-2 text-sm text-white placeholder:text-slate-500"
              onKeyDown={(e) => e.key === 'Enter' && addMainComment()}
              maxLength={MAX_COMMENT_LENGTH}
            />
          </div>
          {mainCommentText && (
            <div className="flex items-center justify-end gap-3">
              <span className={`text-[10px] font-medium ${mainCommentText.length >= MAX_COMMENT_LENGTH ? 'text-red-500' : 'text-slate-500'}`}>
                {mainCommentText.length} / {MAX_COMMENT_LENGTH}
              </span>
              <button 
                onClick={() => setMainCommentText('')}
                className="px-4 py-2 text-sm font-bold text-white hover:bg-slate-800 rounded-full transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={addMainComment}
                disabled={mainCommentText.length > MAX_COMMENT_LENGTH}
                className={`px-4 py-2 text-sm font-bold rounded-full transition-colors ${mainCommentText.length <= MAX_COMMENT_LENGTH ? 'bg-sky-500 text-black hover:bg-sky-400' : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}
              >
                Comment
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {sortedComments.map(comment => (
          <CommentItem 
            key={comment.id} 
            comment={comment} 
            onAddReply={handleAddReply}
          />
        ))}
      </div>
    </div>
  );
};
