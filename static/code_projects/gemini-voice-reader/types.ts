
export enum VoiceName {
  Kore = 'Kore',
  Puck = 'Puck',
  Charon = 'Charon',
  Zephyr = 'Zephyr',
  Fenrir = 'Fenrir'
}

export interface VoiceOption {
  id: VoiceName;
  label: string;
  description: string;
  gender: 'Male' | 'Female' | 'Neutral';
}

export interface AudioState {
  isPlaying: boolean;
  isGenerating: boolean;
  progress: number;
  duration: number;
}
