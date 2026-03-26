import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  icon?: React.ReactNode;
  positive?: boolean;
  negative?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, icon, positive, negative }) => {
  let valueClass = '';
  if (positive) valueClass = 'metric-positive';
  if (negative) valueClass = 'metric-negative';

  return (
    <div className="metric-card">
      {icon && (
        <div className="metric-icon">
          {icon}
        </div>
      )}
      <div style={{
        fontSize: '0.875rem',
        color: 'var(--color-text-secondary)',
        marginBottom: '0.25rem'
      }}>
        {label}
      </div>
      <div className={`metric-value ${valueClass}`}>{value}</div>
    </div>
  );
};
