
import { GoogleGenAI } from "@google/genai";
import { DetailLevel } from "../types";

const MODEL_NAME = 'gemini-3-flash-preview';

export const generateBookSummary = async (base64Pdf: string, detailLevel: DetailLevel): Promise<string> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  const detailInstructions = {
    concise: "Keep the summary brief and high-level. Focus only on the core themes, major arguments, and primary takeaways. Avoid minor details.",
    balanced: "Provide a standard, comprehensive summary. Cover each chapter or part with a mix of main points and significant supporting details.",
    detailed: "Provide an in-depth analysis. Include nuanced arguments, specific examples, character arcs (if fiction), and thorough chapter-by-chapter breakdowns."
  };

  const prompt = `
    Please act as a professional literary analyst and technical writer. 
    Analyze the provided PDF (a book) and generate a structured summary.
    
    LEVEL OF DETAIL REQUESTED: ${detailLevel.toUpperCase()}
    INSTRUCTION: ${detailInstructions[detailLevel]}

    CRITICAL STRUCTURE REQUIREMENTS:
    1. Use H1 (#) for Chapter or Part titles.
    2. Use H2 (##) for major Sections within chapters.
    3. Use H3 (###) for Sub-sections or detailed points.
    
    CONTENT REQUIREMENTS:
    - Group insights logically by the book's original structure.
    - Provide an overview of the main arguments, narrative arcs, or key concepts based on the requested detail level.
    - Use bullet points for key takeaways within sections.
    - Maintain a professional, objective, and clear tone.
    - Ensure the hierarchy of headers is strictly followed (H1 -> H2 -> H3).
  `;

  try {
    const response = await ai.models.generateContent({
      model: MODEL_NAME,
      contents: {
        parts: [
          {
            inlineData: {
              mimeType: 'application/pdf',
              data: base64Pdf,
            },
          },
          { text: prompt },
        ],
      },
    });

    if (!response || !response.text) {
      throw new Error("Failed to generate content from AI.");
    }

    return response.text;
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw new Error(error instanceof Error ? error.message : "An unknown error occurred while processing the PDF.");
  }
};
