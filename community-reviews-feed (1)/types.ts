
export enum MediaType {
  MANGA = 'manga',
  ANIME = 'anime',
  BOOK = 'book'
}

export enum MediaStatus {
  COMPLETED = 'Completed',
  READING = 'Reading',
  ON_HOLD = 'On-Hold'
}

export enum SortOption {
  NEWEST = 'newest',
  OLDEST = 'oldest',
  HIGHEST_RATED = 'highest_rated',
  LOWEST_RATED = 'lowest_rated'
}

export interface User {
  id: string;
  username: string;
  avatarUrl: string;
}

export interface ReviewComment {
  id: string;
  userId: string;
  user: User;
  body: string;
  createdAt: string;
  replies?: ReviewComment[];
  likesCount: number;
  isLiked: boolean;
}

export interface Review {
  id: string;
  userId: string;
  user: User;
  mediaId: string;
  media: Media;
  rating: number;
  body: string;
  bodyPlain: string;
  hasSpoilers: boolean;
  status: MediaStatus;
  likesCount: number;
  isLiked: boolean;
  comments: ReviewComment[];
  createdAt: string;
  updatedAt: string;
}

export interface Media {
  id: string;
  type: MediaType;
  title: string;
  slug: string;
  coverUrl: string;
  tags: string[];
}

export interface ReviewFiltersState {
  mode: MediaType;
  search: string;
  sort: SortOption;
  ratingMin: number;
  status: MediaStatus | 'Any';
  hideSpoilers: boolean;
}
