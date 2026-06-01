import { useState } from 'react';
import { logbook } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

export default function LogbookDelete({ entryId }: { entryId: number }) {
  const isAdmin = useIsAdmin();
  const [busy, setBusy] = useState(false);
  if (isAdmin !== true) return null;

  async function remove() {
    if (busy) return;
    if (!confirm('Hide this logbook entry?')) return;
    setBusy(true);
    try {
      await logbook.remove(entryId);
      location.reload();
    } catch {
      setBusy(false);
      alert('Delete failed.');
    }
  }

  return (
    <button
      type="button"
      className="logbook-delete"
      title="Hide this entry"
      onClick={remove}
      disabled={busy}
    >
      ×
    </button>
  );
}
