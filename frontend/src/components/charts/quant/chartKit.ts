/**
 * Shared chart chrome so every chart reads as one system:
 * recessive grid and axes, ink text, colour only on the data.
 */

export const AXIS_TICK = {
  fill: 'var(--chart-axis)',
  fontSize: 11,
  fontFamily: 'var(--font-sans)',
} as const;

export const axisProps = {
  tick: AXIS_TICK,
  tickLine: false,
  axisLine: false,
} as const;

export const gridProps = {
  stroke: 'var(--chart-grid)',
  strokeDasharray: '0',
  vertical: false,
} as const;

export const crosshair = {
  stroke: 'var(--chart-crosshair)',
  strokeWidth: 1,
  strokeOpacity: 0.35,
} as const;

export const SERIES = [1, 2, 3, 4, 5, 6, 7, 8].map((n) => `var(--series-${n})`);

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** "Mar ’21" style ticks: short, unambiguous across years. */
export function tickDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${MONTHS[d.getMonth()]} ’${String(d.getFullYear()).slice(2)}`;
}

export function longDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

export function compactMoney(v: number, symbol = '$'): string {
  const a = Math.abs(v);
  const sign = v < 0 ? '−' : '';
  if (a >= 1e9) return `${sign}${symbol}${(a / 1e9).toFixed(2)}B`;
  if (a >= 1e6) return `${sign}${symbol}${(a / 1e6).toFixed(2)}M`;
  if (a >= 1e3) return `${sign}${symbol}${(a / 1e3).toFixed(a >= 1e5 ? 0 : 1)}K`;
  return `${sign}${symbol}${a.toFixed(0)}`;
}

export function signedPct(v: number, digits = 1): string {
  const sign = v > 0 ? '+' : v < 0 ? '−' : '';
  return `${sign}${Math.abs(v).toFixed(digits)}%`;
}

/** Evenly spaced tick values for a category axis so labels never collide. */
export function evenTicks<T>(rows: T[], key: keyof T, count = 6): string[] {
  if (rows.length === 0) return [];
  const step = Math.max(1, Math.floor((rows.length - 1) / (count - 1)));
  const out: string[] = [];
  for (let i = 0; i < rows.length; i += step) out.push(String(rows[i][key]));
  const last = String(rows[rows.length - 1][key]);
  if (out[out.length - 1] !== last) out[out.length - 1] = last;
  return out;
}

export type Range = '6M' | '1Y' | '3Y' | 'All';

/** Trim a dated series to the trailing window. */
export function sliceRange<T extends { date: string }>(rows: T[], range: Range): T[] {
  if (range === 'All' || rows.length === 0) return rows;
  const end = new Date(rows[rows.length - 1].date).getTime();
  const days = range === '6M' ? 182 : range === '1Y' ? 365 : 365 * 3;
  const start = end - days * 86_400_000;
  return rows.filter((r) => new Date(r.date).getTime() >= start);
}

/** Daily simple returns from an equity series. */
export function dailyReturns(equity: { date: string; equity: number }[]) {
  const out: { date: string; r: number }[] = [];
  for (let i = 1; i < equity.length; i++) {
    const prev = equity[i - 1].equity;
    if (prev > 0) out.push({ date: equity[i].date, r: equity[i].equity / prev - 1 });
  }
  return out;
}
