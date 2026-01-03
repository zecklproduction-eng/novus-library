
import React, { useState, useMemo } from 'react';
import { User, Review } from '../types';
import ReviewCard from './ReviewCard';

interface UserProfileProps {
  user: User;
  allReviews: Review[];
  onBack: () => void;
  hideSpoilers: boolean;
  onLike: (id: string) => void;
  // Fix: updated onReport signature to match ReviewCard and App handleReport
  onReport: (id: string, reason: string, details: string) => Promise<void>;
  // Added onEditReview prop to match ReviewCard requirements
  onEditReview: (reviewId: string, updates: Partial<Review>) => Promise<void>;
  onAddComment: (reviewId: string, comment: string) => Promise<void>;
  onAddReply: (reviewId: string, parentId: string, comment: string) => Promise<void>;
  onEditComment: (reviewId: string, commentId: string, text: string) => Promise<void>;
  onDeleteComment: (reviewId: string, commentId: string) => Promise<void>;
  // Fix: changed onLikeComment type to Promise<void>
  onLikeComment: (reviewId: string, commentId: string) => Promise<void>;
  onProfileClick: (username: string) => void;
}

type TabType = 'reviews' | 'comments' | 'likes';

const UserProfile: React.FC<UserProfileProps> = ({ 
  user, 
  allReviews, 
  onBack, 
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
  const [activeTab, setActiveTab] = useState<TabType>('reviews');

  const userReviews = useMemo(() => 
    allReviews.filter(r => r.user.username === user.username), 
    [allReviews, user.username]
  );

  const userComments = useMemo(() => {
    const comments: any[] = [];
    allReviews.forEach(r => {
      r.comments.forEach(c => {
        if (c.user.username === user.username) {
          comments.push({ ...c, media: r.media, reviewId: r.id });
        }
      });
    });
    return comments;
  }, [allReviews, user.username]);

  const userLikedReviews = useMemo(() => 
    allReviews.filter(r => r.isLiked), 
    [allReviews]
  );

  const tabs: { id: TabType; label: string; count: number }[] = [
    { id: 'reviews', label: 'Reviews', count: userReviews.length },
    { id: 'comments', label: 'Comments', count: userComments.length },
    { id: 'likes', label: 'Likes', count: userLikedReviews.length },
  ];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <button 
        onClick={onBack}
        className="mb-6 flex items-center text-sm font-bold text-slate-500 hover:text-indigo-600 transition-colors group focus:outline-none"
      >
        <svg className="w-4 h-4 mr-2 transform group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Feed
      </button>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 mb-8">
        <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
          <div className="relative">
            <img 
              src={user.avatarUrl} 
              alt={user.username} 
              className="w-32 h-32 rounded-full border-4 border-white shadow-md"
            />
            <div className="absolute bottom-1 right-1 w-6 h-6 bg-green-500 border-4 border-white rounded-full"></div>
          </div>
          
          <div className="flex-grow text-center md:text-left">
            <div className="flex flex-col md:flex-row md:items-center gap-4 mb-4">
              <h2 className="text-3xl font-extrabold text-slate-900">{user.username}</h2>
              <div className="flex gap-2 justify-center md:justify-start">
                <button className="px-6 py-2 bg-indigo-600 text-white text-sm font-bold rounded-lg hover:bg-indigo-700 transition-all shadow-sm">
                  Follow
                </button>
              </div>
            </div>
            
            <div className="flex justify-center md:justify-start gap-6 mb-6">
              <div className="text-center md:text-left">
                <span className="block text-xl font-bold text-slate-900">{userReviews.length}</span>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider text-[10px]">Reviews</span>
              </div>
              <div className="text-center md:text-left">
                <span className="block text-xl font-bold text-slate-900">1.2k</span>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider text-[10px]">Followers</span>
              </div>
              <div className="text-center md:text-left">
                <span className="block text-xl font-bold text-slate-900">450</span>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider text-[10px]">Following</span>
              </div>
            </div>

            <p className="text-slate-600 text-sm leading-relaxed max-w-2xl">
              Avid reader and anime enthusiast. I love deep world-building and complex characters. 
              Always looking for new recommendations in the Seinen and Fantasy genres!
            </p>
          </div>
        </div>
      </div>

      <div className="flex border-b border-slate-200 mb-8 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center space-x-2 px-6 py-4 text-sm font-bold border-b-2 transition-all whitespace-nowrap focus:outline-none ${
              activeTab === tab.id
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <span>{tab.label}</span>
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
              activeTab === tab.id ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-500'
            }`}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      <div className="space-y-6">
        {activeTab === 'reviews' && (
          userReviews.length > 0 ? (
            <div className="space-y-6">
              {userReviews.map(review => (
                <ReviewCard 
                  key={review.id} 
                  review={review} 
                  currentUser={user}
                  hideSpoilers={hideSpoilers}
                  onLike={onLike}
                  onReport={onReport}
                  // Passed onEditReview to ReviewCard
                  onEditReview={onEditReview}
                  onAddComment={onAddComment}
                  onAddReply={onAddReply}
                  onEditComment={onEditComment}
                  onDeleteComment={onDeleteComment}
                  onLikeComment={onLikeComment}
                  onProfileClick={onProfileClick}
                />
              ))}
            </div>
          ) : (
            <EmptyState message="This user hasn't posted any reviews yet." />
          )
        )}

        {activeTab === 'comments' && (
          userComments.length > 0 ? (
            <div className="space-y-4">
              {userComments.map(comment => (
                <div key={comment.id} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:border-indigo-100 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Commented on</span>
                      <a href={`#media/${comment.media.slug}`} className="text-xs font-bold text-indigo-600 hover:underline">
                        {comment.media.title}
                      </a>
                    </div>
                    <span className="text-[10px] text-slate-400 font-medium">
                      {new Date(comment.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border-l-4 border-indigo-400">
                    "{comment.body}"
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No comments found for this user." />
          )
        )}

        {activeTab === 'likes' && (
          userLikedReviews.length > 0 ? (
            <div className="space-y-6">
              {userLikedReviews.map(review => (
                <ReviewCard 
                  key={review.id} 
                  review={review} 
                  currentUser={user}
                  hideSpoilers={hideSpoilers}
                  onLike={onLike}
                  onReport={onReport}
                  // Passed onEditReview to ReviewCard
                  onEditReview={onEditReview}
                  onAddComment={onAddComment}
                  onAddReply={onAddReply}
                  onEditComment={onEditComment}
                  onDeleteComment={onDeleteComment}
                  onLikeComment={onLikeComment}
                  onProfileClick={onProfileClick}
                />
              ))}
            </div>
          ) : (
            <EmptyState message="This user hasn't liked any reviews yet." />
          )
        )}
      </div>
    </div>
  );
};

const EmptyState = ({ message }: { message: string }) => (
  <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center shadow-sm">
    <div className="inline-flex items-center justify-center w-12 h-12 bg-slate-50 rounded-full mb-4">
      <svg className="w-6 h-6 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
    </div>
    <p className="text-slate-500 font-medium">{message}</p>
  </div>
);

export default UserProfile;
