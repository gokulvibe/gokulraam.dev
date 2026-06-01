import { useState } from 'react';
import { til } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

interface Props {
  postId: number;
  initial: string[];
}

function toCsv(tags: string[]) {
  return tags.join(', ');
}
function fromCsv(raw: string): string[] {
  return raw
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);
}

export default function EditableTags({ postId, initial }: Props) {
  const isAdmin = useIsAdmin();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState<string[]>(initial);
  const [draft, setDraft] = useState(toCsv(initial));
  const [status, setStatus] = useState('');

  async function save() {
    const next = fromCsv(draft);
    setStatus('saving…');
    try {
      const updated = await til.update(postId, { tags: next });
      setValue(updated.tags);
      setDraft(toCsv(updated.tags));
      setStatus('');
      setEditing(false);
    } catch {
      setStatus('save failed');
    }
  }

  function cancel() {
    setDraft(toCsv(value));
    setEditing(false);
    setStatus('');
  }

  if (!isAdmin || !editing) {
    const empty = value.length === 0;
    return (
      <div
        className={isAdmin ? 'editable editable--admin' : ''}
        onClick={() => isAdmin && setEditing(true)}
        title={isAdmin ? 'Click to edit tags' : undefined}
      >
        {empty && isAdmin && (
          <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-ghost italic">
            + add tags
          </span>
        )}
        {!empty && (
          <div className="flex flex-wrap gap-2">
            {value.map((t) => (
              <span key={t} className="chip">
                #{t}
              </span>
            ))}
          </div>
        )}
        {isAdmin && <span className="editable__pencil" aria-hidden>✏</span>}
      </div>
    );
  }

  return (
    <div
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <input
        className="editable-input font-mono text-sm"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') save();
          else if (e.key === 'Escape') cancel();
        }}
        placeholder="postgres, performance, sql"
        autoFocus
      />
      <div className="editable-row">
        <button type="button" className="save" onClick={save}>
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
