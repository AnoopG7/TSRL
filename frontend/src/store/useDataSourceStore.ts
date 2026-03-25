import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type DataSource = 'yahoo' | 'alpha_vantage';

interface DataSourceState {
  source: DataSource;
  setSource: (source: DataSource) => void;
}

export const useDataSourceStore = create<DataSourceState>()(
  persist(
    (set) => ({
      source: 'yahoo',
      setSource: (source) => set({ source }),
    }),
    {
      name: 'tsrl-data-source',
    }
  )
);
