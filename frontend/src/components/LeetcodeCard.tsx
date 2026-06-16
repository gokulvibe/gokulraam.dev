/**
 * Subtle LeetCode card for the /now page. Three states:
 *
 *   • No username configured        — admin sees a small setup nudge,
 *                                     visitors see nothing.
 *   • Configured, never synced yet  — shows username + "syncing soon"
 *                                     plus a manual refresh button for
 *                                     admin.
 *   • Configured + has data         — compact display: streak, total,
 *                                     E/M/H breakdown, ranking. Admin
 *                                     gets a small refresh button.
 *
 * Deliberately understated. The user is good at LeetCode but it's not
 * their primary expertise — so this lives below LiveStatus on /now,
 * never on the homepage.
 */

import { useEffect, useState } from 'react';
import { leetcode, ApiError, type LeetcodeStats } from '@/lib/api';
import { useIsAdmin } from './admin/useIsAdmin';
import LeetcodeLogo from './LeetcodeLogo';

function timeAgo(iso: string | null): string {
  if (!iso) return 'never';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

export default function LeetcodeCard() {
  const isAdmin = useIsAdmin();
  const [stats, setStats] = useState<LeetcodeStats | null>(null);
  const [editingName, setEditingName] = useState(false);
  const [draftName, setDraftName] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    let alive = true;
    leetcode
      .get()
      .then((s) => alive && setStats(s))
      .catch(() => alive && setStats(null));
    return () => { alive = false; };
  }, []);

  async function saveUsername() {
    const next = draftName.trim();
    setBusy(true);
    setErr('');
    try {
      const updated = await leetcode.setUsername(next);
      setStats(updated);
      setEditingName(false);
      if (next) {
        // Kick off a sync so the visitor sees real numbers fast.
        void doRefresh();
      }
    } catch (e) {
      setErr(e instanceof ApiError ? `save failed (${e.status})` : 'save failed');
    } finally {
      setBusy(false);
    }
  }

  async function doRefresh() {
    setBusy(true);
    setErr('');
    try {
      const updated = await leetcode.refresh();
      setStats(updated);
    } catch (e) {
      setErr(e instanceof ApiError ? `sync failed (${e.status})` : 'sync failed');
    } finally {
      setBusy(false);
    }
  }

  // Loading state — keep blank to avoid flash.
  if (!stats) return null;

  const hasName = (stats.username || '').trim().length > 0;
  const hasData = stats.total_solved > 0 || stats.streak_days > 0;

  // Visitor with no configured username → render nothing at all.
  if (!hasName && isAdmin !== true) return null;

  return (
    <section className="leetcode">
      <div className="leetcode__head">
        <span className="leetcode__label">
          <LeetcodeLogo size={14} className="leetcode__logo" />
          // solving
        </span>
        {hasName && !editingName && (
          <a
            href={`https://leetcode.com/${stats.username}`}
            className="leetcode__handle"
            target="_blank"
            rel="noopener"
          >
            leetcode · {stats.username} ↗
          </a>
        )}
      </div>

      {/* Admin-only username setup row */}
      {isAdmin === true && (editingName || !hasName) && (
        <div className="leetcode__setup">
          <input
            type="text"
            className="leetcode__input"
            placeholder="leetcode username"
            value={draftName}
            onChange={(e) => setDraftName(e.target.value)}
            disabled={busy}
            autoFocus
          />
          <button
            type="button"
            className="leetcode__btn"
            onClick={saveUsername}
            disabled={busy}
          >
            {busy ? 'saving…' : 'save'}
          </button>
          {hasName && (
            <button
              type="button"
              className="leetcode__btn leetcode__btn--ghost"
              onClick={() => { setEditingName(false); setDraftName(''); }}
              disabled={busy}
            >
              cancel
            </button>
          )}
        </div>
      )}

      {/* Numbers — only when we have data. */}
      {hasName && hasData && !editingName && (
        <>
          <div className="leetcode__primary">
            <span className="leetcode__streak">{stats.streak_days}</span>
            <span className="leetcode__streak-unit">
              day{stats.streak_days === 1 ? '' : 's'} · current streak
            </span>
          </div>
          <div className="leetcode__breakdown">
            <span><strong>{stats.total_solved}</strong> solved</span>
            <span className="leetcode__sep">·</span>
            <span><strong>{stats.easy_solved}</strong> easy</span>
            <span><strong>{stats.medium_solved}</strong> medium</span>
            <span><strong>{stats.hard_solved}</strong> hard</span>
            {stats.ranking > 0 && (
              <>
                <span className="leetcode__sep">·</span>
                <span>rank #{stats.ranking.toLocaleString()}</span>
              </>
            )}
          </div>
          <div className="leetcode__foot">
            <span>synced {timeAgo(stats.last_synced_at)}</span>
            {isAdmin === true && (
              <>
                <span className="leetcode__sep">·</span>
                <button type="button" className="leetcode__link" onClick={doRefresh} disabled={busy}>
                  {busy ? 'syncing…' : 'sync now'}
                </button>
                <span className="leetcode__sep">·</span>
                <button
                  type="button"
                  className="leetcode__link"
                  onClick={() => { setEditingName(true); setDraftName(stats.username); }}
                >
                  change
                </button>
              </>
            )}
            {stats.last_error && (
              <>
                <span className="leetcode__sep">·</span>
                <span className="leetcode__err">{stats.last_error}</span>
              </>
            )}
          </div>
        </>
      )}

      {/* Configured but never synced */}
      {hasName && !hasData && !editingName && (
        <div className="leetcode__pending">
          <span>connected · waiting on first sync</span>
          {isAdmin === true && (
            <button type="button" className="leetcode__link" onClick={doRefresh} disabled={busy}>
              {busy ? 'syncing…' : 'sync now'}
            </button>
          )}
        </div>
      )}

      {err && <p className="leetcode__err">{err}</p>}
    </section>
  );
}
