/**
 * Tiny ambient-music player that appears only in the "Daylight" light theme.
 *
 * Behaviour:
 *  - Looks for /audio/ambient.mp3 (drop your track there)
 *  - If found, click to play/pause. Volume defaults to 30%, persisted.
 *  - If missing, shows a soft "no track loaded" hint instead of erroring.
 *  - Auto-pauses when the browser tab is hidden, resumes on return.
 *  - Never autoplays — browsers block that anyway.
 */

import { useEffect, useRef, useState } from 'react';

const SRC = '/audio/ambient.mp3';
const STORAGE_KEY = 'ambient.muted';

export default function AmbientPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [playing, setPlaying] = useState(false);

  // On mount, do a HEAD request to confirm the file exists. Don't preload audio.
  useEffect(() => {
    let alive = true;
    fetch(SRC, { method: 'HEAD' })
      .then((r) => {
        if (alive) setAvailable(r.ok);
      })
      .catch(() => {
        if (alive) setAvailable(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  // Pause on tab hide; resume on tab return only if user had it playing
  useEffect(() => {
    function onVisibility() {
      const el = audioRef.current;
      if (!el) return;
      if (document.hidden) {
        el.pause();
      } else if (playing) {
        void el.play().catch(() => undefined);
      }
    }
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, [playing]);

  async function toggle() {
    if (!available) return;
    const el = audioRef.current;
    if (!el) return;
    if (el.paused) {
      try {
        el.volume = 0.3;
        await el.play();
        setPlaying(true);
        try {
          localStorage.setItem(STORAGE_KEY, 'false');
        } catch {
          /* ignore */
        }
      } catch {
        setPlaying(false);
      }
    } else {
      el.pause();
      setPlaying(false);
      try {
        localStorage.setItem(STORAGE_KEY, 'true');
      } catch {
        /* ignore */
      }
    }
  }

  // Render the chip regardless — but content differs by availability
  return (
    <button
      type="button"
      className="ambient-player"
      onClick={toggle}
      disabled={available === false}
      title={available === false ? 'No ambient track loaded' : playing ? 'Pause ambient music' : 'Play ambient music'}
    >
      <span className="ap-icon">{playing ? '❚❚' : '♪'}</span>
      <span>{playing ? 'now playing' : 'play ambient'}</span>
      {available === false && (
        <span className="ap-state">— add /audio/ambient.mp3</span>
      )}
      {available && <audio ref={audioRef} src={SRC} loop preload="none" />}
    </button>
  );
}
