import { useState, useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { AlertCircle, TrendingUp, TrendingDown, Activity, PieChart, RefreshCw, Award, Target } from 'lucide-react';
import { PageHeader } from '../components/ui/PageHeader';
import { strategyLabel } from '../lib/strategies';
import { toast } from 'sonner';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine
} from 'recharts';

import { PerformanceChart } from '../components/charts/quant/PerformanceChart';
import { ParameterEditor } from '../components/forms/ParameterEditor';
import { MetricCard } from '../components/ui/MetricCard';
import { SkeletonMetricGrid } from '../components/ui/SkeletonMetricGrid';
import { SkeletonChart } from '../components/ui/SkeletonChart';
import { PageFooter } from '../components/ui/PageFooter';
import { useStrategies, useRunPortfolioBacktest } from '../hooks/apiHooks';
import { DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_INITIAL_CAPITAL } from '../lib/constants';
import type { PortfolioConfig, PortfolioResult } from '../lib/schemas';

const COLORS = [1, 2, 3, 4, 5, 6, 7, 8].map((n) => `var(--series-${n})`);

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

// Custom tooltip for bar chart
const PerformanceTooltip: React.FC<{ active?: boolean; payload?: Array<{ payload: { symbol: string; return: number; weight: number; trades: number } }> }> = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-header">{data.symbol}</div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Return</span>
        <span className={`chart-tooltip-value ${data.return >= 0 ? 'positive' : 'negative'}`}>
          {(data.return * 100).toFixed(2)}%
        </span>
      </div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Weight</span>
        <span className="chart-tooltip-value">{(data.weight * 100).toFixed(1)}%</span>
      </div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-label">Trades</span>
        <span className="chart-tooltip-value">{data.trades}</span>
      </div>
    </div>
  );
};

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

  // Calculate per-asset chart data and summary stats
  const { assetPerformanceData, allocationData, summaryStats } = useMemo(() => {
    if (!result) return { assetPerformanceData: [], allocationData: [], summaryStats: null };

    const perfData = result.symbols.map((symbol, idx) => ({
      symbol,
      return: result.per_asset_results[symbol]?.total_return || 0,
      weight: result.weights[symbol] || 0,
      trades: result.per_asset_results[symbol]?.trades || 0,
      color: COLORS[idx % COLORS.length],
    })).sort((a, b) => b.return - a.return);

    const allocData = result.symbols.map((symbol, idx) => ({
      name: symbol,
      value: (result.weights[symbol] || 0) * 100,
      fill: COLORS[idx % COLORS.length],
    }));

    const returns = perfData.map(d => d.return);
    const bestAsset = perfData[0];
    const worstAsset = perfData[perfData.length - 1];
    const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
    const profitableCount = returns.filter(r => r > 0).length;

    return {
      assetPerformanceData: perfData,
      allocationData: allocData,
      summaryStats: {
        bestAsset,
        worstAsset,
        avgReturn,
        profitableCount,
        totalAssets: result.symbols.length,
      },
    };
  }, [result]);

  return (
    <div className="animate-fadeIn">
      <PageHeader
        kicker="Research"
        icon={PieChart}
        title="Portfolio backtest"
        lede="Trade one strategy across a basket of assets with target weights, scheduled rebalancing and a benchmark to measure against."
      />

      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Portfolio setup</h2>
          <p className="card-description">Symbols, weights and rebalancing rules</p>
        </div>
        <div className="card-content">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="form-grid" style={{ marginBottom: 'var(--spacing-lg)' }}>
              <div className="form-group">
                <label className="form-label">Strategy</label>
                <select className="form-input" {...register('strategy_name')}>
                  {strategies.map((s) => (
                    <option key={s.registry_key || s.name} value={s.registry_key || s.name}>
                      {strategyLabel(s)}
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
          {/* Summary Stats Bar */}
          {summaryStats && (
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">Portfolio Overview</h2>
              </div>
              <div className="card-content">
                <div className="chart-stats-bar">
                  <StatCard
                    label="Portfolio Return"
                    value={`${(result.results.total_return * 100).toFixed(2)}%`}
                    icon={result.results.total_return >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                    positive={result.results.total_return >= 0}
                    negative={result.results.total_return < 0}
                  />
                  <StatCard
                    label="Best Asset"
                    value={summaryStats.bestAsset.symbol}
                    subtext={`+${(summaryStats.bestAsset.return * 100).toFixed(1)}%`}
                    icon={<Award size={16} />}
                    positive
                  />
                  <StatCard
                    label="Profitable Assets"
                    value={`${summaryStats.profitableCount}/${summaryStats.totalAssets}`}
                    icon={<Target size={16} />}
                    positive={summaryStats.profitableCount > summaryStats.totalAssets / 2}
                  />
                  <StatCard
                    label="Sharpe Ratio"
                    value={result.results.sharpe_ratio.toFixed(2)}
                    icon={<Activity size={16} />}
                    positive={result.results.sharpe_ratio > 1}
                  />
                </div>
              </div>
            </section>
          )}

          {/* Allocation & Performance Charts */}
          <div className="grid-2" style={{ marginBottom: 'var(--spacing-lg)' }}>
            {/* Allocation Pie Chart */}
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">Target allocation</h2>
                <p className="card-description">Weights the portfolio rebalances back to</p>
              </div>
              <div className="card-content">
                <div className="alloc-strip" role="img" aria-label="Allocation by asset">
                  {allocationData.map((d) => (
                    <span key={d.name} style={{ flexGrow: d.value, background: d.fill }} title={`${d.name} ${d.value.toFixed(1)}%`} />
                  ))}
                </div>
                <table className="alloc-table">
                  <tbody>
                    {allocationData.map((d) => (
                      <tr key={d.name}>
                        <td><i style={{ background: d.fill }} />{d.name}</td>
                        <td className="t-right">{d.value.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* Per-Asset Performance Bar Chart */}
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">Per-Asset Performance</h2>
                <p className="card-description">Individual asset returns sorted by performance</p>
              </div>
              <div className="card-content">
                <div style={{ height: 280 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={assetPerformanceData} layout="vertical" margin={{ top: 10, right: 30, bottom: 10, left: 50 }}>
                      <CartesianGrid stroke="var(--chart-grid)" horizontal={false} />
                      <XAxis
                        type="number"
                        tick={{ fill: 'var(--chart-axis)', fontSize: 11 }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
                      />
                      <YAxis
                        type="category"
                        dataKey="symbol"
                        tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
                        tickLine={false}
                        axisLine={false}
                        width={56}
                      />
                      <Tooltip
                        content={<PerformanceTooltip />}
                        position={{ x: 100, y: 10 }}
                        wrapperStyle={{ pointerEvents: 'none' }}
                      />
                      <ReferenceLine x={0} stroke="var(--chart-baseline)" />
                      <Bar dataKey="return" radius={[0, 4, 4, 0]} barSize={18} isAnimationActive={false}>
                        {assetPerformanceData.map((entry, index) => (
                          <Cell
                            key={index}
                            fill={entry.return >= 0 ? 'var(--color-up)' : 'var(--color-down)'}
                            fillOpacity={0.85}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>
          </div>

          {/* Performance Summary */}
          <section className="card">
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
            <section className="card">
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
            <section className="card">
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
                <h2 className="card-title">Portfolio equity</h2>
              </div>
              <div className="card-content">
                <PerformanceChart equity={equityCurveData} initialCapital={equityCurveData[0]?.equity ?? 100000} />
              </div>
            </section>
          )}
        </>
      )}

      {/* Page Footer */}
      <PageFooter
        title="portfolio backtesting"
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