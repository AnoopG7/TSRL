import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FlaskConical, AlertCircle, Play } from 'lucide-react';
import { toast } from 'sonner';
import { BacktestConfigSchema } from '../lib/schemas';
import type { BacktestConfig } from '../lib/schemas';
import { useBacktestStore } from '../store';
import { ParameterEditor } from '../components/forms/ParameterEditor';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState, RunProgress } from '../components/ui/RunState';
import { PageFooter } from '../components/ui/PageFooter';
import { BacktestResults } from '../components/results/BacktestResults';
import { useStrategies, useRunBacktest } from '../hooks/apiHooks';
import { strategyKey, strategyLabel, familyLabel } from '../lib/strategies';
import { formatPct } from '../lib/utils';
import {
  DEFAULT_SYMBOL, DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_INITIAL_CAPITAL, DEFAULT_DATA_SOURCE,
} from '../lib/constants';

export const BacktestPage: React.FC = () => {
  const { data: strategies = [], isLoading: isLoadingStrategies } = useStrategies();
  const runBacktest = useRunBacktest();
  const {
    config, result, trades, error, equityCurve, drawdownSeries, monthlyReturns,
    setConfig, setResult, setError, setTrades, setEquityCurve, setDrawdownSeries, setMonthlyReturns,
  } = useBacktestStore();

  const { register, handleSubmit, watch, setValue, getValues, formState: { errors } } = useForm<BacktestConfig>({
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
    if (strategies.length > 0 && !getValues('strategy_name')) {
      setValue('strategy_name', strategyKey(strategies[0]));
    }
  }, [strategies, setValue, getValues]);

  // Group strategies by family for the picker
  const grouped = useMemo(() => {
    const map = new Map<string, typeof strategies>();
    strategies.forEach((s) => map.set(s.type, [...(map.get(s.type) ?? []), s]));
    return [...map.entries()];
  }, [strategies]);

  const selectedKey = watch('strategy_name');
  const selected = strategies.find((s) => strategyKey(s) === selectedKey);

  const onSubmit = async (data: BacktestConfig) => {
    setError(null);
    try {
      const response = await runBacktest.mutateAsync(data);
      setConfig(data);
      setResult(response.results);
      setTrades(response.trades || []);
      setEquityCurve(response.equity_curve || []);
      setDrawdownSeries(response.drawdown_series || []);
      setMonthlyReturns(response.monthly_returns || []);
      toast.success('Backtest finished', {
        description: `${response.results?.total_trades ?? 0} trades · ${formatPct(response.results?.total_return ?? 0)}`,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error('Backtest failed', { description: message });
    }
  };

  const isRunning = runBacktest.isPending;
  const isML = selected?.type === 'ml';

  return (
    <div className="animate-fadeIn">
      <PageHeader
        kicker="Research"
        icon={FlaskConical}
        title="Backtest a strategy"
        lede="Replay a strategy bar by bar over real price history, with commission and slippage charged on every fill."
      />

      <div className="workbench">
        {/* Configuration rail */}
        <form className="card rail" onSubmit={handleSubmit(onSubmit)} aria-label="Backtest configuration">
          <div className="card-content">
            <div className="form-grid">
              <div className="form-group span-2">
                <label className="form-label" htmlFor="bt-strategy">Strategy</label>
                <select id="bt-strategy" className="form-input" {...register('strategy_name')} disabled={isLoadingStrategies}>
                  {grouped.map(([family, list]) => (
                    <optgroup key={family} label={familyLabel(family)}>
                      {list.map((s) => (
                        <option key={strategyKey(s)} value={strategyKey(s)}>{strategyLabel(s)}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {selected && <span className="form-hint">{selected.description}</span>}
                {errors.strategy_name && <span className="form-error">{errors.strategy_name.message}</span>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="bt-symbol">Symbol</label>
                <input id="bt-symbol" type="text" className="form-input" {...register('symbol')} placeholder="AAPL" autoCapitalize="characters" />
                {errors.symbol && <span className="form-error">{errors.symbol.message}</span>}
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="bt-capital">Capital</label>
                <input id="bt-capital" type="number" className="form-input" {...register('initial_capital', { valueAsNumber: true })} />
                {errors.initial_capital && <span className="form-error">{errors.initial_capital.message}</span>}
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="bt-start">From</label>
                <input id="bt-start" type="date" className="form-input" {...register('start_date')} />
                {errors.start_date && <span className="form-error">{errors.start_date.message}</span>}
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="bt-end">To</label>
                <input id="bt-end" type="date" className="form-input" {...register('end_date')} />
                {errors.end_date && <span className="form-error">{errors.end_date.message}</span>}
              </div>

              <ParameterEditor strategy={selected} onChange={(p) => setValue('parameters', p)} />
            </div>

            {error && (
              <div className="error-message" role="alert">
                <AlertCircle size={16} />
                {error}
              </div>
            )}
          </div>
          <div className="rail-foot">
            <button type="submit" className="btn btn-primary btn-block" disabled={isRunning || isLoadingStrategies}>
              <Play size={15} />
              {isRunning ? 'Running backtest…' : 'Run backtest'}
            </button>
          </div>
        </form>

        {/* Results */}
        <div className="results">
          {isRunning ? (
            <RunProgress
              title={`Backtesting ${strategyLabel(selected)} on ${watch('symbol').toUpperCase()}`}
              pace={isML ? 2.5 : 1.2}
              steps={[
                'Loading price history',
                isML ? 'Engineering features and retraining the model on an expanding window' : 'Generating signals',
                'Simulating fills with commission and slippage',
                'Computing risk metrics',
              ]}
              note={isML ? 'ML strategies refit as they go, so this takes a few seconds longer.' : undefined}
            />
          ) : result ? (
            <BacktestResults
              result={result}
              trades={trades}
              equityCurve={equityCurve}
              drawdownSeries={drawdownSeries}
              monthlyReturns={monthlyReturns}
              caption={config ? `${strategyLabel(config.strategy_name)} on ${config.symbol.toUpperCase()}` : undefined}
            />
          ) : (
            <EmptyState
              title="Nothing run yet"
              body="Pick a strategy and a date range, then run it. You'll get an equity curve, drawdowns, a monthly returns heatmap, a full risk tear sheet and the trade log."
            />
          )}
        </div>
      </div>

      <PageFooter
        title="backtesting"
        description="The event-driven engine processes the series one bar at a time, opening and closing positions as signals fire. Every fill is charged commission (0.1%) and slippage (0.05%), so the numbers reflect trading costs rather than a frictionless ideal."
        parameters={[
          { name: 'Strategy', description: 'Any strategy in the registry: momentum, mean reversion, breakout or ML.' },
          { name: 'Symbol', description: 'A ticker in the selected market, e.g. AAPL, RELIANCE.NS or BTC-USD.' },
          { name: 'Capital', description: 'Starting portfolio value for the simulation.' },
        ]}
        tips={[
          'Use at least two years of data so results span more than one market regime.',
          'A high return with a low Sharpe usually means you were paid for taking on volatility.',
          'Before trusting a parameter set, check it out-of-sample with Walk-forward.',
        ]}
      />
    </div>
  );
};
