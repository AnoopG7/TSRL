import React, { useMemo, useState } from 'react';
import { LineChart, Activity, BarChart3, CalendarRange, Gauge, ListOrdered } from 'lucide-react';
import { MonthlyReturnsHeatmap } from '../charts';
import { PerformanceChart } from '../charts/quant/PerformanceChart';
import { RollingSharpeChart } from '../charts/quant/RollingSharpeChart';
import { ReturnHistogram } from '../charts/quant/ReturnHistogram';
import { RiskPanel } from '../ui/RiskPanel';
import { formatMoney, formatPct, formatCurrency } from '../../lib/utils';
import type {
  BacktestResult, Trade, EquityCurvePoint, DrawdownPoint, MonthlyReturn,
} from '../../lib/schemas';

interface BacktestResultsProps {
  result: BacktestResult;
  trades: Trade[];
  equityCurve: EquityCurvePoint[];
  drawdownSeries?: DrawdownPoint[];
  monthlyReturns?: MonthlyReturn[];
  /** Short line describing the run, e.g. "EMA Crossover on AAPL". */
  caption?: React.ReactNode;
}

type ChartTab = 'equity' | 'rolling' | 'dist' | 'monthly';

export const BacktestResults: React.FC<BacktestResultsProps> = ({
  result, trades, equityCurve, drawdownSeries = [], monthlyReturns = [], caption,
}) => {
  const [chartTab, setChartTab] = useState<ChartTab>('equity');
  const m = result.metrics;
  const initialCapital = result.final_capital / (1 + result.total_return);
  const profit = result.final_capital - initialCapital;
  const winners = typeof m.winning_trades === 'number' ? m.winning_trades : null;
  const losers = typeof m.losing_trades === 'number' ? m.losing_trades : null;

  const tradeStats = useMemo(() => {
    if (!trades.length) return null;
    // The API returns only the first few trades, so only badge a row when it is the
    // best / worst trade of the whole run (per the engine's own metrics).
    const near = (a: number, b: number | null | undefined) => typeof b === 'number' && Math.abs(a - b) < 0.01;
    const best = trades.find((t) => near(t.pnl, m.largest_win)) ?? null;
    const worst = trades.find((t) => near(t.pnl, m.largest_loss)) ?? null;
    const avgHold = trades.reduce((sum, t) =>
      sum + (new Date(t.exit_time).getTime() - new Date(t.entry_time).getTime()) / 86_400_000, 0) / trades.length;
    return { best, worst, avgHold };
  }, [trades, m.largest_win, m.largest_loss]);

  const tabs: { id: ChartTab; label: string; icon: React.ReactNode; show: boolean }[] = [
    { id: 'equity', label: 'Equity & drawdown', icon: <LineChart size={14} />, show: equityCurve.length > 0 },
    { id: 'rolling', label: 'Rolling Sharpe', icon: <Activity size={14} />, show: equityCurve.length > 80 },
    { id: 'dist', label: 'Return distribution', icon: <BarChart3 size={14} />, show: equityCurve.length > 20 },
    { id: 'monthly', label: 'Monthly', icon: <CalendarRange size={14} />, show: monthlyReturns.length > 0 },
  ];

  return (
    <div className="animate-fadeIn">
      {/* Headline numbers */}
      <div className="result-hero">
        <div className="lead">
          <div className="label">Total return{caption ? <> · {caption}</> : null}</div>
          <div className={`big ${result.total_return >= 0 ? 'text-positive' : 'text-negative'}`}>
            {formatPct(result.total_return)}
          </div>
          <div className="note">
            {formatMoney(profit)} on {formatMoney(initialCapital)} · ends at {formatMoney(result.final_capital)}
          </div>
        </div>
        <div>
          <div className="label">Sharpe ratio</div>
          <div className={`mid ${m.sharpe_ratio >= 1 ? 'text-positive' : m.sharpe_ratio < 0 ? 'text-negative' : ''}`}>
            {m.sharpe_ratio.toFixed(2)}
          </div>
          <div className="note">Sortino {m.sortino_ratio.toFixed(2)}</div>
        </div>
        <div>
          <div className="label">Max drawdown</div>
          <div className="mid text-negative">−{m.max_drawdown_pct.toFixed(2)}%</div>
          <div className="note">Profit factor {m.profit_factor.toFixed(2)}</div>
        </div>
        <div>
          <div className="label">Win rate</div>
          <div className="mid">{(m.win_rate * 100).toFixed(1)}%</div>
          <div className="note">
            {result.total_trades} trades{winners != null && losers != null ? ` · ${winners}W / ${losers}L` : ''}
          </div>
        </div>
      </div>

      {/* Charts */}
      {tabs.some((t) => t.show) && (
        <section className="card">
          <div className="card-header card-row">
            <h2 className="card-title">Performance</h2>
            <div className="tab-nav" role="tablist">
              {tabs.filter((t) => t.show).map((t) => (
                <button
                  key={t.id}
                  role="tab"
                  aria-selected={chartTab === t.id}
                  className={`tab-item ${chartTab === t.id ? 'tab-active' : ''}`}
                  onClick={() => setChartTab(t.id)}
                >
                  {t.icon} {t.label}
                </button>
              ))}
            </div>
          </div>
          <div className="card-content">
            {chartTab === 'equity' && equityCurve.length > 0 && (
              <PerformanceChart equity={equityCurve} drawdown={drawdownSeries} initialCapital={initialCapital} />
            )}
            {chartTab === 'rolling' && <RollingSharpeChart equity={equityCurve} />}
            {chartTab === 'dist' && <ReturnHistogram equity={equityCurve} />}
            {chartTab === 'monthly' && monthlyReturns.length > 0 && <MonthlyReturnsHeatmap data={monthlyReturns} />}
          </div>
        </section>
      )}

      {/* Tear sheet */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title"><Gauge size={16} /> Risk tear sheet</h2>
          <p className="card-description">
            {Object.values(m).filter((v) => typeof v === 'number').length} metrics computed by the analytics engine for this run
            {typeof result.execution_time_ms === 'number' && <> · simulated in {result.execution_time_ms.toFixed(0)} ms</>}
          </p>
        </div>
        <div className="card-content">
          <RiskPanel metrics={m} />
        </div>
      </section>

      {/* Trades */}
      {trades.length > 0 && (
        <section className="card">
          <div className="card-header card-row">
            <div>
              <h2 className="card-title"><ListOrdered size={16} /> Trade log</h2>
              <p className="card-description">
                First {trades.length} of {result.total_trades} trades
                {tradeStats && <> · these average {tradeStats.avgHold.toFixed(1)} days held</>}
              </p>
            </div>
          </div>
          <div className="card-content">
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Entry</th>
                    <th>Exit</th>
                    <th>Side</th>
                    <th className="t-right">Entry price</th>
                    <th className="t-right">Exit price</th>
                    <th className="t-right">P&amp;L</th>
                    <th className="t-right">Return</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((t, i) => {
                    const isBest = tradeStats && t === tradeStats.best;
                    const isWorst = tradeStats && t === tradeStats.worst;
                    return (
                      <tr key={i} className={isBest ? 'row-best' : isWorst ? 'row-worst' : undefined}>
                        <td>{new Date(t.entry_time).toLocaleDateString()}</td>
                        <td>{new Date(t.exit_time).toLocaleDateString()}</td>
                        <td>
                          <span className={t.side === 'LONG' ? 'badge badge-success' : 'badge badge-danger'}>
                            {t.side === 'LONG' ? 'Long' : 'Short'}
                          </span>
                        </td>
                        <td className="t-right">{formatCurrency(t.entry_price)}</td>
                        <td className="t-right">{formatCurrency(t.exit_price)}</td>
                        <td className={`t-right ${t.pnl >= 0 ? 'text-positive' : 'text-negative'}`}>
                          {formatMoney(t.pnl)}
                          {isBest && <span className="badge badge-success" style={{ marginLeft: 6 }}>Best of run</span>}
                          {isWorst && <span className="badge badge-danger" style={{ marginLeft: 6 }}>Worst of run</span>}
                        </td>
                        <td className={`t-right ${t.pnl_pct >= 0 ? 'text-positive' : 'text-negative'}`}>
                          {formatPct(t.pnl_pct / 100)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
