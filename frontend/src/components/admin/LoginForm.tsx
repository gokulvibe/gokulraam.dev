import { useState } from 'react';
import { auth, ApiError } from '@/lib/api';

export default function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await auth.login(username, password);
      window.location.href = '/admin';
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError('Invalid credentials.');
      } else {
        setError('Login failed. Is the backend running?');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="game-card max-w-md p-8" style={{ '--card-bar': '#c9a96e' } as React.CSSProperties}>
      <span className="game-card__edge" aria-hidden></span>
      <span className="game-card__numeral">№ ∅ · admin</span>
      <span className="game-card__glyph">⛬</span>

      <header className="mb-6 mt-2">
        <p className="label" style={{ marginBottom: '0.4rem' }}>// sign in</p>
        <h1 className="display text-4xl">
          Open the<br />
          <span className="display-italic text-ember">folio.</span>
        </h1>
      </header>

      <div className="space-y-4">
        <label className="block">
          <span className="label block mb-1.5">username</span>
          <input
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="admin-input"
            required
          />
        </label>

        <label className="block">
          <span className="label block mb-1.5">password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="admin-input"
            required
          />
        </label>

        {error && (
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-rose">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting || !username || !password}
          className="admin-btn-primary w-full mt-2"
        >
          {submitting ? 'verifying…' : 'enter →'}
        </button>
      </div>

      <p className="mt-6 font-mono text-[10.5px] uppercase tracking-[0.18em] text-ghost">
        single-user folio · gokul only
      </p>
    </form>
  );
}
