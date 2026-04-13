// Default trading parameters (matches backend config/settings.yaml)
export const DEFAULT_COMMISSION = 0.001;
export const DEFAULT_SLIPPAGE = 0.0005;

// Default form values
export const DEFAULT_SYMBOL = 'AAPL';
export const DEFAULT_START_DATE = '2020-01-01';
export const DEFAULT_END_DATE = '2024-01-01';
export const DEFAULT_INITIAL_CAPITAL = 100000;
export const DEFAULT_DATA_SOURCE = 'yahoo';

// Data source options
export const DATA_SOURCE_OPTIONS: Array<{
  value: 'yahoo' | 'alpha_vantage';
  label: string;
  warning?: string | null;
}> = [
  { 
    value: 'yahoo', 
    label: 'Yahoo Finance', 
    warning: null 
  },
  { 
    value: 'alpha_vantage', 
    label: 'Alpha Vantage', 
    warning: 'Free tier: max 100 days, 25 requests/day' 
  },
] as const;

// API endpoints
export const API_ENDPOINTS = {
  strategies: '/api/v1/strategies',
  backtestRun: '/api/v1/backtests/run',
  backtestCompare: '/api/v1/backtests/compare',
  backtestPortfolio: '/api/v1/backtests/portfolio',
  optimization: (method: string) => `/api/v1/optimization/${method}`,
  walkforward: '/api/v1/walkforward/run',
  fundamentals: (symbol: string) => `/api/v1/fundamentals/${symbol}`,
  fundamentalsNews: (symbol: string) => `/api/v1/fundamentals/${symbol}/news`,
  fundamentalsInsiders: (symbol: string) => `/api/v1/fundamentals/${symbol}/insiders`,
  fundamentalsCompare: '/api/v1/fundamentals/compare',
} as const;

// Query keys for React Query
export const QUERY_KEYS = {
  strategies: ['strategies'] as const,
  fundamentals: (symbol: string) => ['fundamentals', symbol] as const,
} as const;

// Cache times (in milliseconds)
export const CACHE_TIMES = {
  strategies: 5 * 60 * 1000, // 5 minutes - strategies rarely change
  fundamentals: 60 * 60 * 1000, // 1 hour - fundamentals update intraday
} as const;
