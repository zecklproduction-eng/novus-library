
import { GoogleGenAI } from "@google/genai";

const API_KEY = process.env.API_KEY || "";

export const getAIInsights = async (chapterTitle: string, context: string) => {
  if (!API_KEY) return "AI insights are currently unavailable.";
  
  const ai = new GoogleGenAI({ apiKey: API_KEY });
  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: `Analyze this manga chapter context and provide 3-4 bullet points of "Smart Summary" for the chapter titled "${chapterTitle}". Context: ${context}`,
      config: {
        temperature: 0.7,
        maxOutputTokens: 500,
      }
    });

    return response.text;
  } catch (error) {
    console.error("Gemini Error:", error);
    return "Could not generate AI insights at this time.";
  }
};
