import { useState } from 'react';
import { photos } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

/**
 * Admin-only compose form at the top of /photos. Three fields:
 *   - image URL (required)  — pasted public image link
 *   - caption (optional)
 *   - when (optional)       — free-form date string
 *
 * Submits → POST /api/photos → page reloads so the new frame slots into
 * the film strip in the right place.
 */
export default function PhotoAdd() {
  const isAdmin = useIsAdmin();
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState('');
  const [caption, setCaption] = useState('');
  const [takenAt, setTakenAt] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');

  if (isAdmin !== true) return null;

  function reset() {
    setUrl('');
    setCaption('');
    setTakenAt('');
    setStatus('');
  }

  async function submit() {
    const trimmed = url.trim();
    if (!trimmed) {
      setStatus('image url is required');
      return;
    }
    setBusy(true);
    setStatus('adding…');
    try {
      await photos.create({
        url: trimmed,
        caption: caption.trim(),
        taken_at: takenAt.trim(),
      });
      reset();
      setStatus('added — refreshing');
      setTimeout(() => location.reload(), 400);
    } catch {
      setStatus('add failed');
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <div className="photo-add">
        <button type="button" className="photo-add__open" onClick={() => setOpen(true)}>
          + add photo
        </button>
      </div>
    );
  }

  return (
    <div className="photo-add photo-add--open">
      <div className="photo-add__head">
        <span className="photo-add__label">✎ new photo</span>
        <button
          type="button"
          className="photo-add__close"
          onClick={() => { setOpen(false); reset(); }}
          aria-label="Cancel"
        >
          ×
        </button>
      </div>
      <div className="photo-add__row">
        <input
          className="photo-add__input"
          type="url"
          placeholder="https://… (direct image URL)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          autoFocus
          disabled={busy}
        />
      </div>
      <div className="photo-add__row photo-add__row--split">
        <input
          className="photo-add__input"
          type="text"
          placeholder="caption (optional)"
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          disabled={busy}
        />
        <input
          className="photo-add__input photo-add__input--narrow"
          type="text"
          placeholder="when · e.g. Mar 2026"
          value={takenAt}
          onChange={(e) => setTakenAt(e.target.value)}
          disabled={busy}
        />
      </div>
      {url.trim() && (
        <div className="photo-add__preview">
          <img src={url.trim()} alt="preview" onError={(e) => { (e.target as HTMLImageElement).style.opacity = '0.2'; }} />
        </div>
      )}
      <div className="photo-add__actions">
        <button type="button" className="photo-add__submit" onClick={submit} disabled={busy || !url.trim()}>
          add to camera roll
        </button>
        <button
          type="button"
          className="photo-add__cancel"
          onClick={() => { setOpen(false); reset(); }}
          disabled={busy}
        >
          cancel
        </button>
        {status && <span className="photo-add__status">{status}</span>}
      </div>
    </div>
  );
}
