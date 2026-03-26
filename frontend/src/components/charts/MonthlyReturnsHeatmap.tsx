import type { MonthlyReturn } from '../../lib/schemas';

interface MonthlyReturnsHeatmapProps {
  data: MonthlyReturn[];
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Enhanced color scale with more granularity
const getColor = (value: number): string => {
  if (value > 10) return '#14532d'; // Very strong positive
  if (value > 7) return '#166534';
  if (value > 5) return '#15803d';
  if (value > 3) return '#22c55e';
  if (value > 1.5) return '#4ade80';
  if (value > 0.5) return '#86efac';
  if (value > 0) return '#bbf7d0';
  if (value === 0) return 'var(--color-bg-input)';
  if (value > -0.5) return '#fecaca';
  if (value > -1.5) return '#fca5a5';
  if (value > -3) return '#f87171';
  if (value > -5) return '#ef4444';
  if (value > -7) return '#dc2626';
  if (value > -10) return '#b91c1c';
  return '#7f1d1d'; // Very strong negative
};

const getTextColor = (value: number): string => {
  if (Math.abs(value) > 3) return 'white';
  return 'var(--color-text-primary)';
};

export const MonthlyReturnsHeatmap: React.FC<MonthlyReturnsHeatmapProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  // Group by year
  const years = [...new Set(data.map((d) => d.year))].sort();
  const yearMap: Record<number, Record<number, number>> = {};

  for (const d of data) {
    if (!yearMap[d.year]) yearMap[d.year] = {};
    yearMap[d.year][d.month] = d.return_pct;
  }

  // Calculate yearly totals (approximation: sum of monthly returns)
  const yearlyTotals: Record<number, number> = {};
  for (const year of years) {
    const monthlyReturns = Object.values(yearMap[year] || {});
    yearlyTotals[year] = monthlyReturns.reduce((sum, r) => sum + r, 0);
  }

  // Calculate monthly averages
  const monthlyAvg: Record<number, { sum: number; count: number }> = {};
  for (let m = 1; m <= 12; m++) {
    monthlyAvg[m] = { sum: 0, count: 0 };
    for (const year of years) {
      const val = yearMap[year]?.[m];
      if (val !== undefined) {
        monthlyAvg[m].sum += val;
        monthlyAvg[m].count++;
      }
    }
  }

  return (
    <div className="heatmap-wrapper">
      <div className="heatmap-grid" style={{ gridTemplateColumns: `80px repeat(12, 1fr) 80px` }}>
        {/* Header row */}
        <div className="heatmap-header" />
        {MONTHS.map((m) => (
          <div key={m} className="heatmap-header">{m}</div>
        ))}
        <div className="heatmap-header" style={{ fontWeight: 600 }}>Year</div>

        {/* Data rows */}
        {years.map((year) => (
          <div key={year} className="heatmap-row" style={{ display: 'contents' }}>
            <div className="heatmap-year">{year}</div>
            {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
              const val = yearMap[year]?.[month];
              const hasVal = val !== undefined;
              return (
                <div
                  key={`${year}-${month}`}
                  className="heatmap-cell"
                  style={{
                    backgroundColor: hasVal ? getColor(val) : 'transparent',
                    color: hasVal ? getTextColor(val) : 'var(--color-text-muted)',
                    fontWeight: hasVal && Math.abs(val) > 5 ? 600 : 400,
                  }}
                  title={hasVal ? `${MONTHS[month - 1]} ${year}: ${val.toFixed(2)}%` : ''}
                >
                  {hasVal ? `${val.toFixed(1)}%` : '–'}
                </div>
              );
            })}
            {/* Yearly total */}
            <div
              className="heatmap-cell heatmap-total"
              style={{
                backgroundColor: getColor(yearlyTotals[year]),
                color: getTextColor(yearlyTotals[year]),
                fontWeight: 600,
              }}
              title={`${year} Total: ${yearlyTotals[year].toFixed(2)}%`}
            >
              {yearlyTotals[year].toFixed(1)}%
            </div>
          </div>
        ))}

        {/* Average row */}
        <div className="heatmap-row" style={{ display: 'contents' }}>
          <div className="heatmap-year" style={{ fontWeight: 600, color: 'var(--color-accent-400)' }}>Avg</div>
          {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
            const { sum, count } = monthlyAvg[month];
            const avg = count > 0 ? sum / count : undefined;
            const hasVal = avg !== undefined;
            return (
              <div
                key={`avg-${month}`}
                className="heatmap-cell"
                style={{
                  backgroundColor: hasVal ? getColor(avg) : 'transparent',
                  color: hasVal ? getTextColor(avg) : 'var(--color-text-muted)',
                  fontWeight: 500,
                  borderTop: '2px solid var(--color-border-default)',
                }}
                title={hasVal ? `${MONTHS[month - 1]} Average: ${avg.toFixed(2)}%` : ''}
              >
                {hasVal ? `${avg.toFixed(1)}%` : '–'}
              </div>
            );
          })}
          <div className="heatmap-cell" style={{ borderTop: '2px solid var(--color-border-default)' }} />
        </div>
      </div>

      {/* Legend */}
      <div className="heatmap-legend">
        <span className="heatmap-legend-label">Loss</span>
        <div className="heatmap-legend-scale">
          {[-10, -5, -3, -1, 0, 1, 3, 5, 10].map((v, i) => (
            <div
              key={i}
              className="heatmap-legend-item"
              style={{ backgroundColor: getColor(v) }}
              title={`${v > 0 ? '+' : ''}${v}%`}
            />
          ))}
        </div>
        <span className="heatmap-legend-label">Gain</span>
      </div>
    </div>
  );
};
