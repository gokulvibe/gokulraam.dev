/**
 * Easter-egg client component. Mounted once at the layout level. Listens
 * for typed keywords anywhere outside a text input. Two triggers today:
 *
 *   - "snap"  → camera-flash overlay + toast linking to /photos
 *   - "knock" → toast linking to /museum/enter
 *
 * Both are typed in quick succession (< ~1.5s between letters). The buffer
 * resets on pause and on modifier keys (so ⌘K and friends are unaffected).
 * Adding a new keyword is a one-line entry in TRIGGERS — keep them short,
 * easy to discover, and unlikely to collide with normal speech-typing.
 */

import { useEffect } from 'react';

const TYPE_BUFFER_MS = 1500;

interface ToastSpec {
  glyph: string;
  title: string;
  link: { href: string; label: string };
}

interface Trigger {
  word: string;
  /** localStorage key for the discovery ledger (for a future "secrets" panel) */
  ledgerKey: string;
  /** Optional side-effect (e.g. the camera flash for /photos) */
  effect?: () => void;
  toast: ToastSpec;
}

const TRIGGERS: Trigger[] = [
  {
    word: 'snap',
    ledgerKey: 'photos',
    effect: cameraFlash,
    toast: {
      glyph: '📸',
      title: 'found the camera roll',
      link: { href: '/photos', label: '/photos' },
    },
  },
  {
    word: 'knock',
    ledgerKey: 'museum',
    effect: doorKnock,
    toast: {
      glyph: '🚪',
      title: "knock knock — who's there?",
      link: { href: '/museum/enter', label: '/museum/enter' },
    },
  },
];

const MAX_WORD = Math.max(...TRIGGERS.map((t) => t.word.length));

function showToast({ glyph, title, link }: ToastSpec) {
  document.querySelectorAll('.egg-toast').forEach((el) => el.remove());

  const t = document.createElement('div');
  t.className = 'egg-toast';
  t.setAttribute('role', 'status');
  t.innerHTML = `
    <span class="egg-toast__glyph" aria-hidden>${glyph}</span>
    <div class="egg-toast__body">
      <div class="egg-toast__title">${title}</div>
      <a href="${link.href}" class="egg-toast__link">${link.label} →</a>
    </div>
    <button type="button" class="egg-toast__x" aria-label="Dismiss">×</button>
  `;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add('is-open'));

  function dismiss() {
    t.classList.remove('is-open');
    setTimeout(() => t.remove(), 400);
  }
  const auto = window.setTimeout(dismiss, 5500);
  t.querySelector('.egg-toast__x')?.addEventListener('click', () => {
    window.clearTimeout(auto);
    dismiss();
  });
}

function cameraFlash() {
  const flash = document.createElement('div');
  flash.className = 'egg-flash';
  document.body.appendChild(flash);
  requestAnimationFrame(() => flash.classList.add('is-on'));
  setTimeout(() => flash.remove(), 700);
}

/**
 * Door-knock effect. Three quick low-frequency thumps via WebAudio
 * (no asset file needed) + a tiny page shake synced to each thump.
 * Skips the audio if AudioContext is blocked or unavailable; the
 * visual still fires.
 */
function doorKnock() {
  // Visual: small page rumble. Class is removed after the animation
  // completes; CSS @keyframes drives the three knocks.
  document.body.classList.remove('egg-knock-shake');  // reset if mid-anim
  // Force reflow so re-adding the class restarts the animation
  void document.body.offsetWidth;
  document.body.classList.add('egg-knock-shake');
  setTimeout(() => document.body.classList.remove('egg-knock-shake'), 700);

  // Audio: three thumps. Each is a sub-100Hz sine with an envelope
  // that decays in ~120ms — sounds like a closed-fist door knock.
  try {
    const Ctx = (window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext) as
      | typeof AudioContext
      | undefined;
    if (!Ctx) return;
    const ctx = new Ctx();
    const SPACING = 0.16;
    for (let i = 0; i < 3; i++) {
      const t = ctx.currentTime + i * SPACING;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(110, t);
      osc.frequency.exponentialRampToValueAtTime(45, t + 0.09);
      gain.gain.setValueAtTime(0, t);
      gain.gain.linearRampToValueAtTime(0.32, t + 0.005);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.15);
    }
    // Release the context after the sounds finish.
    setTimeout(() => ctx.close().catch(() => undefined), 800);
  } catch {
    /* AudioContext unavailable / blocked — visual still played */
  }
}

