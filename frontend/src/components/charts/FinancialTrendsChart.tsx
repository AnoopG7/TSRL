import {
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend,
  ResponsiveContainer, Line, ComposedChart, Area, Bar, ReferenceLine
} from 'recharts';
import { ChartTooltip } from './ChartTooltip';

interface TrendPoint {
  year: number | string;
  value: number;
}

interface Props {
  revenue: TrendPoint[];
  netIncome: TrendPoint[];
  fcf: TrendPoint[];
  grossMargin: TrendPoint[];
  operatingMargin: TrendPoint[];
  companyName: string;
}

export function FinancialTrendsChart({
  revenue, netIncome, fcf, grossMargin, operatingMargin, companyName,
}: Props) {
  // Merge all data by year
  const chartData = revenue.map((r) => {
    const ni = netIncome.find((n) => n.year === r.year);
    const f = fcf.find((fc) => fc.year === r.year);
    const gm = grossMargin.find((g) => g.year === r.year);
    const om = operatingMargin.find((o) => o.year === r.year);
    
    return {
      year: String(r.year),
      Revenue: r.value,
      'Net Income': ni?.value ?? null,
      'FCF': f?.value ?? null,
      'Gross Margin': gm?.value ?? null,
      'Operating Margin': om?.value ?? null,
    };
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
      {/* Primary Financials: Revenue (Bar), Net Income (Line), FCF (Area) */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Financial Performance</h2>
          <p className="card-description">Revenue, Net Income & Free Cash Flow in billions ({companyName})</p>
        </div>
        <div className="card-content">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border-default)" />
                <XAxis dataKey="year" scale="point" padding={{ left: 40, right: 40 }} tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} axisLine={{ stroke: 'var(--color-bg-primary)' }} />
                <YAxis yAxisId="left" tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} axisLine={false} tickFormatter={(v) => `$${v}B`} />
                <YAxis yAxisId="right" orientation="right" tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} axisLine={false} tickFormatter={(v) => `${v}%`} />
                <RechartsTooltip 
                  content={<ChartTooltip 
                    formatter={(val, name) => {
                      const numVal = Number(val);
                      if (Number.isNaN(numVal)) return { label: name, value: String(val) };
                      if (name && name.includes('Margin')) return { label: name, value: numVal.toFixed(1), suffix: '%' };
                      return { label: name, value: numVal.toFixed(2), prefix: '$', suffix: 'B' };
                    }} 
                  />} 
                  cursor={{ fill: 'var(--color-bg-hover)' }} 
                />
                <Legend 
                  wrapperStyle={{ paddingTop: '20px' }} 
                  content={({ payload }) => (
                    <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
                      {payload?.map((entry, index) => {
                        const isRevenue = entry.dataKey === 'Revenue';
                        return (
                          <div key={`item-${index}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {isRevenue ? (
                              <div style={{ width: '12px', height: '12px', backgroundColor: 'var(--color-text-primary)', opacity: 0.15, borderRadius: '2px' }} />
                            ) : typeof entry.type === 'string' && entry.type.includes('line') ? (
                              <div style={{ display: 'flex', alignItems: 'center' }}>
                                <div style={{ width: '12px', height: '2px', backgroundColor: entry.color, position: 'absolute' }} />
                                <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: entry.color, zIndex: 1, marginLeft: '3px' }} />
                              </div>
                            ) : (
                              <div style={{ width: '12px', height: '12px', backgroundColor: entry.color, borderRadius: '2px' }} />
                            )}
                            <span style={{ textTransform: 'none', color: 'var(--color-text-primary)', fontSize: '0.875rem' }}>{entry.value}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                />
                <ReferenceLine y={0} yAxisId="left" stroke="var(--color-border-default)" />

                {/* Left Axis: Billions */}
                <Bar yAxisId="left" dataKey="Revenue" fill="var(--color-text-primary)" fillOpacity={0.15} radius={[4, 4, 0, 0]} />
                <Area yAxisId="left" type="monotone" dataKey="FCF" fill="var(--color-accent-500)" fillOpacity={0.2} stroke="var(--color-accent-500)" strokeWidth={2} />
                <Line yAxisId="left" type="monotone" dataKey="Net Income" stroke="var(--color-positive)" strokeWidth={3} dot={{ r: 4 }} />

                {/* Right Axis: Margins (%) */}
                <Line yAxisId="right" type="monotone" dataKey="Gross Margin" stroke="var(--color-warning)" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                <Line yAxisId="right" type="monotone" dataKey="Operating Margin" stroke="var(--color-negative)" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ textAlign: 'center', color: 'var(--color-text-tertiary)', padding: 'var(--spacing-xl)' }}>
              No financial statement data available
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
