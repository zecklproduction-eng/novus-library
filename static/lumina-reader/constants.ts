
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
      custom_summary?: string;
      is_editor?: boolean;
      user_plan?: string;  // 'basic', 'pro', or 'ultimate'
    };
  }
}

// Helper to generate pages from book description
const generatePagesFromDescription = (description: string, pageCount: number = 25) => {
  const trimmed = description.trim();

  // If it's structured HTML, handle it differently
  if (trimmed.startsWith('<')) {
    // We want to split by <h1> but KEEP the <h1> tag itself in the result
    // We use a regex with a lookahead or a specific matching strategy
    // Split into sections starting with <h1
    const sections: string[] = [];
    let remaining = trimmed;

    // Check for content before first H1
    const firstH1Index = remaining.search(/<h1/i);
    if (firstH1Index > 0) {
      sections.push(remaining.substring(0, firstH1Index));
      remaining = remaining.substring(firstH1Index);
    } else if (firstH1Index === -1 && remaining.length > 0) {
      // No H1s at all
      sections.push(remaining);
      remaining = "";
    }

    // Now split the rest by H1 (keeping the H1 at the start of each section)
    const h1SplitRegex = /(?=<h1)/i;
    const h1Sections = remaining.split(h1SplitRegex).filter(s => s.trim().length > 0);
    sections.push(...h1Sections);

    if (sections.length > 0) {
      const pages: { pageNumber: number; title: string; content: string }[] = [];
      let globalPageNum = 1;

      sections.forEach((sectionContent, i) => {
        // Try to extract the first heading text for the title
        // Matches <h1>...</h1> or <h2>...</h2> or <h3>...</h3>
        const hMatch = sectionContent.match(/<h[123][^>]*>(.*?)<\/h[123]>/i);
        const sectionTitle = hMatch ? hMatch[1].replace(/<[^>]*>/g, '').trim() : `Section ${i + 1}`;

        // Secondary split: If a section is too long (> 1100 chars), split it by paragraphs
        // Aggressive limit to prevent overflow in the white page container
        if (sectionContent.length > 1100) {
          const paragraphs = sectionContent.split(/<\/p>/i).filter(p => p.trim().length > 0);
          let currentPageContent = "";
          let subSectionCounter = 0;

          paragraphs.forEach((p) => {
            let pWithClosing = p.toLowerCase().includes('<p') ? p + "</p>" : "<p>" + p + "</p>";

            // IF a single paragraph is extremely long (> 1000 chars), split it
            if (pWithClosing.length > 1000) {
              // Try splitting by sentences first
              let chunks: string[] = Array.from(pWithClosing.match(/[^\.!\?]+[\.!\?]+/g) || []);

              // Fallback: if no sentences found, split by fixed character chunks (e.g., 800 chars)
              if (chunks.length === 0) {
                chunks = [];
                for (let j = 0; j < pWithClosing.length; j += 800) {
                  chunks.push(pWithClosing.substring(j, j + 800));
                }
              }

              chunks.forEach(chunk => {
                if (currentPageContent.length + chunk.length > 900 && currentPageContent.length > 0) {
                  pages.push({
                    pageNumber: globalPageNum++,
                    title: subSectionCounter === 0 ? sectionTitle : `${sectionTitle} (Part ${subSectionCounter + 1})`,
                    content: currentPageContent.endsWith('</p>') ? currentPageContent : currentPageContent + "</p>"
                  });
                  currentPageContent = "<p>"; // Restart with p tag
                  subSectionCounter++;
                }
                currentPageContent += chunk;
              });
            } else {
              // Standard behavior for normal-sized paragraphs
              if (currentPageContent.length + pWithClosing.length > 950 && currentPageContent.length > 0) {
                pages.push({
                  pageNumber: globalPageNum++,
                  title: subSectionCounter === 0 ? sectionTitle : `${sectionTitle} (Part ${subSectionCounter + 1})`,
                  content: currentPageContent.endsWith('</p>') ? currentPageContent : currentPageContent + "</p>"
                });
                currentPageContent = "";
                subSectionCounter++;
              }
              currentPageContent += pWithClosing;
            }
          });

          if (currentPageContent.trim()) {
            pages.push({
              pageNumber: globalPageNum++,
              title: subSectionCounter === 0 ? sectionTitle : `${sectionTitle} (Part ${subSectionCounter + 1})`,
              content: currentPageContent
            });
          }
        } else {
          pages.push({
            pageNumber: globalPageNum++,
            title: sectionTitle,
            content: sectionContent
          });
        }
      });
      return pages;
    }
  }

  // Original fallback logic for plain text descriptions
  const sentences = trimmed.split(/(?<=[.!?])\s+/).filter(s => s.trim().length > 0);
  if (sentences.length === 0) {
    return [{
      pageNumber: 1,
      title: "Loading",
      content: "Content for this page is being loaded..."
    }];
  }

  // For plain text, we keep the original force-pagination logic but more carefully
  return Array.from({ length: pageCount }, (_, i) => ({
    pageNumber: i + 1,
    title: i === 0 ? "Chapter 1: Introduction" :
      i === 4 ? "Chapter 2: Main Content" :
        i === 11 ? "Chapter 3: Deep Dive" :
          `Section ${Math.floor(i / 3) + 1}.${(i % 3) + 1}: Continued`,
    content: sentences[i % sentences.length] + " " + (sentences[(i + 1) % sentences.length] || "") + " " + (sentences[(i + 2) % sentences.length] || "")
  }));
};

