/**
 * Compact LeetCode card for non-/now placements (e.g. homepage tail).
 * Shows on one line: streak + total solved + difficulty split, with a
 * small link to the profile.
 *
 * Renders nothing when there's no data yet (no username configured,
 * or pre-first-sync) so the homepage never carries a blank slot.
 * Honors the same SoundToggle / theme / etc. as the rest of the site.
 */

import { useEffect, useState } from 'react';
import { leetcode, type LeetcodeStats } from '@/lib/api';

export default function LeetcodeMiniCard() {
  const [stats, setStats] = useState<LeetcodeStats | null>(null);

  useEffect(() => {
    let alive = true;
    leetcode
      .get()
      .then((s) => alive && setStats(s))
      .catch(() => alive && setStats(null));
    return () => { alive = false; };
  }, []);

  if (!stats) return null;
  const hasName = (stats.username || '').trim().length > 0;
  const hasData = stats.total_solved > 0 || stats.streak_days > 0;
  if (!hasName || !hasData) return null;

  return (
    <a
      href={`https://leetcode.com/${stats.username}`}
      className="leetcode-mini"
      target="_blank"
      rel="noopener"
      title={`Solving on LeetCode · last synced ${stats.last_synced_at ? new Date(stats.last_synced_at).toLocaleDateString() : 'never'}`}
    >
      <span className="leetcode-mini__label">// solving</span>
      <span className="leetcode-mini__primary">
        <strong>{stats.streak_days}</strong>
        <span className="leetcode-mini__unit">day{stats.streak_days === 1 ? '' : 's'}</span>
      </span>
      <span className="leetcode-mini__sep">·</span>
      <span className="leetcode-mini__primary">
        <strong>{stats.total_solved}</strong>
        <span className="leetcode-mini__unit">solved</span>
      </span>
      <span className="leetcode-mini__split">
        {stats.easy_solved}E / {stats.medium_solved}M / {stats.hard_solved}H
      </span>
      <span className="leetcode-mini__handle">
        leetcode · {stats.username} ↗
      </span>
    </a>
  );
}
