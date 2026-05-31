/**
 * Admin-only sections rendered inside /til. Shows drafts in their own block
 * and adds a small per-row "delete" action on published posts.
 *
 * For visitors, this component renders nothing — they see only the existing
 * server-rendered published list.
 */

import { useEffect, useState } from 'react';
import { til, type TilPost } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

const fmt = (s: string) =>
  new Date(s).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: '2-digit' });

export default function AdminTilSection() {
  const isAdmin = useIsAdmin();
  const [posts, setPosts] = useState<TilPost[] | null>(null);

  useEffect(() => {
    if (!isAdmin) return;
    void til.list(true).then(setPosts).catch(() => setPosts([]));
  }, [isAdmin]);

  if (!isAdmin) return null;
  if (posts === null) {
    return (
      <p className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-mist mt-6">
        loading admin view…
      </p>
    );
  }

  const drafts = posts.filter((p) => p.draft);

  async function createNew() {
    try {
      const post = await til.create({
        title: 'Untitled',
        body_md: '',
        tags: [],
        draft: true,
      });
      window.location.href = `/til/${post.slug}?new=1`;
    } catch {
      alert('Could not create post.');
    }
  }

  async function remove(p: TilPost) {
    if (!confirm(`Delete "${p.title}"? This cannot be undone.`)) return;
    try {
      await til.remove(p.id);
      setPosts((prev) => (prev ?? []).filter((x) => x.id !== p.id));
    } catch {
      alert('Delete failed.');
    }
  }

  async function publish(p: TilPost) {
    try {
      await til.update(p.id, { draft: false });
      // Refresh — published posts are now in the main list, so re-fetch.
      const next = await til.list(true);
      setPosts(next);
    } catch {
      alert('Publish failed.');
    }
  }

  return (
    <div className="mb-10">
      {/* Quick-create row */}
      <div className="mb-8 flex items-center gap-3 rounded-md border border-rule bg-smoke/40 px-4 py-3">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-gold">
          admin
        </span>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-mist">
          managing this page
        </span>
        <button
          type="button"
          onClick={createNew}
          className="ml-auto font-mono text-[10.5px] uppercase tracking-[0.18em] text-ember hover:opacity-80"
        >
          + new entry
        </button>
      </div>

      {/* Drafts */}
      {drafts.length > 0 && (
        <section className="mb-10">
          <p className="label mb-3">
            // drafts <span className="text-gold">({drafts.length})</span>
          </p>
          <ul className="space-y-2">
            {drafts.map((p) => (
              <li
                key={p.id}
                className="flex items-center justify-between gap-4 rounded-md border border-dashed border-rule bg-smoke/30 px-4 py-3"
              >
                <a
                  href={`/til/${p.slug}`}
                  className="min-w-0 flex-1 truncate font-display text-lg hover:text-ember"
                >
                  {p.title || <span className="italic text-mist">untitled</span>}
                </a>
                <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-gold shrink-0">
                  draft · {fmt(p.updated_at)}
                </span>
                <button
                  type="button"
                  onClick={() => publish(p)}
                  className="font-mono text-[10px] uppercase tracking-[0.18em] text-ember hover:opacity-80 shrink-0"
                  title="Publish this draft"
                >
                  publish ▸
                </button>
                <button
                  type="button"
                  onClick={() => remove(p)}
                  className="font-mono text-[10px] uppercase tracking-[0.18em] text-rose hover:opacity-80 shrink-0"
                  title="Delete draft"
                >
                  🗑
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
