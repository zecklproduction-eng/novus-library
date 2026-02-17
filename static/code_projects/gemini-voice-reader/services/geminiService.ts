
import { GoogleGenAI, Modality } from "@google/genai";
import { VoiceName } from '../types';

export async function generateSpeech(text: string, voice: VoiceName, pitch: number, apiKey: string, model: string = "gemini-2.5-flash-preview-tts"): Promise<string | undefined> {
  if (!apiKey) throw new Error("API Key is required");
  const trimmedText = text.trim() || "No text provided.";

  // Initialize with the provided API key
  const ai = new GoogleGenAI({ apiKey });

  // Use stylistic instructions in the prompt to simulate pitch control 
  let styleInstruction = "";
  if (pitch >= 0.4) {
    styleInstruction = "In a very high-pitched and bright voice, say: ";
  } else if (pitch > 0.1) {
    styleInstruction = "In a slightly high-pitched voice, say: ";
  } else if (pitch <= -0.4) {
    styleInstruction = "In a very deep, low-pitched voice, say: ";
  } else if (pitch < -0.1) {
    styleInstruction = "In a slightly deep voice, say: ";
  }

  const finalPrompt = styleInstruction ? `${styleInstruction}${trimmedText}` : trimmedText;

  try {
    const response = await ai.models.generateContent({
      model: model,
      contents: [{ parts: [{ text: finalPrompt }] }],
      config: {
        responseModalities: [Modality.AUDIO],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: { voiceName: voice },
          },
        },
      },
    });

    const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    if (!base64Audio) {
      console.warn("API returned successfully but without audio data. Candidates:", response.candidates);
    }
    return base64Audio;
  } catch (error: any) {
    console.error(`Gemini Service Error [Model: ${model}]:`, error);
    if (error.message?.includes("requested response modalities")) {
      throw new Error(`The model "${model}" doesn't support built-in audio output yet. Try switching to "gemini-1.5-flash-8b" or "gemini-2.0-flash-exp" in Settings.`);
    }
    throw error;
  }
}
