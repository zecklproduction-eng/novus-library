
export type ContentType = 'Manga' | 'Book';
export type FilterType = 'Hottest' | 'Trending' | 'Completed' | 'Ongoing' | 'Fiction' | 'Non-Fiction' | 'Most Viewed' | 'Most Popular';
export type SortBy = 'Rank' | 'Views' | 'Title';
export type SortOrder = 'Asc' | 'Desc';

export interface RankingItem {
  id: string;
  rank: number;
  title: string;
  author: string;
  description: string;
  views: number;
  imageUrl: string;
  languages: string[];
  type: ContentType;
  category: FilterType;
}