// Get book data from Flask template or use fallback mock data
const getBookData = (): BookMetadata => {
  const flaskData = window.__BOOK_DATA__;

  if (flaskData) {
    let transcriptData = flaskData.transcript || "";
    // Try to parse JSON string if applicable
    if (typeof transcriptData === 'string' && (transcriptData.trim().startsWith('[') || transcriptData.trim().startsWith('{'))) {
      try {
        transcriptData = JSON.parse(transcriptData);
      } catch (e) {
        console.warn("Failed to parse transcript JSON", e);
      }
    }

    let tocData = flaskData.toc || "";
    // Try to parse JSON string if applicable
    if (typeof tocData === 'string' && (tocData.trim().startsWith('[') || tocData.trim().startsWith('{'))) {
      try {
        tocData = JSON.parse(tocData);
      } catch (e) {
        console.warn("Failed to parse TOC JSON", e);
      }
    }

    // Ensure custom_summary is mapped correctly
    const summary = flaskData.custom_summary || "";

    return {
      id: flaskData.id,
      title: flaskData.title,
      author: flaskData.author,
      pdfUrl: flaskData.pdfUrl,
      audioUrl: flaskData.audioUrl || '',
      coverUrl: flaskData.coverUrl || undefined,
      custom_summary: summary,
      preUploadedSummary: summary, // Sync preUploadedSummary with custom_summary
      transcript: transcriptData,
      toc: tocData,
      is_editor: flaskData.is_editor,
      user_plan: flaskData.user_plan || 'basic'  // Default to basic if not provided
    };
  }

  // Fallback mock data for development
  const mockSummary = `This book explores the historical timeline and future prospects of Martian colonization. Dr. Valis delves into the geological challenges of the Red Planet, the psychological impacts of long-term isolation on crews, and the innovative life-support systems being developed. Key takeaways include the feasibility of terraforming and the critical role of international collaboration in space exploration.`;
  return {
    id: '1',
    title: 'The Great Exploration of Mars',
    author: 'Dr. Sarah Valis',
    pdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
    audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    coverUrl: 'https://picsum.photos/seed/bookcover/400/600',
    custom_summary: mockSummary,
    preUploadedSummary: mockSummary,
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

// If the summary is very short, adjust page count or use a minimum of 5 pages
const effectivePageCount = (MOCK_BOOK.preUploadedSummary && MOCK_BOOK.preUploadedSummary.length < 500) ? 5 : 25;
export const MOCK_PAGES = generatePagesFromDescription(MOCK_BOOK.preUploadedSummary || "", effectivePageCount);
