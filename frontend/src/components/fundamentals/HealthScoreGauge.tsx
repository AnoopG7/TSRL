interface Props {
  score: number | null | undefined;
  grade: string | null | undefined;
  breakdown?: Record<string, { score: number; weight: number; metrics?: Record<string, number> }>;
}

export function HealthScoreGauge({ score, grade, breakdown }: Props) {
  const numericScore = score ?? 0;

  const getColor = (s: number) => {
    if (s >= 80) return 'var(--color-positive)';
    if (s >= 65) return '#22d3ee';
    if (s >= 50) return 'var(--color-warning)';
    if (s >= 35) return '#fb923c';
    return 'var(--color-negative)';
  };

  const getLabel = (g: string | null | undefined) => {
    const labels: Record<string, string> = {
      A: 'Excellent',
      B: 'Good',
      C: 'Fair',
      D: 'Weak',
      F: 'Poor',
    };
    return g ? labels[g] || g : '—';
  };

  const color = getColor(numericScore);
  const pillars = ['profitability', 'valuation', 'cash_flow', 'solvency', 'growth'];
  const pillarLabels: Record<string, string> = {
    profitability: 'Profitability',
    valuation: 'Valuation',
    cash_flow: 'Cash Flow',
    solvency: 'Solvency',
    growth: 'Growth',
  };

  return (
    <section className="card">
      <div className="card-header">
        <h2 className="card-title">Health Score</h2>
      </div>
      <div className="card-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-lg)' }}>
        {/* Circular Gauge */}
        <div style={{ position: 'relative', width: 160, height: 160 }}>
          <svg width="160" height="160" viewBox="0 0 160 160">
            {/* Background ring */}
            <circle cx="80" cy="80" r="65" fill="none" stroke="var(--color-border-default)" strokeWidth="12" />
            {/* Score arc */}
            <circle
              cx="80" cy="80" r="65" fill="none"
              stroke={color} strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${(numericScore / 100) * 408.4} 408.4`}
              transform="rotate(-90 80 80)"
              style={{ transition: 'stroke-dasharray 0.8s ease-out' }}
            />
          </svg>
          <div style={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)', textAlign: 'center',
          }}>
            <div style={{ fontSize: '2rem', fontWeight: 700, color, lineHeight: 1 }}>
              {numericScore.toFixed(0)}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              / 100
            </div>
          </div>
        </div>

        {/* Grade badge */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 'var(--spacing-sm)',
          padding: '6px 16px', borderRadius: '9999px',
          backgroundColor: `${color}20`, color, fontWeight: 600, fontSize: '0.875rem',
        }}>
          Grade: {grade || '—'} — {getLabel(grade)}
        </div>

        {/* Pillar breakdown */}
        {breakdown && (
          <div style={{ width: '100%' }}>
            {pillars.map((key) => {
              if (!breakdown[key]) return null;
              const { score: pScore, weight } = breakdown[key];
              const pColor = getColor(pScore);
              return (
                <div key={key} style={{ marginBottom: 'var(--spacing-sm)' }}>
                  <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    fontSize: '0.75rem', marginBottom: '3px',
                  }}>
                    <span style={{ color: 'var(--color-text-secondary)' }}>
                      {pillarLabels[key]} ({weight}%)
                    </span>
                    <span style={{ color: pColor, fontWeight: 600 }}>
                      {pScore.toFixed(0)}/100
                    </span>
                  </div>
                  <div style={{
                    width: '100%', height: 6, borderRadius: 3,
                    backgroundColor: 'var(--color-border-default)',
                  }}>
                    <div style={{
                      width: `${pScore}%`, height: '100%', borderRadius: 3,
                      backgroundColor: pColor,
                      transition: 'width 0.6s ease-out',
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
