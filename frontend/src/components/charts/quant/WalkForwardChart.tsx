import { useMemo, useState } from 'react';
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Cell,
} from 'recharts';
import { axisProps, gridProps, crosshair, signedPct } from './chartKit';

interface Window {
  test_start: string;
  test_end: string;
  test_return: number;
  test_trades: number;
  best_params?: Record<string, unknown>;
}

interface Row {
  label: string;
  ret: number;
  cum: number;
  trades: number;
  period: string;
  params: string;
}

/** Bar with only its data end rounded; the baseline end stays square. */
function DataEndBar(props: { x?: number; y?: number; width?: number; height?: number; fill?: string; value?: number }) {
  const { x = 0, y = 0, width = 0, height = 0, fill } = props;
  if (!width || !height) return null;
  const r = Math.min(4, width / 2, Math.abs(height));
  const top = Math.min(y, y + height);
  const h = Math.abs(height);
  const negative = height < 0 || (props.value ?? 0) < 0;
  const d = negative
    ? `M${x},${top} h${width} v${h - r} a${r},${r} 0 0 1 ${-r},${r} h${-(width - 2 * r)} a${r},${r} 0 0 1 ${-r},${-r} z`
    : `M${x},${top + h} v${-(h - r)} a${r},${r} 0 0 1 ${r},${-r} h${width - 2 * r} a${r},${r} 0 0 1 ${r},${r} v${h - r} z`;
  return <path d={d} fill={fill} />;
}

const fmtDate = (s: string) => s.split('T')[0];

/**
 * Out-of-sample results only: compounded return across test windows on top,
 * each window's own return below. Two panels, one axis each.
 */
export function WalkForwardChart({ windows }: { windows: Window[] }) {
  const [hover, setHover] = useState<number | null>(null);

  const rows = useMemo<Row[]>(() => {
    const out: Row[] = [];
    windows.forEach((w, i) => {
      const prev = out.length ? 1 + out[out.length - 1].cum / 100 : 1;
      const growth = prev * (1 + w.test_return);
      out.push({
        label: `W${i + 1}`,
        ret: w.test_return * 100,
        cum: (growth - 1) * 100,
        trades: w.test_trades,
        period: `${fmtDate(w.test_start)} → ${fmtDate(w.test_end)}`,
        params: Object.entries(w.best_params ?? {}).map(([k, v]) => `${k}=${v}`).join(', '),
      });
    });
    return out;
  }, [windows]);

  if (rows.length === 0) return null;
  const shown = hover != null ? rows[hover] : null;
  const last = rows[rows.length - 1];
  const wins = rows.filter((r) => r.ret > 0).length;

  const onMove = (s: { activeTooltipIndex?: number | string | null } | undefined) => {
    const i = s?.activeTooltipIndex;
    const idx = typeof i === 'string' ? Number(i) : i;
    setHover(typeof idx === 'number' && rows[idx] ? idx : null);
  };

  return (
    <div className="qc">
      <div className="qc-head">
        <div className="qc-readout">
          {shown ? (
            <>
              <div><span className="qc-k">{shown.label} test window</span><span className="qc-v">{shown.period}</span></div>
              <div><span className="qc-k">Window return</span><span className={`qc-v ${shown.ret >= 0 ? 'text-positive' : 'text-negative'}`}>{signedPct(shown.ret, 2)}</span></div>
              <div><span className="qc-k">Compounded so far</span><span className={`qc-v ${shown.cum >= 0 ? 'text-positive' : 'text-negative'}`}>{signedPct(shown.cum, 2)}</span></div>
              <div><span className="qc-k">Trades</span><span className="qc-v">{shown.trades}</span></div>
            </>
          ) : (
            <>
              <div><span className="qc-k">Out-of-sample, compounded</span><span className={`qc-v ${last.cum >= 0 ? 'text-positive' : 'text-negative'}`}>{signedPct(last.cum, 2)}</span></div>
              <div><span className="qc-k">Profitable windows</span><span className="qc-v">{wins} of {rows.length}</span></div>
              <div><span className="qc-k">Best / worst window</span><span className="qc-v">{signedPct(Math.max(...rows.map((r) => r.ret)), 1)} / {signedPct(Math.min(...rows.map((r) => r.ret)), 1)}</span></div>
            </>
          )}
        </div>
      </div>

      <div onMouseLeave={() => setHover(null)}>
        <ResponsiveContainer width="100%" height={190}>
          <ComposedChart data={rows} syncId="wf" margin={{ top: 8, right: 8, bottom: 0, left: 0 }} onMouseMove={onMove}>
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="label" hide />
            <YAxis {...axisProps} width={48} tickFormatter={(v: number) => `${v.toFixed(0)}%`} />
            <Tooltip content={() => null} cursor={crosshair} />
            <ReferenceLine y={0} stroke="var(--chart-baseline)" />
            <Line type="linear" dataKey="cum" stroke="var(--series-1)" strokeWidth={2} isAnimationActive={false}
              dot={{ r: 3, strokeWidth: 0, fill: 'var(--series-1)' }}
              activeDot={{ r: 5, strokeWidth: 2, stroke: 'var(--color-bg-card)', fill: 'var(--series-1)' }} />
          </ComposedChart>
        </ResponsiveContainer>
        <div className="qc-sublabel" style={{ marginLeft: 48 }}>Return in each test window</div>
        <ResponsiveContainer width="100%" height={170}>
          <ComposedChart data={rows} syncId="wf" margin={{ top: 4, right: 8, bottom: 0, left: 0 }} onMouseMove={onMove} barCategoryGap="22%">
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="label" {...axisProps} dy={6} interval={rows.length > 16 ? 'preserveStartEnd' : 0} />
            <YAxis {...axisProps} width={48} tickFormatter={(v: number) => `${v.toFixed(0)}%`} />
            <Tooltip content={() => null} cursor={{ fill: 'var(--color-bg-hover)' }} />
            <ReferenceLine y={0} stroke="var(--chart-baseline)" />
            <Bar dataKey="ret" shape={<DataEndBar />} isAnimationActive={false}>
              {rows.map((r, i) => (
                <Cell key={i} fill={r.ret >= 0 ? 'var(--color-up)' : 'var(--color-down)'} fillOpacity={hover == null || hover === i ? 0.85 : 0.4} />
              ))}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="qc-legend">
        <span><i style={{ background: 'var(--series-1)' }} /> Compounded out-of-sample return</span>
        <span><i style={{ background: 'var(--color-up)' }} /> Profitable window</span>
        <span><i style={{ background: 'var(--color-down)' }} /> Losing window</span>
      </div>
    </div>
  );
}
