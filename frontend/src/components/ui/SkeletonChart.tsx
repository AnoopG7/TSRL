import React from 'react';
import { Skeleton } from './Skeleton';

interface SkeletonChartProps {
  height?: number;
}

export const SkeletonChart: React.FC<SkeletonChartProps> = ({
  height = 240,
}) => {
  return (
    <div className="card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Skeleton width="30%" height={20} />
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Skeleton width={80} height={28} />
            <Skeleton width={80} height={28} />
            <Skeleton width={80} height={28} />
          </div>
        </div>
      </div>
      <div className="card-content">
        <Skeleton width="100%" height={height} />
      </div>
    </div>
  );
};
