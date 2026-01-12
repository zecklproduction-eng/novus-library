
export interface TranscriptSegment {
  startTime: string; // format "MM:SS"
  startSeconds: number;
  endTime: string;   // format "MM:SS"
  endSeconds: number;
  text: string;
}

export interface TranscriptionResponse {
  segments: TranscriptSegment[];
  summary?: string;
}

export interface PendingFile {
  id: string;
  file: File;
  duration: number;
  previewUrl: string;
}

export enum AppStatus {
  IDLE = 'IDLE',
  UPLOADING = 'UPLOADING',
  TRANSCRIBING = 'TRANSCRIBING',
  COMPLETED = 'COMPLETED',
  ERROR = 'ERROR'
}
