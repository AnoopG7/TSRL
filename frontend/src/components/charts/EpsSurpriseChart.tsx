import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import type { FundamentalReport } from '../../lib/schemas/fundamental.schema';

interface Props {
  history: FundamentalReport['eps_surprise_history'];
}

interface EpsData {
  quarter: string;
  actual: number;
  estimate: number;
  surprise: number;
  surprise_pct: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: EpsData }>;
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const isBeat = data.surprise >= 0;

    return (
      <div className="chart-tooltip">
        <div className="chart-tooltip-header">{label}</div>

        <div className="chart-tooltip-row">
          <span className="chart-tooltip-label">Estimate</span>
          <span className="chart-tooltip-value">${data.estimate.toFixed(2)}</span>
        </div>

        <div className="chart-tooltip-row">
          <span className="chart-tooltip-label">Actual Reported</span>
          <span className="chart-tooltip-value">${data.actual.toFixed(2)}</span>
        </div>

        <div className="chart-tooltip-divider" />

        <div className="chart-tooltip-row">
          <span className="chart-tooltip-label">Surprise</span>
          <span className={`chart-tooltip-value ${isBeat ? 'positive' : 'negative'}`}>
            {isBeat ? '+' : ''}{data.surprise.toFixed(2)} ({isBeat ? '+' : ''}{data.surprise_pct.toFixed(2)}%)
          </span>
        </div>
      </div>
    );
  }
  return null;
};

export function EpsSurpriseChart({ history }: Props) {
  if (!history || history.length === 0) {
    return (
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Earnings Surprise History</h2>
        </div>
        <div className="card-content">
          <p style={{ textAlign: 'center', color: 'var(--color-text-tertiary)', padding: 'var(--spacing-xl)' }}>
            No EPS surprise data available. This data comes from Finnhub API.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2 className="card-title">Earnings Surprise History</h2>
        <p className="card-description">Actual EPS vs Consensus Estimate</p>
      </div>
      <div className="card-content">
        <div className="chart-container" style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={history.slice().reverse()}
              margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border-default)" />
              <XAxis 
                dataKey="quarter" 
                tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
                tickLine={false}
                axisLine={{ stroke: 'var(--color-border-default)' }}
              />
              <YAxis 
                tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) => `$${val}`}
              />
              <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: 'var(--color-bg-hover)' }} />
              <ReferenceLine y={0} stroke="var(--color-border-default)" />
              
              <Bar dataKey="estimate" fill="var(--color-text-primary)" fillOpacity={0.15} radius={[2, 2, 0, 0]} name="Estimate" />
              <Bar dataKey="actual" radius={[2, 2, 0, 0]} name="Actual">
                {
                  history.slice().reverse().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.surprise >= 0 ? 'var(--color-positive)' : 'var(--color-negative)'} />
                  ))
                }
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="chart-legend" style={{ marginTop: 'var(--spacing-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: 'var(--color-text-primary)', opacity: 0.15, borderRadius: '2px' }} />
            <span className="chart-legend-label" style={{ textTransform: 'none', color: 'var(--color-text-primary)' }}>Consensus Estimate</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'var(--spacing-md)' }}>
            <div style={{ width: '12px', height: '12px', background: 'var(--color-positive)', borderRadius: '2px' }} />
            <span className="chart-legend-label" style={{ textTransform: 'none', color: 'var(--color-text-primary)' }}>Actual (Beat)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'var(--spacing-md)' }}>
            <div style={{ width: '12px', height: '12px', background: 'var(--color-negative)', borderRadius: '2px' }} />
            <span className="chart-legend-label" style={{ textTransform: 'none', color: 'var(--color-text-primary)' }}>Actual (Miss)</span>
          </div>
        </div>
      </div>
    </section>
  );
}