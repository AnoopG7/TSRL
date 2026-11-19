import React from 'react';
import { formatMoney } from '../../lib/utils';

type Metrics = Record<string, number | null | undefined>;

type Fmt = 'pct' | 'ratio' | 'money' | 'int';

interface Row {
  key: string;
  label: string;
  fmt: Fmt;
  /** Which sign reads as good. Omit for neutral. */
  good?: 'up' | 'down';
}

const SECTIONS: { title: string; rows: Row[] }[] = [
  {
    title: 'Return',
    rows: [
      { key: 'cagr', label: 'CAGR', fmt: 'pct', good: 'up' },
      { key: 'volatility', label: 'Volatility', fmt: 'pct' },
      { key: 'expectancy', label: 'Expectancy / trade', fmt: 'money', good: 'up' },
      { key: 'kelly_criterion', label: 'Kelly fraction', fmt: 'ratio' },
    ],
  },
  {
    title: 'Risk-adjusted',
    rows: [
      { key: 'sharpe_ratio', label: 'Sharpe', fmt: 'ratio', good: 'up' },
      { key: 'sortino_ratio', label: 'Sortino', fmt: 'ratio', good: 'up' },
      { key: 'calmar_ratio', label: 'Calmar', fmt: 'ratio', good: 'up' },
      { key: 'omega_ratio', label: 'Omega', fmt: 'ratio', good: 'up' },
      { key: 'gain_to_pain', label: 'Gain to pain', fmt: 'ratio', good: 'up' },
      { key: 'upside_ratio', label: 'Upside ratio', fmt: 'ratio' },
    ],
  },
  {
    title: 'Tail & drawdown',
    rows: [
      { key: 'var_95', label: 'VaR 95%', fmt: 'pct' },
      { key: 'cvar_95', label: 'CVaR 95%', fmt: 'pct' },
      { key: 'var_99', label: 'VaR 99%', fmt: 'pct' },
      { key: 'cvar_99', label: 'CVaR 99%', fmt: 'pct' },
      { key: 'ulcer_index', label: 'Ulcer index', fmt: 'ratio' },
      { key: 'downside_risk', label: 'Downside deviation', fmt: 'pct' },
      { key: 'recovery_factor', label: 'Recovery factor', fmt: 'ratio', good: 'up' },
      { key: 'risk_of_ruin', label: 'Risk of ruin', fmt: 'pct' },
    ],
  },
  {
    title: 'Trades',
    rows: [
      { key: 'winning_trades', label: 'Winners', fmt: 'int' },
      { key: 'losing_trades', label: 'Losers', fmt: 'int' },
      { key: 'avg_win', label: 'Average win', fmt: 'money', good: 'up' },
      { key: 'avg_loss', label: 'Average loss', fmt: 'money', good: 'up' },
      { key: 'win_loss_ratio', label: 'Win / loss size', fmt: 'ratio' },
      { key: 'skewness', label: 'Return skew', fmt: 'ratio' },
      { key: 'kurtosis', label: 'Return kurtosis', fmt: 'ratio' },
    ],
  },
];

function format(v: number, fmt: Fmt): string {
  switch (fmt) {
    case 'pct': return `${(v * 100).toFixed(2)}%`;
    case 'money': return formatMoney(v);
    case 'int': return Math.round(v).toLocaleString();
    default: return v.toFixed(2);
  }
}

/** Risk metrics from the engine, grouped like a tear sheet. */
export const RiskPanel: React.FC<{ metrics: Metrics }> = ({ metrics }) => {
  const sections = SECTIONS.map((s) => ({
    ...s,
    rows: s.rows.filter((r) => typeof metrics[r.key] === 'number' && Number.isFinite(metrics[r.key] as number)),
  })).filter((s) => s.rows.length > 0);

  if (sections.length === 0) return null;

  return (
    <div className="kv-grid">
      {sections.map((s) => (
        <React.Fragment key={s.title}>
          <div className="kv-section-title">{s.title}</div>
          {s.rows.map((r) => {
            const v = metrics[r.key] as number;
            const tone = r.good === 'up' ? (v > 0 ? 'positive' : v < 0 ? 'negative' : '') : '';
            return (
              <div className="kv-row" key={r.key}>
                <span className="kv-label">{r.label}</span>
                <span className={`kv-value ${tone}`}>{format(v, r.fmt)}</span>
              </div>
            );
          })}
        </React.Fragment>
      ))}
    </div>
  );
};

