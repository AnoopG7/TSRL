import React, { useEffect, useState } from 'react';
import { Check } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  body: React.ReactNode;
  action?: React.ReactNode;
}

/** Placeholder shown in the results column before anything has run. */
export const EmptyState: React.FC<EmptyStateProps> = ({ title, body, action }) => (
  <div className="empty-state">
    <svg className="ghost-chart" viewBox="0 0 560 90" preserveAspectRatio="none" aria-hidden>
      <path
        d="M0 70 L40 62 L80 66 L120 48 L160 54 L200 40 L240 46 L280 30 L320 38 L360 22 L400 34 L440 18 L480 26 L520 10 L560 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeDasharray="5 6"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
    <h3>{title}</h3>
    <p>{body}</p>
    {action}
  </div>
);

interface RunProgressProps {
  title: string;
  steps: string[];
  /** Rough seconds per step, used only to pace the visual. */
  pace?: number;
  note?: React.ReactNode;
}

/**
 * Shown while a long request is in flight. The backend doesn't stream progress,
 * so steps advance on a timer and the last one holds until the response lands.
 */
export const RunProgress: React.FC<RunProgressProps> = ({ title, steps, pace = 2.5, note }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = window.setInterval(() => setElapsed((Date.now() - started) / 1000), 200);
    return () => window.clearInterval(id);
  }, []);

  const active = Math.min(steps.length - 1, Math.floor(elapsed / pace));

  return (
    <div className="empty-state" aria-live="polite">
      <div className="row" style={{ justifyContent: 'space-between', width: '100%' }}>
        <h3>{title}</h3>
        <span className="run-timer">{elapsed.toFixed(1)}s</span>
      </div>
      <div className="run-steps">
        {steps.map((s, i) => (
          <div key={s} className={`run-step ${i < active ? 'done' : i === active ? 'active' : ''}`}>
            <span className="dot">{i < active && <Check size={11} strokeWidth={3} />}</span>
            {s}
          </div>
        ))}
      </div>
      {note && <p className="form-hint" style={{ marginTop: 'var(--spacing-sm)' }}>{note}</p>}
    </div>
  );
};
