import { z } from 'zod';

// ============================================
// Base Schemas (reusable building blocks)
// ============================================

export const BaseConfigSchema = z.object({
  symbol: z.string().min(1, 'Symbol is required').max(10, 'Symbol too long'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  initial_capital: z.number().min(1000, 'Minimum capital is $1,000').max(100000000, 'Maximum capital is $100M'),
  source: z.enum(['yahoo', 'alpha_vantage']),
}).passthrough();

export type BaseConfig = z.infer<typeof BaseConfigSchema>;

export const RiskMetricsSchema = z.object({
  sharpe_ratio: z.number(),
  max_drawdown_pct: z.number(),
  win_rate: z.number(),
  sortino_ratio: z.number(),
  profit_factor: z.number(),
});

export type RiskMetrics = z.infer<typeof RiskMetricsSchema>;

// ============================================
// Backtest Schemas
// ============================================

export const BacktestConfigSchema = BaseConfigSchema.extend({
  strategy_name: z.string().min(1, 'Strategy is required'),
  parameters: z.record(z.string(), z.unknown()).optional(),
}).refine((data) => new Date(data.start_date) < new Date(data.end_date), {
  message: 'Start date must be before end date',
  path: ['start_date'],
});

export type BacktestConfig = z.infer<typeof BacktestConfigSchema>;

export const BacktestResultSchema = z.object({
  final_capital: z.number(),
  total_return: z.number(),
  total_trades: z.number(),
  metrics: RiskMetricsSchema,
});

export type BacktestResult = z.infer<typeof BacktestResultSchema>;

export const TradeSchema = z.object({
  entry_time: z.string(),
  exit_time: z.string(),
  entry_price: z.number(),
  exit_price: z.number(),
  pnl: z.number(),
  pnl_pct: z.number(),
  side: z.string(),
});

export type Trade = z.infer<typeof TradeSchema>;

export const StrategySchema = z.object({
  name: z.string(),
  version: z.string(),
  type: z.string(),
  description: z.string(),
  registry_key: z.string().optional(),
  parameters: z.record(z.string(), z.unknown()).optional(),
});

export type Strategy = z.infer<typeof StrategySchema>;

// ============================================
// Chart Data Types
// ============================================

export interface EquityCurvePoint {
  date: string;
  equity: number;
}

export interface DrawdownPoint {
  date: string;
  drawdown: number;
}

export interface MonthlyReturn {
  year: number;
  month: number;
  return_pct: number;
}

// ============================================
// Comparison Schemas
// ============================================

export const ComparisonConfigSchema = BaseConfigSchema;

export type ComparisonConfig = z.infer<typeof ComparisonConfigSchema>;

export interface ComparisonStrategyResult {
  strategy: string;
  final_capital: number;
  total_return: number;
  total_trades: number;
  metrics: RiskMetrics;
  execution_time_ms: number;
  equity_curve: EquityCurvePoint[];
  drawdown_series: DrawdownPoint[];
}

export interface ComparisonResult {
  symbol: string;
  data_source: string;
  initial_capital: number;
  strategies: Record<string, ComparisonStrategyResult>;
}

// ============================================
// Optimization Schemas
// ============================================

export const OptimizationConfigSchema = BaseConfigSchema.extend({
  strategy_name: z.string().min(1, 'Strategy is required'),
  method: z.enum(['grid', 'random', 'genetic']),
  metric: z.enum(['sharpe_ratio', 'total_return', 'sortino_ratio', 'max_drawdown', 'win_rate']),
  n_iterations: z.number().min(5).max(1000).optional(),
});

export type OptimizationConfig = z.infer<typeof OptimizationConfigSchema>;

export interface OptimizationResultEntry {
  params: Record<string, number | boolean | string>;
  score: number;
}

export interface OptimizationResult {
  best_params: Record<string, number | boolean | string>;
  best_score: number;
  results: OptimizationResultEntry[];
  execution_time_ms: number;
}

// ============================================
// Walk-Forward Schemas
// ============================================

export const WalkForwardConfigSchema = BaseConfigSchema.extend({
  strategy_name: z.string().min(1, 'Strategy is required'),
  train_days: z.number().min(30).max(1000),
  test_days: z.number().min(10).max(365),
});

export type WalkForwardConfig = z.infer<typeof WalkForwardConfigSchema>;

export interface WalkForwardWindow {
  test_start: string;
  test_end: string;
  best_params: Record<string, number | boolean | string>;
  test_return: number;
  test_trades: number;
}

export interface WalkForwardResult {
  avg_train_sharpe: number;
  avg_test_sharpe: number;
  stability_score: number;
  total_test_return: number;
  windows: WalkForwardWindow[];
  execution_time_ms: number;
}

// ============================================
// Portfolio Schemas
// ============================================

export const PortfolioConfigSchema = z.object({
  strategy_name: z.string().min(1, 'Strategy is required'),
  symbols: z.string().min(1, 'Symbols required'),
  weights: z.string().optional(),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  initial_capital: z.number().min(1000).max(100000000),
  rebalance_frequency: z.enum(['none', 'monthly', 'quarterly', 'yearly']),
  rebalance_threshold: z.string().optional(),
  benchmark_symbol: z.string().optional(),
  parameters: z.record(z.string(), z.unknown()).optional(),
});

export type PortfolioConfig = z.infer<typeof PortfolioConfigSchema>;

export interface PortfolioMetrics {
  beta: number;
  alpha: number;
  diversification_ratio: number;
  avg_correlation: number;
  tracking_error: number;
  information_ratio: number;
}

export interface PortfolioAssetResult {
  total_return: number;
  trades: number;
  sharpe: number;
}

export interface PortfolioResult {
  symbols: string[];
  weights: Record<string, number>;
  results: {
    total_return: number;
    total_trades: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    execution_time_ms: number;
  };
  rebalancing: {
    total_events: number;
    total_cost: number;
  };
  portfolio_metrics: PortfolioMetrics | null;
  equity_curve: Array<{ date: string; total: number }>;
  per_asset_results: Record<string, PortfolioAssetResult>;
}
