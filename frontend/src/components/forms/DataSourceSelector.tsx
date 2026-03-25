import { AlertTriangle } from 'lucide-react';
import { useDataSourceStore, type DataSource } from '../../store/useDataSourceStore';
import { DATA_SOURCE_OPTIONS } from '../../lib/constants';

export function DataSourceSelector() {
  const { source, setSource } = useDataSourceStore();
  const currentOption = DATA_SOURCE_OPTIONS.find(opt => opt.value === source);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
      <select
        value={source}
        onChange={(e) => setSource(e.target.value as DataSource)}
        style={{
          padding: '6px 10px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          background: 'var(--color-bg-secondary)',
          color: 'var(--color-text-primary)',
          fontSize: '0.8125rem',
          cursor: 'pointer',
          minWidth: '140px',
        }}
      >
        {DATA_SOURCE_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      
      {currentOption?.warning && (
        <div
          title={currentOption.warning}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: '#f59e0b',
            fontSize: '0.6875rem',
            fontWeight: 500,
          }}
        >
          <AlertTriangle size={12} />
          <span>Limited</span>
        </div>
      )}
    </div>
  );
}
