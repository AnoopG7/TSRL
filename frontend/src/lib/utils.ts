import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { useDataSourceStore, type Market } from "../store/useDataSourceStore"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const CURRENCY_CONFIG: Record<Market, { symbol: string; locale: string; decimals: number }> = {
  us: { symbol: '$', locale: 'en-US', decimals: 2 },
  india: { symbol: '₹', locale: 'en-IN', decimals: 2 },
  crypto: { symbol: '$', locale: 'en-US', decimals: 2 },
};

/**
 * Get current currency symbol based on market
 */
export function useCurrencySymbol(): string {
  const market = useDataSourceStore((state) => state.market);
  return CURRENCY_CONFIG[market].symbol;
}

/**
 * Get current market from store
 */
export function useCurrentMarket(): Market {
  return useDataSourceStore((state) => state.market);
}

/**
 * Format a number as currency based on the selected market
 * @example formatCurrency(1565.40) => "$1,565.40" (US) or "₹1,565.40" (India)
 */
export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—';
  
  const market = useDataSourceStore.getState().market;
  const config = CURRENCY_CONFIG[market];
  
  return `${config.symbol}${amount.toLocaleString(config.locale, { 
    minimumFractionDigits: config.decimals,
    maximumFractionDigits: config.decimals 
  })}`;
}

/**
 * Format large numbers with abbreviation (T, B, M)
 * @example formatLargeCurrency(1_500_000_000) => "$1.50B" or "₹1.50B"
 */
export function formatLargeCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—';
  
  const market = useDataSourceStore.getState().market;
  const config = CURRENCY_CONFIG[market];
  
  const absAmount = Math.abs(amount);
  let scaled: number;
  let suffix: string;
  
  if (absAmount >= 1e12) {
    scaled = amount / 1e12;
    suffix = 'T';
  } else if (absAmount >= 1e9) {
    scaled = amount / 1e9;
    suffix = 'B';
  } else if (absAmount >= 1e6) {
    scaled = amount / 1e6;
    suffix = 'M';
  } else {
    return formatCurrency(amount);
  }
  
  return `${config.symbol}${scaled.toFixed(2)}${suffix}`;
}

/**
 * Convert snake_case to Title Case
 * @example snakeToTitleCase('short_period') => 'Short Period'
 */
export function snakeToTitleCase(str: string): string {
  return str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

/**
 * Parse comma-separated string into array of trimmed, non-empty strings
 * @example parseCommaSeparated('AAPL, GOOGL, MSFT') => ['AAPL', 'GOOGL', 'MSFT']
 */
export function parseCommaSeparated(str: string): string[] {
  return str.split(',').map(s => s.trim()).filter(Boolean);
}

/**
 * Extract value from parameter object (handles both raw values and {value: T} objects)
 */
export function extractParamValue<T>(rawVal: T | { value: T }): T {
  if (typeof rawVal === 'object' && rawVal !== null && 'value' in rawVal) {
    return (rawVal as { value: T }).value;
  }
  return rawVal as T;
}