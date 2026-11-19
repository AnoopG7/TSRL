import type { Strategy } from './schemas';
import { snakeToTitleCase } from './utils';

const OVERRIDES: Record<string, string> = {
  ema_crossover: 'EMA Crossover',
  rsi_mean_reversion: 'RSI Mean Reversion',
  breakout: 'Breakout',
  volume_profile: 'Volume Profile',
  volume_breakout: 'Volume Breakout',
  macd: 'MACD',
  ma_ribbon: 'MA Ribbon',
  triple_ma: 'Triple MA',
  bbands: 'Bollinger Breakout',
  bollinger_bands: 'Bollinger Reversion',
  ml_random_forest: 'Random Forest',
  ml_gradient_boosting: 'Gradient Boosting',
};

export const FAMILY_LABELS: Record<string, string> = {
  momentum: 'Momentum',
  mean_reversion: 'Mean reversion',
  breakout: 'Breakout',
  volatility: 'Volatility',
  ml: 'Machine learning',
};

export const strategyKey = (s: Strategy) => s.registry_key || s.name;

/** Human label for a strategy, falling back gracefully when the backend name is a raw key. */
export function strategyLabel(s: Strategy | string | undefined | null): string {
  if (!s) return '';
  const key = typeof s === 'string' ? s : strategyKey(s);
  if (OVERRIDES[key]) return OVERRIDES[key];
  const name = typeof s === 'string' ? s : s.name;
  return name.includes('_') || name === name.toLowerCase() ? snakeToTitleCase(name) : name;
}

export const familyLabel = (type: string) => FAMILY_LABELS[type] ?? snakeToTitleCase(type);

export const isMLStrategy = (s: Strategy) => s.type === 'ml';
