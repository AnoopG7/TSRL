import { useMemo, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea,
} from 'recharts';
import { TrendingDown, Clock, AlertTriangle } from 'lucide-react';
import type { DrawdownPoint } from '../../lib/schemas';

interface DrawdownChartProps {
  data: DrawdownPoint[];
}

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
  payload?: Array<{ value: number }>;
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;

  const drawdown = payload[0]?.value || 0;
  const recoveryNeeded = (-drawdown / (100 + drawdown)) * 100;

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-header">{formatFullDate(label)}</div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Drawdown</span>
        <span className="chart-tooltip-value negative">
          {drawdown.toFixed(2)}%
        </span>
      </div>
      {drawdown < 0 && (
        <div className="chart-tooltip-row">
          <span className="chart-tooltip-label">To Recover</span>
          <span className="chart-tooltip-value" style={{ color: 'var(--color-warning-400)' }}>
            +{recoveryNeeded.toFixed(2)}%
          </span>
        </div>
      )}
    </div>
  );
};

// Stats card
const StatCard: React.FC<{ label: string; value: string; icon: React.ReactNode }> = ({ label, value, icon }) => (
  <div className="chart-stat-card">
    <div className="chart-stat-icon" style={{ color: 'var(--color-danger-400)' }}>{icon}</div>
    <div className="chart-stat-content">
      <span className="chart-stat-label">{label}</span>
      <span className="chart-stat-value negative">{value}</span>
    </div>
  </div>
);

interface UnderwaterPeriod {
  start: string;
  end: string;
  maxDrawdown: number;
  duration: number;
}

