import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface Props {
  report: Record<string, unknown>;
}

interface RatioRow {
  label: string;
  value: string;
  status: 'good' | 'warning' | 'poor' | 'neutral';
  interpretation: string;
}

function formatPct(v: number | null | undefined): string {
  if (v == null) return '—';
  return `${(v * 100).toFixed(2)}%`;
}

function formatRatio(v: number | null | undefined): string {
  if (v == null) return '—';
  return v.toFixed(2);
}

function getStatus(
  value: number | null | undefined,
  goodThreshold: number,
  warnThreshold: number,
  lowerIsBetter = false,
): 'good' | 'warning' | 'poor' | 'neutral' {
  if (value == null) return 'neutral';
  if (lowerIsBetter) {
    if (value <= goodThreshold) return 'good';
    if (value <= warnThreshold) return 'warning';
    return 'poor';
  }
  if (value >= goodThreshold) return 'good';
  if (value >= warnThreshold) return 'warning';
  return 'poor';
}

const StatusIcon = ({ status }: { status: string }) => {
  if (status === 'good') return <CheckCircle size={14} style={{ color: 'var(--color-positive)' }} />;
  if (status === 'warning') return <AlertTriangle size={14} style={{ color: 'var(--color-warning)' }} />;
  if (status === 'poor') return <XCircle size={14} style={{ color: 'var(--color-negative)' }} />;
  return <span style={{ width: 14, height: 14, display: 'inline-block' }} />;
};

export function RatioTable({ report }: Props) {
  const r = report as Record<string, number | null | undefined | string>;

  const sections: { title: string; rows: RatioRow[] }[] = [
    {
      title: 'Valuation Ratios',
      rows: [
        { label: 'P/E Ratio (TTM)', value: formatRatio(r.pe_ratio as number), status: getStatus(r.pe_ratio as number, 15, 25, true), interpretation: '< 15 cheap, > 25 expensive' },
        { label: 'Forward P/E', value: formatRatio(r.forward_pe as number), status: getStatus(r.forward_pe as number, 15, 25, true), interpretation: 'Based on analyst estimates' },
        { label: 'PEG Ratio', value: formatRatio(r.peg_ratio as number), status: getStatus(r.peg_ratio as number, 1.0, 1.5, true), interpretation: '< 1 undervalued for growth' },
        { label: 'P/B Ratio', value: formatRatio(r.pb_ratio as number), status: getStatus(r.pb_ratio as number, 2, 4, true), interpretation: '< 1 = below book value' },
        { label: 'P/S Ratio', value: formatRatio(r.ps_ratio as number), status: getStatus(r.ps_ratio as number, 2, 5, true), interpretation: '< 1 = very cheap' },
        { label: 'EV/EBITDA', value: formatRatio(r.ev_ebitda as number), status: getStatus(r.ev_ebitda as number, 10, 20, true), interpretation: '< 10 undervalued' },
      ],
    },
    {
      title: 'Profitability',
      rows: [
        { label: 'ROE', value: formatPct(r.roe as number), status: getStatus(r.roe as number, 0.15, 0.1), interpretation: '> 15% excellent (Buffett rule)' },
        { label: 'ROA', value: formatPct(r.roa as number), status: getStatus(r.roa as number, 0.08, 0.05), interpretation: '> 5% good' },
        { label: 'Gross Margin', value: formatPct(r.gross_margin as number), status: getStatus(r.gross_margin as number, 0.5, 0.35), interpretation: '> 40% strong pricing power' },
        { label: 'Operating Margin', value: formatPct(r.operating_margin as number), status: getStatus(r.operating_margin as number, 0.15, 0.1), interpretation: '> 15% healthy' },
        { label: 'Net Profit Margin', value: formatPct(r.net_margin as number), status: getStatus(r.net_margin as number, 0.1, 0.05), interpretation: '> 10% good' },
        { label: 'EPS (TTM)', value: formatRatio(r.eps_trailing as number), status: getStatus(r.eps_trailing as number, 3, 1), interpretation: 'Higher = more profitable' },
      ],
    },
    {
      title: 'Liquidity',
      rows: [
        { label: 'Current Ratio', value: formatRatio(r.current_ratio as number), status: getStatus(r.current_ratio as number, 1.5, 1.0), interpretation: '1.5–3.0 healthy' },
        { label: 'Quick Ratio', value: formatRatio(r.quick_ratio as number), status: getStatus(r.quick_ratio as number, 1.0, 0.7), interpretation: '> 1.0 safe' },
      ],
    },
    {
      title: 'Solvency',
      rows: [
        { label: 'Debt/Equity', value: formatRatio(r.debt_to_equity as number), status: getStatus(r.debt_to_equity as number, 0.7, 1.5, true), interpretation: '< 1.0 low leverage' },
        { label: 'Interest Coverage', value: formatRatio(r.interest_coverage as number), status: getStatus(r.interest_coverage as number, 3, 1.5), interpretation: '> 3 safe' },
      ],
    },
    {
      title: 'Cash Flow',
      rows: [
        { label: 'Free Cash Flow', value: r.free_cash_flow != null ? `$${((r.free_cash_flow as number) / 1e9).toFixed(2)}B` : '—', status: getStatus(r.free_cash_flow as number, 0, -1e8), interpretation: 'Positive = generating real cash' },
        { label: 'FCF Margin', value: formatPct(r.fcf_margin as number), status: getStatus(r.fcf_margin as number, 0.1, 0.05), interpretation: '> 10% excellent quality' },
        { label: 'FCF Yield', value: formatPct(r.fcf_yield as number), status: getStatus(r.fcf_yield as number, 0.05, 0.02), interpretation: 'High = potentially undervalued' },
        { label: 'Cash Conversion', value: formatRatio(r.cash_conversion as number), status: getStatus(r.cash_conversion as number, 1.0, 0.7), interpretation: '> 1.0 = earnings backed by cash' },
      ],
    },
    {
      title: 'Growth (CAGR)',
      rows: [
        { label: 'Revenue CAGR (3yr)', value: formatPct(r.revenue_cagr_3yr as number), status: getStatus(r.revenue_cagr_3yr as number, 0.1, 0.05), interpretation: '> 10% growth company' },
        { label: 'Earnings CAGR (3yr)', value: formatPct(r.earnings_cagr_3yr as number), status: getStatus(r.earnings_cagr_3yr as number, 0.1, 0.05), interpretation: 'Consistent growth = quality' },
        { label: 'FCF CAGR (3yr)', value: formatPct(r.fcf_cagr_3yr as number), status: getStatus(r.fcf_cagr_3yr as number, 0.1, 0.05), interpretation: 'Improving capital efficiency' },
      ],
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
      {sections.map((section) => (
        <section className="card" key={section.title}>
          <div className="card-header">
            <h2 className="card-title">{section.title}</h2>
          </div>
          <div className="card-content" style={{ padding: 0 }}>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th style={{ width: '25%' }}>Metric</th>
                    <th style={{ width: '15%' }}>Value</th>
                    <th style={{ width: '15%', textAlign: 'center' }}>Status</th>
                    <th style={{ width: '45%' }}>Interpretation</th>
                  </tr>
                </thead>
                <tbody>
                  {section.rows.map((row) => (
                    <tr key={row.label}>
                      <td style={{ fontWeight: 500, color: 'var(--color-text-primary)' }}>{row.label}</td>
                      <td style={{ fontFamily: 'var(--font-mono, monospace)', fontWeight: 600 }}>{row.value}</td>
                      <td style={{ textAlign: 'center' }}><StatusIcon status={row.status} /></td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{row.interpretation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      ))}
    </div>
  );
}
