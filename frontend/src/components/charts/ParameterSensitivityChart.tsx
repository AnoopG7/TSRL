import React, { useState, useMemo } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis, Cell
} from 'recharts';

interface ParameterSensitivityChartProps {
  results: { params: Record<string, any>; score: number }[];
  parameterKeys: string[];
  metricName: string;
}

// Color scale from red (low) to green (high)
const getScoreColor = (score: number, min: number, max: number): string => {
  const range = max - min;
  if (range === 0) return '#14b8a6';

  const normalized = (score - min) / range;

  if (normalized < 0.2) return '#ef4444';
  if (normalized < 0.4) return '#f97316';
  if (normalized < 0.5) return '#fbbf24';
  if (normalized < 0.6) return '#84cc16';
  if (normalized < 0.8) return '#22c55e';
  return '#15803d';
};

export const ParameterSensitivityChart: React.FC<ParameterSensitivityChartProps> = ({
  results, parameterKeys, metricName
}) => {
  const [selectedParam, setSelectedParam] = useState<string>(parameterKeys[0] || '');

  const { data, minScore, maxScore, bestPoint } = useMemo(() => {
    if (!results || results.length === 0 || !selectedParam) {
      return { data: [], minScore: 0, maxScore: 1, bestPoint: null };
    }

    const formatted = results.map(r => ({
      x: typeof r.params[selectedParam] === 'number' ? r.params[selectedParam] : String(r.params[selectedParam]),
      y: r.score,
      ...r.params
    }));

    const scores = results.map(r => r.score);
    const min = Math.min(...scores);
    const max = Math.max(...scores);
    const best = formatted.reduce((b, p) => p.y > (b?.y ?? -Infinity) ? p : b, formatted[0]);

    return { data: formatted, minScore: min, maxScore: max, bestPoint: best };
  }, [results, selectedParam]);

  if (!results || results.length === 0 || !selectedParam) return null;

  // Identify type of axis based on data
  const isNumericX = data.every(d => typeof d.x === 'number');

  const formatParamName = (key: string) => {
    return key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  return (
    <div className="card" style={{ marginTop: 'var(--spacing-lg)' }}>
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
        <div>
          <h3 className="card-title">Parameter Sensitivity</h3>
          <p className="card-description">Explore how parameter values affect {formatParamName(metricName)}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>Parameter:</label>
          <select
            className="form-input"
            style={{ width: 'auto', padding: '0.5rem 2rem 0.5rem 0.75rem', minWidth: '160px' }}
            value={selectedParam}
            onChange={e => setSelectedParam(e.target.value)}
          >
            {parameterKeys.map(k => (
              <option key={k} value={k}>{formatParamName(k)}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="card-content" style={{ paddingBottom: '0.5rem' }}>
        <div style={{ height: 380 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 30 }}>
              <defs>
                <filter id="scatterGlow">
                  <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-default)" opacity={0.4} />
              <XAxis
                type={isNumericX ? "number" : "category"}
                dataKey="x"
                name={selectedParam}
                tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
                stroke="var(--color-border-default)"
                domain={isNumericX ? ['auto', 'auto'] : undefined}
                label={{
                  value: formatParamName(selectedParam),
                  position: 'bottom',
                  offset: 0,
                  fontSize: 12,
                  fill: 'var(--color-text-secondary)'
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name={metricName}
                tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
                stroke="var(--color-border-default)"
                domain={['auto', 'auto']}
                label={{
                  value: formatParamName(metricName),
                  angle: -90,
                  position: 'insideLeft',
                  offset: 10,
                  fontSize: 12,
                  fill: 'var(--color-text-secondary)'
                }}
              />
              <ZAxis type="number" range={[80, 200]} />
              <Tooltip
                cursor={{ strokeDasharray: '3 3', stroke: 'var(--color-accent-400)' }}
                content={({ active, payload }) => {
                  if (!active || !payload || !payload.length) return null;
                  const d = payload[0].payload;
                  const isBest = d === bestPoint;
                  return (
                    <div className="chart-tooltip" style={{ minWidth: '180px' }}>
                      <div className="chart-tooltip-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>Score</span>
                        {isBest && <span className="chart-tooltip-badge">Best</span>}
                      </div>
                      <div className="chart-tooltip-score" style={{
                        fontSize: '1.5rem',
                        fontWeight: 700,
                        color: getScoreColor(d.y, minScore, maxScore),
                        marginBottom: '0.5rem'
                      }}>
                        {typeof d.y === 'number' ? d.y.toFixed(4) : d.y}
                      </div>
                      <div className="chart-tooltip-divider" />
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '0.5rem' }}>
                        {Object.entries(d).map(([k, v]) => {
                          if (k !== 'x' && k !== 'y') {
                            return (
                              <div key={k} className="chart-tooltip-row">
                                <span className="chart-tooltip-label">{formatParamName(k)}</span>
                                <span className="chart-tooltip-value">{String(v)}</span>
                              </div>
                            );
                          }
                          return null;
                        })}
                      </div>
                    </div>
                  );
                }}
              />
              <Scatter name="Results" data={data} filter="url(#scatterGlow)">
                {data.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={getScoreColor(entry.y, minScore, maxScore)}
                    opacity={entry === bestPoint ? 1 : 0.7}
                    stroke={entry === bestPoint ? '#fff' : 'none'}
                    strokeWidth={entry === bestPoint ? 2 : 0}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Color scale legend */}
        <div className="chart-legend">
          <span className="chart-legend-label">Lower Score</span>
          <div className="chart-legend-scale">
            <div className="chart-legend-gradient" style={{
              background: 'linear-gradient(to right, #ef4444, #f97316, #fbbf24, #84cc16, #22c55e, #15803d)'
            }} />
          </div>
          <span className="chart-legend-label">Higher Score</span>
        </div>
      </div>
    </div>
  );
};
