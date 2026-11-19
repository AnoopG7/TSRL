import { useMemo, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, LabelList,
} from 'recharts';
import { axisProps, gridProps, crosshair, tickDate, longDate, signedPct, evenTicks, SERIES } from './chartKit';

interface Props {
  /** Equity curve per series, keyed by a stable id (colour follows the id, not the rank). */
  series: Record<string, { date: string; equity: number }[]>;
  labelFor?: (key: string) => string;
  height?: number;
}

/**
 * Several equity curves indexed to % return from their own start, so series with
 * different capital share one honest axis. Ends are direct-labelled (≤ 4 series).
 */
export function MultiEquityChart({ series, labelFor = (k) => k, height = 360 }: Props) {
  const keys = useMemo(() => Object.keys(series), [series]);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(new Set());

  const rows = useMemo(() => {
    const dates = new Set<string>();
    keys.forEach((k) => series[k].forEach((p) => dates.add(p.date)));
    const sorted = [...dates].sort();
    const lookups = keys.map((k) => new Map(series[k].map((p) => [p.date, p.equity])));
    const base = keys.map((k) => series[k][0]?.equity || 1);
    const last: (number | undefined)[] = keys.map(() => undefined);
    return sorted.map((date) => {
      const row: Record<string, number | string> = { date };
      keys.forEach((k, i) => {
        const v = lookups[i].get(date);
        if (v !== undefined) last[i] = v;
        if (last[i] !== undefined) row[k] = ((last[i] as number) / base[i] - 1) * 100;
      });
      return row;
    });
  }, [series, keys]);

  const ticks = evenTicks(rows as { date: string }[], 'date', 6);
  const active = hoverIdx != null ? rows[hoverIdx] : rows[rows.length - 1];
  const ranked = keys
    .filter((k) => !hidden.has(k))
    .map((k) => ({ k, v: Number(active?.[k] ?? 0) }))
    .sort((a, b) => b.v - a.v);
  const directLabels = keys.length <= 4;
  const lastIndex = rows.length - 1;

  const toggle = (k: string) =>
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k); else if (next.size < keys.length - 1) next.add(k);
      return next;
    });

  return (
    <div className="qc">
      <div className="qc-head">
        <div className="qc-readout">
          <div>
            <span className="qc-k">Return since start</span>
            <span className="qc-v">{hoverIdx != null ? longDate(String(active.date)) : 'End of period'}</span>
          </div>
          {ranked.map(({ k, v }) => (
            <div key={k}>
              <span className="qc-k"><i className="qc-swatch" style={{ background: SERIES[keys.indexOf(k) % SERIES.length] }} />{labelFor(k)}</span>
              <span className={`qc-v ${v >= 0 ? 'text-positive' : 'text-negative'}`}>{signedPct(v, 2)}</span>
            </div>
          ))}
        </div>
      </div>

      <div onMouseLeave={() => setHoverIdx(null)}>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart
            data={rows}
            margin={{ top: 8, right: directLabels ? 112 : 12, bottom: 0, left: 0 }}
            onMouseMove={(s) => {
              const i = s?.activeTooltipIndex;
              const idx = typeof i === 'string' ? Number(i) : i;
              setHoverIdx(typeof idx === 'number' ? idx : null);
            }}
          >
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="date" {...axisProps} ticks={ticks} tickFormatter={tickDate} interval={0} dy={6} />
            <YAxis {...axisProps} width={48} tickFormatter={(v: number) => `${v.toFixed(0)}%`} domain={['auto', 'auto']} />
            <Tooltip content={() => null} cursor={crosshair} />
            <ReferenceLine y={0} stroke="var(--chart-baseline)" />
            {keys.map((k, i) => (
              <Line
                key={k}
                type="linear"
                dataKey={k}
                hide={hidden.has(k)}
                stroke={SERIES[i % SERIES.length]}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                activeDot={{ r: 4, strokeWidth: 2, stroke: 'var(--color-bg-card)' }}
                connectNulls
              >
                {directLabels && (
                  <LabelList
                    dataKey={k}
                    content={(p) => {
                      const { x, y, index } = p as { x?: number; y?: number; index?: number };
                      if (index !== lastIndex || x == null || y == null) return null;
                      return (
                        <text x={Number(x) + 8} y={Number(y)} dy={4} fontSize={11} fill="var(--color-text-secondary)">
                          {labelFor(k)}
                        </text>
                      );
                    }}
                  />
                )}
              </Line>
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="qc-legend" role="group" aria-label="Series">
        {keys.map((k, i) => (
          <button key={k} type="button" className={hidden.has(k) ? 'off' : ''} onClick={() => toggle(k)} aria-pressed={!hidden.has(k)}>
            <i style={{ background: SERIES[i % SERIES.length] }} /> {labelFor(k)}
          </button>
        ))}
      </div>
    </div>
  );
}
