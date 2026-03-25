import React, { useState } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis
} from 'recharts';

interface ParameterSensitivityChartProps {
  results: { params: Record<string, any>; score: number }[];
  parameterKeys: string[];
  metricName: string;
}

export const ParameterSensitivityChart: React.FC<ParameterSensitivityChartProps> = ({ 
  results, parameterKeys, metricName 
}) => {
  const [selectedParam, setSelectedParam] = useState<string>(parameterKeys[0] || '');

  if (!results || results.length === 0 || !selectedParam) return null;

  // Format data for Recharts ScatterPlot
  const data = results.map(r => ({
    x: typeof r.params[selectedParam] === 'number' ? r.params[selectedParam] : String(r.params[selectedParam]),
    y: r.score,
    ...r.params
  }));

  // Identify type of axis based on data
  const isNumericX = data.every(d => typeof d.x === 'number');

  return (
    <div className="card" style={{ marginTop: 'var(--spacing-lg)' }}>
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="card-title">Parameter Sensitivity</h3>
        <select 
          className="form-input" 
          style={{ width: 'auto', padding: '0.25rem 2rem 0.25rem 0.5rem', minWidth: '150px' }}
          value={selectedParam} 
          onChange={e => setSelectedParam(e.target.value)}
        >
          {parameterKeys.map(k => (
            <option key={k} value={k}>{k.replace('_', ' ').toUpperCase()}</option>
          ))}
        </select>
      </div>
      <div className="card-content" style={{ height: 350 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.5} />
            <XAxis 
              type={isNumericX ? "number" : "category"} 
              dataKey="x" 
              name={selectedParam} 
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
              stroke="var(--color-border)"
              domain={isNumericX ? ['auto', 'auto'] : undefined}
            />
            <YAxis 
              type="number" 
              dataKey="y" 
              name={metricName} 
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
              stroke="var(--color-border)"
              domain={['auto', 'auto']}
              label={{ value: metricName.replace('_', ' ').toUpperCase(), angle: -90, position: 'insideLeft', fill: 'var(--color-text-secondary)' }}
            />
            <ZAxis type="number" range={[60, 60]} />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div style={{ background: 'var(--color-bg-tertiary)', padding: 'var(--spacing-md)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                      <p style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px' }}>Score: {typeof d.y === 'number' ? d.y.toFixed(4) : d.y}</p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {Object.entries(d).map(([k, v]) => {
                          if (k !== 'x' && k !== 'y') {
                            return <span key={k} style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}><strong>{k}:</strong> {String(v)}</span>;
                          }
                          return null;
                        })}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Scatter name="Results" data={data} fill="var(--color-accent-500)" opacity={0.7} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
