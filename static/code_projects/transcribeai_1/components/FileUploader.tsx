
import React, { useRef } from 'react';

interface FileUploaderProps {
  onFilesSelect: (files: FileList) => void;
  disabled: boolean;
}

const FileUploader: React.FC<FileUploaderProps> = ({ onFilesSelect, disabled }) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFilesSelect(files);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      !disabled && inputRef.current?.click();
    }
  };

  return (
    <div 
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload audio or video files to transcribe"
      aria-disabled={disabled}
      onKeyDown={handleKeyDown}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-10 transition-all cursor-pointer text-center outline-none focus-visible:ring-2 focus-visible:ring-indigo-500
        ${disabled ? 'border-slate-700 bg-slate-900/50 cursor-not-allowed' : 'border-indigo-500/50 hover:border-indigo-400 bg-slate-800/50 hover:bg-slate-800'}`}
    >
      <input 
        type="file" 
        ref={inputRef} 
        onChange={handleFileChange} 
        className="hidden" 
        accept="audio/*,video/*"
        multiple
        disabled={disabled}
        aria-hidden="true"
      />
      <div className="flex flex-col items-center gap-4">
        <div className="p-4 bg-indigo-500/10 rounded-full" aria-hidden="true">
          <svg className="w-10 h-10 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <div>
          <h3 className="text-xl font-semibold text-white">Upload Files</h3>
          <p className="text-slate-400 mt-1">Select one or multiple files to transcribe in sequence</p>
        </div>
      </div>
    </div>
  );
};

export default FileUploader;
