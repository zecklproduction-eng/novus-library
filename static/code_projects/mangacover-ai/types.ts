
export interface GenerationState {
  status: 'idle' | 'processing' | 'analyzing' | 'generating' | 'completed' | 'error';
  progress: number;
  error?: string;
  coverUrl?: string;
  analysis?: string;
}

export interface CoverOptions {
  style: string;
  mood: string;
  addTitle: boolean;
  aspectRatio: "1:1" | "3:4" | "4:3" | "9:16" | "16:9";
}

export enum AppStyle {
  MANGA = 'Japanese Manga / Anime Style',
  REALISTIC = 'Realistic Cinematic',
  OIL_PAINTING = 'Classic Oil Painting',
  MINIMALIST = 'Modern Minimalist',
  DARK_FANTASY = 'Dark Fantasy Concept Art'
}
