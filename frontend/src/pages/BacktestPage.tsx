import { useState, useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Target, AlertCircle, DollarSign, TrendingUp, TrendingDown, Activity, BarChart3, LineChart, Award, Zap } from 'lucide-react';
import { toast } from 'sonner';
import { BacktestConfigSchema } from '../lib/schemas';
import type { BacktestConfig } from '../lib/schemas';
import { useBacktestStore } from '../store';
import { EquityCurveChart, DrawdownChart, MonthlyReturnsHeatmap } from '../components/charts';
import { ParameterEditor } from '../components/forms/ParameterEditor';
import { MetricCard } from '../components/ui/MetricCard';
import { SkeletonCard } from '../components/ui/SkeletonCard';
import { SkeletonMetricGrid } from '../components/ui/SkeletonMetricGrid';
import { SkeletonChart } from '../components/ui/SkeletonChart';
import { PageFooter } from '../components/ui/PageFooter';
import { useStrategies, useRunBacktest } from '../hooks/apiHooks';
import { DEFAULT_SYMBOL, DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_INITIAL_CAPITAL, DEFAULT_DATA_SOURCE } from '../lib/constants';

// Stats card component
const StatCard: React.FC<{ label: string; value: string; subtext?: string; icon: React.ReactNode; positive?: boolean; negative?: boolean }> = ({
  label, value, subtext, icon, positive, negative
}) => (
  <div className="chart-stat-card">
    <div className={`chart-stat-icon ${positive ? 'positive' : ''} ${negative ? 'negative' : ''}`}>{icon}</div>
    <div className="chart-stat-content">
      <span className="chart-stat-label">{label}</span>
      <span className={`chart-stat-value ${positive ? 'positive' : ''} ${negative ? 'negative' : ''}`}>{value}</span>
      {subtext && <span className="chart-stat-subtext">{subtext}</span>}
    </div>
  </div>
);

