import React from 'react';
import { useDataSourceStore } from '../../store/useDataSourceStore';

type Market = 'us' | 'india' | 'crypto';

const markets: { value: Market; label: string }[] = [
  { value: 'us', label: 'US' },
  { value: 'india', label: 'India' },
  { value: 'crypto', label: 'Crypto' },
];

export const MarketSelector: React.FC = () => {
  const { market, setMarket } = useDataSourceStore();

  return (
    <div
      style={{
        display: 'flex',
        gap: '2px',
        background: 'var(--color-border)',
        padding: '2px',
        borderRadius: '6px',
      }}
    >
      {markets.map((m) => {
        const isActive = market === m.value;
        return (
          <button
            key={m.value}
            onClick={() => setMarket(m.value)}
            style={{
              padding: '4px 12px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer',
              background: isActive ? 'var(--color-primary)' : 'transparent',
              color: isActive ? 'var(--color-primary-foreground)' : 'var(--color-text-muted)',
              transition: 'all 0.15s ease',
            }}
          >
            {m.label}
          </button>
        );
      })}
    </div>
  );
};