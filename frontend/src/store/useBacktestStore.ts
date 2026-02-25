import { create } from 'zustand';
import type { BacktestConfig, BacktestResult, Trade, Strategy } from '../lib/schemas';

interface BacktestState {
  // State
  config: BacktestConfig | null;
  result: BacktestResult | null;
  trades: Trade[];
  strategies: Strategy[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setConfig: (config: BacktestConfig) => void;
  setResult: (result: BacktestResult) => void;
  setTrades: (trades: Trade[]) => void;
  setStrategies: (strategies: Strategy[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
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
  ],
  loading: false,
  error: null,
};

export const useBacktestStore = create<BacktestState>((set) => ({
  ...initialState,
  
  setConfig: (config) => set({ config }),
  setResult: (result) => set({ result }),
  setTrades: (trades) => set({ trades }),
  setStrategies: (strategies) => set({ strategies }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),
}));
