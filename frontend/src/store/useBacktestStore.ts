import { create } from 'zustand';
import type {
  BacktestConfig, BacktestResult, Trade, Strategy,
  EquityCurvePoint, DrawdownPoint, MonthlyReturn,
  ComparisonResult,
} from '../lib/schemas';

interface BacktestState {
  // State
  config: BacktestConfig | null;
  result: BacktestResult | null;
  trades: Trade[];
  strategies: Strategy[];
  loading: boolean;
  error: string | null;
  activeTab: 'backtest' | 'compare';

  // Chart data
  equityCurve: EquityCurvePoint[];
  drawdownSeries: DrawdownPoint[];
  monthlyReturns: MonthlyReturn[];

  // Comparison
  comparisonResult: ComparisonResult | null;
  comparisonLoading: boolean;

  // Actions
  setConfig: (config: BacktestConfig) => void;
  setResult: (result: BacktestResult) => void;
  setTrades: (trades: Trade[]) => void;
  setStrategies: (strategies: Strategy[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setActiveTab: (tab: 'backtest' | 'compare') => void;
  setEquityCurve: (data: EquityCurvePoint[]) => void;
  setDrawdownSeries: (data: DrawdownPoint[]) => void;
  setMonthlyReturns: (data: MonthlyReturn[]) => void;
  setComparisonResult: (result: ComparisonResult | null) => void;
  setComparisonLoading: (loading: boolean) => void;
  reset: () => void;
}

const initialState = {
  config: null,
  result: null,
  trades: [],
  strategies: [
    { name: 'ema_crossover', version: '1.0.0', type: 'momentum', description: 'EMA Crossover Strategy' },
    { name: 'rsi_mean_reversion', version: '1.0.0', type: 'mean_reversion', description: 'RSI Mean Reversion' },
    { name: 'breakout', version: '1.0.0', type: 'breakout', description: 'Breakout Strategy' },
    { name: 'macd', version: '1.0.0', type: 'momentum', description: 'MACD Crossover Strategy' },
    { name: 'bollinger_bands', version: '1.0.0', type: 'mean_reversion', description: 'Bollinger Bands' },
    { name: 'bbands', version: '1.0.0', type: 'breakout', description: 'BB Breakout Strategy' },
    { name: 'ma_ribbon', version: '1.0.0', type: 'momentum', description: 'MA Ribbon Strategy' },
    { name: 'triple_ma', version: '1.0.0', type: 'momentum', description: 'Triple MA Crossover' },
    { name: 'volume_profile', version: '1.0.0', type: 'momentum', description: 'Volume Profile Strategy' },
    { name: 'volume_breakout', version: '1.0.0', type: 'breakout', description: 'Volume Breakout Strategy' },
  ],
  loading: false,
  error: null,
  activeTab: 'backtest' as const,
  equityCurve: [],
  drawdownSeries: [],
  monthlyReturns: [],
  comparisonResult: null,
  comparisonLoading: false,
};

export const useBacktestStore = create<BacktestState>((set) => ({
  ...initialState,

  setConfig: (config) => set({ config }),
  setResult: (result) => set({ result }),
  setTrades: (trades) => set({ trades }),
  setStrategies: (strategies) => set({ strategies }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setEquityCurve: (equityCurve) => set({ equityCurve }),
  setDrawdownSeries: (drawdownSeries) => set({ drawdownSeries }),
  setMonthlyReturns: (monthlyReturns) => set({ monthlyReturns }),
  setComparisonResult: (comparisonResult) => set({ comparisonResult }),
  setComparisonLoading: (comparisonLoading) => set({ comparisonLoading }),
  reset: () => set(initialState),
}));
