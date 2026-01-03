
import React, { useState, useEffect } from 'react';
import { Review, User, MediaStatus } from '../types';
import StarRating from './StarRating';
import CommentSection from './CommentSection';
import ReportModal from './ReportModal';

interface ReviewCardProps {
  review: Review;
  currentUser: User;
  hideSpoilers: boolean;
  onLike: (id: string) => void;
  onReport: (id: string, reason: string, details: string) => Promise<void>;
  onEditReview: (reviewId: string, updates: Partial<Review>) => Promise<void>;
  onAddComment: (reviewId: string, comment: string) => Promise<void>;
  onAddReply: (reviewId: string, parentId: string, comment: string) => Promise<void>;
  onEditComment: (reviewId: string, commentId: string, text: string) => Promise<void>;
  onDeleteComment: (reviewId: string, commentId: string) => Promise<void>;
  // Fix: changed onLikeComment type to Promise<void>
  onLikeComment: (reviewId: string, commentId: string) => Promise<void>;
  onProfileClick: (username: string) => void;
}

const getTagColor = (tag: string) => {
  const colors: Record<string, string> = {
    'Action': 'bg-red-50 text-red-600 border-red-100',
    'Adventure': 'bg-orange-50 text-orange-600 border-orange-100',
    'Fantasy': 'bg-purple-50 text-purple-600 border-purple-100',
    'Sci-Fi': 'bg-blue-50 text-blue-600 border-blue-100',
    'Drama': 'bg-pink-50 text-pink-600 border-pink-100',
    'Supernatural': 'bg-indigo-50 text-indigo-600 border-indigo-100',
    'Dark': 'bg-slate-900 text-slate-100 border-slate-700',
    'New Release': 'bg-emerald-50 text-emerald-600 border-emerald-100',
    'Literary': 'bg-amber-50 text-amber-600 border-amber-100',
    'Space': 'bg-cyan-50 text-cyan-600 border-cyan-100',
    'General': 'bg-slate-50 text-slate-500 border-slate-200',
  };
  return colors[tag] || 'bg-slate-50 text-slate-500 border-slate-200';
};

const getSentimentEmoji = (rating: number) => {
  if (rating >= 4.5) return { emoji: '🤩', label: 'Exceptional' };
  if (rating >= 4.0) return { emoji: '😊', label: 'Great' };
  if (rating >= 3.0) return { emoji: '😐', label: 'Average' };
  if (rating >= 2.0) return { emoji: '🙁', label: 'Poor' };
  return { emoji: '😡', label: 'Terrible' };
};

