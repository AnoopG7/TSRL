import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  icon?: React.ReactNode;
  positive?: boolean;
  negative?: boolean;
  subtext?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, icon, positive, negative, subtext }) => {
  let valueClass = '';
  if (positive) valueClass = 'metric-positive';
  if (negative) valueClass = 'metric-negative';

  return (
    <div className="metric-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
          <div style={{
            fontSize: '0.875rem',
            color: 'var(--color-text-secondary)',
            marginBottom: '0.25rem'
          }}>
            {label}
          </div>
          <div className={`metric-value ${valueClass}`}>{value}</div>
          {subtext && (
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
              {subtext}
            </div>
          )}
        </div>
        {icon && (
          <div className="metric-icon" style={{ marginLeft: 'var(--spacing-sm)' }}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};
