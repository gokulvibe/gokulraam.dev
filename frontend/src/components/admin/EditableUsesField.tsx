/**
 * One editable field of a UsesItem (either `name` or `note`).
 * Follows the same view/edit/save convention as the other Editable* components.
 *
 * Two usages per row in /uses.astro:
 *   <EditableUsesField itemId={id} field="name" initial={name} ... />
 *   <EditableUsesField itemId={id} field="note" initial={note} ... />
 */

import { useRef, useState } from 'react';
import { uses } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

interface Props {
  itemId: number;
  field: 'name' | 'note';
  initial: string;
  className?: string;
  placeholder?: string;
}

export default function EditableUsesField({
  itemId,
  field,
  initial,
  className = '',
  placeholder = '',
}: Props) {
  const isAdmin = useIsAdmin();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(initial);
  const [draft, setDraft] = useState(initial);
  const [status, setStatus] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // For visual display: name with leading "—" is a placeholder
  const isPlaceholder = field === 'name' && value.startsWith('—');

  async function save() {
    const next = draft.trim();
    if (!next || next === value) {
      setEditing(false);
      setStatus('');
      return;
    }
    setStatus('saving…');
    try {
      const updated = await uses.update(itemId, { [field]: next });
      setValue(field === 'name' ? updated.name : updated.note);
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
        className={`${className} ${isPlaceholder ? 'italic text-mist' : ''} ${isAdmin ? 'editable editable--admin' : ''}`}
        onClick={startEdit}
        title={isAdmin ? 'Click to edit' : undefined}
      >
        {value || (isAdmin ? <span className="italic text-ghost">empty — click to edit</span> : '')}
        {isAdmin && <span className="editable__pencil" aria-hidden>✏</span>}
      </span>
    );
  }

  return (
    <span
      style={{ display: 'inline-block', width: '100%' }}
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <input
        ref={inputRef}
        className={`editable-input ${className}`}
        value={draft}
        placeholder={placeholder}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') save();
          else if (e.key === 'Escape') cancel();
        }}
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
    </span>
  );
}
