import { useEffect } from 'react';
import { useIsFetching, useIsMutating } from '@tanstack/react-query';
import { useApiHealth } from '../../hooks/apiHooks';

export function ApiStatus() {
  const { data, isError, isLoading, refetch } = useApiHealth();
  // Long runs keep the single-worker API busy, so a missed health check then means "busy", not "down".
  const fetching = useIsFetching({ predicate: (q) => q.queryKey[0] !== 'health' });
  const busy = useIsMutating() + fetching > 0;

  // Re-check as soon as a run finishes instead of waiting for the next poll.
  useEffect(() => {
    if (!busy) refetch();
  }, [busy, refetch]);
  const ok = !!data && !isError;

  const state = isLoading ? 'connecting' : busy ? 'busy' : ok ? 'ok' : 'down';
  const label = {
    connecting: 'Connecting…',
    busy: 'Engine running',
    ok: 'Engine online',
    down: 'Engine offline',
  }[state];

  return (
    <span
      className="status-pill"
      role="status"
      title={state === 'down' ? 'Start the API with: PYTHONPATH=. python src/main.py' : 'FastAPI backend'}
    >
      <span className={`status-dot ${state === 'ok' ? 'ok' : state === 'down' ? 'down' : state === 'busy' ? 'busy' : ''}`} />
      {label}
    </span>
  );
}