function rememberDiscovery(key: string) {
  try {
    const raw = localStorage.getItem('egg.found') ?? '{}';
    const obj = JSON.parse(raw) as Record<string, number>;
    obj[key] = Date.now();
    localStorage.setItem('egg.found', JSON.stringify(obj));
  } catch {
    /* localStorage disabled — silently ignore */
  }
}

export default function EasterEggs() {
  useEffect(() => {
    let buffer = '';
    let lastAt = 0;

    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (!target) return;
      // Skip when typing into an editable surface.
      if (
        target.matches('input, textarea, [contenteditable=""], [contenteditable="true"]') ||
        target.closest('[contenteditable="true"], .ProseMirror')
      ) {
        return;
      }
      // Ignore chords and non-character keys; lets ⌘K etc. pass through.
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key.length !== 1) return;

      const now = Date.now();
      if (now - lastAt > TYPE_BUFFER_MS) buffer = '';
      lastAt = now;
      buffer = (buffer + e.key.toLowerCase()).slice(-MAX_WORD);

      for (const trig of TRIGGERS) {
        if (buffer.endsWith(trig.word)) {
          buffer = '';
          trig.effect?.();
          rememberDiscovery(trig.ledgerKey);
          showToast(trig.toast);
          break;
        }
      }
    }

    document.addEventListener('keydown', onKey);

    // ─── Page-wide tap counter (mobile-friendly) ─────────────────
    // No specific target needed — tap anywhere a few times and an egg
    // fires after a short pause. Counts:
    //
    //   3 taps → snap   (photos)
    //   5 taps → knock  (museum)
    //
    // Why pause-then-fire instead of fire-on-3rd? Because some users
    // want museum (5) and we don't want photos to fire on the way. The
    // count is evaluated only after the user stops tapping for ~700ms.
    //
    // Clicks on real interactive elements (inputs, buttons, the inline
    // editor, expandable cards) are ignored so tap-counting never
    // interferes with editing or admin actions. Link clicks cause a
    // page navigation which resets state implicitly.
    const TAP_WINDOW_MS = 700;
    const TAP_COUNTS: Record<number, string> = { 3: 'snap', 5: 'knock' };
    const MAX_TAP_COUNT = Math.max(...Object.keys(TAP_COUNTS).map(Number));

    const indicator = document.createElement('div');
    indicator.className = 'egg-tap-indicator';
    indicator.innerHTML = `<span>tap</span>${
      Array.from({ length: MAX_TAP_COUNT })
        .map(() => '<span class="egg-tap-indicator__dot"></span>')
        .join('')
    }`;
    document.body.appendChild(indicator);
    const dots = indicator.querySelectorAll<HTMLSpanElement>('.egg-tap-indicator__dot');

    let tapCount = 0;
    let tapResetTimer: number | null = null;

    function updateIndicator() {
      if (tapCount <= 0) {
        indicator.classList.remove('is-on');
        dots.forEach((d) => d.classList.remove('is-lit'));
        return;
      }
      // Show only after the 2nd tap so a single accidental click isn't
      // surfaced — but once shown, light up every dot we've earned.
      if (tapCount >= 2) indicator.classList.add('is-on');
      dots.forEach((d, i) => d.classList.toggle('is-lit', i < tapCount));
    }

    function onPageTap(e: MouseEvent) {
      const t = e.target as HTMLElement | null;
      if (!t) return;
      // Ignore taps on explicit interactive targets — they have their
      // own handlers, and counting them surprises users editing/admin-ing.
      // Anchor clicks cause navigation which resets state implicitly.
      if (
        t.closest(
          'input, textarea, button, select, [contenteditable="true"], ' +
            '.ProseMirror, [data-expandable], .card-clone',
        )
      ) {
        return;
      }
      tapCount += 1;
      if (tapCount > MAX_TAP_COUNT) tapCount = 1;  // wrap so they can keep trying
      updateIndicator();
      if (tapResetTimer) window.clearTimeout(tapResetTimer);
      tapResetTimer = window.setTimeout(() => {
        const word = TAP_COUNTS[tapCount];
        tapCount = 0;
        tapResetTimer = null;
        updateIndicator();
        if (word) {
          const trig = TRIGGERS.find((tr) => tr.word === word);
          if (trig) {
            trig.effect?.();
            rememberDiscovery(trig.ledgerKey);
            showToast(trig.toast);
          }
        }
      }, TAP_WINDOW_MS);
    }

    document.addEventListener('click', onPageTap);

    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('click', onPageTap);
      if (tapResetTimer) window.clearTimeout(tapResetTimer);
      indicator.remove();
    };
  }, []);

  return null;
}
