import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type DataSource = 'yahoo' | 'alpha_vantage';
export type Market = 'us' | 'india' | 'crypto';

interface CurrencyInfo {
  symbol: string;
  code: string;
  position: 'prefix' | 'suffix';
}

const CURRENCY_MAP: Record<Market, CurrencyInfo> = {
  us: { symbol: '$', code: 'USD', position: 'prefix' },
  india: { symbol: '₹', code: 'INR', position: 'prefix' },
  crypto: { symbol: '$', code: 'USD', position: 'prefix' },
};

interface DataSourceState {
  source: DataSource;
  market: Market;
  setSource: (source: DataSource) => void;
  setMarket: (market: Market) => void;
  getCurrency: () => CurrencyInfo;
}

export const useDataSourceStore = create<DataSourceState>()(
  persist(
    (set, get) => ({
      source: 'yahoo',
      market: 'us',
      setSource: (source) => set({ source }),
      setMarket: (market) => set({ market }),
      getCurrency: () => CURRENCY_MAP[get().market],
    }),
    {
      name: 'tsrl-data-source',
    }
  )
);
