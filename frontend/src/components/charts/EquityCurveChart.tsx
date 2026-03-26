import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Line, ComposedChart,
  ReferenceLine, Brush,
} from 'recharts';
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
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, initialCapital = 100000 }) => {
  if (!active || !payload || !payload.length) return null;

  const equity = payload[0]?.value || 0;
  const returnPct = ((equity - initialCapital) / initialCapital) * 100;
  const isProfit = equity >= initialCapital;

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-header">{formatFullDate(label)}</div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Portfolio Value</span>
        <span className={`chart-tooltip-value ${isProfit ? 'positive' : 'negative'}`}>
          {formatCurrency(equity)}
        </span>
      </div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Return</span>
        <span className={`chart-tooltip-value ${isProfit ? 'positive' : 'negative'}`}>
          {returnPct >= 0 ? '+' : ''}{returnPct.toFixed(2)}%
        </span>
      </div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">P&L</span>
        <span className={`chart-tooltip-value ${isProfit ? 'positive' : 'negative'}`}>
          {equity - initialCapital >= 0 ? '+' : ''}{formatCurrency(equity - initialCapital)}
        </span>
      </div>
    </div>
  );
};

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({
  data,
  comparisonData,
  initialCapital = 100000,
}) => {
  // Comparison mode: overlay multiple strategy curves
  if (comparisonData && Object.keys(comparisonData).length > 0) {
    const strategyNames = Object.keys(comparisonData);

    // Merge all curves into unified data points
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
                    {payload.map((entry, i) => (
                      <div key={i} className="chart-tooltip-row">
                        <span className="chart-tooltip-label" style={{ color: entry.color }}>
                          {entry.name}
                        </span>
                        <span className="chart-tooltip-value">
                          {formatCurrency(Number(entry.value))}
                        </span>
                      </div>
                    ))}
                  </div>
                );
              }}
            />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
                fontSize: '12px',
              }}
              iconType="line"
            />
            <ReferenceLine
              y={initialCapital}
              stroke="var(--color-text-muted)"
              strokeDasharray="5 5"
              strokeOpacity={0.5}
              label={{
                value: 'Initial',
                position: 'right',
                fontSize: 10,
                fill: 'var(--color-text-muted)'
              }}
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

  // Single strategy mode
  const isProfit = data.length > 0 && data[data.length - 1].equity >= initialCapital;
  const maxEquity = data.length > 0 ? Math.max(...data.map(d => d.equity)) : initialCapital;
  const minEquity = data.length > 0 ? Math.min(...data.map(d => d.equity)) : initialCapital;

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
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
            domain={[minEquity * 0.98, maxEquity * 1.02]}
            dx={-10}
          />
          <Tooltip content={<CustomTooltip initialCapital={initialCapital} />} />
          <ReferenceLine
            y={initialCapital}
            stroke="var(--color-text-muted)"
            strokeDasharray="5 5"
            strokeOpacity={0.6}
            label={{
              value: `Initial: ${formatCurrency(initialCapital)}`,
              position: 'insideTopRight',
              fontSize: 10,
              fill: 'var(--color-text-muted)'
            }}
          />
          <Area
            type="monotone"
            dataKey="equity"
            stroke={isProfit ? '#22c55e' : '#ef4444'}
            strokeWidth={2.5}
            fill={isProfit ? 'url(#equityGradientProfit)' : 'url(#equityGradientLoss)'}
            filter="url(#glow)"
            animationDuration={1000}
            animationEasing="ease-out"
          />
          {data.length > 50 && (
            <Brush
              dataKey="date"
              height={30}
              stroke="var(--color-border-default)"
              fill="var(--color-bg-secondary)"
              tickFormatter={formatDate}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
