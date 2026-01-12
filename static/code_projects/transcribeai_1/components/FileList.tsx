
import React from 'react';
import { PendingFile } from '../types';

interface FileListProps {
  files: PendingFile[];
  onRemove: (id: string) => void;
  onMove: (id: string, direction: 'up' | 'down') => void;
  disabled: boolean;
}

const FileList: React.FC<FileListProps> = ({ files, onRemove, onMove, disabled }) => {
  if (files.length === 0) return null;

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="mt-6 space-y-3">
      <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 px-1">Queue ({files.length} files)</h4>
      <div className="space-y-2 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
        {files.map((item, index) => (
          <div 
            key={item.id} 
            className="flex items-center gap-4 bg-slate-900 border border-slate-800 p-3 rounded-xl group transition-all hover:border-slate-700"
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">
              {index + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{item.file.name}</p>
              <p className="text-xs text-slate-500">{formatSize(item.file.size)}</p>
            </div>
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button 
                onClick={() => onMove(item.id, 'up')}
                disabled={disabled || index === 0}
                className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-20"
                title="Move Up"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" /></svg>
              </button>
              <button 
                onClick={() => onMove(item.id, 'down')}
                disabled={disabled || index === files.length - 1}
                className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-20"
                title="Move Down"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </button>
              <button 
                onClick={() => onRemove(item.id)}
                disabled={disabled}
                className="p-1.5 rounded hover:bg-red-500/10 text-slate-400 hover:text-red-400 disabled:opacity-20 ml-2"
                title="Remove"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FileList;
