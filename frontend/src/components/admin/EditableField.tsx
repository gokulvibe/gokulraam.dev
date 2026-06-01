/**
 * Generic single-field editor following the SPEC §5 convention.
 *
 * Usage:
 *   <EditableField
 *     endpoint="/api/badminton/players/3"
 *     field="next_event"
 *     initial={p.next_event}
 *     className="font-mono"
 *   />
 *
 * Formats:
 *   - text     (default) — single-line input; renders as plain text
 *   - longtext           — multi-line textarea; renders as plain text
 *   - bullets            — multi-line textarea; renders newline-split as styled bullets
 *   - chips              — single-line input (comma-separated); renders as chip cloud
 */

import { useEffect, useRef, useState } from 'react';
import { patchEntity } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

type Format = 'text' | 'longtext' | 'bullets' | 'chips';

interface Props {
  endpoint: string;
  field: string;
  initial: string;
  className?: string;
  placeholder?: string;
  format?: Format;
  /** For chips: extra className applied to each chip. */
  chipClass?: string;
  /** If true, render nothing for non-admins (hides raw values like image URLs). */
  adminOnly?: boolean;
}

export default function EditableField({
  endpoint,
  field,
  initial,
  className = '',
  placeholder = '',
  format = 'text',
  chipClass = 'chip',
  adminOnly = false,
}: Props) {
  const isAdmin = useIsAdmin();
  if (adminOnly && isAdmin !== true) return null;
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(initial);
  const [draft, setDraft] = useState(initial);
  const [status, setStatus] = useState('');
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  const isMultiline = format === 'longtext' || format === 'bullets';

  async function save() {
    const next = format === 'chips' ? draft.trim() : draft;
    if (next === value) {
      setEditing(false);
      setStatus('');
      return;
    }
    setStatus('saving…');
    try {
      await patchEntity(endpoint, field, next);
      setValue(next);
      setEditing(false);
      setStatus('');
      // Sync peer EditableField instances bound to the same field (e.g.
      // when the homepage card is expanded into a clone with its own
      // hydrated React instance, the underlying original must learn the
      // new value too so it doesn't show stale content when the clone
      // collapses away).
      window.dispatchEvent(
        new CustomEvent('editable:saved', {
          detail: { endpoint, field, value: next },
        }),
      );
    } catch {
      setStatus('save failed');
    }
  }

  // Listen for sync events from peer instances.
  useEffect(() => {
    function onPeerSaved(e: Event) {
      const d = (e as CustomEvent<{ endpoint: string; field: string; value: string }>).detail;
      if (!d || d.endpoint !== endpoint || d.field !== field) return;
      setValue(d.value);
      setDraft(d.value);
    }
    window.addEventListener('editable:saved', onPeerSaved);
    return () => window.removeEventListener('editable:saved', onPeerSaved);
  }, [endpoint, field]);

  function cancel() {
    setDraft(value);
    setEditing(false);
    setStatus('');
  }

  function startEdit() {
    if (!isAdmin) return;
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 30);
  }

  // ─── View mode ───────────────────────────────────────────────
  if (!isAdmin || !editing) {
    const wrapClass = `${className} ${isAdmin ? 'editable editable--admin' : ''}`;

    if (format === 'bullets') {
      const lines = value.split('\n').map((l) => l.trim()).filter(Boolean);
      if (lines.length === 0 && !isAdmin) return null;
      return (
        <div className={wrapClass} onClick={startEdit} title={isAdmin ? `Click to edit ${field}` : undefined}>
          {lines.length === 0 ? (
            isAdmin && <span className="italic text-ghost">empty — click to edit bullets</span>
          ) : (
            <ul className="space-y-3">
              {lines.map((line, i) => (
                <li key={i} className="flex gap-3 leading-relaxed text-cream/80">
                  <span className="font-mono text-ember shrink-0">→</span>
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          )}
          {isAdmin && <span className="editable__pencil" aria-hidden>✏</span>}
        </div>
      );
    }

    if (format === 'chips') {
      const chips = value.split(',').map((c) => c.trim()).filter(Boolean);
      if (chips.length === 0 && !isAdmin) return null;
      return (
        <div className={wrapClass} onClick={startEdit} title={isAdmin ? `Click to edit ${field}` : undefined}>
          {chips.length === 0 ? (
            isAdmin && <span className="italic text-ghost text-[11px]">empty — click to add chips</span>
          ) : (
            <span className="inline-flex flex-wrap gap-2">
              {chips.map((c, i) => (
                <span key={i} className={chipClass}>{c}</span>
              ))}
            </span>
          )}
          {isAdmin && <span className="editable__pencil" aria-hidden>✏</span>}
        </div>
      );
    }

    // text / longtext
    return (
      <span
        className={wrapClass}
        onClick={startEdit}
        title={isAdmin ? `Click to edit ${field}` : undefined}
      >
        {value || (isAdmin ? <span className="italic text-ghost">empty — click to edit</span> : '')}
        {isAdmin && <span className="editable__pencil" aria-hidden>✏</span>}
      </span>
    );
  }

  // ─── Edit mode ───────────────────────────────────────────────
  const placeholderHint =
    placeholder ||
    (format === 'bullets'
      ? 'one bullet per line'
      : format === 'chips'
      ? 'comma, separated, chips'
      : '');

  return (
    <span style={{ display: 'inline-block', width: '100%' }}>
      {isMultiline ? (
        <textarea
          ref={inputRef as React.RefObject<HTMLTextAreaElement>}
          className={`editable-input ${className}`}
          value={draft}
          rows={format === 'bullets' ? 6 : 3}
          placeholder={placeholderHint}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') cancel();
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) save();
          }}
        />
      ) : (
        <input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          className={`editable-input ${className}`}
          value={draft}
          placeholder={placeholderHint}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') save();
            else if (e.key === 'Escape') cancel();
          }}
        />
      )}
      <div className="editable-row">
        <button type="button" className="save" onClick={save}>
          save {isMultiline ? '⌘↵' : '↵'}
        </button>
        <button type="button" className="cancel" onClick={cancel}>
          cancel
        </button>
        {status && <span className="editable-row__status">{status}</span>}
      </div>
    </span>
  );
}
