
import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { CoverOptions } from "../types";

export async function analyzeContent(base64Images: string[]): Promise<string> {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
  
  const imageParts = base64Images.map(data => ({
    inlineData: {
      mimeType: 'image/jpeg',
      data
    }
  }));

  const prompt = `Analyze these pages from a book/manga. Describe the core theme, the main characters shown (appearance, vibes), the setting, and the overall mood. Summarize this into a detailed creative description that could be used as a prompt for an illustrator to design a cover page. Focus on visual details.`;

  const response: GenerateContentResponse = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: {
      parts: [...imageParts, { text: prompt }]
    }
  });

  return response.text || "A mysterious story waiting to be told.";
}

export async function generateCoverImage(analysis: string, options: CoverOptions): Promise<string> {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
  
  const finalPrompt = `Professional book cover illustration. ${options.style}. Mood: ${options.mood}. Scene details: ${analysis}. Extremely high quality, vibrant colors, detailed textures, professional composition. No text or typography if addTitle is false. Style: ${options.style}.`;

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: {
      parts: [{ text: finalPrompt }]
    },
    config: {
      imageConfig: {
        aspectRatio: options.aspectRatio
      }
    }
  });

  for (const part of response.candidates?.[0]?.content.parts || []) {
    if (part.inlineData) {
      return `data:image/png;base64,${part.inlineData.data}`;
    }
  }

  throw new Error("Failed to generate image part.");
}
