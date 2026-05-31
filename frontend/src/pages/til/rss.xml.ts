import rss from '@astrojs/rss';
import type { APIRoute } from 'astro';

export const prerender = false;

const API_BASE = import.meta.env.PUBLIC_API_BASE ?? 'http://localhost:8000';
const SITE = 'https://gokulraam.dev';

interface TilSummary {
  id: number;
  slug: string;
  title: string;
  body_html: string;
  tags: string[];
  draft: boolean;
  created_at: string;
}

export const GET: APIRoute = async () => {
  let posts: TilSummary[] = [];
  try {
    const res = await fetch(`${API_BASE}/api/til`);
    if (res.ok) posts = await res.json();
  } catch {
    posts = [];
  }

  return rss({
    title: 'Gokul Raam — Today I Learnt',
    description: 'A microblog of small things learned working with Python, Postgres, Redis, and whatever else is biting me this week.',
    site: SITE,
    items: posts
      .filter((p) => !p.draft)
      .map((p) => ({
        title: p.title,
        link: `/til/${p.slug}/`,
        pubDate: new Date(p.created_at),
        description: p.body_html
          ? p.body_html
              .replace(/<[^>]+>/g, ' ')
              .replace(/\s+/g, ' ')
              .trim()
              .slice(0, 280) + (p.body_html.length > 280 ? '…' : '')
          : '',
        content: p.body_html,
        categories: p.tags,
      })),
    customData: '<language>en-us</language>',
    stylesheet: false,
  });
};
