import type { MonthlyReturn } from '../../lib/schemas';

interface MonthlyReturnsHeatmapProps {
  data: MonthlyReturn[];
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const getColor = (value: number): string => {
  if (value > 8) return '#166534';
  if (value > 5) return '#15803d';
  if (value > 3) return '#22c55e';
  if (value > 1) return '#4ade80';
  if (value > 0) return '#86efac';
  if (value === 0) return 'var(--color-bg-input)';
  if (value > -1) return '#fca5a5';
  if (value > -3) return '#f87171';
  if (value > -5) return '#ef4444';
  if (value > -8) return '#dc2626';
  return '#991b1b';
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

  return (
    <div className="heatmap-wrapper">
      <div className="heatmap-grid" style={{ gridTemplateColumns: `80px repeat(12, 1fr)` }}>
        {/* Header row */}
        <div className="heatmap-header" />
        {MONTHS.map((m) => (
          <div key={m} className="heatmap-header">{m}</div>
        ))}

        {/* Data rows */}
        {years.map((year) => (
          <>
            <div key={`label-${year}`} className="heatmap-year">{year}</div>
            {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
              const val = yearMap[year]?.[month];
              const hasVal = val !== undefined;
              return (
                <div
                  key={`${year}-${month}`}
                  className="heatmap-cell"
                  style={{
                    backgroundColor: hasVal ? getColor(val) : 'transparent',
                    color: hasVal
                      ? (Math.abs(val) > 3 ? 'white' : 'var(--color-text-primary)')
                      : 'var(--color-text-muted)',
                  }}
                  title={hasVal ? `${MONTHS[month - 1]} ${year}: ${val.toFixed(2)}%` : ''}
                >
                  {hasVal ? `${val.toFixed(1)}%` : '–'}
                </div>
              );
            })}
          </>
        ))}
      </div>
    </div>
  );
};
