import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertCircle, BarChart3 } from 'lucide-react';
import { z } from 'zod';
import { toast } from 'sonner';

import { useBacktestStore } from '../store';
import { EquityCurveChart } from '../components/charts';
import { SkeletonCard } from '../components/ui/SkeletonCard';
import { SkeletonChart } from '../components/ui/SkeletonChart';
import { PageFooter } from '../components/ui/PageFooter';
import { useStrategies, useCompareStrategies } from '../hooks/apiHooks';
import { DEFAULT_SYMBOL, DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_INITIAL_CAPITAL, DEFAULT_DATA_SOURCE } from '../lib/constants';

const ComparisonFormSchema = z.object({
  symbol: z.string().min(1, 'Symbol is required').max(10),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  initial_capital: z.number().min(1000).max(100000000),
  source: z.enum(['yahoo', 'alpha_vantage']).default('yahoo'),
});

export const ComparisonPage: React.FC = () => {
  const { data: strategies = [], isLoading: isLoadingStrategies } = useStrategies();
  const compareMutation = useCompareStrategies();
  const { comparisonResult, setComparisonResult, error, setError } = useBacktestStore();
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(ComparisonFormSchema),
    defaultValues: {
      symbol: DEFAULT_SYMBOL,
      start_date: DEFAULT_START_DATE,
      end_date: DEFAULT_END_DATE,
      initial_capital: DEFAULT_INITIAL_CAPITAL,
      source: DEFAULT_DATA_SOURCE,
    },
  });

  const toggleStrategy = (name: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]
    );
  };

  const onSubmit = async (data: { symbol: string; start_date: string; end_date: string; initial_capital: number; source: 'yahoo' | 'alpha_vantage' }) => {
    if (selectedStrategies.length < 2) return;
    setError(null);
    try {
      const result = await compareMutation.mutateAsync({ strategyNames: selectedStrategies, config: data });
      setComparisonResult(result);
      toast.success('Comparison completed', {
        description: `Compared ${selectedStrategies.length} strategies`,
      });
    } catch (err: Error | unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error('Comparison failed', { description: message });
    }
  };

  const comparisonLoading = compareMutation.isPending;

  const strategyResults = comparisonResult ? Object.values(comparisonResult.strategies) : [];
  const equityCurveData = comparisonResult
    ? Object.fromEntries(
        Object.entries(comparisonResult.strategies).map(([name, res]) => [name, res.equity_curve])
      )
    : undefined;

  return (
    <div className="animate-fadeIn">
      {/* Configuration */}
      <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <BarChart3 size={20} style={{ color: 'var(--color-accent-400)' }} />
            <h2 className="card-title">Strategy Comparison</h2>
          </div>
          <p className="card-description">Select strategies to compare on the same data</p>
        </div>
        <div className="card-content">
          <div style={{ marginBottom: 'var(--spacing-lg)' }}>
            <label className="form-label" style={{ marginBottom: 'var(--spacing-sm)', display: 'block' }}>
              Select Strategies (min 2)
            </label>
            <div className="strategy-grid">
              {strategies.map((s) => {
                const key = s.registry_key || s.name;
                return (
                  <button
                    key={key}
                    type="button"
                    className={`strategy-chip ${selectedStrategies.includes(key) ? 'strategy-chip-active' : ''}`}
                    onClick={() => toggleStrategy(key)}
                  >
                    {s.name}
                    <span className="strategy-chip-type">{s.type}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="form-grid" style={{ marginBottom: 'var(--spacing-lg)' }}>
              <div className="form-group">
                <label className="form-label">Symbol</label>
                <input type="text" className="form-input" {...register('symbol')} placeholder="AAPL" />
                {errors.symbol && <span className="form-error">{errors.symbol.message}</span>}
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
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={comparisonLoading || isLoadingStrategies || selectedStrategies.length < 2}
            >
              {comparisonLoading ? 'Comparing...' : `Compare ${selectedStrategies.length} Strategies`}
            </button>
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
      {comparisonLoading && !comparisonResult && (
        <>
          <SkeletonChart height={300} />
          <div style={{ marginTop: 'var(--spacing-lg)' }}>
            <SkeletonCard lines={6} />
          </div>
        </>
      )}

      {/* Chart with overlaid equity curves */}
      {comparisonResult && equityCurveData && (
        <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <div className="card-header">
            <h2 className="card-title">Equity Curves</h2>
          </div>
          <div className="card-content">
            <EquityCurveChart
              data={[]}
              comparisonData={equityCurveData}
              initialCapital={comparisonResult.initial_capital}
            />
          </div>
        </section>
      )}

      {/* Comparison table */}
      {strategyResults.length > 0 && (
        <section className="card">
          <div className="card-header">
            <h2 className="card-title">Metrics Comparison</h2>
          </div>
          <div className="card-content">
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th style={{ textAlign: 'right' }}>Return</th>
                    <th style={{ textAlign: 'right' }}>Final Capital</th>
                    <th style={{ textAlign: 'right' }}>Sharpe</th>
                    <th style={{ textAlign: 'right' }}>Max DD</th>
                    <th style={{ textAlign: 'right' }}>Win Rate</th>
                    <th style={{ textAlign: 'right' }}>Trades</th>
                    <th style={{ textAlign: 'right' }}>Profit Factor</th>
                  </tr>
                </thead>
                <tbody>
                  {strategyResults
                    .sort((a, b) => b.total_return - a.total_return)
                    .map((r) => (
                    <tr key={r.strategy}>
                      <td style={{ fontWeight: 600 }}>{r.strategy}</td>
                      <td className={r.total_return >= 0 ? 'text-positive' : 'text-negative'} style={{ textAlign: 'right', fontWeight: 500 }}>
                        {(r.total_return * 100).toFixed(2)}%
                      </td>
                      <td style={{ textAlign: 'right' }}>${r.final_capital.toLocaleString()}</td>
                      <td className={r.metrics.sharpe_ratio >= 0 ? 'text-positive' : 'text-negative'} style={{ textAlign: 'right' }}>
                        {r.metrics.sharpe_ratio.toFixed(2)}
                      </td>
                      <td className="text-negative" style={{ textAlign: 'right' }}>
                        {r.metrics.max_drawdown_pct.toFixed(2)}%
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {(r.metrics.win_rate * 100).toFixed(1)}%
                      </td>
                      <td style={{ textAlign: 'right' }}>{r.total_trades}</td>
                      <td style={{ textAlign: 'right' }}>{r.metrics.profit_factor.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* Page Footer */}
      <PageFooter
        title="Strategy Comparison"
        description="Compare multiple trading strategies side-by-side on identical market data. Visualize equity curves together and compare key performance metrics to select the best approach."
        parameters={[
          { name: 'Strategies', description: 'Select 2 or more strategies to compare' },
          { name: 'Symbol', description: 'Stock ticker to test all strategies against' },
          { name: 'Date Range', description: 'Historical period for the comparison' },
        ]}
        tips={[
          'Compare strategies on the same data for fair evaluation',
          'Look beyond total return - consider Sharpe ratio for risk-adjusted performance',
          'Higher win rate does not always mean better strategy (position sizing matters)',
          'Profit factor > 2 indicates strong risk/reward characteristics',
        ]}
      />
    </div>
  );
};
