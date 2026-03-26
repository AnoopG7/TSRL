import { useState, useMemo } from 'react';
import {
  Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Line, ComposedChart,
  ReferenceLine, Brush, ReferenceDot,
} from 'recharts';
import { TrendingUp, TrendingDown, Activity, Maximize2 } from 'lucide-react';
import type { EquityCurvePoint } from '../../lib/schemas';

interface EquityCurveChartProps {
  data: EquityCurvePoint[];
  comparisonData?: Record<string, EquityCurvePoint[]>;
  initialCapital?: number;
}

const COLORS = [
  '#6366f1', '#22c55e', '#f59e0b', '#ef4444',
  '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6',
];

const formatCurrency = (value: number) => {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
};

const formatDate = (dateStr: unknown) => {
  const d = new Date(String(dateStr));
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const formatFullDate = (dateStr: unknown) => {
  const d = new Date(String(dateStr));
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
  label?: string;
  initialCapital?: number;
  highWatermark?: number;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, initialCapital = 100000, highWatermark }) => {
  if (!active || !payload || !payload.length) return null;

  const equity = payload[0]?.value || 0;
  const returnPct = ((equity - initialCapital) / initialCapital) * 100;
  const isProfit = equity >= initialCapital;
  const drawdownFromPeak = highWatermark ? ((equity - highWatermark) / highWatermark) * 100 : 0;

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-header">{formatFullDate(label)}</div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Portfolio</span>
        <span className={`chart-tooltip-value ${isProfit ? 'positive' : 'negative'}`}>
          {formatCurrency(equity)}
        </span>
      </div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Total Return</span>
        <span className={`chart-tooltip-value ${isProfit ? 'positive' : 'negative'}`}>
          {returnPct >= 0 ? '+' : ''}{returnPct.toFixed(2)}%
        </span>
      </div>
      {highWatermark && equity < highWatermark && (
        <div className="chart-tooltip-row">
          <span className="chart-tooltip-label">From Peak</span>
          <span className="chart-tooltip-value negative">
            {drawdownFromPeak.toFixed(2)}%
          </span>
        </div>
      )}
    </div>
  );
};

