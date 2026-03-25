import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AlertCircle, Settings2, Table } from 'lucide-react';
import { toast } from 'sonner';
import { useStrategies, useRunOptimization } from '../hooks/apiHooks';
import { ParameterSensitivityChart } from '../components/charts';
import { DEFAULT_SYMBOL, DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_INITIAL_CAPITAL } from '../lib/constants';
import { snakeToTitleCase, extractParamValue, parseCommaSeparated } from '../lib/utils';
import type { OptimizationResult } from '../lib/schemas';

const OptimizationConfigSchema = z.object({
  strategy_name: z.string().min(1, 'Strategy is required'),
  symbol: z.string().min(1, 'Symbol is required').max(10),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  initial_capital: z.number().min(1000).max(100000000),
  method: z.enum(['grid', 'random', 'genetic']),
  metric: z.enum(['sharpe_ratio', 'total_return', 'sortino_ratio', 'max_drawdown', 'win_rate']),
  n_iterations: z.number().min(5).max(1000).optional(),
});

type OptimizationConfig = z.infer<typeof OptimizationConfigSchema>;

export const OptimizationPage: React.FC = () => {
  const { data: strategies = [], isLoading: isLoadingStrategies } = useStrategies();
  const optimizeMutation = useRunOptimization();

  const [paramGridInputs, setParamGridInputs] = useState<Record<string, string>>({});
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<OptimizationConfig>({
    resolver: zodResolver(OptimizationConfigSchema),
    defaultValues: {
      strategy_name: '',
      symbol: DEFAULT_SYMBOL,
      start_date: DEFAULT_START_DATE,
      end_date: DEFAULT_END_DATE,
      initial_capital: DEFAULT_INITIAL_CAPITAL,
      method: 'grid',
      metric: 'sharpe_ratio',
      n_iterations: 50,
    },
  });

  useEffect(() => {
    if (strategies.length > 0) {
      const defaultStrategy = strategies[0]?.registry_key || strategies[0]?.name || '';
      setValue('strategy_name', defaultStrategy);
    }
  }, [strategies, setValue]);

  const selectedStrategyName = watch('strategy_name');
  const selectedMethod = watch('method');
  const selectedStrategy = strategies.find(s => (s.registry_key || s.name) === selectedStrategyName);

  // Initialize param inputs when strategy changes
  React.useEffect(() => {
    if (selectedStrategy?.parameters) {
      const initialGrid: Record<string, string> = {};
      Object.entries(selectedStrategy.parameters).forEach(([key, rawVal]) => {
        const val = extractParamValue(rawVal);

        // Only allow array inputs for numbers and booleans
        if (typeof val === 'number') {
          // Generate a small default grid
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

  const onSubmit = async (data: OptimizationConfig) => {
    setError(null);
    setResult(null);

    try {
      // Parse the grid inputs into proper arrays
      const parsedGrid: Record<string, any[]> = {};

      Object.entries(paramGridInputs).forEach(([key, valueString]) => {
        const parts = parseCommaSeparated(valueString);

        // Find the original type from the schema to cast properly
        const rawVal = selectedStrategy?.parameters?.[key];
        const defaultVal = extractParamValue(rawVal);
        const type = typeof defaultVal;

        parsedGrid[key] = parts.map(p => {
          if (type === 'number') return parseFloat(p);
          if (type === 'boolean') return p.toLowerCase() === 'true';
          return p;
        });
      });

      const configToSend = {
        ...data,
        param_grid: parsedGrid,
      };

      const response = await optimizeMutation.mutateAsync({
        method: data.method,
        config: configToSend,
      });

      setResult(response);
      toast.success('Optimization completed', {
        description: `Best score: ${response.best_score.toFixed(4)}`,
      });
    } catch (err: Error | unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error('Optimization failed', { description: message });
    }
  };

  const isLoading = optimizeMutation.isPending || isLoadingStrategies;

  return (
    <div className="animate-fadeIn">
      {/* Configuration Form */}
      <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <Settings2 size={20} style={{ color: 'var(--color-accent-400)' }} />
            <h2 className="card-title">Hyperparameter Optimization</h2>
          </div>
          <p className="card-description">Sweep strategy parameters to find the optimal configuration</p>
        </div>
        <div className="card-content">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--spacing-md)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              
              {/* Basic Fields */}
              <div className="form-group">
                <label className="form-label">Strategy</label>
                <select className="form-input" {...register('strategy_name')}>
                  {strategies.map((s) => (
                    <option key={s.registry_key || s.name} value={s.registry_key || s.name}>
                      {s.name} ({s.type})
                    </option>
                  ))}
                </select>
                {errors.strategy_name && <span className="form-error">{errors.strategy_name.message}</span>}
              </div>
              <div className="form-group">
                <label className="form-label">Optimization Method</label>
                <select className="form-input" {...register('method')}>
                  <option value="grid">Grid Search (Exhaustive)</option>
                  <option value="random">Random Search</option>
                  <option value="genetic">Genetic Algorithm</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Target Metric</label>
                <select className="form-input" {...register('metric')}>
                  <option value="sharpe_ratio">Sharpe Ratio</option>
                  <option value="total_return">Total Return</option>
                  <option value="max_drawdown">Max Drawdown</option>
                  <option value="win_rate">Win Rate</option>
                </select>
              </div>
              
              {/* Show n_iterations only for random and genetic */}
              {(selectedMethod === 'random' || selectedMethod === 'genetic') && (
                <div className="form-group">
                  <label className="form-label">Iterations</label>
                  <input type="number" className="form-input" {...register('n_iterations', { valueAsNumber: true })} />
                  {errors.n_iterations && <span className="form-error">{errors.n_iterations.message}</span>}
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Symbol</label>
                <input type="text" className="form-input" {...register('symbol')} placeholder="AAPL" />
              </div>
              <div className="form-group">
                <label className="form-label">Start Date</label>
                <input type="date" className="form-input" {...register('start_date')} />
              </div>
              <div className="form-group">
                <label className="form-label">End Date</label>
                <input type="date" className="form-input" {...register('end_date')} />
              </div>

              {/* Parameter Grid Editor */}
              {selectedStrategy && selectedStrategy.parameters && (
                <div className="form-group" style={{ gridColumn: '1 / -1', marginTop: 'var(--spacing-md)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)' }}>
                    <Table size={16} style={{ color: 'var(--color-accent-400)' }} />
                    <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Parameter Grid</h3>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-md)' }}>
                    Enter comma-separated values to test. Example: <code>10, 15, 20</code>
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
                {isLoading ? 'Optimizing...' : 'Run Optimization'}
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

      {/* Results Display */}
      {result && (
        <>
          {/* Best Parameters Summary */}
          <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <div className="card-header">
              <h2 className="card-title">Best Configuration</h2>
            </div>
            <div className="card-content">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
                <div style={{ padding: 'var(--spacing-md)', background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: '0.25rem' }}>Best Score ({selectedMethod})</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-accent-400)' }}>
                    {typeof result.best_score === 'number' ? result.best_score.toFixed(4) : result.best_score}
                  </div>
                </div>
                
                <div style={{ padding: 'var(--spacing-md)', background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>Optimal Parameters</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {Object.entries(result.best_params || {}).map(([k, v]) => (
                      <span key={k} style={{ 
                        background: 'var(--color-bg-secondary)', 
                        padding: '2px 8px', 
                        borderRadius: '12px', 
                        fontSize: '0.75rem',
                        border: '1px solid var(--color-border)'
                      }}>
                        <strong>{k}:</strong> {String(v)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Scatter Plot */}
          {result.results && result.results.length > 0 && result.best_params && (
            <ParameterSensitivityChart 
              results={result.results} 
              parameterKeys={Object.keys(result.best_params)} 
              metricName={watch('metric')} 
            />
          )}

          {/* Results Table */}
          {result.results && result.results.length > 0 && (
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">All Combinations</h2>
              </div>
              <div className="card-content">
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Parameters</th>
                        <th style={{ textAlign: 'right' }}>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.results.map((r: any, idx: number) => (
                        <tr key={idx}>
                          <td>#{idx + 1}</td>
                          <td style={{ fontSize: '0.875rem' }}>
                            {Object.entries(r.params).map(([k, v]) => `${k}: ${v}`).join(' | ')}
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--color-accent-400)' }}>
                            {typeof r.score === 'number' ? r.score.toFixed(4) : r.score}
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
    </div>
  );
};
