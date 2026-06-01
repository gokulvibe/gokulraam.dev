/**
 * Easter-egg client component. Mounted once at the layout level. Listens
 * for two discovery gestures:
 *
 *   1. Shift + click on any element marked `data-egg-shutter` (currently
 *      the header brand). Flashes the screen white like a camera shutter
 *      and shows a toast linking to /photos.
 *
 *   2. Typing the letters k-n-o-c-k in quick succession anywhere outside
 *      a text input. Shows a "knock knock — who's there?" toast linking
 *      to /museum/enter.
 *
 * Both eggs persist their last-discovered timestamp in localStorage so a
 * future "secrets" panel can show what's been found.
 */

import { useEffect } from 'react';

const TOAST_HOLD_MS = 5500;
const TYPE_BUFFER_MS = 1500;
const TARGET_PHRASE = 'knock';

interface ToastSpec {
  glyph: string;
  title: string;
  link: { href: string; label: string };
}

function showToast({ glyph, title, link }: ToastSpec) {
  // Dedupe: if a toast is currently visible, replace it
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
  const auto = window.setTimeout(dismiss, TOAST_HOLD_MS);
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
    // 1) Shutter chord
    function onClick(e: MouseEvent) {
      if (!e.shiftKey) return;
      const target = (e.target as HTMLElement | null)?.closest('[data-egg-shutter]');
      if (!target) return;
      e.preventDefault();
      cameraFlash();
      rememberDiscovery('photos');
      showToast({
        glyph: '📸',
        title: 'found the camera roll',
        link: { href: '/photos', label: '/photos' },
      });
    }
    document.addEventListener('click', onClick);

    // 2) k-n-o-c-k anywhere outside an input
    let buffer = '';
    let lastAt = 0;
    function onKey(e: KeyboardEvent) {
      const t = e.target as HTMLElement;
      if (!t) return;
      if (
        t.matches('input, textarea, [contenteditable=""], [contenteditable="true"]') ||
        t.closest('[contenteditable="true"], .ProseMirror')
      ) {
        return;
      }
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key.length !== 1) return;
      const now = Date.now();
      if (now - lastAt > TYPE_BUFFER_MS) buffer = '';
      lastAt = now;
      buffer = (buffer + e.key.toLowerCase()).slice(-TARGET_PHRASE.length);
      if (buffer === TARGET_PHRASE) {
        buffer = '';
        rememberDiscovery('museum');
        showToast({
          glyph: '🚪',
          title: "knock knock — who's there?",
          link: { href: '/museum/enter', label: '/museum/enter' },
        });
      }
    }
    document.addEventListener('keydown', onKey);

    return () => {
      document.removeEventListener('click', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, []);

  return null;
}
