/**
 * Live "currently" status chip — polls /api/status every 30s.
 * Renders nothing for the initial 'away' state until the first ping ever arrives.
 *
 * Props:
 *   variant: 'inline' (single chip) | 'card' (with duration + detail)
 */

import { useEffect, useState } from 'react';
import { status, type LiveStatus as LS } from '@/lib/api';

interface Props {
  variant?: 'inline' | 'card';
  /** Hide the component entirely if the user has never pinged. Default: true. */
  hideIfNever?: boolean;
}

const POLL_MS = 30_000;

function fmtDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const hrs = Math.floor(mins / 60);
  return `${hrs}h ${mins % 60}m`;
}

function ageLabel(age: number): string {
  if (age < 60) return 'just now';
  if (age < 3600) return `${Math.floor(age / 60)} min ago`;
  if (age < 86400) return `${Math.floor(age / 3600)}h ago`;
  return `${Math.floor(age / 86400)}d ago`;
}

export default function LiveStatus({ variant = 'inline', hideIfNever = true }: Props) {
  const [data, setData] = useState<LS | null>(null);

  useEffect(() => {
    let alive = true;
    async function pull() {
      try {
        const s = await status.get();
        if (alive) setData(s);
      } catch {
        if (alive) setData(null);
      }
    }
    void pull();
    const interval = setInterval(pull, POLL_MS);
    return () => {
      alive = false;
      clearInterval(interval);
    };
  }, []);

  if (!data) return null;
  // Treat ridiculous ages (never been pinged) as 'no status'
  if (hideIfNever && data.age_seconds > 90 * 86400) return null;

  const aliveness = data.aliveness;
  const dotClass = `live-status__dot live-status__dot--${aliveness}`;

  if (variant === 'inline') {
    return (
      <span className="live-status live-status--inline">
        <span className={dotClass} />
        <span className="live-status__state">{data.state}</span>
        {data.detail && (
          <span className="live-status__detail">· {data.detail}</span>
        )}
      </span>
    );
  }

  // Card variant
  const startedAt = new Date(data.started_at);
  const durationS = Math.max(0, Math.round((Date.now() - startedAt.getTime()) / 1000));

  return (
    <div className="live-status live-status--card">
      <div className="live-status__head">
        <span className={dotClass} />
        <span className="live-status__aliveness">{aliveness}</span>
        <span className="live-status__age">· {ageLabel(data.age_seconds)}</span>
      </div>
      <p className="live-status__line">
        <span className="live-status__state">{data.state}</span>
        {aliveness === 'live' && (
          <span className="live-status__duration"> · {fmtDuration(durationS)}</span>
        )}
      </p>
      {data.detail && <p className="live-status__detail">{data.detail}</p>}
    </div>
  );
}
