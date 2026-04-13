import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../lib/api';
import {
  DEFAULT_COMMISSION,
  DEFAULT_SLIPPAGE,
  API_ENDPOINTS,
  QUERY_KEYS,
  CACHE_TIMES,
} from '../lib/constants';
import { useDataSourceStore } from '../store/useDataSourceStore';
import { parseCommaSeparated } from '../lib/utils';
import type {
  Strategy,
  BacktestConfig,
  ComparisonConfig,
  ComparisonResult,
  PortfolioConfig,
  PortfolioResult,
  OptimizationResult,
  WalkForwardResult,
} from '../lib/schemas';
import type { FundamentalReport } from '../lib/schemas/fundamental.schema';

interface BacktestResponse {
  status: string;
  backtest_id?: string;
  results: {
    final_capital: number;
    total_return: number;
    total_trades: number;
    metrics: {
      sharpe_ratio: number;
      max_drawdown_pct: number;
      win_rate: number;
      sortino_ratio: number;
      profit_factor: number;
    };
    execution_time_ms: number;
  };
  equity_curve: Array<{ date: string; equity: number }>;
  drawdown_series: Array<{ date: string; drawdown: number }>;
  monthly_returns: Array<{ year: number; month: number; return_pct: number }>;
  trades: Array<{
    entry_time: string;
    exit_time: string;
    entry_price: number;
    exit_price: number;
    pnl: number;
    pnl_pct: number;
    side: string;
  }>;
}

export function useStrategies() {
  return useQuery<Strategy[]>({
    queryKey: QUERY_KEYS.strategies,
    queryFn: async () => {
      const { data } = await api.get(API_ENDPOINTS.strategies);
      return data.strategies;
    },
    staleTime: CACHE_TIMES.strategies,
  });
}

export function useRunBacktest() {
  const source = useDataSourceStore((state) => state.source);
  return useMutation<BacktestResponse, Error, BacktestConfig>({
    mutationFn: async (config) => {
      const { data } = await api.post(API_ENDPOINTS.backtestRun, {
        ...config,
        commission: DEFAULT_COMMISSION,
        slippage: DEFAULT_SLIPPAGE,
        source,
      });
      return data;
    },
  });
}

export function useCompareStrategies() {
  const source = useDataSourceStore((state) => state.source);
  return useMutation<ComparisonResult, Error, { strategyNames: string[]; config: ComparisonConfig }>({
    mutationFn: async ({ strategyNames, config }) => {
      const { data } = await api.post(API_ENDPOINTS.backtestCompare, {
        ...config,
        strategy_names: strategyNames,
        commission: DEFAULT_COMMISSION,
        slippage: DEFAULT_SLIPPAGE,
        source,
      });
      return data;
    },
  });
}

export function useRunPortfolioBacktest() {
  const source = useDataSourceStore((state) => state.source);
  return useMutation<PortfolioResult, Error, PortfolioConfig>({
    mutationFn: async (config) => {
      const symbolList = parseCommaSeparated(config.symbols);
      let weightsDict: Record<string, number> | undefined;

      if (config.weights && config.weights.trim()) {
        try {
          weightsDict = JSON.parse(config.weights);
        } catch {
          const parts = parseCommaSeparated(config.weights);
          if (parts.length === symbolList.length) {
            weightsDict = Object.fromEntries(
              symbolList.map((sym, idx) => [sym, parseFloat(parts[idx])])
            );
          }
        }
      }

      const { data } = await api.post(API_ENDPOINTS.backtestPortfolio, {
        strategy_name: config.strategy_name,
        symbols: symbolList,
        weights: weightsDict,
        start_date: config.start_date,
        end_date: config.end_date,
        initial_capital: config.initial_capital,
        rebalance_frequency: config.rebalance_frequency,
        rebalance_threshold: config.rebalance_threshold ? parseFloat(config.rebalance_threshold) : undefined,
        benchmark_symbol: config.benchmark_symbol || undefined,
        parameters: config.parameters,
        commission: DEFAULT_COMMISSION,
        slippage: DEFAULT_SLIPPAGE,
        source,
      });
      return data;
    },
  });
}

interface OptimizationInput {
  method: 'grid' | 'random' | 'genetic';
  config: {
    strategy_name: string;
    symbol: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    metric: string;
    n_iterations?: number;
    param_grid: Record<string, (number | boolean | string)[]>;
  };
}

export function useRunOptimization() {
  const source = useDataSourceStore((state) => state.source);
  return useMutation<OptimizationResult, Error, OptimizationInput>({
    mutationFn: async ({ method, config }) => {
      const payload: Record<string, unknown> = {
        ...config,
        commission: DEFAULT_COMMISSION,
        slippage: DEFAULT_SLIPPAGE,
        source,
      };
      if (config.n_iterations !== undefined) {
        payload.n_iterations = config.n_iterations;
      }
      const { data } = await api.post(API_ENDPOINTS.optimization(method), payload);
      return data;
    },
  });
}

interface WalkForwardInput {
  strategy_name: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  train_days: number;
  test_days: number;
  param_grid: Record<string, (number | boolean | string)[]>;
}

export function useRunWalkForward() {
  const source = useDataSourceStore((state) => state.source);
  return useMutation<WalkForwardResult, Error, WalkForwardInput>({
    mutationFn: async (config) => {
      const { data } = await api.post(API_ENDPOINTS.walkforward, {
        ...config,
        commission: DEFAULT_COMMISSION,
        slippage: DEFAULT_SLIPPAGE,
        source,
      });
      return data;
    },
  });
}

// ── Fundamental Analysis Hooks ─────────────────────────────────────────

export function useFundamentals(symbol: string, source: 'yfinance' | 'fmp' = 'yfinance', enabled: boolean = true, useCache: boolean = true) {
  return useQuery<FundamentalReport & { from_cache?: boolean }>({
    queryKey: [...QUERY_KEYS.fundamentals(symbol), source],
    queryFn: async () => {
      const { data } = await api.get(`${API_ENDPOINTS.fundamentals(symbol)}?source=${source}&use_cache=${useCache}`);
      return data;
    },
    enabled: enabled && symbol.length > 0,
    staleTime: useCache ? CACHE_TIMES.fundamentals : 0,
  });
}

export function useCompareFundamentals() {
  return useMutation({
    mutationFn: async ({ symbols, source = 'yfinance' }: { symbols: string, source?: 'yfinance' | 'fmp' }) => {
      const { data } = await api.get(
        `${API_ENDPOINTS.fundamentalsCompare}?symbols=${symbols}&source=${source}`
      );
      return data;
    },
  });
}

export function useInsiders(symbol: string, source: 'yfinance' | 'fmp' = 'yfinance', enabled: boolean = true) {
  return useQuery({
    queryKey: ['insiders', symbol, source],
    queryFn: async () => {
      const { data } = await api.get(`${API_ENDPOINTS.fundamentalsInsiders(symbol)}?source=${source}`);
      return data;
    },
    enabled: enabled && symbol.length > 0,
    staleTime: CACHE_TIMES.fundamentals,
  });
}

