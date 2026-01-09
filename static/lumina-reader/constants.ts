
import { BookMetadata } from './types';

// Declare the global window property for TypeScript
declare global {
  interface Window {
    __BOOK_DATA__?: {
      id: string;
      title: string;
      author: string;
      description: string;
      pdfUrl: string;
      audioUrl: string;
      coverUrl: string;
      transcript?: string;
      toc?: string;
    };
  }
}

// Helper to generate pages from book description
const generatePagesFromDescription = (description: string, pageCount: number = 25) => {
  const sentences = description.split(/(?<=[.!?])\s+/).filter(s => s.trim().length > 0);

  return Array.from({ length: pageCount }, (_, i) => ({
    pageNumber: i + 1,
    title: i === 0 ? "Chapter 1: Introduction" :
      i === 4 ? "Chapter 2: Main Content" :
        i === 11 ? "Chapter 3: Deep Dive" :
          `Section ${Math.floor(i / 3) + 1}.${(i % 3) + 1}: Continued`,
    content: sentences.length > 0
      ? sentences[i % sentences.length] + " " + (sentences[(i + 1) % sentences.length] || "") + " " + (sentences[(i + 2) % sentences.length] || "")
      : "Content for this page is being loaded..."
  }));
};

// Get book data from Flask template or use fallback mock data
const getBookData = (): BookMetadata => {
  const flaskData = window.__BOOK_DATA__;

  if (flaskData) {
    return {
      id: flaskData.id,
      title: flaskData.title,
      author: flaskData.author,
      pdfUrl: flaskData.pdfUrl,
      audioUrl: flaskData.audioUrl || '',
      coverUrl: flaskData.coverUrl,
      preUploadedSummary: flaskData.description || 'No summary available for this book.',
      transcript: flaskData.transcript || "",
      toc: flaskData.toc || ""
    };
  }

  // Fallback mock data for development
  return {
    id: '1',
    title: 'The Great Exploration of Mars',
    author: 'Dr. Sarah Valis',
    pdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    coverUrl: 'https://picsum.photos/seed/bookcover/400/600',
    preUploadedSummary: `This book explores the historical timeline and future prospects of Martian colonization. Dr. Valis delves into the geological challenges of the Red Planet, the psychological impacts of long-term isolation on crews, and the innovative life-support systems being developed. Key takeaways include the feasibility of terraforming and the critical role of international collaboration in space exploration.`,
    toc: [
      { id: 't1', title: 'Chapter 1: The Red Horizon', pageNumber: 1, level: 1 },
      { id: 't2', title: 'Early Observations', pageNumber: 2, level: 2 },
      { id: 't3', title: 'Modern Rover Insights', pageNumber: 3, level: 2 },
      { id: 't4', title: 'Chapter 2: Geological Diversity', pageNumber: 5, level: 1 },
      { id: 't5', title: 'Valles Marineris', pageNumber: 6, level: 2 },
      { id: 't6', title: 'Olympus Mons Analysis', pageNumber: 8, level: 2 },
      { id: 't7', title: 'Chapter 3: Future Frontiers', pageNumber: 12, level: 1 },
      { id: 't8', title: 'Life Support Systems', pageNumber: 15, level: 2 },
      { id: 't9', title: 'Terraforming Ethics', pageNumber: 20, level: 2 },
    ],
    transcript: [
      { id: '1', startTime: 0, endTime: 5, text: "Welcome to the first chapter of our exploration into Mars.", pageNumber: 1 },
      { id: '2', startTime: 5, endTime: 12, text: "Mars has fascinated humanity for centuries, often appearing as a bright red jewel in our night sky.", pageNumber: 1 },
      { id: '3', startTime: 12, endTime: 18, text: "In this section, we examine the early telescopic observations that shaped our understanding.", pageNumber: 2 },
      { id: '4', startTime: 18, endTime: 25, text: "From Percival Lowell's canals to the high-resolution imagery provided by modern rovers.", pageNumber: 3 },
      { id: '5', startTime: 25, endTime: 32, text: "The geological diversity of Mars is staggering, featuring the largest volcano in the solar system.", pageNumber: 5 },
      { id: '6', startTime: 32, endTime: 40, text: "Olympus Mons towers nearly three times the height of Mount Everest, a testament to Martian volcanic activity.", pageNumber: 8 },
      { id: '7', startTime: 40, endTime: 50, text: "Future missions aim to send humans to live and work on this distant world within the next decade.", pageNumber: 12 }
    ]
  };
};

export const MOCK_BOOK: BookMetadata = getBookData();

export const MOCK_PAGES = generatePagesFromDescription(MOCK_BOOK.preUploadedSummary, 25);
