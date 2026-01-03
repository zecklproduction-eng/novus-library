
import React from 'react';
import { ReviewFiltersState, SortOption, MediaStatus } from '../types';

interface ReviewFiltersProps {
  filters: ReviewFiltersState;
  onFilterChange: (updates: Partial<ReviewFiltersState>) => void;
}

const ReviewFilters: React.FC<ReviewFiltersProps> = ({ filters, onFilterChange }) => {
  return (
    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-4 md:space-y-0 md:flex md:items-center md:gap-4 flex-wrap sticky top-4 z-10">
      {/* Search Input */}
      <div className="relative flex-grow min-w-[200px]">
        <span className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
          <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </span>
        <input 
          type="text" 
          placeholder="Search media or users..."
          className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          value={filters.search}
          onChange={(e) => onFilterChange({ search: e.target.value })}
        />
      </div>

      {/* Sort Dropdown */}
      <div className="flex flex-col sm:flex-row gap-4 items-center flex-shrink-0">
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <label className="text-xs font-bold text-slate-500 uppercase whitespace-nowrap">Sort By</label>
          <select 
            className="flex-grow sm:flex-grow-0 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={filters.sort}
            onChange={(e) => onFilterChange({ sort: e.target.value as SortOption })}
          >
            <option value={SortOption.NEWEST}>Newest</option>
            <option value={SortOption.OLDEST}>Oldest</option>
            <option value={SortOption.HIGHEST_RATED}>Highest Rated</option>
            <option value={SortOption.LOWEST_RATED}>Lowest Rated</option>
          </select>
        </div>

        {/* Rating Filter */}
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <label className="text-xs font-bold text-slate-500 uppercase whitespace-nowrap">Rating</label>
          <select 
            className="flex-grow sm:flex-grow-0 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={filters.ratingMin}
            onChange={(e) => onFilterChange({ ratingMin: Number(e.target.value) })}
          >
            <option value={0}>Any</option>
            <option value={4.5}>4.5★+</option>
            <option value={4}>4★+</option>
            <option value={3}>3★+</option>
            <option value={2}>2★+</option>
          </select>
        </div>

        {/* Status Filter */}
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <label className="text-xs font-bold text-slate-500 uppercase whitespace-nowrap">Status</label>
          <select 
            className="flex-grow sm:flex-grow-0 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={filters.status}
            onChange={(e) => onFilterChange({ status: e.target.value as MediaStatus | 'Any' })}
          >
            <option value="Any">Any</option>
            <option value={MediaStatus.COMPLETED}>Completed</option>
            <option value={MediaStatus.READING}>Reading</option>
            <option value={MediaStatus.ON_HOLD}>On-Hold</option>
          </select>
        </div>
      </div>

      {/* Spoiler Toggle */}
      <div className="flex items-center justify-between w-full md:w-auto md:border-l md:border-slate-200 md:pl-4">
        <span className="text-xs font-bold text-slate-500 uppercase md:hidden">Hide Spoilers</span>
        <button 
          onClick={() => onFilterChange({ hideSpoilers: !filters.hideSpoilers })}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${filters.hideSpoilers ? 'bg-indigo-600' : 'bg-slate-200'}`}
        >
          <span className="sr-only">Hide spoilers</span>
          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${filters.hideSpoilers ? 'translate-x-6' : 'translate-x-1'}`} />
        </button>
        <span className="hidden md:block ml-2 text-xs font-bold text-slate-500 uppercase">Hide Spoilers</span>
      </div>
    </div>
  );
};

export default ReviewFilters;
