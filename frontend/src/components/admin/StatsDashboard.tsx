/**
 * /admin/stats dashboard. Admin-only — fetches all data client-side with
 * credentials. Falls back to a graceful "not authorized" / "loading" state.
 */

import { useEffect, useState } from 'react';
import {
  stats,
  type StatsSummary,
  type DailyView,
  type TopPath,
  type TopReferrer,
  type PageViewRow,
  ApiError,
} from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

function fmtNumber(n: number) {
  if (n < 1000) return n.toString();
  if (n < 1_000_000) return (n / 1000).toFixed(n < 10_000 ? 1 : 0) + 'k';
  return (n / 1_000_000).toFixed(1) + 'M';
}

function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

function shortUA(ua: string): string {
  if (!ua) return '';
  if (ua.includes('Firefox/')) return 'Firefox';
  if (ua.includes('Edg/')) return 'Edge';
  if (ua.includes('Chrome/')) return 'Chrome';
  if (ua.includes('Safari/')) return 'Safari';
  if (ua.includes('curl/')) return 'curl';
  if (ua.includes('bot') || ua.includes('Bot')) return 'bot';
  return 'other';
}

export default function StatsDashboard() {
  const isAdmin = useIsAdmin();
  const [data, setData] = useState<{
    summary: StatsSummary;
    daily: DailyView[];
    paths: TopPath[];
    referrers: TopReferrer[];
    recent: PageViewRow[];
  } | null>(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (isAdmin === false) {
      window.location.href = '/admin/login';
      return;
    }
    if (isAdmin !== true) return;

    let alive = true;
    Promise.all([
      stats.summary(),
      stats.daily(30),
      stats.topPaths(15),
      stats.topReferrers(10),
      stats.recent(40),
    ])
      .then(([summary, daily, paths, referrers, recent]) => {
        if (alive) setData({ summary, daily, paths, referrers, recent });
      })
      .catch((e: unknown) => {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401) {
          window.location.href = '/admin/login';
          return;
        }
        setErr('Could not load stats. Backend reachable?');
      });

    return () => { alive = false; };
  }, [isAdmin]);

  if (isAdmin !== true && !data) {
    return (
      <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-mist">
        verifying session…
      </p>
    );
  }
  if (err) {
    return <p className="font-mono text-[12px] uppercase tracking-[0.16em] text-rose">{err}</p>;
  }
  if (!data) {
    return (
      <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-mist">
        loading stats…
      </p>
    );
  }

  const { summary, daily, paths, referrers, recent } = data;
  const dailyMax = Math.max(1, ...daily.map((d) => d.count));
  const totalReferrers = referrers.reduce((s, r) => s + r.count, 0) || 1;
  const totalPathHits = paths.reduce((s, p) => s + p.count, 0) || 1;

  return (
    <div className="space-y-10">
      {/* Stat tiles */}
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile label="total views" value={fmtNumber(summary.total_views)} />
        <StatTile label="last 30 days" value={fmtNumber(summary.last_30_days)} />
        <StatTile label="last 7 days" value={fmtNumber(summary.last_7_days)} />
        <StatTile label="last 24h" value={fmtNumber(summary.last_24_hours)} />
      </section>

      {/* Daily chart */}
      <section>
        <p className="label mb-4">// daily views · last 30 days</p>
        <div className="stat-chart">
          {daily.map((d) => {
            const h = Math.max(2, Math.round((d.count / dailyMax) * 100));
            return (
              <div
                key={d.date}
                className={`stat-chart__bar ${d.count > 0 ? 'is-data' : ''}`}
                style={{ height: `${h}%` }}
                title={`${d.date} · ${d.count}`}
              />
            );
          })}
        </div>
        <p className="mt-2 font-mono text-[10.5px] uppercase tracking-[0.16em] text-ghost">
          {daily[0]?.date} → {daily[daily.length - 1]?.date} · peak {dailyMax}
        </p>
      </section>

      {/* Side-by-side top paths + referrers */}
      <section className="grid gap-8 md:grid-cols-2">
        <div>
          <p className="label mb-4">// top paths</p>
          {paths.length === 0 ? (
            <p className="font-mono text-[11px] text-mist">no data yet</p>
          ) : (
            <ul className="space-y-1.5">
              {paths.map((p) => (
                <li key={p.path} className="stat-row">
                  <span className="stat-row__bar" style={{ width: `${(p.count / totalPathHits) * 100}%` }} />
                  <span className="stat-row__label truncate font-mono">{p.path}</span>
                  <span className="stat-row__count">{fmtNumber(p.count)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <p className="label mb-4">// top referrers</p>
          {referrers.length === 0 ? (
            <p className="font-mono text-[11px] text-mist">no data yet</p>
          ) : (
            <ul className="space-y-1.5">
              {referrers.map((r) => (
                <li key={r.host} className="stat-row">
                  <span className="stat-row__bar" style={{ width: `${(r.count / totalReferrers) * 100}%` }} />
                  <span className="stat-row__label truncate font-display">{r.host}</span>
                  <span className="stat-row__count">{fmtNumber(r.count)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* Recent feed */}
      <section>
        <p className="label mb-4">// recent · last 40 views</p>
        {recent.length === 0 ? (
          <p className="font-mono text-[11px] text-mist">nothing yet — share your URL</p>
        ) : (
          <ul className="space-y-1">
            {recent.map((r, i) => (
              <li key={i} className="stat-recent">
                <span className="font-mono text-[10.5px] text-ghost shrink-0 w-16">{timeAgo(r.created_at)}</span>
                <a href={r.path} className="font-mono text-[12px] text-cream truncate hover:text-ember flex-1">
                  {r.path}
                </a>
                {r.referrer && (
                  <span className="font-mono text-[10px] text-mist truncate hidden md:inline-block max-w-[200px]">
                    ← {(() => {
                      try {
                        return new URL(r.referrer).host;
                      } catch {
                        return r.referrer.slice(0, 30);
                      }
                    })()}
                  </span>
                )}
                <span className="font-mono text-[10px] text-ghost shrink-0">{shortUA(r.user_agent)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {summary.first_view_at && (
        <p className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-ghost">
          tracking since · {new Date(summary.first_view_at).toLocaleDateString('en-US', {
            day: '2-digit', month: 'short', year: 'numeric',
          })}
        </p>
      )}
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="card !p-5">
      <p className="font-display text-3xl text-ember">{value}</p>
      <p className="label mt-1">{label}</p>
    </div>
  );
}
