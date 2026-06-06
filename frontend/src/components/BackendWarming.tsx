/**
 * "Warming up" state for Render free-tier cold starts.
 *
 * Render's free instance sleeps after 15 minutes of idle. The first
 * request after sleep takes ~30s while the container wakes. Before
 * this component existed, each page silently rendered a "// backend
 * offline" card — accurate to the symptom but misleading about the
 * cause and offering no recovery.
 *
 * Now: SSR pages that fail to reach the backend mount this island
 * instead. It pings `/api/health` every 4s; the moment it succeeds it
 * reloads the page so the rest of the SSR refetch lands on a warm
 * backend. After ~45s of trying with no luck it falls back to a
 * harder "really seems offline" state and stops polling.
 */

import { useEffect, useState } from 'react';

const API_BASE =
  (import.meta.env.PUBLIC_API_BASE as string | undefined) ?? '';
const POLL_MS = 4000;
const GIVE_UP_AFTER_MS = 45_000;

type State = 'warming' | 'offline';

export default function BackendWarming() {
  const [state, setState] = useState<State>('warming');
  const [tick, setTick] = useState(0);
  const [secondsTried, setSecondsTried] = useState(0);

  useEffect(() => {
    if (state === 'offline') return;
    let timer: number | null = null;
    const startedAt = Date.now();

    async function ping() {
      try {
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 3000);
        const res = await fetch(`${API_BASE}/api/health`, {
          signal: controller.signal,
          credentials: 'include',
        });
        window.clearTimeout(timeout);
        if (res.ok) {
          window.location.reload();
          return;
        }
      } catch {
        /* timeout or network — try again */
      }
      const elapsed = Date.now() - startedAt;
      setSecondsTried(Math.floor(elapsed / 1000));
      if (elapsed >= GIVE_UP_AFTER_MS) {
        setState('offline');
        return;
      }
      setTick((t) => t + 1);
      timer = window.setTimeout(ping, POLL_MS);
    }

    timer = window.setTimeout(ping, 600);  // small initial delay
    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [state]);

  if (state === 'offline') {
    return (
      <div className="warming warming--cold">
        <p className="warming__label">// backend unreachable</p>
        <p className="warming__body">
          The API at <code>{API_BASE}</code> isn't responding. If you're me, check Render's status; if you're a visitor, refresh in a minute or two.
        </p>
        <button
          type="button"
          className="warming__retry"
          onClick={() => window.location.reload()}
        >
          retry
        </button>
      </div>
    );
  }

  return (
    <div className="warming">
      <p className="warming__label">// warming up</p>
      <p className="warming__body">
        The free-tier backend went idle. It's waking up — usually takes
        about 30 seconds the first time. This page will refresh
        automatically as soon as the API responds.
      </p>
      <div className="warming__meter">
        <div className="warming__dot" />
        <span className="warming__time">
          {secondsTried}s · tried {tick + 1} time{tick === 0 ? '' : 's'}
        </span>
      </div>
    </div>
  );
}
