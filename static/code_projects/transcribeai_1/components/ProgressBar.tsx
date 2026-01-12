
import React, { useRef, useEffect, useState } from 'react';

interface ProgressBarProps {
  currentTime: number;
  duration: number;
  onSeek: (seconds: number) => void;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ currentTime, duration, onSeek }) => {
  const barRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  const handleInteraction = (e: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent) => {
    if (!barRef.current || duration === 0) return;

    const rect = barRef.current.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : (e as MouseEvent).clientX;
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percentage = x / rect.width;
    onSeek(percentage * duration);
  };

  const onMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    handleInteraction(e);
  };

  useEffect(() => {
    if (!isDragging) return;

    const onMouseMove = (e: MouseEvent) => handleInteraction(e);
    const onMouseUp = () => setIsDragging(false);

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('touchmove', onMouseMove);
    window.addEventListener('touchend', onMouseUp);

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onMouseMove);
      window.removeEventListener('touchend', onMouseUp);
    };
  }, [isDragging, duration]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-2 mb-6 group">
      <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-slate-500">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>
      <div 
        ref={barRef}
        onMouseDown={onMouseDown}
        onTouchStart={(e) => { setIsDragging(true); handleInteraction(e); }}
        className="relative h-2 w-full bg-slate-800 rounded-full cursor-pointer overflow-hidden transition-all group-hover:h-3"
      >
        {/* Background Track Fill */}
        <div 
          className="absolute top-0 left-0 h-full bg-indigo-600 rounded-full shadow-[0_0_15px_rgba(79,70,229,0.4)] transition-all duration-100 ease-out"
          style={{ width: `${progress}%` }}
        />
        
        {/* Interactive Hover Highlight */}
        <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity" />
      </div>
    </div>
  );
};

export default ProgressBar;
