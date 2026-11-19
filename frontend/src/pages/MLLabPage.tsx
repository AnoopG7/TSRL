import { useMemo, useState } from 'react';
import { BrainCircuit, AlertCircle, Play, Trees, Layers } from 'lucide-react';
import { toast } from 'sonner';
import { PageHeader } from '../components/ui/PageHeader';
import { ParameterEditor } from '../components/forms/ParameterEditor';
import { EmptyState, RunProgress } from '../components/ui/RunState';
import { PageFooter } from '../components/ui/PageFooter';
import { BacktestResults } from '../components/results/BacktestResults';
import { useStrategies, useRunBacktest, type BacktestResponse } from '../hooks/apiHooks';
import { strategyKey, strategyLabel } from '../lib/strategies';
import { formatPct } from '../lib/utils';
import { DEFAULT_INITIAL_CAPITAL, DEFAULT_DATA_SOURCE } from '../lib/constants';

/** Feature subsets each model trains on (mirrors src/ml/strategies/ml_strategies.py). */
const MODEL_FEATURES: Record<string, string[]> = {
  ml_random_forest: [
    'rsi_14', 'rsi_30', 'momentum_10', 'momentum_20', 'volatility_14', 'atr_14',
    'volume_ratio_20', 'ema_9_21_diff', 'bb_position_20', 'returns', 'returns_5d', 'returns_10d', 'mfi',
  ],
  ml_gradient_boosting: [
    'rsi_14', 'momentum_10', 'momentum_20', 'volatility_14', 'atr_14',
    'volume_ratio_20', 'ema_9_21_diff', 'bb_position_20', 'returns', 'returns_5d', 'cci',
  ],
};

const MODEL_BLURB: Record<string, { icon: typeof Trees; text: string }> = {
  ml_random_forest: { icon: Trees, text: 'Bagged decision trees, robust to noisy features' },
  ml_gradient_boosting: { icon: Layers, text: 'Boosted shallow trees, each fixing the last one’s errors' },
};

type Params = Record<string, string | number | boolean>;

/** Expanding-window diagram: train → embargo → predict until the next refit. */
function WindowDiagram({ every, horizon }: { every: number; horizon: number }) {
  const rows = [0, 1, 2];
  return (
    <svg className="window-viz" viewBox="0 0 520 118" role="img"
      aria-label={`Every ${every} bars the model refits on all resolved labels, skips a ${horizon}-bar embargo, then predicts until the next refit`}>
      {rows.map((r) => {
        const trainW = 200 + r * 64;
        const y = 8 + r * 34;
        return (
          <g key={r}>
            <rect className="train" x={20} y={y} width={trainW} height={22} rx={5} />
            <rect className="gap" x={20 + trainW + 4} y={y} width={40} height={22} rx={5} />
            <rect className="test" x={20 + trainW + 48} y={y} width={60} height={22} rx={5} />
            {r === 0 && (
              <>
                <text x={30} y={y + 15}>fit on labels already resolved</text>
                <text x={20 + trainW + 8} y={y + 15}>gap {horizon}</text>
                <text x={20 + trainW + 54} y={y + 15}>predict {every}</text>
              </>
            )}
          </g>
        );
      })}
      <text x={20} y={114}>time →  ·  the gap equals the {horizon}-bar label horizon, so no label peeks ahead</text>
    </svg>
  );
}

