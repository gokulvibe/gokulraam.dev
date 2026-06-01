import { useState } from 'react';
import { auth, ApiError } from '@/lib/api';

export default function MuseumEnterForm() {
  const [code, setCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await auth.museumEnter(code);
      window.location.href = '/museum';
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError('Wrong code.');
      } else if (err instanceof ApiError && err.status === 503) {
        setError('The museum is not open yet.');
      } else {
        setError('Could not verify. Backend reachable?');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="museum-enter">
      <label className="museum-enter__label" htmlFor="museum-code">
        the code
      </label>
      <input
        id="museum-code"
        type="password"
        autoComplete="off"
        spellCheck={false}
        value={code}
        onChange={(e) => setCode(e.target.value)}
        className="museum-enter__input"
        placeholder="…"
        autoFocus
      />
      {error && <p className="museum-enter__error">{error}</p>}
      <button type="submit" disabled={submitting || !code} className="museum-enter__btn">
        {submitting ? 'opening…' : 'open the door'}
      </button>
    </form>
  );
}
