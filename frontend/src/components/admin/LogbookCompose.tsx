import { useState } from 'react';
import { logbook } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

const QUICK_TAGS = ['thought', 'noted', 'win', 'fail', 'watching', 'shipping'];

export default function LogbookCompose() {
  const isAdmin = useIsAdmin();
  const [body, setBody] = useState('');
  const [tag, setTag] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');

  if (isAdmin !== true) return null;

  async function submit() {
    const trimmed = body.trim();
    if (!trimmed) return;
    setBusy(true);
    setStatus('posting…');
    try {
      await logbook.create({ body: trimmed, tag: tag.trim() });
      setBody('');
      setTag('');
      setStatus('posted — refresh to see it');
      setTimeout(() => location.reload(), 400);
    } catch {
      setStatus('post failed');
      setBusy(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      void submit();
    }
  }

  return (
    <div className="logbook-compose">
      <div className="logbook-compose__head">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-gold">
          ✎ new entry
        </span>
        <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-ghost">
          {body.length}/500 · ⌘↵ to post
        </span>
      </div>
      <textarea
        className="logbook-compose__body"
        value={body}
        rows={2}
        maxLength={500}
        placeholder="One observation. Today, this morning, just now."
        onChange={(e) => setBody(e.target.value)}
        onKeyDown={onKeyDown}
        disabled={busy}
      />
      <div className="logbook-compose__row">
        <input
          className="logbook-compose__tag"
          type="text"
          value={tag}
          placeholder="tag (optional)"
          maxLength={40}
          onChange={(e) => setTag(e.target.value)}
          disabled={busy}
        />
        <div className="logbook-compose__quick">
          {QUICK_TAGS.map((t) => (
            <button
              key={t}
              type="button"
              className={`logbook-quick-tag ${tag === t ? 'is-active' : ''}`}
              onClick={() => setTag(t === tag ? '' : t)}
              disabled={busy}
            >
              {t}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="logbook-compose__post"
          onClick={submit}
          disabled={busy || !body.trim()}
        >
          post
        </button>
      </div>
      {status && <p className="logbook-compose__status">{status}</p>}
    </div>
  );
}
