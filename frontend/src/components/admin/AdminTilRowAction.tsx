/** Per-row delete affordance shown inline next to published posts. */

import { til, type TilPost } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

interface Props {
  post: Pick<TilPost, 'id' | 'title'>;
}

export default function AdminTilRowAction({ post }: Props) {
  const isAdmin = useIsAdmin();
  if (!isAdmin) return null;

  async function remove(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm(`Delete "${post.title}"? This cannot be undone.`)) return;
    try {
      await til.remove(post.id);
      window.location.reload();
    } catch {
      alert('Delete failed.');
    }
  }

  return (
    <button
      type="button"
      onClick={remove}
      className="font-mono text-[10px] uppercase tracking-[0.18em] text-rose hover:opacity-80"
      title="Delete post"
    >
      delete
    </button>
  );
}
