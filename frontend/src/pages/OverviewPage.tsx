import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { BrainCircuit, FlaskConical, ShieldCheck, GitBranch, Sigma, Play } from 'lucide-react';
import { useStrategies, useRecentBacktests } from '../hooks/apiHooks';
import { strategyKey, strategyLabel, familyLabel } from '../lib/strategies';
import { formatPct } from '../lib/utils';

/* ---------- Hero trace: a deterministic price walk + a strategy riding it ---------- */

function mulberry32(seed: number) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function useTrace() {
  return useMemo(() => {
    const rnd = mulberry32(7);
    const n = 120;
    const price: number[] = [100];
    for (let i = 1; i < n; i++) {
      const drift = Math.sin(i / 14) * 0.55 + 0.08;
      price.push(price[i - 1] * (1 + (drift + (rnd() - 0.5) * 2.6) / 100));
    }
    // Simple fast/slow EMA cross, long-only, to generate the equity line and markers
    const ema = (k: number) => {
      const a = 2 / (k + 1); const out: number[] = [price[0]];
      for (let i = 1; i < n; i++) out.push(a * price[i] + (1 - a) * out[i - 1]);
      return out;
    };
    const fast = ema(6); const slow = ema(18);
    const equity: number[] = [100];
    const markers: { i: number; type: 'buy' | 'sell' }[] = [];
    let inPos = false;
    for (let i = 1; i < n; i++) {
      const r = price[i] / price[i - 1] - 1;
      equity.push(equity[i - 1] * (1 + (inPos ? r : 0)));
      const cross = fast[i] - slow[i];
      if (!inPos && cross > 0 && fast[i - 1] - slow[i - 1] <= 0) { inPos = true; markers.push({ i, type: 'buy' }); }
      if (inPos && cross < 0 && fast[i - 1] - slow[i - 1] >= 0) { inPos = false; markers.push({ i, type: 'sell' }); }
    }

    const W = 560, H = 220, pad = 10;
    const all = [...price, ...equity];
    const lo = Math.min(...all), hi = Math.max(...all);
    const x = (i: number) => pad + (i / (n - 1)) * (W - pad * 2);
    const y = (v: number) => H - pad - ((v - lo) / (hi - lo)) * (H - pad * 2);
    const path = (arr: number[]) => arr.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');

    return {
      W, H,
      pricePath: path(price),
      equityPath: path(equity),
      areaPath: `${path(equity)} L${x(n - 1)} ${H - pad} L${x(0)} ${H - pad} Z`,
      markers: markers.map((m) => ({ ...m, cx: x(m.i), cy: y(price[m.i]), delay: 0.2 + (m.i / n) * 2.4 })),
    };
  }, []);
}

function HeroTrace({ strategyCount }: { strategyCount: number | null }) {
  const t = useTrace();
  return (
    <div className="pipeline" aria-label="Illustration of a strategy trading a price series">
      <div className="pipeline-head">
        <span>Illustrative run · EMA crossover on a simulated series</span>
        <span className="row" style={{ gap: 12 }}>
          <span className="row" style={{ gap: 5 }}><svg width="14" height="2"><rect width="14" height="2" fill="var(--color-text-muted)" /></svg>Price</span>
          <span className="row" style={{ gap: 5 }}><svg width="14" height="2"><rect width="14" height="2" fill="var(--color-primary)" /></svg>Strategy equity</span>
        </span>
      </div>
      <svg className="pipeline-trace" viewBox={`0 0 ${t.W} ${t.H}`} role="img" aria-hidden>
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} className="gridline" x1={0} x2={t.W} y1={t.H * f} y2={t.H * f} strokeDasharray="2 6" />
        ))}
        <path className="trace-area" d={t.areaPath} opacity={0.6} />
        <path className="trace-price" d={t.pricePath} fill="none" strokeWidth={1.4} />
        <path
          className="trace-equity"
          d={t.equityPath}
          fill="none"
          strokeWidth={2.4}
          strokeLinejoin="round"
          style={{ ['--len' as string]: 1400 }}
        />
        {t.markers.map((m) => (
          <g key={m.i} className="marker" style={{ animationDelay: `${m.delay}s` }}>
            {m.type === 'buy'
              ? <path className="marker-buy" d={`M${m.cx} ${m.cy + 7} l5 8 h-10 z`} />
              : <path className="marker-sell" d={`M${m.cx} ${m.cy - 7} l5 -8 h-10 z`} />}
          </g>
        ))}
      </svg>
      <div className="pipeline-stages">
        <div className="stage"><b>5</b><span>data providers</span></div>
        <div className="stage model"><b>111</b><span>engineered features</span></div>
        <div className="stage"><b>{strategyCount ?? '—'}</b><span>registered strategies</span></div>
        <div className="stage"><b>3</b><span>optimisers</span></div>
        <div className="stage"><b>30+</b><span>risk metrics per run</span></div>
        <div className="stage model"><b>2</b><span>ML classifiers</span></div>
      </div>
    </div>
  );
}

