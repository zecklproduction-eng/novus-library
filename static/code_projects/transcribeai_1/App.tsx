
import React, { useState, useRef, useEffect } from 'react';
import { AppStatus, TranscriptionResponse, TranscriptSegment, PendingFile } from './types';
import { transcribeAudio } from './services/geminiService';
import FileUploader from './components/FileUploader';
import FileList from './components/FileList';
import TranscriptDisplay from './components/TranscriptDisplay';
import ProgressBar from './components/ProgressBar';

const App: React.FC = () => {
  const [status, setStatus] = useState<AppStatus>(AppStatus.IDLE);
  const [error, setError] = useState<string | null>(null);
  const [transcription, setTranscription] = useState<TranscriptionResponse | null>(null);
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [processingProgress, setProcessingProgress] = useState(0);
  
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCopyingAll, setIsCopyingAll] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  
  const audioRef = useRef<HTMLAudioElement>(null);

  // Sync playback speed with audio element
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackSpeed;
    }
  }, [playbackSpeed, currentFileIndex, transcription]);

  const handleFilesSelect = async (files: FileList) => {
    const newPending: PendingFile[] = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const previewUrl = URL.createObjectURL(file);
      
      // Get duration
      const tempAudio = new Audio(previewUrl);
      const duration = await new Promise<number>((resolve) => {
        tempAudio.onloadedmetadata = () => resolve(tempAudio.duration);
        tempAudio.onerror = () => resolve(0);
      });

      newPending.push({
        id: Math.random().toString(36).substring(7),
        file,
        duration,
        previewUrl
      });
    }

    setPendingFiles(prev => [...prev, ...newPending]);
  };

  const removeFile = (id: string) => {
    setPendingFiles(prev => {
      const filtered = prev.filter(f => f.id !== id);
      const removed = prev.find(f => f.id === id);
      if (removed) URL.revokeObjectURL(removed.previewUrl);
      return filtered;
    });
  };

  const moveFile = (id: string, direction: 'up' | 'down') => {
    setPendingFiles(prev => {
      const idx = prev.findIndex(f => f.id === id);
      if (idx === -1) return prev;
      const newArr = [...prev];
      const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
      if (targetIdx < 0 || targetIdx >= newArr.length) return prev;
      [newArr[idx], newArr[targetIdx]] = [newArr[targetIdx], newArr[idx]];
      return newArr;
    });
  };

  const startBatchTranscription = async () => {
    if (pendingFiles.length === 0) return;

    setStatus(AppStatus.TRANSCRIBING);
    setProcessingProgress(0);
    setError(null);

    const allSegments: TranscriptSegment[] = [];
    const summaries: string[] = [];
    let cumulativeOffset = 0;

    try {
      for (let i = 0; i < pendingFiles.length; i++) {
        const item = pendingFiles[i];
        setCurrentFileIndex(i);
        
        // Convert to base64
        const base64Data = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve((reader.result as string).split(',')[1]);
          reader.onerror = reject;
          reader.readAsDataURL(item.file);
        });

        const result = await transcribeAudio(base64Data, item.file.type);
        
        // Adjust timestamps for sequencing
        const adjustedSegments = result.segments.map(seg => {
          const newStart = seg.startSeconds + cumulativeOffset;
          const newEnd = seg.endSeconds + cumulativeOffset;
          return {
            ...seg,
            startSeconds: newStart,
            endSeconds: newEnd,
            startTime: formatTime(newStart),
            endTime: formatTime(newEnd)
          };
        });

        allSegments.push(...adjustedSegments);
        if (result.summary) summaries.push(result.summary);
        
        cumulativeOffset += item.duration;
        setProcessingProgress(Math.round(((i + 1) / pendingFiles.length) * 100));
      }

      setTranscription({
        segments: allSegments,
        summary: summaries.join(' | ')
      });
      setDuration(cumulativeOffset);
      setStatus(AppStatus.COMPLETED);
      setCurrentFileIndex(0); // For playback
    } catch (err: any) {
      setError(err.message || "An error occurred during sequential processing.");
      setStatus(AppStatus.ERROR);
    }
  };

  const formatTime = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = Math.floor(totalSeconds % 60);
    
    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTimeUpdate = () => {
    if (!audioRef.current || !pendingFiles.length) return;
    
    // Calculate global time
    let previousDurations = 0;
    for (let i = 0; i < currentFileIndex; i++) {
      previousDurations += pendingFiles[i].duration;
    }
    setCurrentTime(previousDurations + audioRef.current.currentTime);
  };

  const handleAudioEnded = () => {
    if (currentFileIndex < pendingFiles.length - 1) {
      setCurrentFileIndex(prev => prev + 1);
      // Wait for next render to play the new source
      setTimeout(() => {
        audioRef.current?.play();
      }, 50);
    }
  };

  const jumpToTime = (seconds: number) => {
    let accumulated = 0;
    let targetFileIndex = 0;
    let targetInternalTime = 0;

    for (let i = 0; i < pendingFiles.length; i++) {
      if (seconds >= accumulated && seconds < accumulated + pendingFiles[i].duration) {
        targetFileIndex = i;
        targetInternalTime = seconds - accumulated;
        break;
      }
      accumulated += pendingFiles[i].duration;
    }

    if (targetFileIndex === currentFileIndex) {
      if (audioRef.current) {
        audioRef.current.currentTime = targetInternalTime;
        audioRef.current.play();
      }
    } else {
      setCurrentFileIndex(targetFileIndex);
      setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.currentTime = targetInternalTime;
          audioRef.current.play();
        }
      }, 100);
    }
  };

  const updateSegmentText = (index: number, newText: string) => {
    if (!transcription) return;
    const newSegments = [...transcription.segments];
    newSegments[index] = { ...newSegments[index], text: newText };
    setTranscription({ ...transcription, segments: newSegments });
  };

  const deleteSegment = (index: number) => {
    if (!transcription) return;
    const newSegments = transcription.segments.filter((_, i) => i !== index);
    setTranscription({ ...transcription, segments: newSegments });
  };

  const downloadTranscript = (format: 'text' | 'json' | 'srt' | 'vtt') => {
    if (!transcription) return;

    let content = "";
    const baseName = "unified-transcript";
    let fileName = `${baseName}.${format === 'text' ? 'txt' : format}`;
    let mimeType = 'text/plain';

    if (format === 'json') {
      content = JSON.stringify({
        summary: transcription.summary,
        segments: transcription.segments
      }, null, 2);
      mimeType = 'application/json';
    } else if (format === 'srt') {
      mimeType = 'application/x-subrip';
      content = transcription.segments.map((s, i) => {
        const start = formatTimestamp(s.startSeconds, 'srt');
        const end = formatTimestamp(s.endSeconds, 'srt');
        return `${i + 1}\n${start} --> ${end}\n${s.text}\n`;
      }).join('\n');
    } else if (format === 'vtt') {
      mimeType = 'text/vtt';
      const header = "WEBVTT\n\n";
      const body = transcription.segments.map((s) => {
        const start = formatTimestamp(s.startSeconds, 'vtt');
        const end = formatTimestamp(s.endSeconds, 'vtt');
        return `${start} --> ${end}\n${s.text}\n`;
      }).join('\n');
      content = header + body;
    } else {
      content = transcription.segments
        .map(s => `[${s.startTime} - ${s.endTime}] ${s.text}`)
        .join('\n');
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(url);
  };

  const formatTimestamp = (totalSeconds: number, format: 'srt' | 'vtt') => {
    const hh = Math.floor(totalSeconds / 3600).toString().padStart(2, '0');
    const mm = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, '0');
    const ss = Math.floor(totalSeconds % 60).toString().padStart(2, '0');
    const ms = Math.floor((totalSeconds % 1) * 1000).toString().padStart(3, '0');
    const separator = format === 'srt' ? ',' : '.';
    return `${hh}:${mm}:${ss}${separator}${ms}`;
  };

  const copyFullTranscript = () => {
    if (!transcription) return;
    const text = transcription.segments
      .map(s => `[${s.startTime} - ${s.endTime}] ${s.text}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setIsCopyingAll(true);
    setTimeout(() => setIsCopyingAll(false), 2000);
  };

  const reset = () => {
    pendingFiles.forEach(f => URL.revokeObjectURL(f.previewUrl));
    setTranscription(null);
    setPendingFiles([]);
    setStatus(AppStatus.IDLE);
    setError(null);
    setCurrentTime(0);
    setDuration(0);
    setCurrentFileIndex(0);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-600/20">T</div>
            <h1 className="text-xl font-bold tracking-tight">TranscribeAI</h1>
          </div>
          {status !== AppStatus.IDLE && (
            <button onClick={reset} className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Start New Project</button>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full p-4 md:p-8">
        {status === AppStatus.IDLE && (
          <div className="max-w-2xl mx-auto py-8">
            <div className="text-center mb-10">
              <h2 className="text-4xl font-extrabold text-white mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">Sequential Transcription</h2>
              <p className="text-slate-400 text-lg">Upload multiple files to generate a single unified transcript with continuous timestamps across all tracks.</p>
            </div>
            <FileUploader onFilesSelect={handleFilesSelect} disabled={false} />
            <FileList 
              files={pendingFiles} 
              onRemove={removeFile} 
              onMove={moveFile} 
              disabled={false} 
            />
            {pendingFiles.length > 0 && (
              <button 
                onClick={startBatchTranscription}
                className="w-full mt-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-xl shadow-indigo-600/20 transition-all transform hover:scale-[1.01] active:scale-[0.99]"
              >
                Generate Unified Transcript for {pendingFiles.length} {pendingFiles.length === 1 ? 'File' : 'Files'}
              </button>
            )}
          </div>
        )}

        {status === AppStatus.TRANSCRIBING && (
          <div className="max-w-md mx-auto py-24 text-center space-y-8">
            <div className="relative inline-block">
              <div className="w-24 h-24 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center font-bold text-indigo-400">{processingProgress}%</div>
            </div>
            <div className="space-y-3">
              <h3 className="text-2xl font-bold text-white">Processing Sequence...</h3>
              <p className="text-slate-400">Transcribing part {currentFileIndex + 1} of {pendingFiles.length}</p>
              <p className="text-xs text-slate-500 italic truncate max-w-xs mx-auto">"{pendingFiles[currentFileIndex].file.name}"</p>
              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden mt-6">
                <div className="bg-indigo-500 h-full transition-all duration-500" style={{ width: `${processingProgress}%` }} />
              </div>
            </div>
          </div>
        )}

        {status === AppStatus.ERROR && (
          <div className="max-w-lg mx-auto py-12 text-center bg-red-500/10 border border-red-500/20 rounded-2xl p-8">
            <h3 className="text-xl font-bold text-white mb-4">Transcription Failed</h3>
            <p className="text-red-400 mb-6">{error}</p>
            <button onClick={reset} className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg">Try Again</button>
          </div>
        )}

        {status === AppStatus.COMPLETED && transcription && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Sidebar with Unified Controls */}
            <div className="lg:col-span-5 space-y-6 lg:sticky lg:top-24">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                <div className="p-6 space-y-6">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Unified Playback</span>
                    <h3 className="text-lg font-bold text-white truncate">{pendingFiles[currentFileIndex].file.name}</h3>
                    <p className="text-xs text-slate-500 mt-1">Part {currentFileIndex + 1} of {pendingFiles.length} in sequence</p>
                  </div>

                  <audio 
                    ref={audioRef}
                    src={pendingFiles[currentFileIndex].previewUrl} 
                    controls 
                    className="w-full"
                    onTimeUpdate={handleTimeUpdate}
                    onEnded={handleAudioEnded}
                  />

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mr-1">Playback:</span>
                    {[0.5, 1, 1.25, 1.5, 2].map(speed => (
                      <button
                        key={speed}
                        onClick={() => setPlaybackSpeed(speed)}
                        className={`px-2 py-1 text-xs font-mono rounded-md transition-all border ${
                          playbackSpeed === speed ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
                        }`}
                      >
                        {speed}x
                      </button>
                    ))}
                  </div>

                  {transcription.summary && (
                    <div className="pt-6 border-t border-slate-800">
                      <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Context Summary</span>
                      <p className="mt-2 text-slate-300 text-sm italic leading-relaxed">"{transcription.summary}"</p>
                    </div>
                  )}
                </div>

                <div className="bg-slate-800/40 p-6 space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Unified Export</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <button 
                      onClick={() => downloadTranscript('text')} 
                      className="px-2 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex flex-col items-center gap-1 transition-all"
                      title="Export as Text with timestamps"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                      .TXT
                    </button>
                    <button 
                      onClick={() => downloadTranscript('srt')} 
                      className="px-2 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold rounded-lg flex flex-col items-center gap-1 transition-all"
                      title="Export as industry standard SRT subtitles"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l-3 3m0 0l-3-3m3 3V4m0 13v4" /></svg>
                      .SRT
                    </button>
                    <button 
                      onClick={() => downloadTranscript('vtt')} 
                      className="px-2 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold rounded-lg flex flex-col items-center gap-1 transition-all"
                      title="Export as WebVTT for online players"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      .VTT
                    </button>
                    <button 
                      onClick={() => downloadTranscript('json')} 
                      className="px-2 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold rounded-lg flex flex-col items-center gap-1 transition-all"
                      title="Export raw data as JSON"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2H6c-1.1 0-2 .9-2 2zm14 10H6V7h12v10zM8 9h8v2H8V9zm0 4h5v2H8v-2z" /></svg>
                      .JSON
                    </button>
                  </div>
                  <button 
                    onClick={copyFullTranscript}
                    className={`w-full px-4 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 border 
                      ${isCopyingAll ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-200'}`}
                  >
                    {isCopyingAll ? (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                        Copied Unified Transcript!
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
                        Copy All Segments
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Transcript Area */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  Unified Transcript
                  <span className="text-xs font-normal px-2 py-0.5 bg-slate-800 rounded-full text-slate-400">{transcription.segments.length} segments</span>
                </h3>
                <div className="relative w-full md:w-64">
                  <input 
                    type="text" 
                    placeholder="Search unified transcript..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  />
                  <div className="absolute right-3 top-2.5 text-slate-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                  </div>
                </div>
              </div>

              <ProgressBar currentTime={currentTime} duration={duration} onSeek={jumpToTime} />

              <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-2 min-h-[500px] shadow-inner">
                <TranscriptDisplay 
                  segments={transcription.segments} 
                  currentTime={currentTime}
                  onJumpToTime={jumpToTime}
                  onUpdateSegment={updateSegmentText}
                  onDeleteSegment={deleteSegment}
                  searchQuery={searchQuery}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="py-8 border-t border-slate-900 text-center text-slate-600 text-sm">
        <p>© 2024 TranscribeAI. Sequential Batch Processing with Unified Export enabled.</p>
      </footer>
    </div>
  );
};

export default App;
