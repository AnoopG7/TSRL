import React from 'react';
import { Skeleton } from './Skeleton';

interface SkeletonCardProps {
  showHeader?: boolean;
  lines?: number;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({
  showHeader = true,
  lines = 3,
}) => {
  return (
    <div className="card">
      {showHeader && (
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <Skeleton variant="circular" width={20} height={20} />
            <Skeleton width="60%" height={20} />
          </div>
          <Skeleton width="40%" height={14} className="mt-2" style={{ marginTop: '0.5rem' }} />
        </div>
      )}
      <div className="card-content">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton
            key={i}
            width={i === lines - 1 ? '70%' : '100%'}
            height={16}
            style={{ marginBottom: i < lines - 1 ? '0.75rem' : 0 }}
          />
        ))}
      </div>
    </div>
  );
};
