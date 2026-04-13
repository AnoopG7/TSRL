export interface TooltipRow {
  label?: string;
  value: string;
  prefix?: string;
  suffix?: string;
  isPositive?: boolean;
  isNegative?: boolean;
}

interface PayloadItem {
  name?: string;
  value?: number | string;
  payload?: Record<string, unknown>;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: PayloadItem[];
  label?: string;
  rows?: TooltipRow[];
  formatter?: (value: string | number, name: string, item?: PayloadItem) => TooltipRow | string;
}

export function ChartTooltip({ active, payload, label, rows, formatter }: ChartTooltipProps) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  let displayRows: TooltipRow[] = [];

  if (rows && rows.length > 0) {
    displayRows = rows;
  } else {
    displayRows = payload.map((p) => {
      const value = p.value ?? '';
      if (formatter) {
        const formatted = formatter(String(value), p.name || '', p.payload);
        if (typeof formatted === 'string') {
          return { label: p.name, value: formatted };
        }
        return formatted;
      }
      return {
        label: p.name,
        value: typeof p.value === 'number' ? p.value.toLocaleString() : String(value),
      };
    });
  }

  return (
    <div className="chart-tooltip">
      {label && <div className="chart-tooltip-header">{label}</div>}
      
      {displayRows.map((row, idx) => {
        let valClass = '';
        if (row.isPositive) valClass = 'positive';
        if (row.isNegative) valClass = 'negative';

        return (
          <div className="chart-tooltip-row" key={idx}>
            <span className="chart-tooltip-label">{row.label}</span>
            <span className={`chart-tooltip-value ${valClass}`}>
              {row.prefix}{row.value}{row.suffix}
            </span>
          </div>
        );
      })}
    </div>
  );
}