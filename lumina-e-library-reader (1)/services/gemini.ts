
import { GoogleGenAI } from "@google/genai";
import { ChatMessage } from "../types";

export const getGeminiResponse = async (
  messages: ChatMessage[], 
  context: string, 
  targetUrl?: string,
  queryScope: 'book' | 'general' = 'book'
) => {
  // Always initialize with the environment variable directly as per guidelines
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  let systemInstruction = "";

  if (queryScope === 'book') {
    systemInstruction = `
      You are an expert academic assistant for an e-library. 
      The user is specifically asking about the book titled: "The Great Exploration of Mars".
      Here is the summary of the book for context: ${context}.
      PRIORITIZE information from the book. If the question cannot be answered using the book's context, inform the user but try to provide a helpful related response.
      Keep your answers concise and professional.
    `;
  } else {
    systemInstruction = `
      You are a versatile academic research assistant in a digital library.
      The user is asking a general knowledge question, potentially unrelated to the current book ("The Great Exploration of Mars").
      Feel free to use your broad internal knowledge and Google Search to provide a comprehensive answer.
      While you are in a library context, you are NOT limited to the current book's contents for this query.
      Maintain a professional, scholarly tone.
    `;
  }

  if (targetUrl) {
    systemInstruction += `
      The user has also provided an external URL for analysis: ${targetUrl}.
      Summary of findings from this URL should be integrated into your response.
    `;
  }

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: messages.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'model',
        parts: [{ text: msg.content }]
      })),
      config: {
        systemInstruction,
        temperature: 0.7,
        topP: 0.95,
        tools: [{ googleSearch: {} }]
      }
    });

    const text = response.text || "I'm sorry, I couldn't generate a response.";
    
    // Extract grounding sources as per guidelines
    const groundingChunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
    const sources = groundingChunks?.map((chunk: any) => ({
      title: chunk.web?.title || "Source",
      uri: chunk.web?.uri || "#"
    })).filter((s: any) => s.uri !== "#");

    return { text, sources };
  } catch (error) {
    console.error("Gemini Error:", error);
    return { text: "Error connecting to AI. Please try again.", sources: [] };
  }
};
