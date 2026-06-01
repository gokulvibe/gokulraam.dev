import { useState } from 'react';
import { photos } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

interface Props {
  photoId: number;
}

export default function PhotoDelete({ photoId }: Props) {
  const isAdmin = useIsAdmin();
  const [busy, setBusy] = useState(false);
  if (isAdmin !== true) return null;

  async function remove() {
    if (busy) return;
    if (!confirm('Delete this photo? This cannot be undone.')) return;
    setBusy(true);
    try {
      await photos.remove(photoId);
      location.reload();
    } catch {
      setBusy(false);
      alert('Delete failed.');
    }
  }

  return (
    <button
      type="button"
      className="photo-delete"
      title="Delete photo"
      onClick={remove}
      onMouseDown={(e) => e.stopPropagation()}
      disabled={busy}
    >
      delete ×
    </button>
  );
}
