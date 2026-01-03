
import React from 'react';

const ReviewSkeleton = () => (
  <div className="bg-white rounded-xl border border-slate-100 p-6 flex gap-6 animate-pulse">
    <div className="flex-shrink-0 w-32 aspect-[2/3] bg-slate-100 rounded-lg" />
    <div className="flex-grow space-y-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-slate-100" />
          <div className="space-y-2">
            <div className="h-3 w-24 bg-slate-100 rounded" />
            <div className="h-2 w-16 bg-slate-100 rounded" />
          </div>
        </div>
        <div className="h-4 w-20 bg-slate-100 rounded" />
      </div>
      <div className="h-5 w-48 bg-slate-100 rounded" />
      <div className="space-y-2">
        <div className="h-3 w-full bg-slate-100 rounded" />
        <div className="h-3 w-full bg-slate-100 rounded" />
        <div className="h-3 w-2/3 bg-slate-100 rounded" />
      </div>
      <div className="flex gap-2">
        <div className="h-4 w-12 bg-slate-100 rounded-full" />
        <div className="h-4 w-12 bg-slate-100 rounded-full" />
      </div>
    </div>
  </div>
);

export const ReviewListSkeleton = () => (
  <div className="space-y-4">
    {[1, 2, 3].map(i => <ReviewSkeleton key={i} />)}
  </div>
);