const ReviewCard: React.FC<ReviewCardProps> = ({ 
  review, 
  currentUser,
  hideSpoilers, 
  onLike, 
  onReport,
  onEditReview,
  onAddComment,
  onAddReply,
  onEditComment,
  onDeleteComment,
  onLikeComment,
  onProfileClick
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showSpoilerLocally, setShowSpoilerLocally] = useState(!hideSpoilers);
  const [showComments, setShowComments] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  
  const [isEditing, setIsEditing] = useState(false);
  const [editBody, setEditBody] = useState(review.body);
  const [editRating, setEditRating] = useState(review.rating);
  const [editStatus, setEditStatus] = useState(review.status);
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);

  const isAuthor = review.userId === currentUser.id;
  const sentiment = getSentimentEmoji(review.rating);

  // Reset local spoiler visibility when global toggle changes
  useEffect(() => {
    setShowSpoilerLocally(!hideSpoilers);
  }, [hideSpoilers]);

  const formatTimeAgo = (dateStr: string) => {
    const now = new Date();
    const then = new Date(dateStr);
    const diffInMs = now.getTime() - then.getTime();
    const diffInMins = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMins / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInMins < 1) return 'Just now';
    if (diffInMins < 60) return `${diffInMins}m ago`;
    if (diffInHours < 24) return `${diffInHours}h ago`;
    return `${diffInDays}d ago`;
  };

  const handleShare = () => {
    navigator.clipboard.writeText(`https://mediahub.io/review/${review.id}`);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  // Determine if the safety shield (full blur) should be active
  const isSafetyShieldActive = review.hasSpoilers && hideSpoilers && !showSpoilerLocally;

  const handleProfileLink = (e: React.MouseEvent) => {
    e.preventDefault();
    onProfileClick(review.user.username);
  };

  const handleSaveEdit = async () => {
    if (!editBody.trim() || isSubmittingEdit) return;
    setIsSubmittingEdit(true);
    try {
      await onEditReview(review.id, {
        body: editBody,
        rating: editRating,
        status: editStatus,
        bodyPlain: editBody.replace(/<[^>]*>?/gm, '')
      });
      setIsEditing(false);
    } catch (error) {
      alert("Failed to save changes.");
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  const handleReportSubmit = async (reason: string, details: string) => {
    await onReport(review.id, reason, details);
  };

  const toggleSpoilerReveal = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.classList.contains('spoiler')) {
      target.classList.toggle('revealed');
      return;
    }
    
    if (isSafetyShieldActive) {
      setShowSpoilerLocally(true);
    }
  };

  return (
    <article className={`bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden hover:border-indigo-400 hover:shadow-xl transition-all duration-300 group/card ${showSpoilerLocally ? 'spoilers-revealed' : ''}`} aria-labelledby={`review-title-${review.id}`}>
      <div className="p-6 md:p-8 flex flex-col md:flex-row gap-8 relative">
        
        {isSafetyShieldActive && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white/40 backdrop-blur-xl animate-in fade-in duration-500">
            <div className="bg-white/90 p-8 rounded-[2.5rem] shadow-2xl border border-white/50 text-center max-w-sm mx-auto transform transition-transform group-hover/card:scale-105">
              <div className="w-16 h-16 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-inner">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h4 className="text-lg font-black text-slate-900 mb-2 uppercase tracking-tighter">Spoiler Warning</h4>
              <p className="text-sm text-slate-500 font-medium mb-6">This review contains significant plot details. Do you want to see them?</p>
              <button 
                onClick={() => setShowSpoilerLocally(true)}
                className="w-full py-3 bg-indigo-600 text-white rounded-2xl text-xs font-black uppercase tracking-widest hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-500/20 outline-none transition-all shadow-lg shadow-indigo-100"
              >
                Reveal Review
              </button>
            </div>
          </div>
        )}

        <div className={`flex flex-col md:flex-row gap-8 w-full ${isSafetyShieldActive ? 'spoiler-blur-container' : ''}`}>
          <div className="flex-shrink-0 w-28 md:w-36 mx-auto md:mx-0">
            <div className="relative aspect-[2/3] rounded-2xl overflow-hidden bg-slate-100 shadow-md border border-slate-100">
              <img 
                src={review.media.coverUrl} 
                alt={`${review.media.title} cover`}
                className="w-full h-full object-cover transition-transform duration-700 group-hover/card:scale-110"
              />
              <div className="absolute top-2.5 left-2.5 bg-slate-900/90 backdrop-blur-md text-white text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase tracking-widest shadow-lg">
                {review.media.type}
              </div>
            </div>
          </div>

          <div className="flex-grow flex flex-col min-w-0">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div className="flex items-center space-x-3.5">
                <a 
                  href={`/profile/${review.user.username}`}
                  onClick={handleProfileLink}
                  aria-label={`View ${review.user.username}'s profile`}
                  title={`View ${review.user.username}'s profile`}
                  className="relative flex-shrink-0 focus:outline-none focus:ring-4 focus:ring-indigo-500/20 rounded-full group/avatar overflow-visible block"
                >
                  <img 
                    src={review.user.avatarUrl} 
                    alt="" 
                    className="w-12 h-12 rounded-full border-2 border-white shadow-lg group-hover/avatar:ring-4 group-hover/avatar:ring-indigo-100 transition-all duration-300"
                  />
                  <div className="absolute -bottom-1 -right-1 bg-indigo-600 text-white p-0.5 rounded-full border-2 border-white shadow-sm z-10" aria-hidden="true">
                    <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={4} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                </a>
                <div className="min-w-0">
                  <h4 className="text-sm font-bold text-slate-900 truncate flex items-center gap-2">
                    <a 
                      href={`/profile/${review.user.username}`}
                      onClick={handleProfileLink} 
                      className="text-slate-900 hover:text-indigo-600 hover:underline decoration-2 underline-offset-4 transition-all font-black focus:outline-none focus:text-indigo-700 text-left inline-block rounded-sm focus:ring-2 focus:ring-indigo-500/10 px-1 -mx-1"
                      title={`View ${review.user.username}'s profile`}
                      aria-label={`${review.user.username}, click to view profile`}
                    >
                      {review.user.username}
                    </a>
                    <span className="text-slate-400 font-medium text-xs">shared a review</span>
                  </h4>
                  <p className="text-[11px] text-slate-400 font-black uppercase tracking-widest mt-0.5">
                    <time dateTime={review.createdAt}>{formatTimeAgo(review.createdAt)}</time>
                  </p>
                </div>
              </div>
              
              <div className="flex flex-col items-end">
                {isEditing ? (
                  <div className="flex flex-col items-end gap-3 animate-in fade-in slide-in-from-right-3">
                    <StarRating rating={editRating} editable onChange={setEditRating} size="sm" />
                    <select 
                      aria-label="Media engagement status"
                      className="text-[11px] font-black bg-slate-50 border border-slate-200 rounded-full px-4 py-1.5 text-slate-900 focus:ring-4 focus:ring-indigo-500/10 outline-none transition-all cursor-pointer"
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value as MediaStatus)}
                    >
                      <option value={MediaStatus.READING}>Reading</option>
                      <option value={MediaStatus.COMPLETED}>Completed</option>
                      <option value={MediaStatus.ON_HOLD}>On-Hold</option>
                    </select>
                  </div>
                ) : (
                  <div className="text-right flex items-center gap-3">
                    <div 
                      className="text-2xl" 
                      role="img" 
                      aria-label={`Community sentiment: ${sentiment.label}`}
                    >
                      {sentiment.emoji}
                    </div>
                    <div>
                      <StarRating rating={review.rating} size="sm" />
                      <div className="mt-1 flex justify-end">
                        <span className={`text-[10px] font-black px-3 py-1 rounded-full border uppercase tracking-widest shadow-sm ${
                          review.status === MediaStatus.COMPLETED ? 'bg-emerald-50 text-emerald-600 border-emerald-100' :
                          review.status === MediaStatus.READING ? 'bg-blue-50 text-blue-600 border-blue-100' :
                          'bg-orange-50 text-orange-600 border-orange-100'
                        }`}>
                          {review.status}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <h3 id={`review-title-${review.id}`} className="text-2xl font-black text-slate-900 mb-3 tracking-tighter leading-tight">
              <a href={`#media/${review.media.slug}`} className="hover:text-indigo-600 transition-colors focus:outline-none focus:text-indigo-600 underline-offset-8 decoration-2 hover:underline">
                {review.media.title}
              </a>
            </h3>

            {!isEditing && review.media.tags && review.media.tags.length > 0 && (
              <div className="flex flex-wrap gap-2.5 mb-5" aria-label="Media tags">
                {review.media.tags.map(tag => (
                  <span 
                    key={tag} 
                    className={`px-4 py-1.5 border rounded-full text-[10px] font-black uppercase tracking-widest transition-all hover:scale-105 hover:shadow-md cursor-default ${getTagColor(tag)}`}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="relative mb-8">
              {isEditing ? (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-4">
                  <label htmlFor={`edit-body-${review.id}`} className="sr-only">Edit review text</label>
                  <textarea 
                    id={`edit-body-${review.id}`}
                    className="w-full bg-slate-50 border border-slate-200 rounded-3xl p-6 text-sm text-slate-900 font-medium leading-relaxed focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:bg-white transition-all min-h-[160px] shadow-inner"
                    value={editBody}
                    onChange={(e) => setEditBody(e.target.value)}
                    disabled={isSubmittingEdit}
                  />
                  <div className="flex justify-end space-x-4">
                    <button onClick={() => setIsEditing(false)} className="text-xs font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest transition-colors focus:ring-2 focus:ring-slate-100 rounded-full px-2">
                      Discard Changes
                    </button>
                    <button onClick={handleSaveEdit} disabled={isSubmittingEdit || !editBody.trim()} className="px-7 py-2.5 bg-indigo-600 text-white rounded-full text-xs font-black hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-xl shadow-indigo-100 uppercase tracking-widest focus:ring-4 focus:ring-indigo-500/20 outline-none">
                      {isSubmittingEdit ? 'Saving...' : 'Update Review'}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div 
                    className={`text-slate-600 text-base leading-relaxed whitespace-pre-wrap ${!isExpanded ? 'line-clamp-3' : ''}`}
                    dangerouslySetInnerHTML={{ __html: review.body }}
                    onClick={toggleSpoilerReveal}
                  />
                  
                  {!isExpanded && (
                    <button 
                      onClick={() => setIsExpanded(true)} 
                      aria-expanded="false"
                      className="text-indigo-600 text-[11px] font-black mt-4 hover:text-indigo-800 flex items-center transition-all uppercase tracking-[0.15em] hover:gap-2 group/more focus:outline-none focus:ring-2 focus:ring-indigo-500/10 rounded-lg px-2 -ml-2"
                    >
                      Continue Reading
                      <svg className="w-3 h-3 ml-2 group-hover/more:translate-y-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                         <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  )}
                  
                  {review.hasSpoilers && showSpoilerLocally && (
                    <div className="mt-4 flex items-center gap-2">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Spoilers Revealed</span>
                      <button 
                        onClick={() => setShowSpoilerLocally(false)}
                        className="text-[9px] font-black text-indigo-600 hover:text-indigo-800 uppercase underline focus:ring-2 focus:ring-indigo-500/10 rounded-sm"
                      >
                        Hide Again
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="mt-auto pt-6 border-t border-slate-100 flex items-center justify-between">
              <div className="flex items-center space-x-8">
                <button 
                  onClick={() => onLike(review.id)} 
                  aria-pressed={review.isLiked}
                  aria-label={review.isLiked ? "Remove helpful vote" : "Mark as helpful review"}
                  className={`relative flex items-center space-x-2.5 text-[11px] font-black uppercase tracking-widest transition-all focus:outline-none focus:ring-4 focus:ring-indigo-500/10 rounded-full pr-4 active:scale-95 group/like ${review.isLiked ? 'text-indigo-600' : 'text-slate-400 hover:text-slate-800'}`}
                >
                  <div className="relative p-2 rounded-full flex items-center justify-center">
                    {review.isLiked && (
                      <div 
                        key={`shockwave-${review.id}`} 
                        className="absolute inset-0 bg-indigo-500/20 rounded-full animate-shockwave pointer-events-none" 
                      />
                    )}
                    <svg 
                      key={`heart-${review.isLiked}`}
                      className={`w-5 h-5 relative z-10 transition-all duration-300 ${review.isLiked ? 'fill-current animate-like-pop' : 'group-hover/like:scale-110'}`} 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                  </div>
                  <div className="flex items-center overflow-hidden h-4">
                    <span 
                      key={`count-${review.likesCount}`} 
                      className="animate-number-jump inline-block font-black"
                    >
                      {review.likesCount}
                    </span>
                    <span className="hidden sm:inline ml-1.5 whitespace-nowrap">Found Helpful</span>
                  </div>
                </button>
                
                <button 
                  onClick={() => setShowComments(!showComments)} 
                  aria-expanded={showComments}
                  aria-controls={`comments-section-${review.id}`}
                  className={`flex items-center space-x-2.5 text-[11px] font-black uppercase tracking-widest transition-all focus:outline-none focus:ring-4 focus:ring-indigo-500/10 rounded-full pr-4 ${showComments ? 'text-indigo-600' : 'text-slate-400 hover:text-slate-800'}`}
                >
                  <div className={`p-2 rounded-full transition-colors ${showComments ? 'bg-indigo-50' : 'bg-transparent'}`}>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.827-1.213L3 20l1.391-3.997A10.659 10.659 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <span>{review.comments.length} <span className="hidden sm:inline">Comments</span></span>
                </button>

                <button 
                  onClick={handleShare} 
                  aria-label="Share review link"
                  className={`flex items-center space-x-2.5 text-[11px] font-black uppercase tracking-widest transition-all focus:outline-none focus:ring-4 focus:ring-indigo-500/10 rounded-full pr-4 ${copySuccess ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-800'}`}
                >
                  <div className={`p-2 rounded-full transition-colors ${copySuccess ? 'bg-emerald-50' : 'bg-transparent'}`}>
                    {copySuccess ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                      </svg>
                    )}
                  </div>
                  <span>{copySuccess ? 'Copied!' : <span className="hidden sm:inline">Share</span>}</span>
                </button>
              </div>
              
              <div className="flex items-center space-x-2">
                {isAuthor && !isEditing && (
                  <button 
                    onClick={() => setIsEditing(true)}
                    aria-label="Edit your review"
                    className="p-2.5 rounded-full text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all hover:rotate-12"
                    title="Edit Review"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                )}
                <button 
                  onClick={() => setIsReportModalOpen(true)}
                  aria-label="Report review for policy violation"
                  className="p-2.5 rounded-full text-slate-400 hover:text-red-600 hover:bg-red-50 focus:outline-none focus:ring-4 focus:ring-red-500/10 transition-all hover:scale-110"
                  title="Report Content"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </button>
              </div>
            </div>

            {showComments && (
              <div 
                id={`comments-section-${review.id}`}
                className="animate-in slide-in-from-top-6 duration-500"
              >
                <CommentSection 
                  comments={review.comments}
                  currentUser={currentUser}
                  onAddComment={(text) => onAddComment(review.id, text)}
                  onAddReply={(parentId, text) => onAddReply(review.id, parentId, text)}
                  onEditComment={(commentId, text) => onEditComment(review.id, commentId, text)}
                  onDeleteComment={(commentId) => onDeleteComment(review.id, commentId)}
                  onLikeComment={(commentId) => onLikeComment(review.id, commentId)}
                  onProfileClick={onProfileClick}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      <ReportModal 
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onSubmit={handleReportSubmit}
        targetTitle={review.media.title}
      />
    </article>
  );
};

export default ReviewCard;
