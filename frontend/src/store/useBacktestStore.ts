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
  activeTab: 'backtest' | 'compare' | 'portfolio';

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
  setActiveTab: (tab: 'backtest' | 'compare' | 'portfolio') => void;
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
  strategies: [],
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
