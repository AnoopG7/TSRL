import { useMemo, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Cell,
} from 'recharts';
import { axisProps, gridProps, dailyReturns, signedPct } from './chartKit';

interface Props {
  equity: { date: string; equity: number }[];
}

interface Bin { mid: number; lo: number; hi: number; count: number }

/**
 * Distribution of daily returns of the marked-to-market equity curve.
 * Flat days (no open position) are excluded so they don't swamp the zero bin.
 */
export function ReturnHistogram({ equity }: Props) {
  const [hover, setHover] = useState<Bin | null>(null);

  const data = useMemo(() => {
    const rets = dailyReturns(equity).map((d) => d.r * 100).filter((r) => Math.abs(r) > 1e-6);
    if (rets.length < 10) return null;
    const sorted = [...rets].sort((a, b) => a - b);
    const q = (p: number) => sorted[Math.min(sorted.length - 1, Math.max(0, Math.floor(p * sorted.length)))];
    // Clip the axis to the 1st–99th percentile so one outlier day doesn't flatten the shape.
    const lo = q(0.01);
    const hi = q(0.99);
    const nBins = 31;
    const width = (hi - lo) / nBins || 0.1;
    const bins: Bin[] = Array.from({ length: nBins }, (_, i) => ({
      lo: lo + i * width, hi: lo + (i + 1) * width, mid: lo + (i + 0.5) * width, count: 0,
    }));
    for (const r of rets) {
      const i = Math.min(nBins - 1, Math.max(0, Math.floor((r - lo) / width)));
      bins[i].count += 1;
    }
    const mean = rets.reduce((s, r) => s + r, 0) / rets.length;
    const var95 = q(0.05);
    const tail = sorted.filter((r) => r <= var95);
    const cvar95 = tail.reduce((s, r) => s + r, 0) / (tail.length || 1);
    const positive = rets.filter((r) => r > 0).length / rets.length;
    return { bins, mean, var95, cvar95, positive, n: rets.length, width };
  }, [equity]);

  if (!data) {
    return <p className="text-muted">Too few invested days to draw a distribution.</p>;
  }

  // Snap reference lines to bin centres, since the x axis is categorical.
  const nearest = (v: number) => data.bins.reduce((b, x) => (Math.abs(x.mid - v) < Math.abs(b.mid - v) ? x : b)).mid;

  return (
    <div className="qc">
      <div className="qc-head">
        <div className="qc-readout">
          {hover ? (
            <>
              <div>
                <span className="qc-k">Return</span>
                <span className="qc-v">{signedPct(hover.lo, 2)} to {signedPct(hover.hi, 2)}</span>
              </div>
              <div>
                <span className="qc-k">Count</span>
                <span className="qc-v">{hover.count} ({((hover.count / data.n) * 100).toFixed(1)}%)</span>
              </div>
            </>
          ) : (
            <>
              <div>
                <span className="qc-k">Invested days</span>
                <span className="qc-v">{data.n}</span>
              </div>
              <div>
                <span className="qc-k">Up days</span>
                <span className="qc-v">{(data.positive * 100).toFixed(0)}%</span>
              </div>
              <div>
                <span className="qc-k">Mean</span>
                <span className={`qc-v ${data.mean >= 0 ? 'text-positive' : 'text-negative'}`}>{signedPct(data.mean, 3)}</span>
              </div>
              <div>
                <span className="qc-k">VaR 95%</span>
                <span className="qc-v text-negative">{signedPct(data.var95, 2)}</span>
              </div>
              <div>
                <span className="qc-k">CVaR 95%</span>
                <span className="qc-v text-negative">{signedPct(data.cvar95, 2)}</span>
              </div>
            </>
          )}
        </div>
      </div>

      <div onMouseLeave={() => setHover(null)}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={data.bins}
            margin={{ top: 22, right: 8, bottom: 0, left: 0 }}
            barCategoryGap={2}
            onMouseMove={(s) => {
              const i = s?.activeTooltipIndex;
              const idx = typeof i === 'string' ? Number(i) : i;
              setHover(typeof idx === 'number' ? data.bins[idx] ?? null : null);
            }}
          >
            <CartesianGrid {...gridProps} />
            <XAxis
              dataKey="mid"
              {...axisProps}
              tickFormatter={(v: number) => (Math.abs(v) < 0.05 ? '0%' : `${v.toFixed(1)}%`)}
              interval={4}
              dy={6}
            />
            <YAxis {...axisProps} width={36} allowDecimals={false} />
            <Tooltip content={() => null} cursor={{ fill: 'var(--color-bg-hover)' }} />
            <Bar dataKey="count" radius={[3, 3, 0, 0]} isAnimationActive={false}>
              {data.bins.map((b) => (
                <Cell
                  key={b.mid}
                  fill={b.mid < 0 ? 'var(--color-down)' : 'var(--color-up)'}
                  fillOpacity={b.mid <= data.var95 ? 0.95 : 0.55}
                />
              ))}
            </Bar>
            <ReferenceLine x={nearest(data.var95)} stroke="var(--color-down)" strokeDasharray="4 3"
              label={{ value: 'VaR 95%', position: 'top', fill: 'var(--color-text-secondary)', fontSize: 11 }} />
            <ReferenceLine x={nearest(data.mean)} stroke="var(--color-text-primary)" strokeOpacity={0.6}
              label={{ value: 'Mean', position: 'top', fill: 'var(--color-text-secondary)', fontSize: 11 }} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="qc-note">
        Daily returns on days with an open position, binned at {data.width.toFixed(2)}% width. Axis trimmed to the
        1st–99th percentile; darker bars are the worst 5% of days.
      </p>
    </div>
  );
}
