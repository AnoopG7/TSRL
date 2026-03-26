import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Briefcase, AlertCircle, TrendingUp, TrendingDown, Activity, PieChart, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

import { EquityCurveChart } from '../components/charts';
import { ParameterEditor } from '../components/forms/ParameterEditor';
import { MetricCard } from '../components/ui/MetricCard';
import { SkeletonMetricGrid } from '../components/ui/SkeletonMetricGrid';
import { SkeletonChart } from '../components/ui/SkeletonChart';
import { PageFooter } from '../components/ui/PageFooter';
import { useStrategies, useRunPortfolioBacktest } from '../hooks/apiHooks';
import { DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_INITIAL_CAPITAL } from '../lib/constants';
import type { PortfolioConfig, PortfolioResult } from '../lib/schemas';

export const PortfolioPage: React.FC = () => {
  const { data: strategies = [], isLoading: isLoadingStrategies } = useStrategies();
  const runPortfolioMutation = useRunPortfolioBacktest();
  const [result, setResult] = useState<PortfolioResult | null>(null);

  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<PortfolioConfig>({
    defaultValues: {
      strategy_name: '',
      symbols: 'AAPL,GOOGL,MSFT',
      weights: '',
      start_date: DEFAULT_START_DATE,
      end_date: DEFAULT_END_DATE,
      initial_capital: DEFAULT_INITIAL_CAPITAL,
      rebalance_frequency: 'none',
      rebalance_threshold: '',
      benchmark_symbol: '',
      parameters: {},
    },
  });

  useEffect(() => {
    if (strategies.length > 0) {
      const defaultStrategy = strategies[0]?.registry_key || strategies[0]?.name || '';
      setValue('strategy_name', defaultStrategy);
    }
  }, [strategies, setValue]);

  const onSubmit = async (data: PortfolioConfig) => {
    setError(null);
    try {
      const res = await runPortfolioMutation.mutateAsync(data);
      setResult(res);
      toast.success('Portfolio backtest completed', {
        description: `${res.symbols.length} assets, ${(res.results.total_return * 100).toFixed(2)}% return`,
      });
    } catch (err: Error | unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error('Portfolio backtest failed', { description: message });
    }
  };

  const loading = runPortfolioMutation.isPending;

  const equityCurveData = result?.equity_curve?.map(d => ({
    date: d.date,
    equity: d.total,
  })) || [];

  return (
    <div className="animate-fadeIn">
      {/* Configuration Form */}
      <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <Briefcase size={20} style={{ color: 'var(--color-accent-400)' }} />
            <h2 className="card-title">Portfolio Backtest</h2>
          </div>
          <p className="card-description">Backtest multiple assets with custom allocation weights and rebalancing</p>
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
              </div>
              <div className="form-group">
                <label className="form-label">Symbols (comma-separated)</label>
                <input type="text" className="form-input" {...register('symbols')} placeholder="AAPL,GOOGL,MSFT" />
                {errors.symbols && <span className="form-error">{errors.symbols.message}</span>}
              </div>
              <div className="form-group">
                <label className="form-label">Weights (optional, comma-separated)</label>
                <input type="text" className="form-input" {...register('weights')} placeholder="0.4,0.3,0.3 or leave empty for equal" />
              </div>
              <div className="form-group">
                <label className="form-label">Start Date</label>
                <input type="date" className="form-input" {...register('start_date')} />
              </div>
              <div className="form-group">
                <label className="form-label">End Date</label>
                <input type="date" className="form-input" {...register('end_date')} />
              </div>
              <div className="form-group">
                <label className="form-label">Initial Capital</label>
                <input type="number" className="form-input" {...register('initial_capital', { valueAsNumber: true })} />
              </div>
              <div className="form-group">
                <label className="form-label">Rebalancing</label>
                <select className="form-input" {...register('rebalance_frequency')}>
                  <option value="none">None</option>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Drift Threshold (optional)</label>
                <input type="text" className="form-input" {...register('rebalance_threshold')} placeholder="0.05 for 5%" />
              </div>
              <div className="form-group">
                <label className="form-label">Benchmark (optional)</label>
                <input type="text" className="form-input" {...register('benchmark_symbol')} placeholder="SPY" />
              </div>
              
              <ParameterEditor 
                strategy={strategies.find(s => (s.registry_key || s.name) === watch('strategy_name'))} 
                onChange={(p) => setValue('parameters', p)} 
              />
            </div>
            <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
              <button type="submit" className="btn btn-primary" disabled={loading || isLoadingStrategies}>
                {loading ? 'Running...' : 'Run Portfolio Backtest'}
              </button>
            </div>
          </form>
          {error && (
            <div className="error-message" style={{ marginTop: 'var(--spacing-md)' }}>
              <AlertCircle size={16} />
              {error}
            </div>
          )}
        </div>
      </section>

      {/* Loading Skeletons */}
      {loading && !result && (
        <>
          <SkeletonMetricGrid count={6} />
          <div style={{ marginTop: 'var(--spacing-lg)' }}>
            <SkeletonChart height={300} />
          </div>
        </>
      )}

      {result && (
        <>
          {/* Allocation Summary */}
          <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                <PieChart size={20} style={{ color: 'var(--color-accent-400)' }} />
                <h2 className="card-title">Portfolio Allocation</h2>
              </div>
            </div>
            <div className="card-content">
              <div style={{ display: 'flex', gap: 'var(--spacing-lg)', flexWrap: 'wrap' }}>
                {result.symbols.map((symbol) => (
                  <div key={symbol} style={{
                    padding: 'var(--spacing-md)',
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                    minWidth: '120px',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontWeight: 600, marginBottom: '4px' }}>{symbol}</div>
                    <div style={{ fontSize: '1.25rem', color: 'var(--color-accent-400)' }}>
                      {((result.weights[symbol] || 0) * 100).toFixed(1)}%
                    </div>
                    {result.per_asset_results[symbol] && (
                      <div style={{
                        marginTop: '8px',
                        fontSize: '0.875rem',
                        color: result.per_asset_results[symbol].total_return >= 0 ? 'var(--color-positive)' : 'var(--color-negative)'
                      }}>
                        {(result.per_asset_results[symbol].total_return * 100).toFixed(2)}%
                      </div>
                    )}
                  </div>
                ))}
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
                <MetricCard
                  label="Total Return"
                  value={`${(result.results.total_return * 100).toFixed(2)}%`}
                  icon={result.results.total_return >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  positive={result.results.total_return >= 0}
                  negative={result.results.total_return < 0}
                />
                <MetricCard label="Sharpe Ratio" value={result.results.sharpe_ratio.toFixed(2)} />
                <MetricCard label="Max Drawdown" value={`${(result.results.max_drawdown * 100).toFixed(2)}%`} negative />
                <MetricCard label="Total Trades" value={result.results.total_trades.toString()} icon={<Activity size={16} />} />
                <MetricCard label="Win Rate" value={`${(result.results.win_rate * 100).toFixed(1)}%`} />
                <MetricCard label="Execution Time" value={`${result.results.execution_time_ms.toFixed(0)}ms`} />
              </div>
            </div>
          </section>

          {/* Rebalancing Info */}
          {result.rebalancing.total_events > 0 && (
            <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
              <div className="card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                  <RefreshCw size={20} style={{ color: 'var(--color-accent-400)' }} />
                  <h2 className="card-title">Rebalancing</h2>
                </div>
              </div>
              <div className="card-content">
                <div className="metric-grid">
                  <MetricCard label="Rebalance Events" value={result.rebalancing.total_events.toString()} />
                  <MetricCard label="Total Cost" value={`$${result.rebalancing.total_cost.toFixed(2)}`} />
                </div>
              </div>
            </section>
          )}

          {/* Portfolio Metrics */}
          {result.portfolio_metrics && (
            <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
              <div className="card-header">
                <h2 className="card-title">Portfolio Metrics</h2>
              </div>
              <div className="card-content">
                <div className="metric-grid">
                  <MetricCard label="Beta" value={result.portfolio_metrics.beta.toFixed(3)} />
                  <MetricCard
                    label="Alpha (Ann.)"
                    value={`${(result.portfolio_metrics.alpha * 100).toFixed(2)}%`}
                    positive={result.portfolio_metrics.alpha > 0}
                    negative={result.portfolio_metrics.alpha < 0}
                  />
                  <MetricCard label="Diversification" value={result.portfolio_metrics.diversification_ratio.toFixed(2)} />
                  <MetricCard label="Avg Correlation" value={result.portfolio_metrics.avg_correlation.toFixed(3)} />
                  {result.portfolio_metrics.tracking_error > 0 && (
                    <>
                      <MetricCard label="Tracking Error" value={`${(result.portfolio_metrics.tracking_error * 100).toFixed(2)}%`} />
                      <MetricCard label="Information Ratio" value={result.portfolio_metrics.information_ratio.toFixed(2)} />
                    </>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* Equity Curve */}
          {equityCurveData.length > 0 && (
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">Portfolio Equity Curve</h2>
              </div>
              <div className="card-content">
                <EquityCurveChart data={equityCurveData} initialCapital={100000} />
              </div>
            </section>
          )}
        </>
      )}

      {/* Page Footer */}
      <PageFooter
        title="Portfolio Backtesting"
        description="Test trading strategies across multiple assets with customizable allocation weights and automatic rebalancing. Evaluate portfolio-level metrics including diversification and correlation."
        parameters={[
          { name: 'Symbols', description: 'Comma-separated list of stock tickers to include in the portfolio' },
          { name: 'Weights', description: 'Allocation weights per asset (leave empty for equal weighting)' },
          { name: 'Rebalancing', description: 'Frequency to rebalance to target weights (none, monthly, quarterly, yearly)' },
          { name: 'Drift Threshold', description: 'Trigger rebalance when allocation drifts by this percentage' },
          { name: 'Benchmark', description: 'Optional benchmark symbol (e.g., SPY) for comparison metrics' },
        ]}
        tips={[
          'Diversification ratio > 1 indicates effective risk reduction from diversification',
          'Low average correlation between assets improves portfolio efficiency',
          'Consider rebalancing costs - frequent rebalancing may erode returns',
          'Alpha > 0 with benchmark indicates value-add beyond market exposure',
        ]}
      />
    </div>
  );
};