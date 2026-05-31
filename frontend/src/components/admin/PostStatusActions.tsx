/**
 * In-page admin actions for a single TIL post.
 * Lives at the top of /til/<slug>. Renders nothing for guests.
 *
 * Shows current draft state + publish/unpublish + delete in the page itself,
 * so the floating AdminBar can stay minimal.
 */

import { useState } from 'react';
import { til } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

interface Props {
  postId: number;
  postTitle: string;
  initialDraft: boolean;
}

export default function PostStatusActions({ postId, postTitle, initialDraft }: Props) {
  const isAdmin = useIsAdmin();
  const [draft, setDraft] = useState(initialDraft);
  const [busy, setBusy] = useState<string>('');

  if (isAdmin !== true) return null;

  async function togglePublish() {
    setBusy(draft ? 'publishing…' : 'reverting…');
    try {
      const updated = await til.update(postId, { draft: !draft });
      setDraft(updated.draft);
      setBusy(updated.draft ? 'reverted to draft' : 'published ✓');
      setTimeout(() => setBusy(''), 1800);
    } catch {
      setBusy('failed');
    }
  }

  async function remove() {
    if (!confirm(`Delete "${postTitle}"? This cannot be undone.`)) return;
    setBusy('deleting…');
    try {
      await til.remove(postId);
      window.location.href = '/til';
    } catch {
      setBusy('delete failed');
    }
  }

  return (
    <div className="post-actions">
      <span className="post-actions__hint">admin</span>
      <span className="post-actions__sep" />
      <span className="post-actions__state">
        state ·
        {draft ? (
          <span className="post-actions__chip post-actions__chip--draft">draft</span>
        ) : (
          <span className="post-actions__chip post-actions__chip--published">published</span>
        )}
      </span>

      <button
        type="button"
        onClick={togglePublish}
        disabled={!!busy}
        className={`post-actions__btn ${draft ? 'post-actions__btn--primary' : ''}`}
        title={draft ? 'Make this post public' : 'Move back to drafts'}
      >
        {draft ? 'publish ▸' : '◾ revert to draft'}
      </button>

      <button
        type="button"
        onClick={remove}
        disabled={!!busy}
        className="post-actions__btn post-actions__btn--danger"
        title="Delete this post"
      >
        🗑 delete
      </button>

      {busy && <span className="post-actions__status">{busy}</span>}
    </div>
  );
}
