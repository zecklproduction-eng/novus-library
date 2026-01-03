
import { Review, ReviewComment, User, MediaType, MediaStatus } from '../types';

/**
 * Simulates a backend API call to add a new review.
 */
export const postReview = async (
  user: User,
  data: {
    title: string;
    type: MediaType;
    rating: number;
    status: MediaStatus;
    body: string;
    hasSpoilers: boolean;
    tags: string[];
  }
): Promise<Review> => {
  await new Promise(resolve => setTimeout(resolve, 800));

  const id = `r-${Math.random().toString(36).substr(2, 9)}`;
  return {
    id,
    userId: user.id,
    user: user,
    mediaId: `m-${id}`,
    media: {
      id: `m-${id}`,
      type: data.type,
      title: data.title,
      slug: data.title.toLowerCase().replace(/\s+/g, '-'),
      coverUrl: `https://picsum.photos/seed/${id}/200/300`,
      tags: data.tags
    },
    rating: data.rating,
    body: data.body,
    bodyPlain: data.body.replace(/<[^>]*>?/gm, ''),
    hasSpoilers: data.hasSpoilers,
    status: data.status,
    likesCount: 0,
    isLiked: false,
    comments: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
};

/**
 * Simulates a backend PATCH endpoint for reviews.
 */
export const patchReview = async (
  reviewId: string,
  userId: string,
  updates: { body?: string; rating?: number; status?: MediaStatus; hasSpoilers?: boolean }
): Promise<boolean> => {
  await new Promise(resolve => setTimeout(resolve, 600));
  console.log(`PATCH /api/reviews/${reviewId} - Authorized for user ${userId}`);
  return true;
};

/**
 * Simulates a backend API call to add a comment to a review.
 */
export const postComment = async (
  reviewId: string, 
  user: User, 
  body: string
): Promise<ReviewComment> => {
  await new Promise(resolve => setTimeout(resolve, 600));

  if (!body.trim()) {
    throw new Error("Comment body cannot be empty");
  }

  return {
    id: `c-${Math.random().toString(36).substr(2, 9)}`,
    userId: user.id,
    user: user,
    body: body.trim(),
    createdAt: new Date().toISOString(),
    replies: [],
    likesCount: 0,
    isLiked: false
  };
};

/**
 * Simulates a backend PATCH endpoint for comments.
 */
export const patchComment = async (
  commentId: string,
  userId: string,
  body: string
): Promise<boolean> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  console.log(`PATCH /api/comments/${commentId} - Authorized for user ${userId}`);
  return true;
};

/**
 * Simulates a backend DELETE endpoint for comments.
 */
export const deleteCommentApi = async (
  commentId: string,
  userId: string
): Promise<boolean> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  console.log(`DELETE /api/comments/${commentId} - Authorized for user ${userId}`);
  return true;
};

/**
 * Simulates a backend API call to add a reply to a specific comment.
 */
export const postReply = async (
  reviewId: string,
  parentId: string,
  user: User,
  body: string
): Promise<ReviewComment> => {
  await new Promise(resolve => setTimeout(resolve, 600));

  if (!body.trim()) {
    throw new Error("Reply body cannot be empty");
  }

  return {
    id: `r-${Math.random().toString(36).substr(2, 9)}`,
    userId: user.id,
    user: user,
    body: body.trim(),
    createdAt: new Date().toISOString(),
    replies: [],
    likesCount: 0,
    isLiked: false
  };
};

/**
 * Simulates a backend API call to like/unlike a comment.
 */
export const toggleLikeComment = async (
  commentId: string
): Promise<boolean> => {
  await new Promise(resolve => setTimeout(resolve, 200));
  return true;
};

/**
 * Simulates a backend API call to report content.
 */
export const reportContent = async (
  type: 'review' | 'comment', 
  id: string, 
  reason: string, 
  details?: string
): Promise<boolean> => {
  await new Promise(resolve => setTimeout(resolve, 800));
  console.log(`Reported ${type}: ${id} | Reason: ${reason} | Details: ${details || 'None'}`);
  return true;
};
