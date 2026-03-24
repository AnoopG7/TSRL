import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Target, AlertCircle, DollarSign, TrendingUp, TrendingDown, Activity, BarChart3, LineChart } from 'lucide-react';
import { BacktestConfigSchema } from '../lib/schemas';
import type { BacktestConfig, Strategy } from '../lib/schemas';
import { useBacktestStore } from '../store';
import { EquityCurveChart, DrawdownChart, MonthlyReturnsHeatmap } from '../components/charts';

interface BacktestPageProps {
  strategies: Strategy[];
  onRunBacktest: (config: BacktestConfig) => Promise<void>;
}

export const BacktestPage: React.FC<BacktestPageProps> = ({
  strategies,
  onRunBacktest,
}) => {
  const { result, trades, loading, error, equityCurve, drawdownSeries, monthlyReturns } = useBacktestStore();
  const [chartTab, setChartTab] = useState<'equity' | 'drawdown' | 'monthly'>('equity');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BacktestConfig>({
    resolver: zodResolver(BacktestConfigSchema),
    defaultValues: {
      strategy_name: strategies[0]?.registry_key || strategies[0]?.name || '',
      symbol: 'AAPL',
      start_date: '2023-01-01',
      end_date: '2024-01-01',
      initial_capital: 100000,
    },
  });

  const onSubmit = async (data: BacktestConfig) => {
    await onRunBacktest(data);
  };

  const hasChartData = equityCurve.length > 0 || drawdownSeries.length > 0 || monthlyReturns.length > 0;

  return (
    <div className="animate-fadeIn">
      {/* Configuration Form */}
      <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <Target size={20} style={{ color: 'var(--color-accent-400)' }} />
            <h2 className="card-title">Backtest Configuration</h2>
          </div>
          <p className="card-description">Configure your strategy parameters and run backtests</p>
        </div>
        <div className="card-content">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--spacing-md)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <div className="form-group">
                <label className="form-label">Strategy</label>
                <select className="form-input" {...register('strategy_name')}>
                  {strategies.map((s) => (
                    <option key={s.registry_key || s.name} value={s.registry_key || s.name}>
                      {s.name} ({s.type})
                    </option>
                  ))}
                </select>
                {errors.strategy_name && (
                  <span className="form-error">{errors.strategy_name.message}</span>
                )}
              </div>
              <div className="form-group">
                <label className="form-label">Symbol</label>
                <input type="text" className="form-input" {...register('symbol')} placeholder="AAPL" />
                {errors.symbol && <span className="form-error">{errors.symbol.message}</span>}
              </div>
              <div className="form-group">
                <label className="form-label">Start Date</label>
                <input type="date" className="form-input" {...register('start_date')} />
                {errors.start_date && <span className="form-error">{errors.start_date.message}</span>}
              </div>
              <div className="form-group">
                <label className="form-label">End Date</label>
                <input type="date" className="form-input" {...register('end_date')} />
                {errors.end_date && <span className="form-error">{errors.end_date.message}</span>}
              </div>
              <div className="form-group">
                <label className="form-label">Initial Capital</label>
                <input type="number" className="form-input" {...register('initial_capital', { valueAsNumber: true })} />
                {errors.initial_capital && <span className="form-error">{errors.initial_capital.message}</span>}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Running...' : 'Run Backtest'}
              </button>
            </div>
          </form>
          {error && (
            <div className="error-message">
              <AlertCircle size={16} />
              {error}
            </div>
          )}
        </div>
      </section>

      {result && (
        <>
          {/* Performance Summary */}
          <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <div className="card-header">
              <h2 className="card-title">Performance Summary</h2>
            </div>
            <div className="card-content">
              <div className="metric-grid">
                <MetricCard label="Final Capital" value={`$${result.final_capital.toLocaleString()}`} icon={<DollarSign size={16} />} />
                <MetricCard label="Total Return" value={`${(result.total_return * 100).toFixed(2)}%`}
                  icon={result.total_return >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  positive={result.total_return >= 0} negative={result.total_return < 0} />
                <MetricCard label="Total Trades" value={result.total_trades.toString()} icon={<Activity size={16} />} />
                <MetricCard label="Sharpe Ratio" value={result.metrics.sharpe_ratio.toFixed(2)}
                  positive={result.metrics.sharpe_ratio >= 0} negative={result.metrics.sharpe_ratio < 0} />
                <MetricCard label="Max Drawdown" value={`${result.metrics.max_drawdown_pct.toFixed(2)}%`} negative />
                <MetricCard label="Win Rate" value={`${(result.metrics.win_rate * 100).toFixed(1)}%`} />
                <MetricCard label="Sortino Ratio" value={result.metrics.sortino_ratio.toFixed(2)}
                  positive={result.metrics.sortino_ratio >= 0} negative={result.metrics.sortino_ratio < 0} />
                <MetricCard label="Profit Factor" value={result.metrics.profit_factor.toFixed(2)} />
              </div>
            </div>
          </section>

          {/* Charts Section */}
          {hasChartData && (
            <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
              <div className="card-header">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <h2 className="card-title">Analytics</h2>
                  <div className="tab-nav">
                    <button
                      className={`tab-item ${chartTab === 'equity' ? 'tab-active' : ''}`}
                      onClick={() => setChartTab('equity')}
                    >
                      <LineChart size={14} /> Equity Curve
                    </button>
                    <button
                      className={`tab-item ${chartTab === 'drawdown' ? 'tab-active' : ''}`}
                      onClick={() => setChartTab('drawdown')}
                    >
                      <TrendingDown size={14} /> Drawdown
                    </button>
                    <button
                      className={`tab-item ${chartTab === 'monthly' ? 'tab-active' : ''}`}
                      onClick={() => setChartTab('monthly')}
                    >
                      <BarChart3 size={14} /> Monthly Returns
                    </button>
                  </div>
                </div>
              </div>
              <div className="card-content">
                {chartTab === 'equity' && equityCurve.length > 0 && (
                  <EquityCurveChart data={equityCurve} initialCapital={result.final_capital / (1 + result.total_return)} />
                )}
                {chartTab === 'drawdown' && drawdownSeries.length > 0 && (
                  <DrawdownChart data={drawdownSeries} />
                )}
                {chartTab === 'monthly' && monthlyReturns.length > 0 && (
                  <MonthlyReturnsHeatmap data={monthlyReturns} />
                )}
              </div>
            </section>
          )}

          {/* Trades Table */}
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">Recent Trades</h2>
            </div>
            <div className="card-content">
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Entry</th>
                      <th>Exit</th>
                      <th>Side</th>
                      <th style={{ textAlign: 'right' }}>Entry Price</th>
                      <th style={{ textAlign: 'right' }}>Exit Price</th>
                      <th style={{ textAlign: 'right' }}>P&L</th>
                      <th style={{ textAlign: 'right' }}>P&L %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.slice(0, 10).map((trade, idx) => (
                      <tr key={idx}>
                        <td>{new Date(trade.entry_time).toLocaleDateString()}</td>
                        <td>{new Date(trade.exit_time).toLocaleDateString()}</td>
                        <td>
                          <span className={trade.side === 'LONG' ? 'badge badge-success' : 'badge badge-danger'}>
                            {trade.side}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }}>${trade.entry_price.toFixed(2)}</td>
                        <td style={{ textAlign: 'right' }}>${trade.exit_price.toFixed(2)}</td>
                        <td className={trade.pnl >= 0 ? 'text-positive' : 'text-negative'} style={{ textAlign: 'right', fontWeight: 500 }}>
                          ${trade.pnl.toFixed(2)}
                        </td>
                        <td className={trade.pnl_pct >= 0 ? 'text-positive' : 'text-negative'} style={{ textAlign: 'right', fontWeight: 500 }}>
                          {trade.pnl_pct.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

interface MetricCardProps {
  label: string;
  value: string;
  icon?: React.ReactNode;
  positive?: boolean;
  negative?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, icon, positive, negative }) => {
  let valueClass = '';
  if (positive) valueClass = 'metric-positive';
  if (negative) valueClass = 'metric-negative';

  return (
    <div className="metric-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem', marginBottom: '0.25rem', color: 'var(--color-text-secondary)' }}>
        {icon}
        <span style={{ fontSize: '0.875rem' }}>{label}</span>
      </div>
      <div className={`metric-value ${valueClass}`}>{value}</div>
    </div>
  );
};
