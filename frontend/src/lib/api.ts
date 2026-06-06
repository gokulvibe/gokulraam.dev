/**
 * Tiny API client. All admin/TIL requests go through this.
 * Sends credentials so the auth cookie is included.
 */

const API_BASE = (import.meta.env.PUBLIC_API_BASE as string) ?? 'http://localhost:8000';

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new ApiError(res.status, text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// ─── Types (mirror backend Pydantic schemas) ──────────────────

export interface TilAttachment {
  id: number;
  filename: string;
  stored_path: string;
  mime_type: string;
  size_bytes: number;
}

export interface TilPost {
  id: number;
  slug: string;
  title: string;
  body_md: string;
  body_html: string;
  tags: string[];
  draft: boolean;
  created_at: string;
  updated_at: string;
  attachments: TilAttachment[];
}

// ─── Auth ──────────────────────────────────────────────────────

export const auth = {
  login: (username: string, password: string) =>
    request<{ status: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request<{ status: string }>('/api/auth/logout', { method: 'POST' }),
  me: () => request<{ username: string }>('/api/auth/me'),
  museumEnter: (code: string) =>
    request<{ status: string }>('/api/auth/museum-enter', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),
  museumLeave: () =>
    request<{ status: string }>('/api/auth/museum-leave', { method: 'POST' }),
};

// ─── Museum ────────────────────────────────────────────────────

export interface MuseumExhibit {
  id: number;
  slug: string;
  room_label: string;
  title: string;
  kicker: string;
  body_md: string;
  body_html: string;
  photo_url: string;
  photo_caption: string;
  order: number;
}

export const museum = {
  list: () => request<MuseumExhibit[]>('/api/museum'),
  update: (
    id: number,
    patch: Partial<Pick<MuseumExhibit, 'room_label' | 'title' | 'kicker' | 'body_md' | 'photo_url' | 'photo_caption'>>,
  ) =>
    request<MuseumExhibit>(`/api/museum/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
};

// ─── Photos ───────────────────────────────────────────────────

export interface Photo {
  id: number;
  slug: string;
  url: string;
  caption: string;
  taken_at: string;
  order: number;
}

export const photos = {
  list: () => request<Photo[]>('/api/photos'),
  create: (body: { url: string; caption?: string; taken_at?: string }) =>
    request<Photo>('/api/photos', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  upload: async (file: File, caption: string, taken_at: string): Promise<Photo> => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('caption', caption);
    fd.append('taken_at', taken_at);
    const res = await fetch(`${API_BASE}/api/photos/upload`, {
      method: 'POST',
      credentials: 'include',
      body: fd,
    });
    if (!res.ok) throw new ApiError(res.status, await res.text());
    return res.json();
  },
  update: (id: number, patch: Partial<Pick<Photo, 'url' | 'caption' | 'taken_at'>>) =>
    request<Photo>(`/api/photos/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
  remove: (id: number) => request<void>(`/api/photos/${id}`, { method: 'DELETE' }),
};

/** Resolve a Photo URL — locally-stored uploads have a `/uploads/…`
 * relative path and need the backend origin prefixed for the browser. */
export function resolvePhotoUrl(url: string): string {
  if (!url) return url;
  if (url.startsWith('/uploads/')) return `${API_BASE}${url}`;
  return url;
}

// ─── Books ────────────────────────────────────────────────────

export interface Book {
  id: number;
  slug: string;
  title: string;
  author: string;
  status: 'reading' | 'finished' | 'want' | string;
  year: string;
  link: string;
  cover_url: string;
  note: string;
  order: number;
}

export const books = {
  list: () => request<Book[]>('/api/books'),
  update: (
    id: number,
    patch: Partial<Pick<Book, 'title' | 'author' | 'status' | 'year' | 'link' | 'cover_url' | 'note'>>,
  ) =>
    request<Book>(`/api/books/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
};

// ─── Guestbook ────────────────────────────────────────────────

export interface GuestbookEntry {
  id: number;
  name: string;
  message: string;
  pinned: boolean;
  created_at: string;
}

export const guestbook = {
  list: () => request<GuestbookEntry[]>('/api/guestbook'),
  post: (body: { name: string; message: string; website: string }) =>
    request<GuestbookEntry>('/api/guestbook', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  setPinned: (id: number, pinned: boolean) =>
    request<GuestbookEntry>(`/api/guestbook/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ pinned }),
    }),
  remove: (id: number) =>
    request<void>(`/api/guestbook/${id}`, { method: 'DELETE' }),
};

// ─── Logbook ──────────────────────────────────────────────────

export interface LogbookEntry {
  id: number;
  body: string;
  tag: string;
  created_at: string;
}

