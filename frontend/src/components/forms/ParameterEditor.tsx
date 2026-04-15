import React, { useEffect, useState } from 'react';
import type { Strategy } from '../../lib/schemas';
import { Settings2 } from 'lucide-react';

type ParamValue = string | number | boolean;

interface ParameterEditorProps {
  strategy: Strategy | undefined;
  onChange: (parameters: Record<string, ParamValue>) => void;
}

export const ParameterEditor: React.FC<ParameterEditorProps> = ({ strategy, onChange }) => {
  const [params, setParams] = useState<Record<string, ParamValue>>({});

  useEffect(() => {
    if (strategy?.parameters && Object.keys(strategy.parameters).length > 0) {
      const normalizedParams: Record<string, ParamValue> = {};
      Object.entries(strategy.parameters).forEach(([key, rawVal]) => {
        const val = (typeof rawVal === 'object' && rawVal !== null && 'value' in rawVal) 
          ? (rawVal as { value: ParamValue }).value 
          : rawVal as ParamValue;
        normalizedParams[key] = val;
      });
      setParams(normalizedParams);
      onChange(normalizedParams);
    } else {
      setParams({});
      onChange({});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strategy?.registry_key]);

  const handleChange = (key: string, value: string | number | boolean) => {
    const newParams = { ...params, [key]: value };
    setParams(newParams);
    onChange(newParams);
  };

  if (!strategy || !strategy.parameters || Object.keys(strategy.parameters).length === 0) {
    return null;
  }

  return (
    <div className="form-group" style={{ gridColumn: '1 / -1', marginTop: 'var(--spacing-md)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)' }}>
        <Settings2 size={16} style={{ color: 'var(--color-accent-400)' }} />
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Strategy Parameters</h3>
      </div>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
        gap: 'var(--spacing-md)',
        padding: 'var(--spacing-md)',
        background: 'var(--color-bg-tertiary)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)'
      }}>
        {Object.entries(strategy.parameters).map(([key, rawVal]) => {
          const defaultValue = (typeof rawVal === 'object' && rawVal !== null && 'value' in rawVal) ? rawVal.value : rawVal;
          const type = typeof defaultValue;
          const displayKey = key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
          
          return (
            <div key={key}>
              <label className="form-label" style={{ fontSize: '0.75rem' }}>{displayKey}</label>
              {type === 'boolean' ? (
                <select 
                  className="form-input" 
                  value={params[key]?.toString() || defaultValue?.toString() || 'false'}
                  onChange={(e) => handleChange(key, e.target.value === 'true')}
                >
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              ) : type === 'number' ? (
                <input 
                  type="number" 
                  step="any"
                  className="form-input" 
                  value={String(params[key] ?? defaultValue ?? '')}
                  onChange={(e) => handleChange(key, parseFloat(e.target.value))}
                />
              ) : (
                <input 
                  type="text" 
                  className="form-input" 
                  value={String(params[key] ?? defaultValue ?? '')}
                  onChange={(e) => handleChange(key, e.target.value)}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
