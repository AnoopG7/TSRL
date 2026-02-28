import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Line, ComposedChart,
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
        <ResponsiveContainer width="100%" height={360}>
          <ComposedChart data={mergedData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-default)" opacity={0.3} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="var(--color-text-muted)"
              fontSize={11}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tickFormatter={formatCurrency}
              stroke="var(--color-text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-bg-card)',
                border: '1px solid var(--color-border-default)',
                borderRadius: '8px',
                fontSize: '12px',
                color: 'var(--color-text-primary)',
              }}
              labelFormatter={formatDate}
              formatter={(value: unknown) => [formatCurrency(Number(value)), '']}
            />
            <Legend wrapperStyle={{ fontSize: '12px', color: 'var(--color-text-secondary)' }} />
            {strategyNames.map((name, i) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={false}
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

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={360}>
        <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <defs>
            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={isProfit ? '#22c55e' : '#ef4444'} stopOpacity={0.3} />
              <stop offset="95%" stopColor={isProfit ? '#22c55e' : '#ef4444'} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-default)" opacity={0.3} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke="var(--color-text-muted)"
            fontSize={11}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tickFormatter={formatCurrency}
            stroke="var(--color-text-muted)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-bg-card)',
              border: '1px solid var(--color-border-default)',
              borderRadius: '8px',
              fontSize: '12px',
              color: 'var(--color-text-primary)',
            }}
            labelFormatter={formatDate}
            formatter={(value: unknown) => [`${formatCurrency(Number(value))}`, 'Portfolio']}
          />
          <Area
            type="monotone"
            dataKey="equity"
            stroke={isProfit ? '#22c55e' : '#ef4444'}
            strokeWidth={2}
            fill="url(#equityGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