export const logbook = {
  list: () => request<LogbookEntry[]>('/api/logbook'),
  create: (body: { body: string; tag: string }) =>
    request<LogbookEntry>('/api/logbook', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  update: (id: number, patch: Partial<Pick<LogbookEntry, 'body' | 'tag'>>) =>
    request<LogbookEntry>(`/api/logbook/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
  remove: (id: number) =>
    request<void>(`/api/logbook/${id}`, { method: 'DELETE' }),
};

// ─── TIL ───────────────────────────────────────────────────────

export const til = {
  list: (includeDrafts = false) =>
    request<TilPost[]>(`/api/til?include_drafts=${includeDrafts}`),
  get: (slug: string) => request<TilPost>(`/api/til/${slug}`),
  create: (body: {
    title: string;
    body_md: string;
    tags: string[];
    draft: boolean;
  }) =>
    request<TilPost>('/api/til', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  update: (id: number, body: Partial<{ title: string; body_md: string; tags: string[]; draft: boolean }>) =>
    request<TilPost>(`/api/til/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  remove: (id: number) =>
    request<void>(`/api/til/${id}`, { method: 'DELETE' }),
  upload: async (id: number, file: File): Promise<TilAttachment> => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/api/til/${id}/attachments`, {
      method: 'POST',
      credentials: 'include',
      body: fd,
    });
    if (!res.ok) throw new ApiError(res.status, await res.text());
    return res.json();
  },
  removeAttachment: (attachmentId: number) =>
    request<void>(`/api/til/attachments/${attachmentId}`, { method: 'DELETE' }),
};

export function uploadUrl(stored_path: string): string {
  return `${API_BASE}/uploads/${stored_path}`;
}

// ─── Now items ────────────────────────────────────────────────

export interface NowItem {
  slug: string;
  kind: string;
  label: string;
  value: string;
  order: number;
  updated_at: string;
}

export const now = {
  list: () => request<NowItem[]>('/api/now'),
  update: (slug: string, value: string) =>
    request<NowItem>(`/api/now/${slug}`, {
      method: 'PATCH',
      body: JSON.stringify({ value }),
    }),
};

// ─── Uses items ────────────────────────────────────────────────

export interface UsesItem {
  id: number;
  category: string;
  slug: string;
  name: string;
  note: string;
  order: number;
  updated_at: string;
}

export const uses = {
  list: () => request<UsesItem[]>('/api/uses'),
  update: (id: number, patch: { name?: string; note?: string }) =>
    request<UsesItem>(`/api/uses/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
};

// ─── Badminton ─────────────────────────────────────────────────

export interface BadmintonPlayer {
  id: number;
  slug: string;
  name: string;
  country: string;
  flag: string;
  discipline: string;
  next_event: string;
  order: number;
  updated_at: string;
}

export interface BadmintonTournament {
  id: number;
  slug: string;
  name: string;
  dates: string;
  location: string;
  tier: string;
  order: number;
  updated_at: string;
}

export const badminton = {
  players: () => request<BadmintonPlayer[]>('/api/badminton/players'),
  tournaments: () => request<BadmintonTournament[]>('/api/badminton/tournaments'),
  updatePlayer: (id: number, patch: Partial<Omit<BadmintonPlayer, 'id' | 'slug' | 'order' | 'updated_at'>>) =>
    request<BadmintonPlayer>(`/api/badminton/players/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
  updateTournament: (id: number, patch: Partial<Omit<BadmintonTournament, 'id' | 'slug' | 'order' | 'updated_at'>>) =>
    request<BadmintonTournament>(`/api/badminton/tournaments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
};

// ─── Generic patch (for the generic <EditableField> component) ──

export async function patchEntity(endpoint: string, field: string, value: string): Promise<void> {
  await request(endpoint, {
    method: 'PATCH',
    body: JSON.stringify({ [field]: value }),
  });
}

// ─── Analytics / stats (admin-only reads) ──────────────────────

export interface StatsSummary {
  total_views: number;
  last_7_days: number;
  last_30_days: number;
  last_24_hours: number;
  unique_paths: number;
  first_view_at: string | null;
}
export interface DailyView { date: string; count: number; }
export interface TopPath { path: string; count: number; }
export interface TopReferrer { host: string; count: number; }
export interface PageViewRow {
  path: string;
  referrer: string;
  user_agent: string;
  created_at: string;
}

export const stats = {
  summary: () => request<StatsSummary>('/api/stats/summary'),
  daily: (days = 30) => request<DailyView[]>(`/api/stats/daily?days=${days}`),
  topPaths: (limit = 20) => request<TopPath[]>(`/api/stats/top-paths?limit=${limit}`),
  topReferrers: (limit = 15) => request<TopReferrer[]>(`/api/stats/top-referrers?limit=${limit}`),
  recent: (limit = 50) => request<PageViewRow[]>(`/api/stats/recent?limit=${limit}`),
};

// ─── Search ─────────────────────────────────────────────────────

export interface SearchHit {
  group: string;
  title: string;
  subtitle: string;
  href: string;
  score: number;
}
export interface SearchResponse {
  query: string;
  hits: SearchHit[];
}

export const search = {
  query: (q: string) =>
    request<SearchResponse>(`/api/search?q=${encodeURIComponent(q)}`),
};

// ─── LeetCode profile cache ─────────────────────────────────

export interface LeetcodeStats {
  username: string;
  total_solved: number;
  easy_solved: number;
  medium_solved: number;
  hard_solved: number;
  streak_days: number;
  total_active_days: number;
  ranking: number;
  last_synced_at: string | null;
  last_error: string;
}

export const leetcode = {
  get: () => request<LeetcodeStats>('/api/leetcode'),
  setUsername: (username: string) =>
    request<LeetcodeStats>('/api/leetcode', {
      method: 'PATCH',
      body: JSON.stringify({ username }),
    }),
  refresh: () =>
    request<LeetcodeStats>('/api/leetcode/refresh', { method: 'POST' }),
};

// ─── Live status ─────────────────────────────────────────────

export interface LiveStatus {
  state: string;
  detail: string;
  started_at: string;
  last_seen_at: string;
  age_seconds: number;
  aliveness: 'live' | 'idle' | 'away';
}

export const status = {
  get: () => request<LiveStatus>('/api/status'),
  ping: (state: string, detail = '') =>
    request<LiveStatus>('/api/status', {
      method: 'POST',
      body: JSON.stringify({ state, detail }),
    }),
};
