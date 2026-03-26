import { useMemo, useState } from 'react';
import { TrendingUp, TrendingDown, Calendar, Award } from 'lucide-react';
import type { MonthlyReturn } from '../../lib/schemas';

interface MonthlyReturnsHeatmapProps {
  data: MonthlyReturn[];
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Enhanced color scale
const getColor = (value: number): string => {
  if (value > 10) return '#14532d';
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
  if (value > -10) return '#b91c1b';
  return '#7f1d1d';
};

const getTextColor = (value: number): string => {
  if (Math.abs(value) > 3) return 'white';
  return 'var(--color-text-primary)';
};

// Stats card
const StatCard: React.FC<{ label: string; value: string; subtext?: string; icon: React.ReactNode; positive?: boolean; negative?: boolean }> = ({
  label, value, subtext, icon, positive, negative
}) => (
  <div className="chart-stat-card">
    <div className={`chart-stat-icon ${positive ? 'positive' : ''} ${negative ? 'negative' : ''}`}>{icon}</div>
    <div className="chart-stat-content">
      <span className="chart-stat-label">{label}</span>
      <span className={`chart-stat-value ${positive ? 'positive' : ''} ${negative ? 'negative' : ''}`}>{value}</span>
      {subtext && <span className="chart-stat-subtext">{subtext}</span>}
    </div>
  </div>
);

export const MonthlyReturnsHeatmap: React.FC<MonthlyReturnsHeatmapProps> = ({ data }) => {
  const [highlightBestWorst, setHighlightBestWorst] = useState(true);
  const [selectedCell, setSelectedCell] = useState<{ year: number; month: number } | null>(null);

  const stats = useMemo(() => {
    if (!data || data.length === 0) return null;

    // Group by year
    const years = [...new Set(data.map((d) => d.year))].sort();
    const yearMap: Record<number, Record<number, number>> = {};

    for (const d of data) {
      if (!yearMap[d.year]) yearMap[d.year] = {};
      yearMap[d.year][d.month] = d.return_pct;
    }

    // Yearly totals
    const yearlyTotals: Record<number, number> = {};
    for (const year of years) {
      const returns = Object.values(yearMap[year] || {});
      yearlyTotals[year] = returns.reduce((sum, r) => sum + r, 0);
    }

    // Monthly averages
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

    // Find best and worst
    let bestMonth = { year: 0, month: 0, value: -Infinity };
    let worstMonth = { year: 0, month: 0, value: Infinity };

    for (const d of data) {
      if (d.return_pct > bestMonth.value) {
        bestMonth = { year: d.year, month: d.month, value: d.return_pct };
      }
      if (d.return_pct < worstMonth.value) {
        worstMonth = { year: d.year, month: d.month, value: d.return_pct };
      }
    }

    // Win rate
    const positiveMonths = data.filter(d => d.return_pct > 0).length;
    const winRate = (positiveMonths / data.length) * 100;

    // Average monthly return
    const avgReturn = data.reduce((sum, d) => sum + d.return_pct, 0) / data.length;

    // Best and worst years
    const bestYear = Object.entries(yearlyTotals).reduce((best, [year, total]) =>
      total > (best.total || -Infinity) ? { year: Number(year), total } : best,
      { year: 0, total: -Infinity }
    );
    const worstYear = Object.entries(yearlyTotals).reduce((worst, [year, total]) =>
      total < (worst.total || Infinity) ? { year: Number(year), total } : worst,
      { year: 0, total: Infinity }
    );

    return {
      years,
      yearMap,
      yearlyTotals,
      monthlyAvg,
      bestMonth,
      worstMonth,
      winRate,
      avgReturn,
      bestYear,
      worstYear,
    };
  }, [data]);

  if (!stats) return null;

  const { years, yearMap, yearlyTotals, monthlyAvg, bestMonth, worstMonth, winRate, avgReturn, bestYear, worstYear } = stats;

  const isBestCell = (year: number, month: number) =>
    highlightBestWorst && bestMonth.year === year && bestMonth.month === month;

  const isWorstCell = (year: number, month: number) =>
    highlightBestWorst && worstMonth.year === year && worstMonth.month === month;

  return (
    <div className="chart-wrapper">
      {/* Stats Bar */}
      <div className="chart-stats-bar">
        <StatCard
          label="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          icon={<Award size={16} />}
          positive={winRate > 50}
        />
        <StatCard
          label="Avg Monthly"
          value={`${avgReturn >= 0 ? '+' : ''}${avgReturn.toFixed(2)}%`}
          icon={avgReturn >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
          positive={avgReturn > 0}
          negative={avgReturn < 0}
        />
        <StatCard
          label="Best Month"
          value={`+${bestMonth.value.toFixed(1)}%`}
          subtext={`${MONTHS[bestMonth.month - 1]} ${bestMonth.year}`}
          icon={<TrendingUp size={16} />}
          positive
        />
        <StatCard
          label="Worst Month"
          value={`${worstMonth.value.toFixed(1)}%`}
          subtext={`${MONTHS[worstMonth.month - 1]} ${worstMonth.year}`}
          icon={<TrendingDown size={16} />}
          negative
        />
      </div>

      {/* Controls */}
      <div className="chart-controls">
        <label className="chart-control-toggle">
          <input
            type="checkbox"
            checked={highlightBestWorst}
            onChange={(e) => setHighlightBestWorst(e.target.checked)}
          />
          <span>Highlight Best/Worst</span>
        </label>
      </div>

      {/* Heatmap */}
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
                const isBest = isBestCell(year, month);
                const isWorst = isWorstCell(year, month);
                const isSelected = selectedCell?.year === year && selectedCell?.month === month;

                return (
                  <div
                    key={`${year}-${month}`}
                    className={`heatmap-cell ${isBest ? 'heatmap-cell-best' : ''} ${isWorst ? 'heatmap-cell-worst' : ''} ${isSelected ? 'heatmap-cell-selected' : ''}`}
                    style={{
                      backgroundColor: hasVal ? getColor(val) : 'transparent',
                      color: hasVal ? getTextColor(val) : 'var(--color-text-muted)',
                      fontWeight: hasVal && Math.abs(val) > 5 ? 600 : 400,
                    }}
                    title={hasVal ? `${MONTHS[month - 1]} ${year}: ${val.toFixed(2)}%` : ''}
                    onClick={() => hasVal && setSelectedCell(isSelected ? null : { year, month })}
                  >
                    {hasVal ? `${val.toFixed(1)}%` : '–'}
                    {isBest && <span className="heatmap-badge best">★</span>}
                    {isWorst && <span className="heatmap-badge worst">★</span>}
                  </div>
                );
              })}
              {/* Yearly total */}
              <div
                className={`heatmap-cell heatmap-total ${year === bestYear.year ? 'heatmap-cell-best-year' : ''} ${year === worstYear.year ? 'heatmap-cell-worst-year' : ''}`}                style={{
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
                  className="heatmap-cell heatmap-cell-avg"
                  style={{
                    backgroundColor: hasVal ? getColor(avg) : 'transparent',
                    color: hasVal ? getTextColor(avg) : 'var(--color-text-muted)',
                    fontWeight: 500,
                  }}
                  title={hasVal ? `${MONTHS[month - 1]} Average: ${avg.toFixed(2)}%` : ''}
                >
                  {hasVal ? `${avg.toFixed(1)}%` : '–'}
                </div>
              );
            })}
            <div className="heatmap-cell heatmap-cell-avg" />
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

      {/* Selected Cell Details */}
      {selectedCell && (
        <div className="chart-detail-panel">
          <div className="chart-detail-header">
            <Calendar size={16} />
            <span>{MONTHS[selectedCell.month - 1]} {selectedCell.year}</span>
          </div>
          <div className="chart-detail-content">
            <div className="chart-detail-row">
              <span>Return</span>
              <span className={yearMap[selectedCell.year]?.[selectedCell.month] >= 0 ? 'positive' : 'negative'}>
                {yearMap[selectedCell.year]?.[selectedCell.month]?.toFixed(2)}%
              </span>
            </div>
            <div className="chart-detail-row">
              <span>Month Avg</span>
              <span>
                {(monthlyAvg[selectedCell.month].sum / monthlyAvg[selectedCell.month].count).toFixed(2)}%
              </span>
            </div>
            <div className="chart-detail-row">
              <span>Year Total</span>
              <span className={yearlyTotals[selectedCell.year] >= 0 ? 'positive' : 'negative'}>
                {yearlyTotals[selectedCell.year].toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
