/**
 * Client-side TIL post loader for the cross-origin draft case.
 *
 * Why this exists: when Cloudflare Pages (frontend) and Render (backend) are
 * on different domains, the auth cookie is bound to the backend domain only.
 * The browser doesn't send that cookie to Pages, so Astro SSR fetching the
 * post sees an empty cookie header and the backend treats SSR as a guest.
 * Guests can't read drafts — SSR ends up with `post = null`.
 *
 * This component mounts on the client where `fetch` with `credentials:
 * 'include'` *does* attach the backend cookie (because the request goes
 * directly from browser → backend domain). It retries the read with auth,
 * and renders the full editor if it succeeds.
 *
 * The component renders the same shape as the SSR-rendered article so the
 * page looks identical whether the post came from SSR or client-side.
 */

import { useEffect, useState } from 'react';
import { til, type TilPost, ApiError } from '@/lib/api';
import EditableAttachments from './EditableAttachments';
import EditableBody from './EditableBody';
import EditableTags from './EditableTags';
import EditableTitle from './EditableTitle';
import PostStatusActions from './PostStatusActions';
import { useIsAdmin } from './useIsAdmin';

type State =
  | { kind: 'loading' }
  | { kind: 'found'; post: TilPost }
  | { kind: 'not-found' }
  | { kind: 'unauthorized' };

interface Props {
  slug: string;
}

const fmt = (s: string) =>
  new Date(s).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: '2-digit' });

export default function TilDraftLoader({ slug }: Props) {
  const isAdmin = useIsAdmin();
  const [state, setState] = useState<State>({ kind: 'loading' });

  useEffect(() => {
    // Wait until we know if the visitor is admin. For guests there's no
    // point retrying — they'd just get a 404 again.
    if (isAdmin === null) return;
    if (isAdmin === false) {
      setState({ kind: 'not-found' });
      return;
    }
    let alive = true;
    til
      .get(slug)
      .then((post) => {
        if (alive) setState({ kind: 'found', post });
      })
      .catch((e: unknown) => {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401) {
          setState({ kind: 'unauthorized' });
        } else {
          setState({ kind: 'not-found' });
        }
      });
    return () => {
      alive = false;
    };
  }, [slug, isAdmin]);

  if (state.kind === 'loading') {
    return (
      <div>
        <a href="/til" className="font-mono text-xs text-mist hover:text-cream">
          ← back to til
        </a>
        <p className="mt-12 font-mono text-[11px] uppercase tracking-[0.18em] text-mist">
          loading post…
        </p>
      </div>
    );
  }

  if (state.kind === 'unauthorized') {
    // Session expired or invalid — bounce to login.
    if (typeof window !== 'undefined') {
      window.location.href = '/admin/login';
    }
    return null;
  }

  if (state.kind === 'not-found') {
    return (
      <div>
        <a href="/til" className="font-mono text-xs text-mist hover:text-cream">
          ← back to til
        </a>
        <p className="mt-12 font-display text-3xl text-cream">post not found</p>
        <p className="mt-3 text-sm text-mist max-w-md">
          This post may not exist, may be a draft you don't have access to, or may have been deleted.
        </p>
      </div>
    );
  }

  const post = state.post;
  return (
    <article>
      <a href="/til" className="font-mono text-xs text-mist hover:text-cream">
        ← back to til
      </a>

      <PostStatusActions
        postId={post.id}
        postTitle={post.title}
        initialDraft={post.draft}
      />

      <header className="mt-2 mb-10">
        <div className="label mb-3">// {fmt(post.created_at)}</div>
        <EditableTitle postId={post.id} initial={post.title} />
        <div className="mt-4">
          <EditableTags postId={post.id} initial={post.tags} />
        </div>
      </header>

      <EditableBody
        postId={post.id}
        initialMd={post.body_md}
        initialHtml={post.body_html}
      />

      <EditableAttachments postId={post.id} initial={post.attachments} />
    </article>
  );
}
