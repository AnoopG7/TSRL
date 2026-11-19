import React from 'react';
import { useDataSourceStore, type Market } from '../../store/useDataSourceStore';

const markets: { value: Market; label: string }[] = [
  { value: 'us', label: 'US' },
  { value: 'india', label: 'India' },
  { value: 'crypto', label: 'Crypto' },
];

export const MarketSelector: React.FC = () => {
  const { market, setMarket } = useDataSourceStore();

  return (
    <div className="segmented" role="group" aria-label="Market">
      {markets.map((m) => (
        <button
          key={m.value}
          type="button"
          aria-pressed={market === m.value}
          onClick={() => setMarket(m.value)}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
};
