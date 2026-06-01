import { useEffect, useRef, useState } from 'react';
import { til } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

interface Props {
  postId: number;
  initial: string;
}

export default function EditableTitle({ postId, initial }: Props) {
  const isAdmin = useIsAdmin();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(initial);
  const [draft, setDraft] = useState(initial);
  const [status, setStatus] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-edit when the URL has ?new=1 (just created via AdminBar)
  useEffect(() => {
    if (!isAdmin) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('new') === '1') {
      setEditing(true);
      setTimeout(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      }, 50);
      // Clean the URL so a refresh doesn't re-trigger
      params.delete('new');
      const next = params.toString();
      window.history.replaceState(
        {},
        '',
        window.location.pathname + (next ? `?${next}` : ''),
      );
    }
  }, [isAdmin]);

  async function save() {
    const trimmed = draft.trim();
    if (!trimmed) return;
    setStatus('saving…');
    try {
      const updated = await til.update(postId, { title: trimmed });
      setValue(updated.title);
      setStatus('');
      setEditing(false);
      // If slug changed (rare — only on title edit), update URL
      const currentSlug = window.location.pathname.replace(/^\/til\//, '').replace(/\/$/, '');
      if (updated.slug !== currentSlug) {
        window.history.replaceState({}, '', `/til/${updated.slug}`);
      }
    } catch {
      setStatus('save failed');
    }
  }

  function cancel() {
    setDraft(value);
    setEditing(false);
    setStatus('');
  }

  if (!isAdmin || !editing) {
    return (
      <h1
        className={`font-display text-4xl leading-tight md:text-5xl ${isAdmin ? 'editable editable--admin' : ''}`}
        onClick={() => isAdmin && setEditing(true)}
        title={isAdmin ? 'Click to edit title' : undefined}
      >
        {value}
        {isAdmin && <span className="editable__pencil" aria-hidden>✏</span>}
      </h1>
    );
  }

  return (
    <div
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <input
        ref={inputRef}
        className="editable-input font-display text-4xl leading-tight md:text-5xl"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') save();
          else if (e.key === 'Escape') cancel();
        }}
        placeholder="Title"
      />
      <div className="editable-row">
        <button type="button" className="save" disabled={!draft.trim()} onClick={save}>
          save ↵
        </button>
        <button type="button" className="cancel" onClick={cancel}>
          cancel
        </button>
        {status && <span className="editable-row__status">{status}</span>}
      </div>
    </div>
  );
}
