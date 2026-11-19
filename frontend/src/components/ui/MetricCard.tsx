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
  const valueClass = positive ? 'metric-positive' : negative ? 'metric-negative' : '';

  return (
    <div className="metric-card">
      <div className="metric-card-head">
        <div className="metric-label">{label}</div>
        {icon && <div className="metric-icon">{icon}</div>}
      </div>
      <div className={`metric-value ${valueClass}`}>{value}</div>
      {subtext && <div className="metric-sub">{subtext}</div>}
    </div>
  );
};
