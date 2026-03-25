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
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem', marginBottom: '0.25rem', color: 'var(--color-text-secondary)' }}>
        {icon}
        <span style={{ fontSize: '0.875rem' }}>{label}</span>
      </div>
      <div className={`metric-value ${valueClass}`}>{value}</div>
    </div>
  );
};
