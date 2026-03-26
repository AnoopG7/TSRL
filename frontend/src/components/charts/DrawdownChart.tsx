import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
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

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-header">{formatFullDate(label)}</div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Drawdown</span>
        <span className="chart-tooltip-value negative">
          {drawdown.toFixed(2)}%
        </span>
      </div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Recovery needed</span>
        <span className="chart-tooltip-value" style={{ color: 'var(--color-warning-400)' }}>
          +{((-drawdown / (100 + drawdown)) * 100).toFixed(2)}%
        </span>
      </div>
    </div>
  );
};

export const DrawdownChart: React.FC<DrawdownChartProps> = ({ data }) => {
  // Find max drawdown point
  const maxDrawdownPoint = data.reduce((max, point) =>
    point.drawdown < max.drawdown ? point : max,
    { drawdown: 0, date: '' }
  );

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
          <defs>
            <linearGradient id="drawdownGradient" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={0.5} />
              <stop offset="50%" stopColor="#ef4444" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
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
          <ReferenceLine
            y={0}
            stroke="var(--color-success-500)"
            strokeOpacity={0.5}
            strokeWidth={1.5}
          />
          {maxDrawdownPoint.drawdown < -5 && (
            <ReferenceLine
              y={maxDrawdownPoint.drawdown}
              stroke="#ef4444"
              strokeDasharray="3 3"
              strokeOpacity={0.5}
              label={{
                value: `Max: ${maxDrawdownPoint.drawdown.toFixed(1)}%`,
                position: 'insideBottomRight',
                fontSize: 10,
                fill: '#ef4444'
              }}
            />
          )}
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
  );
};