export const MLLabPage: React.FC = () => {
  const { data: strategies = [] } = useStrategies();
  const run = useRunBacktest();
  const models = useMemo(() => strategies.filter((s) => s.type === 'ml'), [strategies]);

  const [modelKey, setModelKey] = useState('ml_random_forest');
  const [symbol, setSymbol] = useState('AAPL');
  const [start, setStart] = useState('2021-01-01');
  const [end, setEnd] = useState('2024-01-01');
  const [params, setParams] = useState<Params>({});
  const [response, setResponse] = useState<BacktestResponse | null>(null);
  const [ranLabel, setRanLabel] = useState('');
  const [error, setError] = useState<string | null>(null);

  const model = models.find((m) => strategyKey(m) === modelKey);
  const features = MODEL_FEATURES[modelKey] ?? [];
  const every = Number(params.retrain_period ?? 20);
  const horizon = Number(params.prediction_horizon ?? 5);

  const onRun = async () => {
    setError(null);
    if (new Date(start) >= new Date(end)) {
      setError('Start date must be before end date.');
      return;
    }
    try {
      const res = await run.mutateAsync({
        strategy_name: modelKey,
        symbol: symbol.trim().toUpperCase(),
        start_date: start,
        end_date: end,
        initial_capital: DEFAULT_INITIAL_CAPITAL,
        parameters: params,
        source: DEFAULT_DATA_SOURCE,
      });
      setResponse(res);
      setRanLabel(`${strategyLabel(modelKey)} on ${symbol.trim().toUpperCase()}`);
      toast.success('Model trained and backtested', {
        description: `${res.results.total_trades} trades · ${formatPct(res.results.total_return)}`,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error('Training run failed', { description: message });
    }
  };

  return (
    <div className="animate-fadeIn">
      <PageHeader
        kicker="Models"
        icon={BrainCircuit}
        tone="model"
        title="ML Lab"
        lede="Train a tree-ensemble classifier to predict whether price will rise, fall or drift over the next few bars, then trade its predictions through the same backtest engine as every other strategy."
      />

      {/* Method: this really is a sequence */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">How the model is built</h2>
          <p className="card-description">The pipeline that runs when you train. Nothing is fitted on future data.</p>
        </div>
        <div className="card-content stack">
          <div className="method">
            <div className="method-step">
              <span className="idx">1 · Features</span>
              <h4>111 engineered features</h4>
              <p>Lags, rolling stats, technical indicators and volume signals. The model uses a focused subset of {features.length}.</p>
            </div>
            <div className="method-step">
              <span className="idx">2 · Labels</span>
              <h4>Three classes</h4>
              <p>Up if the close {horizon} bars ahead is more than 1% higher, down if more than 1% lower, flat otherwise.</p>
            </div>
            <div className="method-step">
              <span className="idx">3 · Training</span>
              <h4>Expanding window</h4>
              <p>Every {every} bars, standardise and refit on every label already resolved, leaving a {horizon}-bar embargo.</p>
            </div>
            <div className="method-step">
              <span className="idx">4 · Trading</span>
              <h4>Predictions become signals</h4>
              <p>Up opens a long, down opens a short, flat stays out. Costs are charged on every fill.</p>
            </div>
          </div>
          <div className="ml-inputs">
            <div>
              <div className="form-label" style={{ marginBottom: 8 }}>Inputs to {strategyLabel(modelKey)}</div>
              <div className="feature-chips">
                {features.map((f) => <span key={f} className="feature-chip">{f}</span>)}
              </div>
            </div>
            <WindowDiagram every={every} horizon={horizon} />
          </div>
        </div>
      </section>

      <div className="workbench">
        <form className="card rail" onSubmit={(e) => { e.preventDefault(); onRun(); }} aria-label="Model configuration">
          <div className="card-content">
            <div className="form-grid">
              <div className="form-group span-2">
                <span className="form-label">Model</span>
                <div className="model-pick">
                  {(models.length ? models.map(strategyKey) : Object.keys(MODEL_FEATURES)).map((k) => {
                    const blurb = MODEL_BLURB[k];
                    return (
                      <button
                        type="button"
                        key={k}
                        className="model-option"
                        aria-pressed={modelKey === k}
                        onClick={() => setModelKey(k)}
                      >
                        <b>{strategyLabel(k)}</b>
                        {blurb && <span>{blurb.text}</span>}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="form-group span-2">
                <label className="form-label" htmlFor="ml-symbol">Symbol</label>
                <input id="ml-symbol" className="form-input" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="ml-start">From</label>
                <input id="ml-start" type="date" className="form-input" value={start} onChange={(e) => setStart(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="ml-end">To</label>
                <input id="ml-end" type="date" className="form-input" value={end} onChange={(e) => setEnd(e.target.value)} />
              </div>
              <ParameterEditor strategy={model} onChange={setParams} hidden={['lookback']} />
            </div>

            {error && (
              <div className="error-message" role="alert">
                <AlertCircle size={16} />
                {error}
              </div>
            )}
          </div>
          <div className="rail-foot">
            <button type="submit" className="btn btn-primary btn-block" disabled={run.isPending}>
              <Play size={15} />
              {run.isPending ? 'Training…' : 'Train and backtest'}
            </button>
          </div>
        </form>

        <div className="results">
          {run.isPending ? (
            <RunProgress
              title={`Training ${strategyLabel(modelKey)} on ${symbol.toUpperCase()}`}
              pace={2.5}
              steps={[
                'Loading price history',
                `Building ${features.length} features and 3-class labels`,
                `Refitting on an expanding window every ${every} bars`,
                'Trading the predictions through the engine',
                'Computing risk metrics',
              ]}
              note="Three years of daily data usually takes about ten seconds."
            />
          ) : response ? (
            <BacktestResults
              result={response.results}
              trades={response.trades || []}
              equityCurve={response.equity_curve || []}
              drawdownSeries={response.drawdown_series || []}
              monthlyReturns={response.monthly_returns || []}
              caption={ranLabel}
            />
          ) : (
            <EmptyState
              title="No model trained yet"
              body="Choose a model and a symbol, then train it. Results show up here with the same tear sheet as a rule-based backtest, so you can compare the two directly."
            />
          )}
        </div>
      </div>

      <PageFooter
        title="the ML Lab"
        description="Models are scikit-learn RandomForestClassifier and GradientBoostingClassifier with a StandardScaler, refit inside the backtest loop. Because each fit only sees labels whose outcome is already known, results are an honest out-of-sample estimate rather than a curve fit."
        parameters={[
          { name: 'Prediction horizon', description: 'How many bars ahead the label looks when deciding up, down or flat.' },
          { name: 'Retrain period', description: 'How many bars pass between refits. The embargo is always the prediction horizon.' },
          { name: 'Min train samples', description: 'The model stays flat until it has this many labelled bars.' },
        ]}
        tips={[
          'A shorter retrain period adapts faster but costs more fits; 10–20 bars is a reasonable start.',
          'Compare against a rule-based strategy on the same symbol and dates in Compare.',
          'A low win rate with a profit factor above 1 means winners are larger than losers.',
        ]}
      />
    </div>
  );
};
