/**
 * Minimal global admin bar. Only renders when authenticated.
 *
 * Page-specific actions ("+ new", "publish", "delete") live IN the relevant
 * page itself — this bar stays page-agnostic so it doesn't grow forever as
 * more sections become editable.
 */

import { useState } from 'react';
import { auth } from '@/lib/api';
import { useIsAdmin, resetAdminCache } from './useIsAdmin';

/** Registered easter eggs. Mirror of the table in ROADMAP.md / CLAUDE.md.
 *  Keep in sync when adding new ones — this is the in-app reference. */
const EGGS: Array<{ trigger: string; effect: string; reveals: string }> = [
  {
    trigger: 'Type `snap` anywhere (desktop)',
    effect: 'camera-flash overlay + toast',
    reveals: '/photos',
  },
  {
    trigger: 'Type `knock` anywhere (desktop)',
    effect: 'page rumble + 3 audio thumps + haptic + toast',
    reveals: '/museum/enter',
  },
  {
    trigger: 'Tap 3 times anywhere on the page',
    effect: 'same as snap, after a ~700ms pause',
    reveals: '/photos',
  },
  {
    trigger: 'Tap 5 times anywhere on the page',
    effect: 'same as knock, after a ~700ms pause',
    reveals: '/museum/enter',
  },
  {
    trigger: 'On /404 — click the digits 4 → 0 → 4 in order',
    effect: 'digits glow gold, destination cards pulse',
    reveals: 'nothing — playful confirmation',
  },
];

export default function AdminBar() {
  const isAdmin = useIsAdmin();
  const [busy, setBusy] = useState(false);
  const [showEggs, setShowEggs] = useState(false);

  if (isAdmin !== true) return null;

  async function onSignOut() {
    setBusy(true);
    try {
      await auth.logout();
    } finally {
      resetAdminCache();
      window.location.reload();
    }
  }

  return (
    <>
      <div className="admin-bar">
        <span className="admin-bar__chip">
          <span className="admin-bar__dot" />
          admin · gokul
        </span>
        <span className="admin-bar__sep" />
        <button
          type="button"
          className="admin-bar__btn admin-bar__btn--muted"
          onClick={() => setShowEggs(true)}
          title="List registered easter eggs"
        >
          🥚 eggs
        </button>
        <span className="admin-bar__sep" />
        <button
          type="button"
          className="admin-bar__btn admin-bar__btn--muted"
          onClick={onSignOut}
          disabled={busy}
          title="Sign out"
        >
          ⎋ sign out
        </button>
      </div>

      {showEggs && (
        <div
          className="egg-ref-backdrop"
          role="dialog"
          aria-modal="true"
          aria-label="Registered easter eggs"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowEggs(false);
          }}
        >
          <div className="egg-ref">
            <div className="egg-ref__head">
              <span className="egg-ref__title">// registered easter eggs</span>
              <button
                type="button"
                className="egg-ref__close"
                onClick={() => setShowEggs(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <p className="egg-ref__hint">
              For your reference. Visitors discover by trying things; you (as admin)
              just need to remember what's wired.
            </p>
            <ol className="egg-ref__list">
              {EGGS.map((e, i) => (
                <li key={i} className="egg-ref__item">
                  <div className="egg-ref__row">
                    <span className="egg-ref__num">{String(i + 1).padStart(2, '0')}</span>
                    <span className="egg-ref__trigger">{e.trigger}</span>
                  </div>
                  <div className="egg-ref__detail">
                    <span className="egg-ref__effect">{e.effect}</span>
                    <span className="egg-ref__arrow">→</span>
                    <span className="egg-ref__reveals">{e.reveals}</span>
                  </div>
                </li>
              ))}
            </ol>
            <p className="egg-ref__footer">
              Source of truth: <code>frontend/src/components/EasterEggs.tsx</code>.
              Mirror table in <code>ROADMAP.md</code>.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
