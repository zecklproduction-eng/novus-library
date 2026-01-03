
import React, { useState, useEffect, useCallback } from 'react';
import { 
  MediaType, 
  Review, 
  ReviewComment,
  ReviewFiltersState, 
  SortOption, 
  MediaStatus,
  User
} from './types';
import { MOCK_REVIEWS } from './services/mockData';
import { postComment, postReply, patchComment, deleteCommentApi, toggleLikeComment, reportContent, postReview, patchReview } from './services/api';
import ReviewCard from './components/ReviewCard';
import ReviewFilters from './components/ReviewFilters';
import { ReviewListSkeleton } from './components/SkeletonLoader';
import UserProfile from './components/UserProfile';
import PostReviewModal from './components/PostReviewModal';
import Toast, { ToastType } from './components/Toast';

const CURRENT_USER: User = {
  id: 'me',
  username: 'You',
  avatarUrl: 'https://picsum.photos/seed/you/100/100'
};

const App: React.FC = () => {
  const [view, setView] = useState<'feed' | 'profile'>('feed');
  const [profileUser, setProfileUser] = useState<User | null>(null);
  const [isPostModalOpen, setIsPostModalOpen] = useState(false);

  // Toast state
  const [toast, setToast] = useState<{ message: string; type: ToastType; isVisible: boolean }>({
    message: '',
    type: 'success',
    isVisible: false,
  });

  const [filters, setFilters] = useState<ReviewFiltersState>({
    mode: MediaType.MANGA,
    search: '',
    sort: SortOption.NEWEST,
    ratingMin: 0,
    status: 'Any',
    hideSpoilers: true
  });

  const [isLoading, setIsLoading] = useState(true);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [page, setPage] = useState(1);

  // Simulate API fetch with filters
  useEffect(() => {
    const fetchReviews = async () => {
      setIsLoading(true);
      await new Promise(r => setTimeout(r, 800));

      let filtered = [...MOCK_REVIEWS];
      filtered = filtered.filter(r => r.media.type === filters.mode);

      if (filters.search) {
        const query = filters.search.toLowerCase();
        filtered = filtered.filter(r => 
          r.media.title.toLowerCase().includes(query) || 
          r.user.username.toLowerCase().includes(query)
        );
      }

      if (filters.ratingMin > 0) {
        filtered = filtered.filter(r => r.rating >= filters.ratingMin);
      }

      if (filters.status !== 'Any') {
        filtered = filtered.filter(r => r.status === filters.status);
      }

      filtered.sort((a, b) => {
        if (filters.sort === SortOption.NEWEST) return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        if (filters.sort === SortOption.OLDEST) return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
        if (filters.sort === SortOption.HIGHEST_RATED) return b.rating - a.rating;
        if (filters.sort === SortOption.LOWEST_RATED) return a.rating - b.rating;
        return 0;
      });

      setReviews(filtered);
      setIsLoading(false);
    };

    fetchReviews();
  }, [filters]);

  const showToast = (message: string, type: ToastType = 'success') => {
    setToast({ message, type, isVisible: true });
  };

  const handleFilterChange = (updates: Partial<ReviewFiltersState>) => {
    setFilters(prev => ({ ...prev, ...updates }));
    setPage(1);
  };

  const handlePostReview = async (data: {
    title: string;
    type: MediaType;
    rating: number;
    status: MediaStatus;
    body: string;
    hasSpoilers: boolean;
    tags: string[];
  }) => {
    try {
      const newReview = await postReview(CURRENT_USER, data);
      
      if (newReview.media.type === filters.mode) {
        setReviews(prev => [newReview, ...prev]);
      } else {
        handleFilterChange({ mode: newReview.media.type });
      }
      
      showToast("Review published successfully!");
    } catch (error) {
      showToast("Failed to publish review.", "error");
    }
  };

  const handleEditReview = async (reviewId: string, updates: Partial<Review>) => {
    try {
      await patchReview(reviewId, CURRENT_USER.id, updates);
      setReviews(prev => prev.map(r => {
        if (r.id === reviewId) {
          return { ...r, ...updates, updatedAt: new Date().toISOString() };
        }
        return r;
      }));
      showToast("Review updated!");
    } catch (error) {
      showToast("Failed to update review.", "error");
      throw error;
    }
  };

  const handleLike = (id: string) => {
    setReviews(prev => prev.map(r => {
      if (r.id === id) {
        const isLiking = !r.isLiked;
        if (isLiking) showToast("Added to helpful reviews!");
        return {
          ...r,
          isLiked: isLiking,
          likesCount: r.isLiked ? r.likesCount - 1 : r.likesCount + 1
        };
      }
      return r;
    }));
  };

  const handleAddComment = async (reviewId: string, commentBody: string) => {
    const newComment = await postComment(reviewId, CURRENT_USER, commentBody);
    setReviews(prev => prev.map(r => {
      if (r.id === reviewId) return { ...r, comments: [...r.comments, newComment] };
      return r;
    }));
    showToast("Comment posted!");
  };

  const handleAddReply = async (reviewId: string, parentId: string, replyBody: string) => {
    const newReply = await postReply(reviewId, parentId, CURRENT_USER, replyBody);
    const updateNestedReplies = (comments: ReviewComment[]): ReviewComment[] => {
      return comments.map(c => {
        if (c.id === parentId) return { ...c, replies: [...(c.replies || []), newReply] };
        if (c.replies && c.replies.length > 0) return { ...c, replies: updateNestedReplies(c.replies) };
        return c;
      });
    };
    setReviews(prev => prev.map(r => {
      if (r.id === reviewId) return { ...r, comments: updateNestedReplies(r.comments) };
      return r;
    }));
    showToast("Reply posted!");
  };

  const handleEditComment = async (reviewId: string, commentId: string, text: string) => {
    await patchComment(commentId, CURRENT_USER.id, text);
    const updateContent = (comments: ReviewComment[]): ReviewComment[] => {
      return comments.map(c => {
        if (c.id === commentId) return { ...c, body: text };
        if (c.replies && c.replies.length > 0) return { ...c, replies: updateContent(c.replies) };
        return c;
      });
    };
    setReviews(prev => prev.map(r => {
      if (r.id === reviewId) return { ...r, comments: updateContent(r.comments) };
      return r;
    }));
  };

  const handleDeleteComment = async (reviewId: string, commentId: string) => {
    await deleteCommentApi(commentId, CURRENT_USER.id);
    const removeContent = (comments: ReviewComment[]): ReviewComment[] => {
      return comments.filter(c => c.id !== commentId).map(c => ({
        ...c,
        replies: c.replies ? removeContent(c.replies) : []
      }));
    };
    setReviews(prev => prev.map(r => {
      if (r.id === reviewId) return { ...r, comments: removeContent(r.comments) };
      return r;
    }));
    showToast("Comment deleted.");
  };

  const handleLikeComment = async (reviewId: string, commentId: string) => {
    await toggleLikeComment(commentId);
    const toggleLike = (comments: ReviewComment[]): ReviewComment[] => {
      return comments.map(c => {
        if (c.id === commentId) return { ...c, isLiked: !c.isLiked, likesCount: c.isLiked ? c.likesCount - 1 : c.likesCount + 1 };
        if (c.replies && c.replies.length > 0) return { ...c, replies: toggleLike(c.replies) };
        return c;
      });
    };
    setReviews(prev => prev.map(r => {
      if (r.id === reviewId) return { ...r, comments: toggleLike(r.comments) };
      return r;
    }));
  };

  const handleReport = async (id: string, reason: string, details: string) => {
    await reportContent('review', id, reason, details);
    showToast("Report submitted for moderation.", "info");
  };

  const handleProfileClick = (username: string) => {
    // Conceptual navigation log to reflect requested URL structure
    console.log(`Navigating to /profile/${username}`);
    
    const user = reviews.find(r => r.user.username === username)?.user || 
                 MOCK_REVIEWS.find(r => r.user.username === username)?.user ||
                 (username === CURRENT_USER.username ? CURRENT_USER : null);
    if (user) {
      setProfileUser(user);
      setView('profile');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const loadMore = useCallback(() => {
    setPage(p => p + 1);
  }, []);

  return (
    <div className="min-h-screen pb-20">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <button onClick={() => setView('feed')} className="flex items-center space-x-2 focus:outline-none group">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center group-hover:bg-indigo-700 transition-colors">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <span className="font-bold text-xl text-slate-900 tracking-tight group-hover:text-indigo-600 transition-colors">MediaHub</span>
          </button>
          
          <nav className="hidden md:flex items-center space-x-8 text-sm font-semibold text-slate-500">
            <button onClick={() => setView('feed')} className={`hover:text-slate-900 transition-colors py-5 border-b-2 ${view === 'feed' ? 'text-indigo-600 border-indigo-600' : 'border-transparent'}`}>Feed</button>
            <a href="#" className="hover:text-slate-900 transition-colors">Explore</a>
            <a href="#" className="hover:text-slate-900 transition-colors">Community</a>
          </nav>

          <div className="flex items-center space-x-4">
            <button onClick={() => handleProfileClick(CURRENT_USER.username)} className="flex items-center space-x-2 mr-2 focus:outline-none group">
               <img src={CURRENT_USER.avatarUrl} className="w-8 h-8 rounded-full border border-slate-200 group-hover:ring-2 group-hover:ring-indigo-500 transition-all" alt="You" />
               <span className="text-sm font-bold text-slate-700 hidden sm:inline group-hover:text-indigo-600 transition-colors">{CURRENT_USER.username}</span>
            </button>
            <button onClick={() => setIsPostModalOpen(true)} className="px-6 py-2.5 bg-indigo-600 text-white text-xs font-black rounded-xl hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-100 uppercase tracking-widest">
              Post Review
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 pt-8">
        {view === 'feed' ? (
          <>
            <div className="mb-8">
              <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">Recent User Reviews</h1>
              <p className="text-slate-500 font-medium">See what the community is saying about the latest releases.</p>
            </div>

            <div className="flex p-1.5 bg-slate-100 rounded-xl mb-6 w-fit border border-slate-200">
              {[
                { id: MediaType.MANGA, label: 'Manga' },
                { id: MediaType.ANIME, label: 'Anime' },
                { id: MediaType.BOOK, label: 'Books' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => handleFilterChange({ mode: tab.id })}
                  className={`px-6 py-2 text-sm font-bold rounded-lg transition-all ${
                    filters.mode === tab.id 
                      ? 'bg-white text-indigo-600 shadow-sm' 
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <ReviewFilters filters={filters} onFilterChange={handleFilterChange} />

            <div className="mt-8 space-y-6">
              {isLoading ? (
                <ReviewListSkeleton />
              ) : reviews.length > 0 ? (
                <>
                  {reviews.map(review => (
                    <ReviewCard 
                      key={review.id} 
                      review={review} 
                      currentUser={CURRENT_USER}
                      hideSpoilers={filters.hideSpoilers}
                      onLike={handleLike}
                      onReport={handleReport}
                      onEditReview={handleEditReview}
                      onAddComment={handleAddComment}
                      onAddReply={handleAddReply}
                      onEditComment={handleEditComment}
                      onDeleteComment={handleDeleteComment}
                      onLikeComment={handleLikeComment}
                      onProfileClick={handleProfileClick}
                    />
                  ))}
                  <div className="pt-4 flex justify-center">
                    <button onClick={loadMore} className="flex items-center space-x-2 px-8 py-3 bg-white border border-slate-200 text-slate-600 font-bold text-sm rounded-xl hover:bg-slate-50 hover:border-indigo-200 transition-all shadow-sm">
                      <span>Load More Reviews</span>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>
                </>
              ) : (
                <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center shadow-sm">
                  <h3 className="text-xl font-bold text-slate-900 mb-2">No reviews found</h3>
                  <p className="text-slate-500 max-w-xs mx-auto mb-6">We couldn't find any reviews matching your current filters.</p>
                  <button onClick={() => setFilters({ mode: filters.mode, search: '', sort: SortOption.NEWEST, ratingMin: 0, status: 'Any', hideSpoilers: true })} className="text-indigo-600 font-bold hover:underline">
                    Clear all filters
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          profileUser && (
            <UserProfile 
              user={profileUser}
              allReviews={reviews}
              onBack={() => setView('feed')}
              hideSpoilers={filters.hideSpoilers}
              onLike={handleLike}
              onReport={handleReport}
              onEditReview={handleEditReview}
              onAddComment={handleAddComment}
              onAddReply={handleAddReply}
              onEditComment={handleEditComment}
              onDeleteComment={handleDeleteComment}
              onLikeComment={handleLikeComment}
              onProfileClick={handleProfileClick}
            />
          )
        )}
      </main>

      <PostReviewModal 
        isOpen={isPostModalOpen} 
        onClose={() => setIsPostModalOpen(false)}
        onSubmit={handlePostReview}
      />

      <Toast 
        isVisible={toast.isVisible}
        message={toast.message}
        type={toast.type}
        onClose={() => setToast(prev => ({ ...prev, isVisible: false }))}
      />
    </div>
  );
};

export default App;
