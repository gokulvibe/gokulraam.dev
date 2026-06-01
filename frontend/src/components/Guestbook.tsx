/**
 * Guestbook — submission form + entry list, both client-rendered.
 *
 * Spam protection:
 *   - Honeypot field 'website' (visually hidden via CSS, real users never see
 *     or fill it; bots tend to fill every input).
 *   - Server-side rate-limit per IP hash (30s).
 */

import { useEffect, useState } from 'react';
import { guestbook, type GuestbookEntry, ApiError } from '@/lib/api';
import { useIsAdmin } from './admin/useIsAdmin';

function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  if (diff < 2592000) return `${Math.round(diff / 86400)}d ago`;
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
}

export default function Guestbook() {
  const isAdmin = useIsAdmin();
  const [entries, setEntries] = useState<GuestbookEntry[] | null>(null);
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [website, setWebsite] = useState('');  // honeypot
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [errMsg, setErrMsg] = useState('');

  useEffect(() => {
    void guestbook
      .list()
      .then(setEntries)
      .catch(() => setEntries([]));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;
    setStatus('sending');
    setErrMsg('');
    try {
      const newEntry = await guestbook.post({
        name: name.trim(),
        message: message.trim(),
        website,
      });
      // If honeypot was filled the server returns a fake success without
      // persisting. The id will be 0 in that case — don't prepend to the
      // visible list, but still pretend it worked.
      if (newEntry.id > 0) {
        setEntries((prev) => (prev ? [newEntry, ...prev] : [newEntry]));
      }
      setStatus('sent');
      setName('');
      setMessage('');
      setWebsite('');
    } catch (err) {
      setStatus('error');
      if (err instanceof ApiError && err.status === 429) {
        setErrMsg('easy there — wait a few seconds before posting again');
      } else {
        setErrMsg('could not send. backend reachable?');
      }
    }
  }

  async function remove(entry: GuestbookEntry) {
    if (!confirm(`Hide note from ${entry.name || 'anonymous'}?`)) return;
    try {
      await guestbook.remove(entry.id);
      setEntries((prev) => (prev ?? []).filter((e) => e.id !== entry.id));
    } catch {
      alert('Could not hide entry.');
    }
  }

  return (
    <div className="space-y-12">
      {/* Submission form */}
      <form onSubmit={onSubmit} className="guestbook-form">
        <div className="space-y-3">
          <label className="block">
            <span className="label block mb-1.5">name (optional)</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={80}
              className="guestbook-input"
              placeholder="signed —"
            />
          </label>
          <label className="block">
            <span className="label block mb-1.5">a note</span>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxLength={1000}
              rows={4}
              className="guestbook-input guestbook-input--textarea"
              placeholder="say hi, drop a thought, leave a footprint…"
              required
            />
          </label>

          {/* Honeypot: positioned far off-screen, no labels, autocomplete=off */}
          <div aria-hidden="true" className="guestbook-honeypot">
            <label>
              Website
              <input
                type="text"
                tabIndex={-1}
                autoComplete="off"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
              />
            </label>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-4">
          <button
            type="submit"
            disabled={status === 'sending' || !message.trim()}
            className="guestbook-btn"
          >
            {status === 'sending' ? 'sending…' : status === 'sent' ? 'sent ✓' : 'leave a note'}
          </button>
          {status === 'sent' && (
            <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-mist">
              thank you — your note is below
            </span>
          )}
          {status === 'error' && (
            <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-rose">
              {errMsg}
            </span>
          )}
        </div>
      </form>

      {/* Entries */}
      <div>
        <p className="label mb-4">// notes left for me</p>
        {entries === null && (
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-mist">loading…</p>
        )}
        {entries !== null && entries.length === 0 && (
          <p className="text-mist italic">no notes yet — be the first.</p>
        )}
        {entries !== null && entries.length > 0 && (
          <ul className="space-y-5">
            {entries.map((e) => (
              <li key={e.id} className="guestbook-entry">
                <div className="flex items-baseline justify-between gap-3 mb-2">
                  <span className="font-display text-lg text-cream">
                    {e.name?.trim() || <em className="text-mist">anonymous</em>}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-ghost">
                      {timeAgo(e.created_at)}
                    </span>
                    {isAdmin && (
                      <button
                        type="button"
                        onClick={() => remove(e)}
                        className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-rose hover:opacity-80"
                        title="Hide this note"
                      >
                        hide
                      </button>
                    )}
                  </div>
                </div>
                <p className="text-parchment leading-relaxed whitespace-pre-wrap">{e.message}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
