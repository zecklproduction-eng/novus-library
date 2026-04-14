
import { GoogleGenAI, Type } from "@google/genai";
import { TranscriptionResponse } from "../types";

export const transcribeAudio = async (
  fileBase64: string,
  mimeType: string
): Promise<TranscriptionResponse> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: [
      {
        parts: [
          {
            inlineData: {
              data: fileBase64,
              mimeType: mimeType,
            },
          },
          {
            text: "Transcribe this audio file precisely. Provide a list of segments with both start and end timestamps. Ensure timestamps are accurate to the content. Also provide a very brief summary of the audio.",
          },
        ],
      },
    ],
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          segments: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                startTime: {
                  type: Type.STRING,
                  description: "Start timestamp in MM:SS format.",
                },
                startSeconds: {
                  type: Type.NUMBER,
                  description: "Total seconds from start for segment beginning.",
                },
                endTime: {
                  type: Type.STRING,
                  description: "End timestamp in MM:SS format.",
                },
                endSeconds: {
                  type: Type.NUMBER,
                  description: "Total seconds from start for segment ending.",
                },
                text: {
                  type: Type.STRING,
                  description: "The transcribed text for this segment.",
                },
              },
              required: ["startTime", "startSeconds", "endTime", "endSeconds", "text"],
            },
          },
          summary: {
            type: Type.STRING,
            description: "A short summary of the entire audio.",
          },
        },
        required: ["segments"],
      },
    },
  });

  if (!response.text) {
    throw new Error("No transcription text received from Gemini.");
  }

  try {
    return JSON.parse(response.text) as TranscriptionResponse;
  } catch (err) {
    console.error("Failed to parse Gemini response:", response.text);
    throw new Error("Invalid response format from AI.");
  }
};
