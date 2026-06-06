/**
 * Secrets panel — the meta-egg.
 *
 * Trigger: a window-level CustomEvent('secrets:open') (dispatched by
 * EasterEggs.tsx when the visitor types the word `secrets`).
 *
 * Display: slide-out drawer from the right edge. Lists every registered
 * easter egg with two modes per row:
 *
 *   • Found (recorded in localStorage.egg.found) — shows the trigger
 *     plainly + what it reveals + when it was discovered.
 *
 *   • Not yet found — only a cryptic hint that points at the trigger
 *     without naming it. The discovery is still the visitor's to make.
 *
 * Source of truth for the egg list: this component. Mirrors the table
 * in ROADMAP.md / CLAUDE.md / AdminBar's reference modal. When a new
 * egg is added, mirror it here too (ledger key + cryptic hint).
 */

import { useEffect, useState } from 'react';

interface Egg {
  ledgerKey: string;          // matches the key written to localStorage.egg.found
  /** What this egg reveals, shown to those who've found it. */
  reveals: string;
  /** Cryptic hint shown to those who haven't found it yet. */
  hint: string;
  /** The actual trigger description, shown after discovery. */
  trigger: string;
}

const EGGS: Egg[] = [
  {
    ledgerKey: 'photos',
    reveals: '/photos',
    hint: 'four letters · a shutter sound',
    trigger: 'type `snap`  · or tap anywhere three times',
  },
  {
    ledgerKey: 'museum',
    reveals: '/museum/enter',
    hint: 'three quick raps · a question',
    trigger: 'type `knock`  · or tap anywhere five times',
  },
  // The 404 puzzle has no ledger key — it doesn't navigate anywhere —
  // but it's still part of the egg surface. Use a sentinel value that's
  // never written to localStorage so it always shows as "discovered if
  // you've visited /404 with the puzzle solved". We treat it as
  // permanently unknown unless the visitor has solved it.
  // Because we don't track 404-puzzle solves yet, the hint stays.
  {
    ledgerKey: '__404_puzzle',
    reveals: 'a glow on the digits',
    hint: 'on a page that does not exist · the digits remember an order',
    trigger: 'on /404 — click the digits 4 → 0 → 4 in sequence',
  },
];

interface FoundLedger {
  [key: string]: number;  // timestamp
}

function readFound(): FoundLedger {
  try {
    const raw = localStorage.getItem('egg.found') ?? '{}';
    return JSON.parse(raw) as FoundLedger;
  } catch {
    return {};
  }
}

function timeAgo(ts: number): string {
  const diff = (Date.now() - ts) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

export default function SecretsPanel() {
  const [open, setOpen] = useState(false);
  const [found, setFound] = useState<FoundLedger>({});

  useEffect(() => {
    function onOpen() {
      setFound(readFound());
      setOpen(true);
    }
    window.addEventListener('secrets:open', onOpen);
    return () => window.removeEventListener('secrets:open', onOpen);
  }, []);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  if (!open) return null;

  const foundCount = EGGS.filter((e) => found[e.ledgerKey]).length;

  return (
    <div
      className="secrets-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Secrets"
      onClick={(e) => {
        if (e.target === e.currentTarget) setOpen(false);
      }}
    >
      <aside className="secrets" role="document">
        <header className="secrets__head">
          <div>
            <h2 className="secrets__title">// secrets</h2>
            <p className="secrets__count">
              {foundCount} of {EGGS.length} found · keep wandering for the rest
            </p>
          </div>
          <button
            type="button"
            className="secrets__close"
            onClick={() => setOpen(false)}
            aria-label="Close"
          >
            ×
          </button>
        </header>

        <ol className="secrets__list">
          {EGGS.map((egg, i) => {
            const ts = found[egg.ledgerKey];
            const isFound = typeof ts === 'number';
            return (
              <li
                key={egg.ledgerKey}
                className={`secrets__item ${isFound ? 'is-found' : 'is-locked'}`}
              >
                <div className="secrets__row">
                  <span className="secrets__num">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span className="secrets__mark" aria-hidden>
                    {isFound ? '✓' : '?'}
                  </span>
                  <div className="secrets__body">
                    {isFound ? (
                      <>
                        <div className="secrets__found-line">
                          <span className="secrets__trigger">{egg.trigger}</span>
                        </div>
                        <div className="secrets__detail">
                          <span className="secrets__reveals">→ {egg.reveals}</span>
                          <span className="secrets__when">found {timeAgo(ts)}</span>
                        </div>
                      </>
                    ) : (
                      <p className="secrets__hint">{egg.hint}</p>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>

        <footer className="secrets__foot">
          esc to close · no records leave your browser
        </footer>
      </aside>
    </div>
  );
}
