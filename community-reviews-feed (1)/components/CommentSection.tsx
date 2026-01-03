
import React, { useState } from 'react';
import { ReviewComment, User } from '../types';

interface CommentSectionProps {
  comments: ReviewComment[];
  currentUser: User;
  onAddComment: (text: string) => Promise<void>;
  onAddReply: (parentId: string, text: string) => Promise<void>;
  onEditComment: (commentId: string, text: string) => Promise<void>;
  onDeleteComment: (commentId: string) => Promise<void>;
  onLikeComment: (commentId: string) => Promise<void>;
  onProfileClick: (username: string) => void;
}

const LoadingSpinner = ({ size = 'sm', className = '' }: { size?: 'sm' | 'md', className?: string }) => (
  <svg 
    className={`animate-spin ${size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} ${className}`} 
    fill="none" 
    viewBox="0 0 24 24"
    aria-hidden="true"
  >
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
);

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

const CommentItem: React.FC<{
  comment: ReviewComment;
  currentUser: User;
  onAddReply: (parentId: string, text: string) => Promise<void>;
  onEditComment: (commentId: string, text: string) => Promise<void>;
  onDeleteComment: (commentId: string) => Promise<void>;
  onLikeComment: (commentId: string) => Promise<void>;
  onProfileClick: (username: string) => void;
  depth?: number;
}> = ({ 
  comment, 
  currentUser, 
  onAddReply, 
  onEditComment, 
  onDeleteComment, 
  onLikeComment, 
  onProfileClick, 
  depth = 0 
}) => {
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [editText, setEditText] = useState(comment.body);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLiking, setIsLiking] = useState(false);

  const isAuthor = comment.userId === currentUser.id;
  const isAnyActionInProgress = isSubmitting || isLiking;

  const handleReplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onAddReply(comment.id, replyText);
      setReplyText('');
      setShowReplyInput(false);
    } catch (error) {
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editText.trim() || isSubmitting || editText === comment.body) {
      setIsEditing(false);
      return;
    }

    setIsSubmitting(true);
    try {
      await onEditComment(comment.id, editText);
      setIsEditing(false);
    } catch (error) {
      console.error(error);
      setEditText(comment.body);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete this comment?")) return;
    setIsSubmitting(true);
    try {
      await onDeleteComment(comment.id);
    } catch (error) {
      console.error(error);
      setIsSubmitting(false);
    }
  };

  const handleLike = async () => {
    if (isLiking) return;
    setIsLiking(true);
    try {
      await onLikeComment(comment.id);
    } finally {
      setIsLiking(false);
    }
  };

  return (
    <div className={`flex flex-col gap-3 group/comment animate-in fade-in duration-300 ${depth > 0 ? 'ml-6 border-l-2 border-slate-100 pl-4' : ''}`}>
      <div className="flex gap-3">
        <button 
          onClick={() => onProfileClick(comment.user.username)}
          className="flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-full"
          aria-label={`View ${comment.user.username}'s profile`}
          disabled={isAnyActionInProgress}
        >
          <img 
            src={comment.user.avatarUrl} 
            alt="" 
            className={`${depth > 0 ? 'w-6 h-6' : 'w-8 h-8'} rounded-full border border-slate-100 shadow-sm hover:ring-2 hover:ring-indigo-500 transition-all ${isAnyActionInProgress ? 'opacity-50' : ''}`}
          />
        </button>
        <div className="flex-grow">
          <div className={`bg-slate-50 p-3 rounded-2xl text-left hover:bg-slate-100/80 transition-colors ${isAnyActionInProgress ? 'opacity-80' : ''}`}>
            <div className="flex items-center justify-between mb-1">
              <button 
                onClick={() => onProfileClick(comment.user.username)}
                className="text-xs font-bold text-slate-900 hover:text-indigo-600 transition-colors focus:outline-none focus:underline"
                disabled={isAnyActionInProgress}
              >
                {comment.user.username}
              </button>
              <span className="text-[10px] text-slate-400 font-medium">
                {formatTimeAgo(comment.createdAt)}
              </span>
            </div>
            
            {isEditing ? (
              <form onSubmit={handleEditSubmit} className="space-y-2 mt-1">
                <textarea
                  className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:outline-none focus:border-transparent transition-all shadow-sm resize-none"
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  autoFocus
                  rows={3}
                  disabled={isSubmitting}
                />
                <div className="flex justify-end space-x-3">
                  <button 
                    type="button" 
                    onClick={() => {
                      setIsEditing(false);
                      setEditText(comment.body);
                    }}
                    className="text-[10px] font-bold text-slate-400 hover:text-slate-600 transition-colors"
                    disabled={isSubmitting}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    disabled={isSubmitting || !editText.trim()}
                    className="px-3 py-1 bg-indigo-600 text-white rounded-lg text-[10px] font-bold hover:bg-indigo-700 disabled:opacity-50 disabled:bg-slate-300 transition-all shadow-sm flex items-center space-x-1"
                  >
                    {isSubmitting && <LoadingSpinner />}
                    <span>{isSubmitting ? 'Saving...' : 'Save'}</span>
                  </button>
                </div>
              </form>
            ) : (
              <p className="text-xs text-slate-600 leading-relaxed">
                {comment.body}
              </p>
            )}
          </div>
          
          <div className="flex items-center space-x-4 ml-2 mt-1">
            <button 
              onClick={handleLike}
              disabled={isAnyActionInProgress}
              aria-pressed={comment.isLiked}
              className={`flex items-center space-x-1 text-[10px] font-bold transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/10 rounded-sm px-1 -mx-1 ${comment.isLiked ? 'text-indigo-600' : 'text-slate-400 hover:text-indigo-600'} disabled:opacity-40`}
            >
              {isLiking ? (
                <LoadingSpinner />
              ) : (
                <svg className={`w-3 h-3 ${comment.isLiked ? 'fill-current' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              )}
              <span>{comment.likesCount > 0 ? comment.likesCount : 'Like'}</span>
            </button>
            <button 
              onClick={() => setShowReplyInput(!showReplyInput)}
              className="text-[10px] font-bold text-slate-400 hover:text-indigo-600 transition-colors disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-indigo-500/10 rounded-sm px-1 -mx-1"
              disabled={isAnyActionInProgress}
            >
              Reply
            </button>
            {isAuthor && !isEditing && (
              <>
                <button 
                  onClick={() => setIsEditing(true)}
                  className="text-[10px] font-bold text-slate-400 hover:text-indigo-600 transition-colors disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-indigo-500/10 rounded-sm px-1 -mx-1"
                  disabled={isAnyActionInProgress}
                >
                  Edit
                </button>
                <button 
                  onClick={handleDelete}
                  className="text-[10px] font-bold text-slate-400 hover:text-red-500 transition-colors disabled:opacity-40 flex items-center space-x-1 focus:outline-none focus:ring-2 focus:ring-red-500/10 rounded-sm px-1 -mx-1"
                  disabled={isAnyActionInProgress}
                >
                  {isSubmitting && <LoadingSpinner className="text-red-500" />}
                  <span>Delete</span>
                </button>
              </>
            )}
          </div>

          {showReplyInput && (
            <form onSubmit={handleReplySubmit} className="mt-3 flex gap-2 items-start animate-in fade-in slide-in-from-top-1 duration-200">
              <img 
                src={currentUser.avatarUrl} 
                className="w-6 h-6 rounded-full hidden sm:block border border-slate-100" 
                alt="" 
              />
              <div className="flex-grow relative">
                <input 
                  autoFocus
                  placeholder={`Reply to ${comment.user.username}...`}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all pr-14"
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  disabled={isSubmitting}
                />
                <button 
                  type="submit" 
                  disabled={!replyText.trim() || isSubmitting}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-bold text-indigo-600 disabled:text-slate-300 flex items-center space-x-1"
                >
                  {isSubmitting ? <LoadingSpinner /> : 'Post'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
      
      {comment.replies && comment.replies.length > 0 && (
        <div className="space-y-3">
          {comment.replies.map(reply => (
            <CommentItem 
              key={reply.id} 
              comment={reply} 
              currentUser={currentUser} 
              onAddReply={onAddReply} 
              onEditComment={onEditComment}
              onDeleteComment={onDeleteComment}
              onLikeComment={onLikeComment}
              onProfileClick={onProfileClick}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const CommentSection: React.FC<CommentSectionProps> = ({ 
  comments, 
  currentUser, 
  onAddComment, 
  onAddReply,
  onEditComment,
  onDeleteComment,
  onLikeComment,
  onProfileClick 
}) => {
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onAddComment(newComment);
      setNewComment('');
    } catch (error) {
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mt-4 pt-4 border-t border-slate-100 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="space-y-4 mb-6">
        {comments.length > 0 ? (
          comments.map((comment) => (
            <CommentItem 
              key={comment.id} 
              comment={comment} 
              currentUser={currentUser} 
              onAddReply={onAddReply} 
              onEditComment={onEditComment}
              onDeleteComment={onDeleteComment}
              onLikeComment={onLikeComment}
              onProfileClick={onProfileClick}
            />
          ))
        ) : (
          <div className="flex flex-col items-center py-4 text-slate-400">
            <svg className="w-8 h-8 mb-2 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-xs italic">No comments yet. Start the conversation!</p>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3 items-start">
        <img 
          src={currentUser.avatarUrl} 
          alt="" 
          className="w-8 h-8 rounded-full border border-slate-100 shadow-sm hidden sm:block"
        />
        <div className="flex-grow relative">
          <textarea 
            placeholder="Write a comment..."
            rows={1}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all resize-none min-h-[44px]"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            disabled={isSubmitting}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <div className="absolute right-2 bottom-2 flex items-center space-x-2">
            {isSubmitting && <LoadingSpinner size="md" className="text-indigo-600" />}
            
            {newComment.trim() && (
              <button 
                type="submit"
                disabled={isSubmitting}
                className="px-3 py-1 bg-indigo-600 text-white rounded-lg text-[10px] font-bold hover:bg-indigo-700 transition-all animate-in fade-in zoom-in-90 duration-200 shadow-sm disabled:opacity-50"
              >
                {isSubmitting ? 'Posting...' : 'Post Comment'}
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
};

export default CommentSection;
