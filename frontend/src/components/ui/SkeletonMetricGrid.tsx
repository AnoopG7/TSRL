import React from 'react';
import { Skeleton } from './Skeleton';

interface SkeletonMetricGridProps {
  count?: number;
}

export const SkeletonMetricGrid: React.FC<SkeletonMetricGridProps> = ({
  count = 8,
}) => {
  return (
    <div className="metric-grid">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="metric-card" style={{ padding: 'var(--spacing-lg)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <Skeleton variant="circular" width={32} height={32} />
            <Skeleton width="60%" height={14} />
            <Skeleton width="80%" height={28} />
          </div>
        </div>
      ))}
    </div>
  );
};
