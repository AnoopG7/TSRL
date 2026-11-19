import { AlertTriangle } from 'lucide-react';
import { useDataSourceStore, type DataSource } from '../../store/useDataSourceStore';
import { DATA_SOURCE_OPTIONS } from '../../lib/constants';

export function DataSourceSelector() {
  const { source, setSource } = useDataSourceStore();
  const currentOption = DATA_SOURCE_OPTIONS.find((opt) => opt.value === source);

  return (
    <span className="row">
      <select
        className="select-compact"
        aria-label="Price data source"
        value={source}
        onChange={(e) => setSource(e.target.value as DataSource)}
      >
        {DATA_SOURCE_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {currentOption?.warning && (
        <span className="limit-flag" title={currentOption.warning}>
          <AlertTriangle size={12} /> Limited
        </span>
      )}
    </span>
  );
}
