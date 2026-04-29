import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import type { FundamentalComparison } from '../../lib/schemas/fundamental.schema';
import { useDataSourceStore } from '../../store/useDataSourceStore';

interface Props {
  data: FundamentalComparison;
  onRemoveTicker: (symbol: string) => void;
  market?: 'us' | 'india' | 'crypto';
}

type MetricType = 'currency' | 'compact_currency' | 'percent' | 'ratio' | 'score';

export function ComparisonTable({ data, onRemoveTicker, market = 'us' }: Props) {
  const { getCurrency } = useDataSourceStore();
  const currency = market === 'us' ? getCurrency() : { symbol: market === 'india' ? '₹' : '$', code: market === 'india' ? 'INR' : 'USD', position: 'prefix' as const };
  const formatValue = (val: unknown, type: MetricType): string => {
    if (val == null) return '—';
    const numVal = Number(val);
    if (Number.isNaN(numVal)) return String(val);
    if (type === 'currency') return `${currency.symbol}${numVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (type === 'compact_currency') {
      if (numVal >= 1e12) return `${currency.symbol}${(numVal / 1e12).toFixed(2)}T`;
      if (numVal >= 1e9) return `${currency.symbol}${(numVal / 1e9).toFixed(2)}B`;
      if (numVal >= 1e6) return `${currency.symbol}${(numVal / 1e6).toFixed(2)}M`;
      return `${currency.symbol}${numVal.toLocaleString()}`;
    }
    if (type === 'percent') return `${(numVal * 100).toFixed(2)}%`;
    if (type === 'ratio') return numVal.toFixed(2);
    if (type === 'score') return `${numVal.toFixed(0)}/100`;
    return String(val);
  };

  if (!data || !data.symbols || data.symbols.length === 0) return null;

  const symbols = data.symbols;
  
  const metrics = [
    { key: 'current_price', label: 'Price', type: 'currency' as MetricType },
    { key: 'market_cap', label: 'Market Cap', type: 'compact_currency' as MetricType },
    { key: 'pe_ratio', label: 'P/E Ratio', type: 'ratio' as MetricType, invertColor: true },
    { key: 'pb_ratio', label: 'P/B Ratio', type: 'ratio' as MetricType, invertColor: true },
    { key: 'roe', label: 'ROE', type: 'percent' as MetricType },
    { key: 'net_margin', label: 'Net Margin', type: 'percent' as MetricType },
    { key: 'debt_to_equity', label: 'Debt/Equity', type: 'ratio' as MetricType, invertColor: true },
    { key: 'revenue_cagr_3yr', label: 'Rev Growth (3y)', type: 'percent' as MetricType },
    { key: 'health_score', label: 'Health Score', type: 'score' as MetricType },
  ];

  const getCellColor = (val: unknown, allVals: unknown[], invertColor?: boolean): string => {
    if (val == null) return 'inherit';
    const numVal = Number(val);
    if (Number.isNaN(numVal)) return 'inherit';
    const validVals = allVals.map(v => Number(v)).filter(v => !Number.isNaN(v));
    if (validVals.length < 2) return 'inherit';
    
    const max = Math.max(...validVals);
    const min = Math.min(...validVals);
    
    if (numVal === max) return invertColor ? 'var(--color-negative)' : 'var(--color-positive)';
    if (numVal === min) return invertColor ? 'var(--color-positive)' : 'var(--color-negative)';
    return 'inherit';
  };

  return (
    <section className="card animate-fadeIn">
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 className="card-title">Multi-Ticker Comparison</h2>
          <p className="card-description">Compare fundamental metrics side-by-side</p>
        </div>
      </div>
      <div className="card-content" style={{ padding: 0 }}>
        <div className="table-container">
          <table className="table" style={{ borderCollapse: 'collapse', width: '100%' }}>
            <thead>
               <tr style={{ borderBottom: '1px solid var(--color-border-default)' }}>
                 <th style={{ width: '200px', backgroundColor: 'var(--color-bg-card)', position: 'sticky', left: 0, zIndex: 10 }}>Metric</th>
                 {symbols.map(sym => (
                   <th key={sym} style={{ textAlign: 'center', position: 'relative' }}>
                     <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{sym}</div>
                     <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', fontWeight: 'normal' }}>
                       {data.comparison[sym]?.company_name?.slice(0, 20) || 'Unknown'}
                     </div>
                     <button 
                       onClick={() => onRemoveTicker(sym)}
                       style={{ 
                         position: 'absolute', top: '8px', right: '8px', 
                         background: 'none', border: 'none', color: 'var(--color-text-muted)',
                         cursor: 'pointer', fontSize: '1rem'
                       }}
                       title={`Remove ${sym}`}
                     >
                       ×
                     </button>
                   </th>
                 ))}
               </tr>
            </thead>
            <tbody>
              {metrics.map((metric, idx) => {
                const rowVals = symbols.map(sym => data.comparison[sym]?.[metric.key as keyof typeof data.comparison[string]]);
                
                return (
                  <tr key={metric.key} style={{ backgroundColor: idx % 2 === 0 ? 'transparent' : 'var(--color-bg-hover)' }}>
                    <td style={{ 
                      fontWeight: 500, 
                      backgroundColor: idx % 2 === 0 ? 'var(--color-bg-card)' : 'var(--color-bg-hover)',
                      position: 'sticky', left: 0, zIndex: 1 
                    }}>
                      {metric.label}
                    </td>
                    {symbols.map((sym, i) => {
                      const val = rowVals[i];
                      const color = getCellColor(val, rowVals, metric.invertColor);
                      
                      let Icon = null;
                      if (metric.type === 'percent' && val != null && typeof val === 'number') {
                        Icon = val > 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />;
                      }
                      
                      if (data.comparison[sym]?.error) {
                         return <td key={sym} style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>Error</td>;
                      }

                      return (
                        <td key={sym} style={{ textAlign: 'center', color, fontWeight: color !== 'inherit' ? 600 : 400 }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                            {metric.type === 'percent' && color !== 'inherit' && Icon}
                            {formatValue(val, metric.type)}
                          </div>
                          {metric.key === 'health_score' && data.comparison[sym]?.health_grade && (
                            <span className={`badge ${data.comparison[sym]?.health_grade === 'A' ? 'badge-success' : ''}`} style={{ marginTop: '4px', fontSize: '0.7rem' }}>
                              Grade {data.comparison[sym]?.health_grade}
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