export const DrawdownChart: React.FC<DrawdownChartProps> = ({ data }) => {
  const [showUnderwaterPeriods, setShowUnderwaterPeriods] = useState(true);

  // Calculate statistics
  const stats = useMemo(() => {
    if (!data || data.length === 0) return null;

    // Find max drawdown
    const maxDrawdownPoint = data.reduce((max, point) =>
      point.drawdown < max.drawdown ? point : max,
      { drawdown: 0, date: '' }
    );

    // Find underwater periods
    const underwaterPeriods: UnderwaterPeriod[] = [];
    let currentPeriod: UnderwaterPeriod | null = null;

    data.forEach((point) => {
      if (point.drawdown < 0 && currentPeriod === null) {
        // Start new underwater period
        currentPeriod = {
          start: point.date,
          end: point.date,
          maxDrawdown: point.drawdown,
          duration: 1
        };
      } else if (point.drawdown < 0 && currentPeriod !== null) {
        // Continue underwater period
        currentPeriod.end = point.date;
        currentPeriod.maxDrawdown = Math.min(currentPeriod.maxDrawdown, point.drawdown);
        currentPeriod.duration++;
      } else if (point.drawdown >= 0 && currentPeriod !== null) {
        // End underwater period
        underwaterPeriods.push(currentPeriod);
        currentPeriod = null;
      }
    });

    // Don't forget last period if still underwater
    if (currentPeriod !== null) {
      underwaterPeriods.push(currentPeriod);
    }

    // Calculate average drawdown (only when underwater)
    const underwaterPoints = data.filter(d => d.drawdown < 0);
    const avgDrawdown = underwaterPoints.length > 0
      ? underwaterPoints.reduce((sum, d) => sum + d.drawdown, 0) / underwaterPoints.length
      : 0;

    // Calculate time underwater
    const timeUnderwater = (underwaterPoints.length / data.length) * 100;

    // Longest underwater period
    const longestPeriod = underwaterPeriods.reduce((max, p) =>
      p.duration > max.duration ? p : max,
      { duration: 0, start: '', end: '', maxDrawdown: 0 }
    );

    return {
      maxDrawdown: maxDrawdownPoint.drawdown,
      maxDrawdownDate: maxDrawdownPoint.date,
      avgDrawdown,
      timeUnderwater,
      underwaterPeriods,
      longestPeriod,
      currentDrawdown: data[data.length - 1]?.drawdown || 0,
    };
  }, [data]);

  if (!stats) return null;

  // Find significant underwater periods (> 10 days and > -5% drawdown)
  const significantPeriods = stats.underwaterPeriods.filter(
    p => p.duration > 10 && p.maxDrawdown < -5
  );

  return (
    <div className="chart-wrapper">
      {/* Stats Bar */}
      <div className="chart-stats-bar">
        <StatCard
          label="Max Drawdown"
          value={`${stats.maxDrawdown.toFixed(2)}%`}
          icon={<TrendingDown size={16} />}
        />
        <StatCard
          label="Avg Drawdown"
          value={`${stats.avgDrawdown.toFixed(2)}%`}
          icon={<AlertTriangle size={16} />}
        />
        <StatCard
          label="Time Underwater"
          value={`${stats.timeUnderwater.toFixed(1)}%`}
          icon={<Clock size={16} />}
        />
        <StatCard
          label="Current"
          value={`${stats.currentDrawdown.toFixed(2)}%`}
          icon={<TrendingDown size={16} />}
        />
      </div>

      {/* Controls */}
      <div className="chart-controls">
        <label className="chart-control-toggle">
          <input
            type="checkbox"
            checked={showUnderwaterPeriods}
            onChange={(e) => setShowUnderwaterPeriods(e.target.checked)}
          />
          <span>Highlight Underwater Periods</span>
        </label>
      </div>

      {/* Chart */}
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
            <defs>
              <linearGradient id="drawdownGradient" x1="0" y1="1" x2="0" y2="0">
                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.5} />
                <stop offset="50%" stopColor="#ef4444" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="severeDrawdownGradient" x1="0" y1="1" x2="0" y2="0">
                <stop offset="0%" stopColor="#991b1b" stopOpacity={0.6} />
                <stop offset="100%" stopColor="#991b1b" stopOpacity={0.1} />
              </linearGradient>
              <filter id="drawdownGlow">
                <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
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
              tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              stroke="var(--color-text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              domain={['dataMin - 2', 2]}
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Zero line */}
            <ReferenceLine
              y={0}
              stroke="var(--color-success-500)"
              strokeOpacity={0.6}
              strokeWidth={2}
            />

            {/* Max drawdown reference */}
            {stats.maxDrawdown < -5 && (
              <ReferenceLine
                y={stats.maxDrawdown}
                stroke="#ef4444"
                strokeDasharray="3 3"
                strokeOpacity={0.5}
                label={{
                  value: `Max: ${stats.maxDrawdown.toFixed(1)}%`,
                  position: 'insideBottomRight',
                  fontSize: 10,
                  fill: '#ef4444'
                }}
              />
            )}

            {/* Highlight significant underwater periods */}
            {showUnderwaterPeriods && significantPeriods.map((period, i) => (
              <ReferenceArea
                key={i}
                x1={period.start}
                x2={period.end}
                fill="#ef4444"
                fillOpacity={0.1}
                stroke="#ef4444"
                strokeOpacity={0.3}
              />
            ))}

            {/* -10% warning line */}
            <ReferenceLine
              y={-10}
              stroke="var(--color-warning-500)"
              strokeDasharray="5 5"
              strokeOpacity={0.3}
            />

            {/* -20% danger line */}
            <ReferenceLine
              y={-20}
              stroke="var(--color-danger-600)"
              strokeDasharray="5 5"
              strokeOpacity={0.3}
            />

            <Area
              type="monotone"
              dataKey="drawdown"
              stroke="#ef4444"
              strokeWidth={2}
              fill="url(#drawdownGradient)"
              filter="url(#drawdownGlow)"
              animationDuration={1000}
              animationEasing="ease-out"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Underwater Periods List */}
      {stats.longestPeriod.duration > 5 && (
        <div className="chart-annotation">
          <span className="chart-annotation-label">Longest underwater period:</span>
          <span className="chart-annotation-value">
            {stats.longestPeriod.duration} days ({formatDate(stats.longestPeriod.start)} - {formatDate(stats.longestPeriod.end)})
          </span>
        </div>
      )}
    </div>
  );
};
