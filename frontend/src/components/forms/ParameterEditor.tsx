import React, { useEffect, useState } from 'react';
import type { Strategy } from '../../lib/schemas';
import { Settings2 } from 'lucide-react';
import { snakeToTitleCase } from '../../lib/utils';

type ParamValue = string | number | boolean;

interface ParamMeta {
  value: ParamValue;
  min_value?: number;
  max_value?: number;
  step?: number;
  description?: string;
}

interface ParameterEditorProps {
  strategy: Strategy | undefined;
  onChange: (parameters: Record<string, ParamValue>) => void;
  /** Parameter keys to keep at their defaults without showing an input. */
  hidden?: string[];
}

const meta = (raw: unknown): ParamMeta =>
  typeof raw === 'object' && raw !== null && 'value' in raw
    ? (raw as ParamMeta)
    : { value: raw as ParamValue };

export const ParameterEditor: React.FC<ParameterEditorProps> = ({ strategy, onChange, hidden = [] }) => {
  const [params, setParams] = useState<Record<string, ParamValue>>({});

  useEffect(() => {
    if (strategy?.parameters && Object.keys(strategy.parameters).length > 0) {
      const normalized: Record<string, ParamValue> = {};
      Object.entries(strategy.parameters).forEach(([key, raw]) => {
        normalized[key] = meta(raw).value;
      });
      setParams(normalized);
      onChange(normalized);
    } else {
      setParams({});
      onChange({});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strategy?.registry_key]);

  const handleChange = (key: string, value: ParamValue) => {
    const next = { ...params, [key]: value };
    setParams(next);
    onChange(next);
  };

  if (!strategy || !strategy.parameters || Object.keys(strategy.parameters).length === 0) {
    return null;
  }

  const entries = Object.entries(strategy.parameters).filter(([key]) => !hidden.includes(key));

  return (
    <div className="param-panel">
      <div className="param-panel-head">
        <span className="param-panel-title">
          <Settings2 size={15} />
          Strategy parameters
        </span>
        <span className="form-hint">{entries.length} tunable</span>
      </div>

      <div className="param-grid">
        {entries.map(([key, raw]) => {
          const m = meta(raw);
          const type = typeof m.value;
          const id = `param-${key}`;
          const range = m.min_value != null && m.max_value != null ? `${m.min_value}–${m.max_value}` : undefined;

          return (
            <div className="form-group" key={key}>
              <label className="form-label" htmlFor={id} title={m.description}>
                {snakeToTitleCase(key)}
              </label>
              {type === 'boolean' ? (
                <select
                  id={id}
                  className="form-input"
                  value={String(params[key] ?? m.value)}
                  onChange={(e) => handleChange(key, e.target.value === 'true')}
                >
                  <option value="true">On</option>
                  <option value="false">Off</option>
                </select>
              ) : type === 'number' ? (
                <input
                  id={id}
                  type="number"
                  step={m.step ?? 'any'}
                  min={m.min_value}
                  max={m.max_value}
                  className="form-input"
                  value={String(params[key] ?? m.value ?? '')}
                  onChange={(e) => handleChange(key, parseFloat(e.target.value))}
                />
              ) : (
                <input
                  id={id}
                  type="text"
                  className="form-input"
                  value={String(params[key] ?? m.value ?? '')}
                  onChange={(e) => handleChange(key, e.target.value)}
                />
              )}
              {range && <span className="form-hint">{range}</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
};
