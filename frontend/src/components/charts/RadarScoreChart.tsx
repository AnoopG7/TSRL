import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, ResponsiveContainer, Tooltip,
} from 'recharts';
import { ChartTooltip } from './ChartTooltip';

interface Props {
  breakdown?: Record<string, { score: number; weight: number; metrics?: Record<string, number> }>;
}

export function RadarScoreChart({ breakdown }: Props) {
  if (!breakdown || Object.keys(breakdown).length === 0) {
    return (
      <section className="card">
        <div className="card-content" style={{ textAlign: 'center', padding: 'var(--spacing-xl)', color: 'var(--color-text-tertiary)' }}>
          No score breakdown available
        </div>
      </section>
    );
  }

  const pillars = ['profitability', 'valuation', 'cash_flow', 'solvency', 'growth'];
  const labels: Record<string, string> = {
    profitability: 'Profitability',
    valuation: 'Valuation',
    cash_flow: 'Cash Flow',
    solvency: 'Solvency',
    growth: 'Growth',
  };

  const data = pillars
    .filter((key) => breakdown[key])
    .map((key) => ({
      pillar: labels[key] || key,
      score: breakdown[key].score,
      fullMark: 100,
    }));

  return (
    <section className="card">
      <div className="card-header">
        <h2 className="card-title">Health Score Breakdown</h2>
        <p className="card-description">Performance across 5 fundamental pillars</p>
      </div>
      <div className="card-content" style={{ display: 'flex', justifyContent: 'center' }}>
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
            <PolarGrid stroke="var(--color-border)" />
            <PolarAngleAxis
              dataKey="pillar"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: 'var(--color-text-tertiary)', fontSize: 10 }}
            />
            <Radar
              name="Score"
              dataKey="score"
              stroke="var(--color-accent-500)"
              fill="var(--color-accent-500)"
              fillOpacity={0.3}
              strokeWidth={2}
            />
            <Tooltip
              content={<ChartTooltip formatter={(val) => ({ label: 'Score', value: typeof val === 'number' ? val.toFixed(1) : String(val), suffix: '/100' })} />}
              cursor={{ fill: 'var(--color-bg-hover)' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
