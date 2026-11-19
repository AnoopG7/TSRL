import { useMemo, useState } from 'react';
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
  ResponsiveContainer, ReferenceDot,
} from 'recharts';
import {
  axisProps, gridProps, crosshair, tickDate, longDate, compactMoney, signedPct,
  evenTicks, sliceRange, type Range,
} from './chartKit';
import { useCurrencySymbol } from '../../../lib/utils';

interface Point { date: string; equity: number }

interface PerformanceChartProps {
  equity: Point[];
  /** Drawdown series in percent (≤ 0). Derived from equity when omitted. */
  drawdown?: { date: string; drawdown: number }[];
  initialCapital: number;
  /** Line colour; defaults to series 1. */
  color?: string;
}

interface Row {
  date: string;
  equity: number;
  hwm: number;
  dd: number;
}

const RANGES: Range[] = ['6M', '1Y', '3Y', 'All'];

/**
 * Equity on top, underwater drawdown below, one shared crosshair.
 * The readout above the plot replaces a floating tooltip so nothing covers the line.
 */
export function PerformanceChart({ equity, drawdown, initialCapital, color = 'var(--series-1)' }: PerformanceChartProps) {
  const currency = useCurrencySymbol();
  const [range, setRange] = useState<Range>('All');
  const [hover, setHover] = useState<Row | null>(null);

  const all = useMemo<Row[]>(() => {
    const ddByDate = new Map(drawdown?.map((d) => [d.date, d.drawdown]) ?? []);
    const out: Row[] = [];
    for (const p of equity) {
      const peak = Math.max(out.length ? out[out.length - 1].hwm : -Infinity, p.equity);
      const derived = peak > 0 ? (p.equity / peak - 1) * 100 : 0;
      out.push({ date: p.date, equity: p.equity, hwm: peak, dd: ddByDate.get(p.date) ?? derived });
    }
    return out;
  }, [equity, drawdown]);

  const rows = useMemo(() => sliceRange(all, range), [all, range]);
  const availableRanges = RANGES.filter((r) => r === 'All' || sliceRange(all, r).length < all.length);

  const stats = useMemo(() => {
    if (rows.length === 0) return null;
    const first = rows[0].equity;
    const last = rows[rows.length - 1];
    const trough = rows.reduce((m, r) => (r.dd < m.dd ? r : m), rows[0]);
    const lo = Math.min(...rows.map((r) => r.equity), initialCapital);
    const hi = Math.max(...rows.map((r) => r.equity), initialCapital);
    const pad = (hi - lo) * 0.08 || hi * 0.02;
    return { first, last, trough, domain: [lo - pad, hi + pad] as [number, number] };
  }, [rows, initialCapital]);

  if (!stats) return null;

  const shown = hover ?? stats.last;
  const periodReturn = (shown.equity / stats.first - 1) * 100;
  const ticks = evenTicks(rows, 'date', 6);
  const syncId = 'perf';

  const onMove = (state: { activeTooltipIndex?: number | string | null } | undefined) => {
    const i = state?.activeTooltipIndex;
    const idx = typeof i === 'string' ? Number(i) : i;
    setHover(typeof idx === 'number' && rows[idx] ? rows[idx] : null);
  };

  return (
    <div className="qc">
      <div className="qc-head">
        <div className="qc-readout" aria-live="off">
          <div>
            <span className="qc-k">{hover ? longDate(shown.date) : 'Latest'}</span>
            <span className="qc-v">{compactMoney(shown.equity, currency)}</span>
          </div>
          <div>
            <span className="qc-k">Return{range !== 'All' ? ` (${range})` : ''}</span>
            <span className={`qc-v ${periodReturn >= 0 ? 'text-positive' : 'text-negative'}`}>{signedPct(periodReturn, 2)}</span>
          </div>
          <div>
            <span className="qc-k">Drawdown</span>
            <span className={`qc-v ${shown.dd < -0.005 ? 'text-negative' : ''}`}>{shown.dd < -0.005 ? signedPct(shown.dd, 2) : 'At peak'}</span>
          </div>
          <div>
            <span className="qc-k">Worst drawdown</span>
            <span className="qc-v text-negative">{signedPct(stats.trough.dd, 2)}</span>
          </div>
        </div>
        {availableRanges.length > 1 && (
          <div className="segmented" role="group" aria-label="Time range">
            {availableRanges.map((r) => (
              <button key={r} type="button" aria-pressed={range === r} onClick={() => setRange(r)}>{r}</button>
            ))}
          </div>
        )}
      </div>

      <div onMouseLeave={() => setHover(null)}>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={rows} syncId={syncId} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} onMouseMove={onMove}>
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="date" hide />
            <YAxis
              {...axisProps}
              domain={stats.domain}
              tickFormatter={(v: number) => compactMoney(v, currency)}
              width={64}
              tickCount={5}
            />
            <Tooltip content={() => null} cursor={crosshair} />
            <ReferenceLine
              y={initialCapital}
              stroke="var(--chart-baseline)"
              strokeDasharray="4 4"
              label={{ value: 'Start', position: 'insideTopLeft', fill: 'var(--chart-axis)', fontSize: 11 }}
            />
            <Line type="linear" dataKey="hwm" stroke="var(--chart-axis)" strokeOpacity={0.45} strokeWidth={1} dot={false} isAnimationActive={false} name="High-water mark" />
            <Area type="linear" dataKey="equity" stroke={color} strokeWidth={2} fill={color} fillOpacity={0.07} dot={false} isAnimationActive={false}
              activeDot={{ r: 4, strokeWidth: 2, stroke: 'var(--color-bg-card)', fill: color }} name="Equity" />
          </ComposedChart>
        </ResponsiveContainer>

        <div className="qc-sublabel">Underwater: distance below the previous peak</div>
        <ResponsiveContainer width="100%" height={120}>
          <ComposedChart data={rows} syncId={syncId} margin={{ top: 4, right: 8, bottom: 0, left: 0 }} onMouseMove={onMove}>
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="date" {...axisProps} ticks={ticks} tickFormatter={tickDate} interval={0} dy={6} />
            <YAxis
              {...axisProps}
              width={64}
              domain={[Math.min(stats.trough.dd * 1.15, -1), 0]}
              tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              tickCount={3}
            />
            <Tooltip content={() => null} cursor={crosshair} />
            <ReferenceLine y={0} stroke="var(--chart-baseline)" />
            <Area type="linear" dataKey="dd" stroke="var(--color-down)" strokeWidth={1.5} fill="var(--color-down)" fillOpacity={0.14} dot={false} isAnimationActive={false}
              activeDot={{ r: 3, strokeWidth: 2, stroke: 'var(--color-bg-card)', fill: 'var(--color-down)' }} />
            <ReferenceDot
              x={stats.trough.date}
              y={stats.trough.dd}
              r={3.5}
              fill="var(--color-down)"
              stroke="var(--color-bg-card)"
              strokeWidth={2}
              label={{ value: signedPct(stats.trough.dd, 1), position: 'bottom', fill: 'var(--color-text-secondary)', fontSize: 11 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="qc-legend">
        <span><i style={{ background: color }} /> Equity</span>
        <span><i className="dash" /> High-water mark</span>
        <span><i className="dash base" /> Starting capital</span>
      </div>
    </div>
  );
}
