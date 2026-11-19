import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AlertCircle, Table, TrendingUp, TrendingDown, Activity, Target } from 'lucide-react';
import { Footprints } from 'lucide-react';
import { PageHeader } from '../components/ui/PageHeader';
import { WalkForwardChart } from '../components/charts/quant/WalkForwardChart';
import { strategyLabel } from '../lib/strategies';
import { toast } from 'sonner';
import { useStrategies, useRunWalkForward } from '../hooks/apiHooks';
import { SkeletonCard } from '../components/ui/SkeletonCard';
import { SkeletonMetricGrid } from '../components/ui/SkeletonMetricGrid';
import { PageFooter } from '../components/ui/PageFooter';
import { DEFAULT_SYMBOL, DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_INITIAL_CAPITAL } from '../lib/constants';
import { snakeToTitleCase, extractParamValue, parseCommaSeparated } from '../lib/utils';
import type { WalkForwardResult } from '../lib/schemas';

const WalkForwardConfigSchema = z.object({
  strategy_name: z.string().min(1, 'Strategy is required'),
  symbol: z.string().min(1, 'Symbol is required').max(10),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  initial_capital: z.number().min(1000).max(100000000),
  train_days: z.number().min(30).max(1000),
  test_days: z.number().min(10).max(365),
});

type WalkForwardConfig = z.infer<typeof WalkForwardConfigSchema>;

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


