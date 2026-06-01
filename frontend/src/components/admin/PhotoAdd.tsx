import { useRef, useState } from 'react';
import { photos, resolvePhotoUrl } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

/**
 * Admin-only photo composer. Two ways to add:
 *
 *   1. Paste a public image URL (Imgur, GitHub raw, picsum, etc.)
 *   2. Upload an image file (≤15 MB; jpeg/png/webp/gif/avif/heic). Stored
 *      on the backend under /uploads/photos/.
 *
 * Tab UI keeps the two modes distinct so it's obvious which one you're
 * using. Submit reloads the page to slot the new frame into the strip.
 */

type Mode = 'url' | 'upload';

const MAX_BYTES = 15 * 1024 * 1024;
const ALLOWED = /^image\/(jpeg|jpg|png|webp|gif|avif|heic)$/i;

export default function PhotoAdd() {
  const isAdmin = useIsAdmin();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>('url');

  // URL-mode fields
  const [url, setUrl] = useState('');

  // Upload-mode fields
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState<string>('');  // object URL for preview

  // Shared
  const [caption, setCaption] = useState('');
  const [takenAt, setTakenAt] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');

  if (isAdmin !== true) return null;

  function reset() {
    setUrl('');
    setFile(null);
    if (fileUrl) {
      URL.revokeObjectURL(fileUrl);
      setFileUrl('');
    }
    setCaption('');
    setTakenAt('');
    setStatus('');
  }

  function close() {
    setOpen(false);
    reset();
  }

  function pickFile(f: File | null) {
    if (fileUrl) URL.revokeObjectURL(fileUrl);
    if (!f) { setFile(null); setFileUrl(''); return; }
    if (!ALLOWED.test(f.type)) {
      setStatus(`unsupported type: ${f.type || 'unknown'}`);
      setFile(null); setFileUrl('');
      return;
    }
    if (f.size > MAX_BYTES) {
      setStatus(`file too large — max ${Math.round(MAX_BYTES / 1024 / 1024)} MB`);
      setFile(null); setFileUrl('');
      return;
    }
    setFile(f);
    setFileUrl(URL.createObjectURL(f));
    setStatus('');
  }

  async function submit() {
    setBusy(true);
    setStatus(mode === 'upload' ? 'uploading…' : 'adding…');
    try {
      if (mode === 'upload') {
        if (!file) { setStatus('pick an image first'); setBusy(false); return; }
        await photos.upload(file, caption.trim(), takenAt.trim());
      } else {
        const trimmed = url.trim();
        if (!trimmed) { setStatus('paste an image url first'); setBusy(false); return; }
        await photos.create({
          url: trimmed,
          caption: caption.trim(),
          taken_at: takenAt.trim(),
        });
      }
      reset();
      setStatus('added — refreshing');
      setTimeout(() => location.reload(), 400);
    } catch {
      setStatus(mode === 'upload' ? 'upload failed' : 'add failed');
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

  const previewSrc = mode === 'upload' ? fileUrl : (url.trim() ? resolvePhotoUrl(url.trim()) : '');

  return (
    <div className="photo-add photo-add--open">
      <div className="photo-add__head">
        <span className="photo-add__label">✎ new photo</span>
        <button type="button" className="photo-add__close" onClick={close} aria-label="Cancel">×</button>
      </div>

      {/* Mode tabs */}
      <div className="photo-add__tabs">
        <button
          type="button"
          className={`photo-add__tab ${mode === 'url' ? 'is-active' : ''}`}
          onClick={() => { setMode('url'); setStatus(''); }}
          disabled={busy}
        >
          paste url
        </button>
        <button
          type="button"
          className={`photo-add__tab ${mode === 'upload' ? 'is-active' : ''}`}
          onClick={() => { setMode('upload'); setStatus(''); }}
          disabled={busy}
        >
          upload file
        </button>
      </div>

      {mode === 'url' ? (
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
      ) : (
        <div className="photo-add__row photo-add__row--file">
          <input
            ref={fileInputRef}
            id="photo-file-input"
            type="file"
            accept="image/jpeg,image/jpg,image/png,image/webp,image/gif,image/avif,image/heic"
            className="photo-add__file-hidden"
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
            disabled={busy}
          />
          <label htmlFor="photo-file-input" className="photo-add__file-label">
            {file ? `📷 ${file.name}` : 'choose an image · ≤ 15 MB'}
          </label>
          {file && (
            <button
              type="button"
              className="photo-add__file-clear"
              onClick={() => pickFile(null)}
              disabled={busy}
            >
              clear
            </button>
          )}
        </div>
      )}

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

      {previewSrc && (
        <div className="photo-add__preview">
          <img
            src={previewSrc}
            alt="preview"
            onError={(e) => { (e.target as HTMLImageElement).style.opacity = '0.2'; }}
          />
        </div>
      )}

      <div className="photo-add__actions">
        <button
          type="button"
          className="photo-add__submit"
          onClick={submit}
          disabled={busy || (mode === 'upload' ? !file : !url.trim())}
        >
          {mode === 'upload' ? 'upload & add' : 'add to camera roll'}
        </button>
        <button type="button" className="photo-add__cancel" onClick={close} disabled={busy}>
          cancel
        </button>
        {status && <span className="photo-add__status">{status}</span>}
      </div>
    </div>
  );
}