// Stats card component
const StatCard: React.FC<{ label: string; value: string; icon: React.ReactNode; positive?: boolean; negative?: boolean }> = ({
  label, value, icon, positive, negative
}) => (
  <div className="chart-stat-card">
    <div className="chart-stat-icon">{icon}</div>
    <div className="chart-stat-content">
      <span className="chart-stat-label">{label}</span>
      <span className={`chart-stat-value ${positive ? 'positive' : ''} ${negative ? 'negative' : ''}`}>{value}</span>
    </div>
  </div>
);

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({
  data,
  comparisonData,
  initialCapital = 100000,
}) => {
  const [showHighWatermark, setShowHighWatermark] = useState(true);
  const [chartType, setChartType] = useState<'area' | 'line'>('area');

  // Calculate statistics and high watermark
  const stats = useMemo(() => {
    if (!data || data.length === 0) return null;

    let highWatermark = initialCapital;
    let maxDrawdown = 0;
    let maxDrawdownDate = '';
    let bestDay = { date: '', change: 0 };
    let worstDay = { date: '', change: 0 };

    const dataWithHWM = data.map((point, i) => {
      highWatermark = Math.max(highWatermark, point.equity);

      const drawdown = ((point.equity - highWatermark) / highWatermark) * 100;
      if (drawdown < maxDrawdown) {
        maxDrawdown = drawdown;
        maxDrawdownDate = point.date;
      }

      // Daily change
      if (i > 0) {
        const prevEquity = data[i - 1].equity;
        const change = ((point.equity - prevEquity) / prevEquity) * 100;
        if (change > bestDay.change) bestDay = { date: point.date, change };
        if (change < worstDay.change) worstDay = { date: point.date, change };
      }

      return { ...point, hwm: highWatermark };
    });

    const finalEquity = data[data.length - 1].equity;
    const totalReturn = ((finalEquity - initialCapital) / initialCapital) * 100;
    const peakEquity = Math.max(...data.map(d => d.equity));

    return {
      dataWithHWM,
      totalReturn,
      finalEquity,
      peakEquity,
      maxDrawdown,
      maxDrawdownDate,
      bestDay,
      worstDay,
      highWatermark: peakEquity,
    };
  }, [data, initialCapital]);

  // Comparison mode
  if (comparisonData && Object.keys(comparisonData).length > 0) {
    const strategyNames = Object.keys(comparisonData);

    const allDates = new Set<string>();
    for (const pts of Object.values(comparisonData)) {
      pts.forEach((p) => allDates.add(p.date));
    }

    const mergedData = Array.from(allDates)
      .sort()
      .map((date) => {
        const point: Record<string, number | string> = { date };
        for (const name of strategyNames) {
          const pts = comparisonData[name];
          const match = pts.find((p) => p.date === date);
          if (match) point[name] = match.equity;
        }
        return point;
      });

    return (
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={mergedData} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
            <defs>
              {strategyNames.map((name, i) => (
                <linearGradient key={name} id={`gradient-${i}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.2} />
                  <stop offset="95%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-default)" opacity={0.4} vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="var(--color-text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border-default)' }}
              interval="preserveStartEnd"
              dy={10}
            />
            <YAxis
              tickFormatter={formatCurrency}
              stroke="var(--color-text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              dx={-10}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                return (
                  <div className="chart-tooltip">
                    <div className="chart-tooltip-header">{formatFullDate(label)}</div>
                    {payload.map((entry, i) => {
                      const returnPct = ((Number(entry.value) - initialCapital) / initialCapital) * 100;
                      return (
                        <div key={i} className="chart-tooltip-row">
                          <span className="chart-tooltip-label" style={{ color: entry.color }}>
                            {entry.name}
                          </span>
                          <span className="chart-tooltip-value">
                            {formatCurrency(Number(entry.value))}
                            <span style={{ fontSize: '0.7rem', marginLeft: '4px', color: returnPct >= 0 ? 'var(--color-success-500)' : 'var(--color-danger-500)' }}>
                              ({returnPct >= 0 ? '+' : ''}{returnPct.toFixed(1)}%)
                            </span>
                          </span>
                        </div>
                      );
                    })}
                  </div>
                );
              }}
            />
            <Legend
              wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }}
              iconType="line"
            />
            <ReferenceLine
              y={initialCapital}
              stroke="var(--color-text-muted)"
              strokeDasharray="5 5"
              strokeOpacity={0.5}
            />
            {strategyNames.map((name, i) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 6, strokeWidth: 2, stroke: 'var(--color-bg-card)' }}
                name={name}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (!stats) return null;

  const { dataWithHWM, totalReturn, finalEquity, peakEquity, maxDrawdown, bestDay, worstDay } = stats;
  const isProfit = totalReturn >= 0;

  return (
    <div className="chart-wrapper">
      {/* Stats Bar */}
      <div className="chart-stats-bar">
        <StatCard
          label="Total Return"
          value={`${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%`}
          icon={isProfit ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
          positive={isProfit}
          negative={!isProfit}
        />
        <StatCard
          label="Final Value"
          value={formatCurrency(finalEquity)}
          icon={<Activity size={16} />}
        />
        <StatCard
          label="Peak Value"
          value={formatCurrency(peakEquity)}
          icon={<Maximize2 size={16} />}
        />
        <StatCard
          label="Max Drawdown"
          value={`${maxDrawdown.toFixed(2)}%`}
          icon={<TrendingDown size={16} />}
          negative
        />
      </div>

      {/* Chart Controls */}
      <div className="chart-controls">
        <div className="chart-control-group">
          <button
            className={`chart-control-btn ${chartType === 'area' ? 'active' : ''}`}
            onClick={() => setChartType('area')}
          >
            Area
          </button>
          <button
            className={`chart-control-btn ${chartType === 'line' ? 'active' : ''}`}
            onClick={() => setChartType('line')}
          >
            Line
          </button>
        </div>
        <label className="chart-control-toggle">
          <input
            type="checkbox"
            checked={showHighWatermark}
            onChange={(e) => setShowHighWatermark(e.target.checked)}
          />
          <span>High Watermark</span>
        </label>
      </div>

      {/* Chart */}
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={380}>
          <ComposedChart data={dataWithHWM} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
            <defs>
              <linearGradient id="equityGradientProfit" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22c55e" stopOpacity={0.4} />
                <stop offset="50%" stopColor="#22c55e" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="equityGradientLoss" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4} />
                <stop offset="50%" stopColor="#ef4444" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="hwmGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.1} />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-default)" opacity={0.4} vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="var(--color-text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border-default)' }}
              interval="preserveStartEnd"
              dy={10}
            />
            <YAxis
              tickFormatter={formatCurrency}
              stroke="var(--color-text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              dx={-10}
            />
            <Tooltip content={<CustomTooltip initialCapital={initialCapital} highWatermark={stats.highWatermark} />} />

            {/* Initial Capital Reference */}
            <ReferenceLine
              y={initialCapital}
              stroke="var(--color-text-muted)"
              strokeDasharray="5 5"
              strokeOpacity={0.6}
            />

            {/* High Watermark Line */}
            {showHighWatermark && (
              <Area
                type="monotone"
                dataKey="hwm"
                stroke="#f59e0b"
                strokeWidth={1}
                strokeDasharray="3 3"
                fill="url(#hwmGradient)"
                fillOpacity={0.3}
                name="High Watermark"
              />
            )}

            {/* Main Equity Curve */}
            {chartType === 'area' ? (
              <Area
                type="monotone"
                dataKey="equity"
                stroke={isProfit ? '#22c55e' : '#ef4444'}
                strokeWidth={2.5}
                fill={isProfit ? 'url(#equityGradientProfit)' : 'url(#equityGradientLoss)'}
                filter="url(#glow)"
                animationDuration={1000}
                name="Portfolio"
              />
            ) : (
              <Line
                type="monotone"
                dataKey="equity"
                stroke={isProfit ? '#22c55e' : '#ef4444'}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 6, strokeWidth: 2, stroke: 'var(--color-bg-card)' }}
                filter="url(#glow)"
                animationDuration={1000}
                name="Portfolio"
              />
            )}

            {/* Best Day Marker */}
            {bestDay.change > 3 && (
              <ReferenceDot
                x={bestDay.date}
                y={dataWithHWM.find(d => d.date === bestDay.date)?.equity || 0}
                r={5}
                fill="#22c55e"
                stroke="white"
                strokeWidth={2}
              />
            )}

            {/* Worst Day Marker */}
            {worstDay.change < -3 && (
              <ReferenceDot
                x={worstDay.date}
                y={dataWithHWM.find(d => d.date === worstDay.date)?.equity || 0}
                r={5}
                fill="#ef4444"
                stroke="white"
                strokeWidth={2}
              />
            )}

            {dataWithHWM.length > 60 && (
              <Brush
                dataKey="date"
                height={30}
                stroke="var(--color-border-default)"
                fill="var(--color-bg-secondary)"
                tickFormatter={formatDate}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
