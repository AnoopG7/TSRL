import React, { useState, useMemo } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis, Cell, ReferenceLine
} from 'recharts';
import { Target, TrendingUp, BarChart3, Award } from 'lucide-react';

type ParamValue = string | number | boolean;

interface ParameterSensitivityChartProps {
  results: { params: Record<string, ParamValue>; score: number }[];
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

// Stats card component
const StatCard: React.FC<{ label: string; value: string; subtext?: string; icon: React.ReactNode; highlight?: boolean }> = ({
  label, value, subtext, icon, highlight
}) => (
  <div className={`chart-stat-card ${highlight ? 'highlight' : ''}`}>
    <div className={`chart-stat-icon ${highlight ? 'positive' : ''}`}>{icon}</div>
    <div className="chart-stat-content">
      <span className="chart-stat-label">{label}</span>
      <span className={`chart-stat-value ${highlight ? 'positive' : ''}`}>{value}</span>
      {subtext && <span className="chart-stat-subtext">{subtext}</span>}
    </div>
  </div>
);

export const ParameterSensitivityChart: React.FC<ParameterSensitivityChartProps> = ({
  results, parameterKeys, metricName
}) => {
  const [selectedParam, setSelectedParam] = useState<string>(parameterKeys[0] || '');
  const [showMedianLine, setShowMedianLine] = useState(true);

  const { data, minScore, maxScore, bestPoint, stats } = useMemo(() => {
    if (!results || results.length === 0 || !selectedParam) {
      return { data: [], minScore: 0, maxScore: 1, bestPoint: null, stats: null };
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

    // Calculate stats
    const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    const sortedScores = [...scores].sort((a, b) => a - b);
    const medianScore = sortedScores[Math.floor(sortedScores.length / 2)];
    const stdDev = Math.sqrt(scores.reduce((sum, s) => sum + Math.pow(s - avgScore, 2), 0) / scores.length);
    const topQuartile = sortedScores[Math.floor(sortedScores.length * 0.75)];

    return {
      data: formatted,
      minScore: min,
      maxScore: max,
      bestPoint: best,
      stats: {
        avgScore,
        medianScore,
        stdDev,
        topQuartile,
        totalResults: results.length
      }
    };
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
        {/* Stats Bar */}
        {stats && (
          <div className="chart-stats-bar" style={{ marginBottom: 'var(--spacing-md)' }}>
            <StatCard
              label="Best Score"
              value={maxScore.toFixed(4)}
              icon={<Award size={16} />}
              highlight
            />
            <StatCard
              label="Avg Score"
              value={stats.avgScore.toFixed(4)}
              icon={<BarChart3 size={16} />}
            />
            <StatCard
              label="Std Deviation"
              value={stats.stdDev.toFixed(4)}
              subtext={`±${((stats.stdDev / stats.avgScore) * 100).toFixed(1)}%`}
              icon={<TrendingUp size={16} />}
            />
            <StatCard
              label="Total Configs"
              value={stats.totalResults.toString()}
              icon={<Target size={16} />}
            />
          </div>
        )}

        {/* Chart Controls */}
        <div className="chart-controls">
          <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
            {parameterKeys.slice(0, 4).map(k => (
              <button
                key={k}
                className={`chart-control-btn ${selectedParam === k ? 'active' : ''}`}
                onClick={() => setSelectedParam(k)}
                style={{ fontSize: '0.7rem' }}
              >
                {formatParamName(k)}
              </button>
            ))}
          </div>
          <label className="chart-control-toggle">
            <input
              type="checkbox"
              checked={showMedianLine}
              onChange={(e) => setShowMedianLine(e.target.checked)}
            />
            <span>Show Median</span>
          </label>
        </div>

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
                <linearGradient id="scoreGradient" x1="0" y1="1" x2="0" y2="0">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={0.1} />
                  <stop offset="50%" stopColor="#fbbf24" stopOpacity={0.1} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0.1} />
                </linearGradient>
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

              {/* Median reference line */}
              {showMedianLine && stats && (
                <ReferenceLine
                  y={stats.medianScore}
                  stroke="var(--color-accent-400)"
                  strokeDasharray="5 5"
                  strokeOpacity={0.6}
                  label={{
                    value: `Median: ${stats.medianScore.toFixed(3)}`,
                    position: 'insideTopRight',
                    fontSize: 10,
                    fill: 'var(--color-accent-400)'
                  }}
                />
              )}

              {/* Top quartile line */}
              {stats && (
                <ReferenceLine
                  y={stats.topQuartile}
                  stroke="var(--color-success-500)"
                  strokeDasharray="3 3"
                  strokeOpacity={0.4}
                />
              )}

              <Tooltip
                cursor={{ strokeDasharray: '3 3', stroke: 'var(--color-accent-400)' }}
                position={{ x: 100, y: 10 }}
                wrapperStyle={{ pointerEvents: 'none' }}
                content={({ active, payload }) => {
                  if (!active || !payload || !payload.length) return null;
                  const d = payload[0].payload;
                  const isBest = d === bestPoint;
                  const percentile = stats ? ((d.y - minScore) / (maxScore - minScore) * 100).toFixed(0) : '0';
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
                      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                        Top {100 - Number(percentile)}% of results
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

        {/* Best configuration annotation */}
        {bestPoint && (
          <div className="chart-annotation">
            <span className="chart-annotation-label">Best configuration:</span>
            <span className="chart-annotation-value">
              {formatParamName(selectedParam)} = {bestPoint.x}, Score = {bestPoint.y.toFixed(4)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
