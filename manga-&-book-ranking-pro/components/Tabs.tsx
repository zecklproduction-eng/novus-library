
import React from 'react';
import { ContentType } from '../types';

interface TabsProps {
  activeType: ContentType;
  types: ContentType[];
  onChange: (type: ContentType) => void;
}

const Tabs: React.FC<TabsProps> = ({ activeType, types, onChange }) => {
  return (
    <div className="flex items-center space-x-1.5 p-1.5 bg-gray-900/90 rounded-2xl w-fit border border-gray-800 shadow-2xl backdrop-blur-md">
      {types.map((type) => (
        <button
          key={type}
          onClick={() => onChange(type)}
          className={`px-12 py-3 rounded-xl text-xs font-black uppercase tracking-[0.1em] transition-all duration-500 transform active:scale-95 relative overflow-hidden group ${
            activeType === type
              ? 'bg-red-600 text-white shadow-[0_10px_25px_-5px_rgba(220,38,38,0.4)]'
              : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
          }`}
        >
          <span className="relative z-10">{type}</span>
          {activeType === type && (
            <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent pointer-events-none animate-in fade-in duration-700" />
          )}
          {/* Subtle hover line for inactive tabs */}
          {activeType !== type && (
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-[2px] bg-red-600/50 group-hover:w-1/2 transition-all duration-300" />
          )}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