/* ---------- Page ---------- */

const FLOW = [
  {
    to: '/backtest', idx: 'Step 1', title: 'Backtest',
    body: 'Run one strategy over a symbol’s history and read its equity curve, drawdowns and tear sheet.',
  },
  {
    to: '/compare', idx: 'Step 2', title: 'Compare',
    body: 'Put several strategies on the same data and rank them on risk-adjusted return, not raw P&L.',
  },
  {
    to: '/optimization', idx: 'Step 3', title: 'Optimise',
    body: 'Search parameter space with grid, random or genetic search and see how sensitive the result is.',
  },
  {
    to: '/walkforward', idx: 'Step 4', title: 'Validate',
    body: 'Re-fit on rolling windows and score only on unseen data, to tell real edge from overfitting.',
  },
];

export const OverviewPage: React.FC = () => {
  const { data: strategies, isError: strategiesError } = useStrategies();
  const { data: runs = [], isError: runsError } = useRecentBacktests(6);

  const families = useMemo(() => {
    const map = new Map<string, NonNullable<typeof strategies>>();
    (strategies ?? []).forEach((s) => map.set(s.type, [...(map.get(s.type) ?? []), s]));
    return [...map.entries()];
  }, [strategies]);

  return (
    <div>
      {/* Hero */}
      <section className="ov-hero">
        <div>
          <h1 className="ov-title">Find out if a trading idea works before it costs anything.</h1>
          <p className="ov-lede">
            TSRL is a research lab for systematic strategies. Backtest rule-based and machine-learning
            models on US, Indian and crypto markets, tune their parameters, and check whether the edge
            survives on data the model has never seen.
          </p>
          <div className="ov-cta">
            <Link to="/backtest" className="btn btn-primary btn-lg"><Play size={16} /> Run a backtest</Link>
            <Link to="/ml" className="btn btn-secondary btn-lg"><BrainCircuit size={16} /> Open the ML Lab</Link>
          </div>
        </div>
        <HeroTrace strategyCount={strategies?.length ?? null} />
      </section>

      {/* Research loop */}
      <section className="ov-section">
        <div className="ov-section-head">
          <div>
            <h2>The research loop</h2>
            <p>Each page is one stage of taking an idea from hunch to something you’d trust with capital.</p>
          </div>
        </div>
        <div className="flow">
          {FLOW.map((f) => (
            <Link key={f.to} to={f.to} className="flow-step">
              <span className="idx">{f.idx}</span>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* ML callout */}
      <section className="ov-section">
        <div className="ml-callout">
          <div>
            <span className="badge badge-model"><BrainCircuit size={12} /> Machine learning</span>
            <h2 style={{ marginTop: 'var(--spacing-md)' }}>Models that only learn from the past</h2>
            <p>
              Random Forest and Gradient Boosting classifiers predict a three-way label (up, down, flat) and trade
              on it. They’re refit on an expanding window inside the backtest, with an embargo equal to the
              label horizon so no training label peeks at prices the model hasn’t reached yet.
            </p>
            <Link to="/ml" className="btn btn-secondary" style={{ marginTop: 'var(--spacing-lg)', textDecoration: 'none' }}>
              Train a model
            </Link>
          </div>
          <ul className="ml-points">
            <li><Sigma size={18} /><span><b>111 engineered features.</b> Lags, rolling statistics, RSI, MACD, ATR, Bollinger position, MFI, CCI and volume ratios.</span></li>
            <li><ShieldCheck size={18} /><span><b>Leakage-free by construction.</b> Each refit only uses labels whose forward window has already closed, and a unit test checks it.</span></li>
            <li><GitBranch size={18} /><span><b>Same engine, same costs.</b> ML predictions run through the identical event-driven engine and tear sheet as rule-based strategies.</span></li>
          </ul>
        </div>
      </section>

      {/* Registry + runs */}
      <section className="ov-section grid-2" style={{ alignItems: 'start' }}>
        <div>
          <div className="ov-section-head">
            <div>
              <h2>Strategy registry</h2>
              <p>Loaded live from the API. New strategies appear here once they’re registered with a decorator.</p>
            </div>
          </div>
          {strategiesError ? (
            <p className="text-muted">Start the backend to load the registry.</p>
          ) : (
            <div className="registry">
              {families.map(([family, list]) => (
                <div key={family} className="registry-family">
                  <h3>{familyLabel(family)} <span className="text-muted">{list.length}</span></h3>
                  <ul>
                    {list.map((s) => (
                      <li key={strategyKey(s)}>
                        <span>{strategyLabel(s)}</span>
                        <code>{strategyKey(s)}</code>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="ov-section-head">
            <div>
              <h2>Recent runs</h2>
              <p>The latest backtests saved to the database.</p>
            </div>
            <Link to="/backtest" className="btn btn-ghost" style={{ textDecoration: 'none' }}>
              <FlaskConical size={15} /> New run
            </Link>
          </div>
          {runsError ? (
            <p className="text-muted">Start the backend to see saved runs.</p>
          ) : runs.length === 0 ? (
            <p className="text-muted">No runs yet. Your first backtest will show up here.</p>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Symbol</th>
                    <th className="t-right">Trades</th>
                    <th className="t-right">Return</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((r) => (
                    <tr key={r.id}>
                      <td>
                        {strategyLabel(r.strategy ?? r.name)}
                        {r.strategy?.startsWith('ml_') && <span className="badge badge-model" style={{ marginLeft: 6 }}>ML</span>}
                      </td>
                      <td>{r.symbol}</td>
                      <td className="t-right">{r.total_trades ?? '—'}</td>
                      <td className={`t-right ${(r.total_return ?? 0) >= 0 ? 'text-positive' : 'text-negative'}`}>
                        {formatPct(r.total_return)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* Under the hood */}
      <section className="ov-section">
        <div className="ov-section-head">
          <div>
            <h2>Under the hood</h2>
            <p>A clean-architecture Python backend with a typed React client.</p>
          </div>
        </div>
        <div className="stack-strip">
          <div>
            <h4>Engine</h4>
            <p>Event-driven and vectorised backtesters, portfolio rebalancing, grid / random / genetic optimisers and walk-forward analysis.</p>
          </div>
          <div>
            <h4>Models &amp; analytics</h4>
            <p>scikit-learn ensembles on a 111-feature pipeline. Sharpe, Sortino, Omega, VaR / CVaR, Kelly, Ulcer index and more.</p>
          </div>
          <div>
            <h4>Data &amp; API</h4>
            <p>FastAPI over SQLAlchemy and SQLite. Yahoo, NSE, Alpha Vantage, FMP and Finnhub providers behind one interface, with caching.</p>
          </div>
          <div>
            <h4>Client</h4>
            <p>React 19, TypeScript, React Query and Zustand. Charts in Recharts, validation with Zod.</p>
          </div>
        </div>
      </section>
    </div>
  );
};
