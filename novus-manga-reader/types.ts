
export interface MangaPage {
  url: string;
  pageNumber: number;
}

export interface Character {
  id: string;
  name: string;
  role: string;
  image: string;
  description: string;
}

export interface Chapter {
  id: string;
  number: number;
  title: string;
  pages: MangaPage[];
}

export interface MangaSeries {
  id: string;
  title: string;
  description: string;
  author: string;
  coverImage: string;
  chapters: Chapter[];
  characters: Character[];
}

export interface Comment {
  id: string;
  author: string;
  authorAvatar: string;
  text: string;
  timestamp: string;
  likes: number;
  replies: Comment[];
}

export interface Review {
  id: string;
  author: string;
  authorAvatar: string;
  rating: number;
  text: string;
  date: string;
}