export const WalkForwardPage: React.FC = () => {
  const { data: strategies = [], isLoading: isLoadingStrategies } = useStrategies();
  const walkForwardMutation = useRunWalkForward();

  const [paramGridInputs, setParamGridInputs] = useState<Record<string, string>>({});
  const [result, setResult] = useState<WalkForwardResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<WalkForwardConfig>({
    resolver: zodResolver(WalkForwardConfigSchema),
    defaultValues: {
      strategy_name: '',
      symbol: DEFAULT_SYMBOL,
      start_date: DEFAULT_START_DATE,
      end_date: DEFAULT_END_DATE,
      initial_capital: DEFAULT_INITIAL_CAPITAL,
      train_days: 252,
      test_days: 63,
    },
  });

  useEffect(() => {
    if (strategies.length > 0) {
      const defaultStrategy = strategies[0]?.registry_key || strategies[0]?.name || '';
      setValue('strategy_name', defaultStrategy);
    }
  }, [strategies, setValue]);

  const selectedStrategyName = watch('strategy_name');
  const selectedStrategy = strategies.find(s => (s.registry_key || s.name) === selectedStrategyName);

  React.useEffect(() => {
    if (selectedStrategy?.parameters) {
      const initialGrid: Record<string, string> = {};
      Object.entries(selectedStrategy.parameters).forEach(([key, rawVal]) => {
        const val = extractParamValue(rawVal);

        if (typeof val === 'number') {
          if (val === 0) initialGrid[key] = '0, 1, 2';
          else initialGrid[key] = `${val * 0.5}, ${val}, ${val * 1.5}`;
        } else if (typeof val === 'boolean') {
          initialGrid[key] = 'true, false';
        } else {
          initialGrid[key] = String(val);
        }
      });
      setParamGridInputs(initialGrid);
    }
  }, [selectedStrategy]);

  const handleGridInputChange = (key: string, value: string) => {
    setParamGridInputs(prev => ({ ...prev, [key]: value }));
  };

  const onSubmit = async (data: WalkForwardConfig) => {
    setError(null);
    setResult(null);

    try {
      const parsedGrid: Record<string, (number | boolean | string)[]> = {};

      Object.entries(paramGridInputs).forEach(([key, valueString]) => {
        const parts = parseCommaSeparated(valueString);
        const rawVal = selectedStrategy?.parameters?.[key];
        const defaultVal = extractParamValue(rawVal);
        const type = typeof defaultVal;

        parsedGrid[key] = parts.map(p => {
          if (type === 'number') return parseFloat(p);
          if (type === 'boolean') return p.toLowerCase() === 'true';
          return p;
        });
      });

      const response = await walkForwardMutation.mutateAsync({
        ...data,
        param_grid: parsedGrid,
      });

      setResult(response);
      toast.success('Walk-forward analysis completed', {
        description: `${response.windows?.length || 0} windows, stability: ${response.stability_score?.toFixed(2) || 'N/A'}`,
      });
    } catch (err: Error | unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error('Walk-forward analysis failed', { description: message });
    }
  };

  const isLoading = walkForwardMutation.isPending || isLoadingStrategies;

  return (
    <div className="animate-fadeIn">
      <PageHeader
        kicker="Validate"
        icon={Footprints}
        title="Walk-forward validation"
        lede="Re-optimise on a rolling training window, then score only on the unseen window that follows. Consistent out-of-sample results are the signal that an edge is real."
      />

      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Window setup</h2>
          <p className="card-description">Training and test window lengths in trading days</p>
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
                {errors.strategy_name && <span className="form-error">{errors.strategy_name.message}</span>}
              </div>

              <div className="form-group">
                <label className="form-label">Symbol</label>
                <input type="text" className="form-input" {...register('symbol')} placeholder="AAPL" />
              </div>
              
              <div className="form-group">
                <label className="form-label">Start Date (Data Boundary)</label>
                <input type="date" className="form-input" {...register('start_date')} />
              </div>
              <div className="form-group">
                <label className="form-label">End Date (Data Boundary)</label>
                <input type="date" className="form-input" {...register('end_date')} />
              </div>

              <div className="form-group">
                <label className="form-label">Train Window (Days)</label>
                <input type="number" className="form-input" {...register('train_days', { valueAsNumber: true })} />
                {errors.train_days && <span className="form-error">{errors.train_days.message}</span>}
              </div>
              
              <div className="form-group">
                <label className="form-label">Test Window (Days)</label>
                <input type="number" className="form-input" {...register('test_days', { valueAsNumber: true })} />
                {errors.test_days && <span className="form-error">{errors.test_days.message}</span>}
              </div>

              {/* Parameter Grid Editor */}
              {selectedStrategy && selectedStrategy.parameters && (
                <div className="form-group" style={{ gridColumn: '1 / -1', marginTop: 'var(--spacing-md)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)' }}>
                    <Table size={16} style={{ color: 'var(--color-accent-400)' }} />
                    <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Parameter Optimizer Grid</h3>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-md)' }}>
                    These parameters represent the search space the optimizer will look through during every Train Phase. Enter comma-separated values.
                  </p>
                  
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                    gap: 'var(--spacing-md)',
                    padding: 'var(--spacing-md)',
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--color-border)'
                  }}>
                    {Object.keys(selectedStrategy.parameters).map((key) => (
                      <div key={key}>
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>{snakeToTitleCase(key)}</label>
                        <input
                          type="text"
                          className="form-input"
                          value={paramGridInputs[key] || ''}
                          onChange={(e) => handleGridInputChange(key, e.target.value)}
                          placeholder="e.g. 10, 20, 30"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
              <button type="submit" className="btn btn-primary" disabled={isLoading}>
                {isLoading ? 'Running Analysis...' : 'Start Walk-Forward Analysis'}
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
      {isLoading && !result && (
        <>
          <SkeletonMetricGrid count={4} />
          <div style={{ marginTop: 'var(--spacing-lg)' }}>
            <SkeletonCard lines={8} />
          </div>
        </>
      )}

      {/* Results Display */}
      {result && (
        <>
          {/* Analysis Summary with Stats Bar */}
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">Analysis Summary</h2>
            </div>
            <div className="card-content">
              <div className="chart-stats-bar">
                <StatCard
                  label="Avg Train Sharpe"
                  value={result.avg_train_sharpe?.toFixed(2) ?? 'N/A'}
                  icon={<TrendingUp size={16} />}
                  positive={result.avg_train_sharpe > 0}
                />
                <StatCard
                  label="Avg Test Sharpe"
                  value={result.avg_test_sharpe?.toFixed(2) ?? 'N/A'}
                  icon={<Activity size={16} />}
                  positive={result.avg_test_sharpe > 0}
                  negative={result.avg_test_sharpe < 0}
                />
                <StatCard
                  label="Stability Score"
                  value={result.stability_score?.toFixed(2) ?? 'N/A'}
                  subtext={result.stability_score > 0.5 ? 'Robust' : 'Unstable'}
                  icon={<Target size={16} />}
                  positive={result.stability_score > 0.5}
                  negative={result.stability_score < 0.3}
                />
                <StatCard
                  label="Total Test Return"
                  value={`${(result.total_test_return * 100).toFixed(2)}%`}
                  icon={result.total_test_return >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  positive={result.total_test_return >= 0}
                  negative={result.total_test_return < 0}
                />
              </div>
            </div>
          </section>

          {/* Rolling Windows Chart */}
          {result.windows && result.windows.length > 0 && (
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">Out-of-sample performance</h2>
                <p className="card-description">Only the test windows: data the optimiser never saw when choosing parameters</p>
              </div>
              <div className="card-content">
                <WalkForwardChart windows={result.windows} />
              </div>
            </section>
          )}

          {/* Rolling Windows Table */}
          {result.windows && result.windows.length > 0 && (
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">Rolling Windows Performance</h2>
              </div>
              <div className="card-content">
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Window #</th>
                        <th>Test Period</th>
                        <th>Best Train Params</th>
                        <th style={{ textAlign: 'right' }}>Test Horizon Return</th>
                        <th style={{ textAlign: 'right' }}>Test Trades</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.windows.map((w: { test_start: string; test_end: string; best_params: Record<string, number | boolean | string>; test_return: number; test_trades: number }, idx: number) => (
                        <tr key={idx}>
                          <td>#{idx + 1}</td>
                          <td style={{ fontSize: '0.875rem' }}>
                            {w.test_start.split('T')[0]} → {w.test_end.split('T')[0]}
                          </td>
                          <td style={{ fontSize: '0.75rem' }}>
                            {Object.entries(w.best_params).map(([k, v]) => `${k}:${v}`).join(', ')}
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 600, color: w.test_return >= 0 ? 'var(--color-success)' : 'var(--color-error)' }}>
                            {(w.test_return * 100).toFixed(2)}%
                          </td>
                          <td style={{ textAlign: 'right', color: 'var(--color-text-secondary)' }}>
                            {w.test_trades}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          )}
        </>
      )}

      {/* Page Footer */}
      <PageFooter
        title="walk-forward analysis"
        description="Test strategy robustness by repeatedly optimizing on historical data and validating on future data. This rolling window approach helps detect overfitting and validates out-of-sample performance."
        parameters={[
          { name: 'Train Window', description: 'Days to use for parameter optimization (default: 252 = 1 year)' },
          { name: 'Test Window', description: 'Days to validate optimized parameters (default: 63 = 1 quarter)' },
          { name: 'Parameter Grid', description: 'Search space for optimization during each train phase' },
        ]}
        tips={[
          'Stability score > 0.5 indicates parameters are robust across time',
          'Large gaps between train and test Sharpe suggest overfitting',
          'Use longer test windows for more reliable out-of-sample estimates',
          'If test returns are consistently negative, the strategy may not be viable',
        ]}
      />
    </div>
  );
};
