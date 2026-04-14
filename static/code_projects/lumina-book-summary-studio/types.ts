
export type DetailLevel = 'concise' | 'balanced' | 'detailed';

export interface SummaryState {
  isProcessing: boolean;
  content: string | null;
  error: string | null;
  fileName: string | null;
  detailLevel: DetailLevel;
}

export interface ProcessingStep {
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
}
