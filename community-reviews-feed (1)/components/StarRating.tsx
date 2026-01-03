
import React, { useState } from 'react';

interface StarRatingProps {
  rating: number;
  max?: number;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
  editable?: boolean;
  onChange?: (rating: number) => void;
}

const StarRating: React.FC<StarRatingProps> = ({ 
  rating, 
  max = 5, 
  size = 'md',
  className = '',
  editable = false,
  onChange
}) => {
  const [hoverRating, setHoverRating] = useState(0);

  const sizeClasses = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-8 h-8'
  };

  const handleStarClick = (value: number) => {
    if (editable && onChange) {
      onChange(value);
    }
  };

  const stars = [];
  const currentRating = hoverRating || rating;

  for (let i = 1; i <= max; i++) {
    const isFull = i <= currentRating;
    const isHalf = !isFull && i - 0.5 <= currentRating;

    stars.push(
      <div 
        key={i} 
        className={`relative ${editable ? 'cursor-pointer transform hover:scale-110 transition-transform' : ''}`}
        onMouseEnter={() => editable && setHoverRating(i)}
        onMouseLeave={() => editable && setHoverRating(0)}
        onClick={() => handleStarClick(i)}
      >
        <svg 
          className={`${sizeClasses[size]} text-gray-300`} 
          fill="currentColor" 
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
        {isFull && (
          <svg 
            className={`${sizeClasses[size]} text-yellow-400 absolute inset-0`} 
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        )}
        {isHalf && (
          <div className="absolute inset-0 overflow-hidden w-1/2 pointer-events-none">
            <svg 
              className={`${sizeClasses[size]} text-yellow-400`} 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-0.5 ${className}`} aria-label={`Rating: ${rating} out of ${max} stars`}>
      {stars}
      {!editable && <span className="ml-2 text-sm font-medium text-gray-600">{rating.toFixed(1)}</span>}
    </div>
  );
};

export default StarRating;
