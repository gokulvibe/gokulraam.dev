/**
 * Sound toggle — top-right, next to ThemeToggle.
 *
 * Persists to localStorage('sound') and mirrors the value onto
 * `<html data-sound="on|off">`. EasterEggs.tsx and any other audio
 * source checks that attribute before firing a sound or haptic.
 *
 * The pre-paint script in Base.astro sets the attribute before
 * first render so the button matches state without a flash.
 */

import { useEffect, useState } from 'react';

type SoundState = 'on' | 'off';

function readInitial(): SoundState {
  if (typeof document === 'undefined') return 'on';
  const attr = document.documentElement.getAttribute('data-sound');
  return attr === 'off' ? 'off' : 'on';
}

export default function SoundToggle() {
  const [state, setState] = useState<SoundState>(readInitial);

  useEffect(() => {
    document.documentElement.setAttribute('data-sound', state);
    try {
      localStorage.setItem('sound', state);
    } catch {
      /* localStorage disabled — fine */
    }
  }, [state]);

  function toggle() {
    setState((s) => (s === 'on' ? 'off' : 'on'));
  }

  const muted = state === 'off';
  return (
    <button
      type="button"
      className={`sound-toggle ${muted ? 'is-muted' : ''}`}
      onClick={toggle}
      aria-label={muted ? 'Unmute sound effects' : 'Mute sound effects'}
      title={muted ? 'Unmute sound effects' : 'Mute sound effects'}
    >
      ♪
    </button>
  );
}
