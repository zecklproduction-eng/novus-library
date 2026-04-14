
import { BookMetadata } from './types';

// Helper to generate repetitive but diverse mock pages
const generateMockPages = (count: number) => {
  const themes = [
    "The geological history of Mars is as rich and complex as that of the Earth.",
    "One of the most remarkable features of the Martian surface is the Valles Marineris.",
    "As we look toward the future, the challenges of colonization become apparent.",
    "The quest for knowledge is unending. Every rover touchdown adds a piece to the puzzle.",
    "Atmospheric composition is primarily carbon dioxide, offering little protection.",
    "Water ice has been detected at the poles and in subterranean deposits.",
    "The dust storms on Mars can encompass the entire planet for months.",
    "Olympus Mons stands as a silent giant, the tallest volcano in the solar system.",
    "Terraforming concepts include melting the polar caps to release CO2.",
    "The psychology of a small crew on a multi-year mission is a critical study."
  ];
  
  return Array.from({ length: count }, (_, i) => ({
    pageNumber: i + 1,
    title: i === 0 ? "Chapter 1: The Red Horizon" : 
           i === 4 ? "Chapter 2: Geological Diversity" :
           i === 11 ? "Chapter 3: Future Frontiers" :
           `Section 1.${i}: Extended Analysis`,
    content: themes[i % themes.length] + " " + themes[(i + 1) % themes.length] + " " + themes[(i + 2) % themes.length]
  }));
};

export const MOCK_PAGES = generateMockPages(25);

export const MOCK_BOOK: BookMetadata = {
  id: '1',
  title: 'The Great Exploration of Mars',
  author: 'Dr. Sarah Valis',
  pdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
  audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
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
