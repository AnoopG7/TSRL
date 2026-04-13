import type { FundamentalReport } from '../../lib/schemas/fundamental.schema';
import { Target, AlertTriangle, ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';

interface Props {
  report: FundamentalReport;
}

export function QualityScores({ report }: Props) {
  if (report.piotroski_score == null && report.altman_z_score == null) {
    return null;
  }

  // Derived Altman data
  let altmanColor = 'var(--color-text-secondary)';
  let altmanIcon = <AlertTriangle size={24} />;
  let altmanText = 'Unknown';
  let altmanProgress = 50;

  if (report.altman_z_zone === 'safe') {
    altmanColor = 'var(--color-positive)';
    altmanIcon = <ShieldCheck size={24} style={{ color: altmanColor }} />;
    altmanText = 'Safe Zone';
    altmanProgress = 85;
  } else if (report.altman_z_zone === 'grey') {
    altmanColor = 'var(--color-warning)';
    altmanIcon = <AlertTriangle size={24} style={{ color: altmanColor }} />;
    altmanText = 'Grey Zone';
    altmanProgress = 50;
  } else if (report.altman_z_zone === 'distress') {
    altmanColor = 'var(--color-negative)';
    altmanIcon = <Target size={24} style={{ color: altmanColor }} />;
    altmanText = 'Distress Zone';
    altmanProgress = 15;
  }

  // Piotroski data
  const piotroskiLabels: Record<string, string> = {
    F1_roa_positive: 'Positive Return on Assets (ROA)',
    F2_ocf_positive: 'Positive Operating Cash Flow',
    F3_roa_improving: 'ROA higher than prior year',
    F4_accruals_low: 'Cash Flow > Net Income',
    F5_leverage_decreased: 'Long-term debt decreased',
    F6_current_ratio_up: 'Current ratio improved',
    F7_no_dilution: 'No new shares issued',
    F8_gross_margin_up: 'Gross margin improved',
    F9_asset_turnover_up: 'Asset turnover improved',
  };

  const pScore = report.piotroski_score ?? 0;
  const pColor = pScore >= 7 ? 'var(--color-positive)' : pScore >= 4 ? 'var(--color-warning)' : 'var(--color-negative)';

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-lg)' }}>
      {/* Altman Z-Score Card */}
      {report.altman_z_score != null && (
        <section className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <h2 className="card-title">Altman Z-Score</h2>
            <p className="card-description">Bankruptcy prediction model</p>
          </div>
          <div className="card-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '200px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-lg)' }}>
              {altmanIcon}
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: altmanColor }}>
                {report.altman_z_score.toFixed(2)}
              </div>
            </div>
            
            <div style={{ width: '100%', maxWidth: '280px', marginBottom: 'var(--spacing-sm)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                <span>Distress &lt; 1.8</span>
                <span>Safe &gt; 3.0</span>
              </div>
              <div style={{ height: '8px', background: 'linear-gradient(to right, var(--color-negative), var(--color-warning), var(--color-positive))', borderRadius: '4px', position: 'relative' }}>
                <div style={{ 
                  position: 'absolute', 
                  top: '-4px', 
                  bottom: '-4px', 
                  left: `${altmanProgress}%`, 
                  width: '4px', 
                  background: 'var(--color-text-primary)', 
                  borderRadius: '2px',
                  boxShadow: '0 0 4px rgba(0,0,0,0.5)',
                  transform: 'translateX(-50%)'
                }} />
              </div>
            </div>
            
            <div style={{ fontSize: '1.25rem', fontWeight: 600, color: altmanColor, marginTop: 'var(--spacing-md)' }}>
              {altmanText}
            </div>
          </div>
        </section>
      )}

      {/* Piotroski F-Score Card */}
      {report.piotroski_score != null && (
        <section className="card" style={{ marginBottom: 0, gridColumn: report.altman_z_score == null ? '1 / -1' : 'auto' }}>
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 className="card-title">Piotroski F-Score</h2>
              <p className="card-description">Value investing fundamental strength</p>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: pColor }}>
              {pScore}/9
            </div>
          </div>
          <div className="card-content">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 'var(--spacing-sm)' }}>
              {report.piotroski_breakdown && Object.entries(report.piotroski_breakdown).map(([key, val]) => (
                <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', padding: 'var(--spacing-xs) 0' }}>
                  {val === 1 
                    ? <CheckCircle2 size={16} style={{ color: 'var(--color-positive)', flexShrink: 0 }} /> 
                    : <XCircle size={16} style={{ color: 'var(--color-negative)', opacity: 0.5, flexShrink: 0 }} />
                  }
                  <span style={{ fontSize: '0.8rem', color: val === 1 ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                    {piotroskiLabels[key] || key}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
