
import React, { useState, useRef, useEffect } from 'react';
import { TranscriptSegment } from '../types';

interface TranscriptDisplayProps {
  segments: TranscriptSegment[];
  currentTime: number;
  onJumpToTime: (seconds: number) => void;
  onUpdateSegment: (index: number, newText: string) => void;
  onDeleteSegment: (index: number) => void;
  searchQuery: string;
}

const TranscriptDisplay: React.FC<TranscriptDisplayProps> = ({ 
  segments, 
  currentTime, 
  onJumpToTime,
  onUpdateSegment,
  onDeleteSegment,
  searchQuery 
}) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editBuffer, setEditBuffer] = useState("");
  const editRef = useRef<HTMLTextAreaElement>(null);

  const filteredIndices = segments
    .map((s, i) => ({ s, i }))
    .filter(({ s }) => s.text.toLowerCase().includes(searchQuery.toLowerCase()))
    .map(({ i }) => i);

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const startEditing = (index: number, currentText: string) => {
    setEditingIndex(index);
    setEditBuffer(currentText);
  };

  const saveEdit = (index: number) => {
    if (editBuffer.trim() !== segments[index].text) {
      onUpdateSegment(index, editBuffer.trim());
    }
    setEditingIndex(null);
  };

  const cancelEdit = () => {
    setEditingIndex(null);
  };

  const handleDelete = (index: number) => {
    if (window.confirm("Are you sure you want to delete this segment? This action cannot be undone.")) {
      onDeleteSegment(index);
    }
  };

  useEffect(() => {
    if (editingIndex !== null && editRef.current) {
      editRef.current.focus();
      // Move cursor to end
      editRef.current.setSelectionRange(editRef.current.value.length, editRef.current.value.length);
    }
  }, [editingIndex]);

  return (
    <div className="space-y-4" role="list">
      {filteredIndices.length === 0 ? (
        <div className="text-center py-12 text-slate-500 italic" role="status">
          No matches found for "{searchQuery}"
        </div>
      ) : (
        filteredIndices.map((originalIndex) => {
          const segment = segments[originalIndex];
          const isActive = currentTime >= segment.startSeconds && currentTime < segment.endSeconds;
          const isEditing = editingIndex === originalIndex;

          return (
            <div 
              key={`${segment.startTime}-${originalIndex}`}
              role="listitem"
              aria-current={isActive ? 'step' : undefined}
              className={`group flex gap-4 p-4 rounded-lg transition-all duration-200 border border-transparent 
                ${isActive 
                  ? 'bg-indigo-500/10 border-indigo-500/30 shadow-sm shadow-indigo-500/10' 
                  : 'hover:bg-slate-800/80 hover:border-slate-700/50 hover:shadow-md hover:shadow-black/20'}`}
            >
              <button
                onClick={() => onJumpToTime(segment.startSeconds)}
                aria-label={`Jump to ${segment.startTime} in audio`}
                className={`flex-shrink-0 h-fit font-mono text-xs px-2 py-1 rounded bg-slate-800 border border-slate-700 
                  transition-colors outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 whitespace-nowrap
                  ${isActive ? 'text-indigo-400 border-indigo-500/30' : 'text-slate-400 group-hover:text-slate-200 group-hover:border-slate-600'}`}
              >
                {segment.startTime} - {segment.endTime}
              </button>
              
              <div className="flex-1">
                {isEditing ? (
                  <textarea
                    ref={editRef}
                    value={editBuffer}
                    onChange={(e) => setEditBuffer(e.target.value)}
                    onBlur={() => saveEdit(originalIndex)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        saveEdit(originalIndex);
                      }
                      if (e.key === 'Escape') {
                        cancelEdit();
                      }
                    }}
                    className="w-full bg-slate-950 border border-indigo-500/50 rounded p-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none min-h-[60px]"
                    aria-label="Edit segment text"
                  />
                ) : (
                  <p 
                    onClick={() => startEditing(originalIndex, segment.text)}
                    className={`text-sm leading-relaxed transition-colors cursor-text group/text relative
                      ${isActive ? 'text-white font-medium' : 'text-slate-300 group-hover:text-slate-100'}`}
                  >
                    {segment.text}
                    <span className="opacity-0 group-hover/text:opacity-100 ml-2 inline-flex text-xs text-indigo-400 transition-opacity" aria-hidden="true">
                      (click to edit)
                    </span>
                  </p>
                )}
              </div>

              {!isEditing && (
                <div className="flex-shrink-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleCopy(segment.text, originalIndex)}
                    title="Copy segment text"
                    aria-label={copiedIndex === originalIndex ? "Text copied" : "Copy segment text"}
                    className={`p-1.5 rounded hover:bg-slate-700 transition-all focus-visible:opacity-100 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500
                      ${copiedIndex === originalIndex ? 'text-green-400 opacity-100' : 'text-slate-500'}`}
                  >
                    {copiedIndex === originalIndex ? (
                      <svg aria-hidden="true" className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg aria-hidden="true" className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                      </svg>
                    )}
                  </button>

                  <button
                    onClick={() => handleDelete(originalIndex)}
                    title="Delete segment"
                    aria-label="Delete this segment"
                    className="p-1.5 rounded hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-all focus-visible:opacity-100 outline-none focus-visible:ring-2 focus-visible:ring-red-500"
                  >
                    <svg aria-hidden="true" className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
};

export default TranscriptDisplay;
