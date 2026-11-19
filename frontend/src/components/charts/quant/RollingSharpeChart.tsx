import { useMemo, useState } from 'react';
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts';
import { axisProps, gridProps, crosshair, tickDate, longDate, evenTicks, dailyReturns } from './chartKit';

interface Props {
  equity: { date: string; equity: number }[];
}

const WINDOWS = [
  { days: 63, label: '3M' },
  { days: 126, label: '6M' },
  { days: 252, label: '1Y' },
];

/**
 * Annualised Sharpe over a trailing window. Shows whether the edge is steady
 * or came from one lucky stretch, which a single full-period Sharpe hides.
 */
export function RollingSharpeChart({ equity }: Props) {
  const [win, setWin] = useState(126);
  const [hover, setHover] = useState<{ date: string; sharpe: number } | null>(null);

  const rows = useMemo(() => {
    const rets = dailyReturns(equity);
    const out: { date: string; sharpe: number; pos: number; neg: number }[] = [];
    let sum = 0;
    let sumSq = 0;
    for (let i = 0; i < rets.length; i++) {
      sum += rets[i].r;
      sumSq += rets[i].r ** 2;
      if (i >= win) {
        sum -= rets[i - win].r;
        sumSq -= rets[i - win].r ** 2;
      }
      if (i >= win - 1) {
        const mean = sum / win;
        const variance = Math.max(sumSq / win - mean ** 2, 0);
        const sd = Math.sqrt(variance);
        const sharpe = sd > 1e-9 ? (mean / sd) * Math.sqrt(252) : 0;
        const clipped = Math.max(-6, Math.min(6, sharpe));
        out.push({ date: rets[i].date, sharpe: clipped, pos: Math.max(clipped, 0), neg: Math.min(clipped, 0) });
      }
    }
    return out;
  }, [equity, win]);

  const available = WINDOWS.filter((w) => equity.length > w.days * 1.5);

  if (rows.length < 2) {
    return <p className="text-muted">Not enough history for a rolling window. Try a longer date range.</p>;
  }

  const last = rows[rows.length - 1];
  const shown = hover ?? last;
  const share = rows.filter((r) => r.sharpe > 0).length / rows.length;
  const ticks = evenTicks(rows, 'date', 6);

  return (
    <div className="qc">
      <div className="qc-head">
        <div className="qc-readout">
          <div>
            <span className="qc-k">{hover ? longDate(shown.date) : 'Latest'}</span>
            <span className={`qc-v ${shown.sharpe >= 0 ? 'text-positive' : 'text-negative'}`}>{shown.sharpe.toFixed(2)}</span>
          </div>
          <div>
            <span className="qc-k">Time with positive Sharpe</span>
            <span className="qc-v">{(share * 100).toFixed(0)}%</span>
          </div>
          <div>
            <span className="qc-k">Range</span>
            <span className="qc-v">
              {Math.min(...rows.map((r) => r.sharpe)).toFixed(1)} to {Math.max(...rows.map((r) => r.sharpe)).toFixed(1)}
            </span>
          </div>
        </div>
        {available.length > 1 && (
          <div className="segmented" role="group" aria-label="Rolling window">
            {available.map((w) => (
              <button key={w.days} type="button" aria-pressed={win === w.days} onClick={() => setWin(w.days)}>{w.label}</button>
            ))}
          </div>
        )}
      </div>

      <div onMouseLeave={() => setHover(null)}>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart
            data={rows}
            margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
            onMouseMove={(s) => {
              const i = s?.activeTooltipIndex;
              const idx = typeof i === 'string' ? Number(i) : i;
              setHover(typeof idx === 'number' && rows[idx] ? rows[idx] : null);
            }}
          >
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="date" {...axisProps} ticks={ticks} tickFormatter={tickDate} interval={0} dy={6} />
            <YAxis {...axisProps} width={40} allowDecimals={false} domain={[(min: number) => Math.floor(min), (max: number) => Math.ceil(Math.max(max, 1.2))]} />
            <Tooltip content={() => null} cursor={crosshair} />
            <ReferenceLine y={0} stroke="var(--chart-baseline)" />
            <ReferenceLine y={1} stroke="var(--chart-axis)" strokeDasharray="4 4" strokeOpacity={0.6}
              label={{ value: 'Sharpe 1', position: 'insideTopRight', fill: 'var(--chart-axis)', fontSize: 11 }} />
            <Area type="linear" dataKey="pos" stroke="none" fill="var(--color-up)" fillOpacity={0.12} isAnimationActive={false} activeDot={false} />
            <Area type="linear" dataKey="neg" stroke="none" fill="var(--color-down)" fillOpacity={0.12} isAnimationActive={false} activeDot={false} />
            <Line type="linear" dataKey="sharpe" stroke="var(--color-text-primary)" strokeWidth={1.75} dot={false} isAnimationActive={false}
              activeDot={{ r: 4, strokeWidth: 2, stroke: 'var(--color-bg-card)', fill: 'var(--color-text-primary)' }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="qc-note">
        Annualised Sharpe of daily returns over a trailing {WINDOWS.find((w) => w.days === win)?.label} window, risk-free rate 0. Shaded above or below zero.
      </p>
    </div>
  );
}