export const BacktestPage: React.FC = () => {
  const { data: strategies = [], isLoading: isLoadingStrategies } = useStrategies();
  const runBacktestMutation = useRunBacktest();
  const { result, trades, loading, error, equityCurve, drawdownSeries, monthlyReturns, setResult, setError, setTrades, setEquityCurve, setDrawdownSeries, setMonthlyReturns } = useBacktestStore();
  const [chartTab, setChartTab] = useState<'equity' | 'drawdown' | 'monthly'>('equity');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<BacktestConfig>({
    resolver: zodResolver(BacktestConfigSchema),
    defaultValues: {
      strategy_name: '',
      symbol: DEFAULT_SYMBOL,
      start_date: DEFAULT_START_DATE,
      end_date: DEFAULT_END_DATE,
      initial_capital: DEFAULT_INITIAL_CAPITAL,
      parameters: {},
      source: DEFAULT_DATA_SOURCE,
    },
  });

  useEffect(() => {
    if (strategies.length > 0) {
      const defaultStrategy = strategies[0]?.registry_key || strategies[0]?.name || '';
      setValue('strategy_name', defaultStrategy);
    }
  }, [strategies, setValue]);

  const onSubmit = async (data: BacktestConfig) => {
    setError(null);
    try {
      const response = await runBacktestMutation.mutateAsync(data);
      setResult(response.results);
      setTrades(response.trades || []);
      setEquityCurve(response.equity_curve || []);
      setDrawdownSeries(response.drawdown_series || []);
      setMonthlyReturns(response.monthly_returns || []);
      toast.success('Backtest completed', {
        description: `${response.results?.total_trades || 0} trades, ${((response.results?.total_return || 0) * 100).toFixed(2)}% return`,
      });
    } catch (err: Error | unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error('Backtest failed', { description: message });
    }
  };

  const isLoading = runBacktestMutation.isPending || loading;

  const hasChartData = equityCurve.length > 0 || drawdownSeries.length > 0 || monthlyReturns.length > 0;

  // Calculate trade statistics
  const tradeStats = useMemo(() => {
    if (!trades || trades.length === 0) return null;

    const wins = trades.filter(t => t.pnl > 0);
    const losses = trades.filter(t => t.pnl < 0);

    const avgWin = wins.length > 0 ? wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length : 0;
    const avgLoss = losses.length > 0 ? losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length : 0;
    const largestWin = wins.length > 0 ? Math.max(...wins.map(t => t.pnl)) : 0;
    const largestLoss = losses.length > 0 ? Math.min(...losses.map(t => t.pnl)) : 0;
    const avgHoldingDays = trades.reduce((sum, t) => {
      const days = (new Date(t.exit_time).getTime() - new Date(t.entry_time).getTime()) / (1000 * 60 * 60 * 24);
      return sum + days;
    }, 0) / trades.length;

    const bestTrade = trades.reduce((best, t) => t.pnl > best.pnl ? t : best, trades[0]);
    const worstTrade = trades.reduce((worst, t) => t.pnl < worst.pnl ? t : worst, trades[0]);

    return {
      avgWin,
      avgLoss,
      largestWin,
      largestLoss,
      avgHoldingDays,
      winCount: wins.length,
      lossCount: losses.length,
      bestTrade,
      worstTrade,
    };
  }, [trades]);

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
            <div className="form-grid" style={{ marginBottom: 'var(--spacing-lg)' }}>
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

              <ParameterEditor 
                strategy={strategies.find(s => (s.registry_key || s.name) === watch('strategy_name'))} 
                onChange={(p) => setValue('parameters', p)} 
              />
            </div>
            <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
              <button type="submit" className="btn btn-primary" disabled={isLoading || isLoadingStrategies}>
                {isLoading ? 'Running...' : 'Run Backtest'}
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

      {/* Loading Skeletons */}
      {isLoading && !result && (
        <>
          <SkeletonMetricGrid count={8} />
          <div style={{ marginTop: 'var(--spacing-lg)' }}>
            <SkeletonChart height={300} />
          </div>
          <div style={{ marginTop: 'var(--spacing-lg)' }}>
            <SkeletonCard lines={5} />
          </div>
        </>
      )}

      {result && (
        <>
          {/* Quick Summary Bar */}
          <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <div className="card-header">
              <h2 className="card-title">Quick Summary</h2>
            </div>
            <div className="card-content">
              <div className="chart-stats-bar">
                <StatCard
                  label="Total Return"
                  value={`${(result.total_return * 100).toFixed(2)}%`}
                  subtext={`$${(result.final_capital - result.final_capital / (1 + result.total_return)).toLocaleString(undefined, { maximumFractionDigits: 0 })} profit`}
                  icon={result.total_return >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  positive={result.total_return >= 0}
                  negative={result.total_return < 0}
                />
                <StatCard
                  label="Win Rate"
                  value={`${(result.metrics.win_rate * 100).toFixed(1)}%`}
                  subtext={tradeStats ? `${tradeStats.winCount}W / ${tradeStats.lossCount}L` : undefined}
                  icon={<Award size={16} />}
                  positive={result.metrics.win_rate >= 0.5}
                />
                <StatCard
                  label="Risk-Adjusted"
                  value={result.metrics.sharpe_ratio.toFixed(2)}
                  subtext="Sharpe Ratio"
                  icon={<Zap size={16} />}
                  positive={result.metrics.sharpe_ratio > 1}
                  negative={result.metrics.sharpe_ratio < 0}
                />
                <StatCard
                  label="Max Drawdown"
                  value={`${result.metrics.max_drawdown_pct.toFixed(2)}%`}
                  icon={<TrendingDown size={16} />}
                  negative
                />
              </div>
            </div>
          </section>

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
              <h2 className="card-title">Trade History</h2>
              <p className="card-description">Showing {Math.min(trades.length, 10)} of {trades.length} trades</p>
            </div>
            <div className="card-content">
              {/* Trade Statistics */}
              {tradeStats && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                  gap: 'var(--spacing-md)',
                  marginBottom: 'var(--spacing-lg)',
                  padding: 'var(--spacing-md)',
                  background: 'var(--color-bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Avg Win</div>
                    <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-success-500)' }}>
                      ${tradeStats.avgWin.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Avg Loss</div>
                    <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-danger-500)' }}>
                      ${tradeStats.avgLoss.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Best Trade</div>
                    <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-success-500)' }}>
                      ${tradeStats.largestWin.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Worst Trade</div>
                    <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-danger-500)' }}>
                      ${tradeStats.largestLoss.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Avg Holding</div>
                    <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                      {tradeStats.avgHoldingDays.toFixed(1)} days
                    </div>
                  </div>
                </div>
              )}

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
                    {trades.slice(0, 10).map((trade, idx) => {
                      const isBest = tradeStats && trade === tradeStats.bestTrade;
                      const isWorst = tradeStats && trade === tradeStats.worstTrade;
                      return (
                        <tr key={idx} style={isBest ? { background: 'rgba(34, 197, 94, 0.05)' } : isWorst ? { background: 'rgba(239, 68, 68, 0.05)' } : undefined}>
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
                            {isBest && <span style={{ marginLeft: '4px', fontSize: '0.65rem', color: 'var(--color-success-500)' }}>★ Best</span>}
                            {isWorst && <span style={{ marginLeft: '4px', fontSize: '0.65rem', color: 'var(--color-danger-500)' }}>★ Worst</span>}
                          </td>
                          <td className={trade.pnl_pct >= 0 ? 'text-positive' : 'text-negative'} style={{ textAlign: 'right', fontWeight: 500 }}>
                            {trade.pnl_pct.toFixed(2)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </>
      )}

      {/* Page Footer */}
      <PageFooter
        title="Backtesting"
        description="Run historical simulations of trading strategies to evaluate their performance on past market data. Backtesting helps validate strategy logic before deploying capital."
        parameters={[
          { name: 'Strategy', description: 'The trading algorithm to test (EMA Crossover, RSI Mean Reversion, etc.)' },
          { name: 'Symbol', description: 'Stock ticker to backtest against (e.g., AAPL, MSFT)' },
          { name: 'Initial Capital', description: 'Starting portfolio value for the simulation' },
          { name: 'Date Range', description: 'Historical period for the backtest' },
        ]}
        tips={[
          'Use at least 2 years of data for statistically meaningful results',
          'Compare multiple strategies on the same data for fair evaluation',
          'Watch for overfitting - high in-sample returns may not persist out-of-sample',
          'Consider transaction costs and slippage in your analysis',
        ]}
      />
    </div>
  );
};
