import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
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
