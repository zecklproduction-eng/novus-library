
export interface TranscriptItem {
  id: string;
  startTime: number;
  endTime: number;
  text: string;
  pageNumber?: number; // Added for scroll synchronization
}

export interface Highlight {
  id: string;
  pageNumber: number;
  text: string;
  color: string;
  timestamp: number;
}

export interface Note {
  id: string;
  pageNumber: number;
  content: string;
  referenceText?: string;
  highlightId?: string; // Link to a specific highlight
  timestamp: number;
  color: string;
}

export interface TOCItem {
  id: string;
  title: string;
  pageNumber: number;
  level: number; // 1 for Chapter, 2 for Section, etc.
}

export interface BookMetadata {
  id: string;
  title: string;
  author: string;
  pdfUrl: string;
  audioUrl: string;
  preUploadedSummary: string;
  transcript: TranscriptItem[];
  toc: TOCItem[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: { title: string; uri: string }[];
}

export enum SidebarTab {
  Info = 'info',
  Contents = 'contents',
  Summary = 'summary',
  Transcript = 'transcript',
  Assistant = 'assistant',
  Notes = 'notes'
}
