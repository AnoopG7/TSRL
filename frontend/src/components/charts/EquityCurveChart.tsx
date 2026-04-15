import { useState, useMemo, useCallback } from 'react';
import {
  Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Line, ComposedChart,
  ReferenceLine, Brush,
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

interface DataPointWithHWM {
  date: string;
  equity: number;
  hwm: number;
}

interface HoverData {
  date: string;
  equity: number;
  hwm: number;
  returnPct: number;
  drawdownFromPeak: number;
}

// Hover info bar component - displays data above the chart
const HoverInfoBar: React.FC<{ data: HoverData | null; initialCapital: number }> = ({ data, initialCapital }) => {
  if (!data) return <div className="chart-hover-bar chart-hover-bar-empty">Hover over chart to see details</div>;

  const isProfit = data.equity >= initialCapital;

  return (
    <div className="chart-hover-bar">
      <div className="chart-hover-item">
        <span className="chart-hover-label">Date</span>
        <span className="chart-hover-value">{formatFullDate(data.date)}</span>
      </div>
      <div className="chart-hover-item">
        <span className="chart-hover-label">Portfolio</span>
        <span className={`chart-hover-value ${isProfit ? 'positive' : 'negative'}`}>
          {formatCurrency(data.equity)}
        </span>
      </div>
      <div className="chart-hover-item">
        <span className="chart-hover-label">Total Return</span>
        <span className={`chart-hover-value ${isProfit ? 'positive' : 'negative'}`}>
          {data.returnPct >= 0 ? '+' : ''}{data.returnPct.toFixed(2)}%
        </span>
      </div>
      <div className="chart-hover-item">
        <span className="chart-hover-label">From Peak</span>
        <span className={`chart-hover-value ${data.drawdownFromPeak < 0 ? 'negative' : ''}`}>
          {data.drawdownFromPeak.toFixed(2)}%
        </span>
      </div>
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
  const [hoverData, setHoverData] = useState<HoverData | null>(null);

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

    // Calculate Y-axis domain with padding for better visualization
    const allValues = data.map(d => d.equity);
    const minValue = Math.min(...allValues, initialCapital);
    const maxValue = Math.max(...allValues, highWatermark);
    const range = maxValue - minValue;
    const padding = range * 0.1; // 10% padding
    const yMin = Math.max(0, minValue - padding);
    const yMax = maxValue + padding;

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
      yDomain: [yMin, yMax] as [number, number],
    };
  }, [data, initialCapital]);

  // Custom tooltip that updates the hover bar state
  const handleTooltipContent = useCallback(({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPointWithHWM }> }) => {
    if (active && payload && payload.length > 0) {
      const point = payload[0].payload;
      const returnPct = ((point.equity - initialCapital) / initialCapital) * 100;
      const drawdownFromPeak = ((point.equity - point.hwm) / point.hwm) * 100;
      // Use setTimeout to avoid state update during render
      setTimeout(() => {
        setHoverData({
          date: point.date,
          equity: point.equity,
          hwm: point.hwm,
          returnPct,
          drawdownFromPeak,
        });
      }, 0);
    }
    return null; // Return null to hide the default tooltip
  }, [initialCapital]);

  const handleMouseLeave = useCallback(() => {
    setHoverData(null);
  }, []);

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
              position={{ x: 100, y: 10 }}
              wrapperStyle={{ pointerEvents: 'none' }}
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

      {/* Hover Info Bar - displays above chart, never overlaps */}
      <HoverInfoBar data={hoverData} initialCapital={initialCapital} />

      {/* Chart */}
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={380}>
          <ComposedChart
            data={dataWithHWM}
            margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
            onMouseLeave={handleMouseLeave}
          >
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
              domain={stats.yDomain}
            />
            {/* Tooltip that updates hover bar (returns null to hide itself) */}
            <Tooltip content={handleTooltipContent} />

            {/* Initial Capital Reference */}
            <ReferenceLine
              y={initialCapital}
              stroke="var(--color-text-muted)"
              strokeDasharray="5 5"
              strokeOpacity={0.5}
            />

            {/* High Watermark Line - subtle dashed line */}
            {showHighWatermark && (
              <Line
                type="stepAfter"
                dataKey="hwm"
                stroke="var(--color-text-muted)"
                strokeWidth={1}
                strokeDasharray="4 4"
                strokeOpacity={0.4}
                dot={false}
                activeDot={false}
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
