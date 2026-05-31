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

export default function AdminBar() {
  const isAdmin = useIsAdmin();
  const [busy, setBusy] = useState(false);

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
    <div className="admin-bar">
      <span className="admin-bar__chip">
        <span className="admin-bar__dot" />
        admin · gokul
      </span>
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
  );
}
