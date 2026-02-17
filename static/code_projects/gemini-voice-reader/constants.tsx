
import { VoiceName, VoiceOption } from './types';

export const VOICES: VoiceOption[] = [
  { id: VoiceName.Kore, label: 'Kore', description: 'Warm and professional', gender: 'Female' },
  { id: VoiceName.Puck, label: 'Puck', description: 'Energetic and bright', gender: 'Male' },
  { id: VoiceName.Charon, label: 'Charon', description: 'Deep and authoritative', gender: 'Male' },
  { id: VoiceName.Zephyr, label: 'Zephyr', description: 'Calm and soothing', gender: 'Neutral' },
  { id: VoiceName.Fenrir, label: 'Fenrir', description: 'Strong and clear', gender: 'Male' },
];

export const MAX_TEXT_LENGTH = 10000; // Increased to 10k characters for longer document support
