/**
 * Single editable now-item. Follows the convention from SPEC §5.
 *
 * For guests: renders the value as plain text.
 * For admin: hover shows the edit affordance; click swaps to an inline
 * input with save/cancel. Saves via PATCH /api/now/<slug>.
 */

import { useRef, useState } from 'react';
import { now } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

interface Props {
  slug: string;
  initial: string;
  /** Class applied to the view-mode text. Lets the consumer keep its typography. */
  className?: string;
  /** Use a multi-line textarea instead of a single-line input. */
  multiline?: boolean;
  /** Placeholder for the input. */
  placeholder?: string;
}

export default function EditableNowItem({
  slug,
  initial,
  className = '',
  multiline = false,
  placeholder = '',
}: Props) {
  const isAdmin = useIsAdmin();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(initial);
  const [draft, setDraft] = useState(initial);
  const [status, setStatus] = useState('');
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  async function save() {
    const trimmed = draft.trim();
    if (!trimmed || trimmed === value) {
      // No change — just exit edit mode
      setEditing(false);
      setStatus('');
      return;
    }
    setStatus('saving…');
    try {
      const updated = await now.update(slug, trimmed);
      setValue(updated.value);
      setEditing(false);
      setStatus('');
    } catch {
      setStatus('save failed');
    }
  }

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

  if (!isAdmin || !editing) {
    return (
      <span
        className={`${className} ${isAdmin ? 'editable editable--admin' : ''}`}
        onClick={startEdit}
        title={isAdmin ? 'Click to edit' : undefined}
      >
        {value}
        {isAdmin && <span className="editable__pencil" aria-hidden>✏</span>}
      </span>
    );
  }

  return (
    <span style={{ display: 'inline-block', width: '100%' }}>
      {multiline ? (
        <textarea
          ref={inputRef as React.RefObject<HTMLTextAreaElement>}
          className={`editable-input ${className}`}
          value={draft}
          rows={3}
          placeholder={placeholder}
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
          placeholder={placeholder}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') save();
            else if (e.key === 'Escape') cancel();
          }}
        />
      )}
      <div className="editable-row">
        <button type="button" className="save" disabled={!draft.trim()} onClick={save}>
          save {multiline ? '⌘↵' : '↵'}
        </button>
        <button type="button" className="cancel" onClick={cancel}>
          cancel
        </button>
        {status && <span className="editable-row__status">{status}</span>}
      </div>
    </span>
  );
}
