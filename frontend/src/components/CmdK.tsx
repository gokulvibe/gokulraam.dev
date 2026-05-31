/**
 * Site-wide cmd+k / ctrl+k search modal.
 *
 * Mounted globally via Base.astro. Listens for the chord, opens a centered
 * dialog, fetches /api/search?q=… with a small debounce, renders grouped
 * hits, keyboard-navigable (↑↓ + Enter to open, Esc to close).
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { search, type SearchHit } from '@/lib/api';

const DEBOUNCE_MS = 140;

export default function CmdK() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global chord listener
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const isCmdK = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k';
      if (isCmdK) {
        e.preventDefault();
        setOpen((v) => !v);
        return;
      }
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // Focus when opening; reset on close
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 30);
    } else {
      setQuery('');
      setHits([]);
      setActive(0);
    }
  }, [open]);

  // Debounce query input
  useEffect(() => {
    const t = setTimeout(() => setDebounced(query), DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [query]);

  // Fetch results when debounced query changes
  useEffect(() => {
    let alive = true;
    if (!debounced.trim()) {
      setHits([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    search
      .query(debounced)
      .then((r) => {
        if (!alive) return;
        setHits(r.hits);
        setActive(0);
      })
      .catch(() => {
        if (!alive) return;
        setHits([]);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [debounced]);

  // Group hits by group name preserving sorted order
  const grouped = useMemo(() => {
    const map = new Map<string, SearchHit[]>();
    for (const h of hits) {
      if (!map.has(h.group)) map.set(h.group, []);
      map.get(h.group)!.push(h);
    }
    return Array.from(map.entries());
  }, [hits]);

  function go(href: string) {
    setOpen(false);
    window.location.href = href;
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (hits.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, hits.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const target = hits[active];
      if (target) go(target.href);
    }
  }

  if (!open) return null;

  return (
    <div
      className="cmdk-backdrop"
      role="dialog"
      aria-modal="true"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) setOpen(false);
      }}
    >
      <div className="cmdk-panel">
        <div className="cmdk-input-row">
          <span className="cmdk-kbd">⌘K</span>
          <input
            ref={inputRef}
            className="cmdk-input"
            placeholder="Search everything…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            spellCheck={false}
            autoComplete="off"
          />
          {loading && <span className="cmdk-loading">searching…</span>}
        </div>

        <div className="cmdk-results">
          {!query && (
            <p className="cmdk-empty">
              Type to search across TIL, Work, Projects, Now, Uses, Badminton, and more.
            </p>
          )}
          {query && !loading && hits.length === 0 && (
            <p className="cmdk-empty">no matches for "{query}"</p>
          )}
          {grouped.map(([group, items], gi) => {
            // Compute the absolute index range of this group within hits
            const before = grouped.slice(0, gi).reduce((acc, [, arr]) => acc + arr.length, 0);
            return (
              <section key={group} className="cmdk-group">
                <p className="cmdk-group-label">// {group}</p>
                <ul>
                  {items.map((hit, i) => {
                    const abs = before + i;
                    const isActive = abs === active;
                    return (
                      <li key={`${group}-${i}-${hit.title}`}>
                        <button
                          type="button"
                          className={`cmdk-hit ${isActive ? 'is-active' : ''}`}
                          onMouseEnter={() => setActive(abs)}
                          onClick={() => go(hit.href)}
                        >
                          <span className="cmdk-hit-title">{hit.title}</span>
                          {hit.subtitle && (
                            <span className="cmdk-hit-sub">{hit.subtitle}</span>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </div>

        <footer className="cmdk-footer">
          <span><kbd>↑↓</kbd> navigate</span>
          <span><kbd>↵</kbd> open</span>
          <span><kbd>esc</kbd> close</span>
        </footer>
      </div>
    </div>
  );
}
