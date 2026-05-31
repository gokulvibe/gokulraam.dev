import { useEffect, useState } from 'react';
import { auth } from '@/lib/api';

/**
 * Returns true if the visitor has a valid admin session cookie.
 * `null` means we don't know yet (still checking). `false` means guest.
 * Result is cached in-memory across components mounted on the same page.
 */
let cached: boolean | null = null;
let inflight: Promise<boolean> | null = null;

function check(): Promise<boolean> {
  if (cached !== null) return Promise.resolve(cached);
  if (inflight) return inflight;
  inflight = auth
    .me()
    .then(() => {
      cached = true;
      return true;
    })
    .catch(() => {
      cached = false;
      return false;
    })
    .finally(() => {
      inflight = null;
    });
  return inflight;
}

export function useIsAdmin(): boolean | null {
  const [state, setState] = useState<boolean | null>(cached);
  useEffect(() => {
    if (cached !== null) {
      setState(cached);
      return;
    }
    let alive = true;
    void check().then((v) => {
      if (alive) setState(v);
    });
    return () => {
      alive = false;
    };
  }, []);
  return state;
}

/** Force-refresh after login/logout. */
export function resetAdminCache() {
  cached = null;
}
