import { useRef, useState } from 'react';
import { til, type TilAttachment } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';

const API_BASE = (import.meta.env.PUBLIC_API_BASE as string) ?? 'http://localhost:8000';

interface Props {
  postId: number;
  initial: TilAttachment[];
}

const codeExts = new Set([
  'py', 'sql', 'js', 'ts', 'jsx', 'tsx', 'go', 'rs', 'rb',
  'java', 'c', 'cpp', 'h', 'sh', 'yaml', 'yml', 'json', 'toml',
]);
const imageExts = new Set(['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg']);

function classify(a: TilAttachment): 'code' | 'image' | 'doc' {
  const ext = a.filename.split('.').pop()?.toLowerCase() ?? '';
  if (a.mime_type.startsWith('image/') || imageExts.has(ext)) return 'image';
  if (codeExts.has(ext) || a.mime_type.startsWith('text/')) return 'code';
  return 'doc';
}

function fmtSize(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function EditableAttachments({ postId, initial }: Props) {
  const isAdmin = useIsAdmin();
  const [items, setItems] = useState<TilAttachment[]>(initial);
  const [isOver, setIsOver] = useState(false);
  const [uploading, setUploading] = useState(0);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(files: FileList | File[]) {
    setError('');
    const arr = Array.from(files);
    setUploading(arr.length);
    for (const f of arr) {
      try {
        const att = await til.upload(postId, f);
        setItems((prev) => [...prev, att]);
      } catch {
        setError(`Upload failed for ${f.name}.`);
      } finally {
        setUploading((u) => u - 1);
      }
    }
  }

  async function remove(att: TilAttachment) {
    if (!confirm(`Remove "${att.filename}"?`)) return;
    try {
      await til.removeAttachment(att.id);
      setItems((prev) => prev.filter((x) => x.id !== att.id));
    } catch {
      setError('Delete failed.');
    }
  }

  // ─── Render ─────────────────────────────────────────────────────
  if (items.length === 0 && !isAdmin) return null;

  return (
    <section className="mt-16 border-t border-rule pt-10">
      <p className="label mb-5">// attachments</p>

      {items.length > 0 ? (
        <div className="space-y-5 mb-6">
          {items.map((a) => (
            <AttachmentTile key={a.id} a={a} canDelete={!!isAdmin} onDelete={() => remove(a)} />
          ))}
        </div>
      ) : (
        isAdmin && (
          <p className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-mist mb-6">
            no attachments yet
          </p>
        )
      )}

      {isAdmin && (
        <div>
          <div
            className={`dropzone ${isOver ? 'is-over' : ''}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setIsOver(true);
            }}
            onDragLeave={() => setIsOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsOver(false);
              if (e.dataTransfer.files.length > 0) void handleFiles(e.dataTransfer.files);
            }}
            role="button"
            tabIndex={0}
          >
            <p className="font-display text-base text-cream">
              drop files here, or click to choose
            </p>
            <p className="mt-1 font-mono text-[10.5px] uppercase tracking-[0.16em] text-mist">
              any type · 10 MB cap per file
            </p>
            <input
              ref={inputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
            />
          </div>
          {uploading > 0 && (
            <p className="mt-2 font-mono text-[10.5px] uppercase tracking-[0.16em] text-ember">
              uploading {uploading} file{uploading > 1 ? 's' : ''}…
            </p>
          )}
          {error && (
            <p className="mt-2 font-mono text-[10.5px] uppercase tracking-[0.16em] text-rose">
              {error}
            </p>
          )}
        </div>
      )}
    </section>
  );
}

function AttachmentTile({
  a,
  canDelete,
  onDelete,
}: {
  a: TilAttachment;
  canDelete: boolean;
  onDelete: () => void;
}) {
  const kind = classify(a);
  const [code, setCode] = useState<string | null>(null);

  // Lazy-load code content
  if (kind === 'code' && code === null) {
    void fetch(`${API_BASE}/uploads/${a.stored_path}`)
      .then((r) => (r.ok ? r.text() : ''))
      .then(setCode)
      .catch(() => setCode(''));
  }

  return (
    <div className="rounded-md border border-rule bg-smoke/40 p-4">
      <div className="flex items-baseline justify-between gap-3 mb-3">
        <p className="font-display text-base text-cream">{a.filename}</p>
        <div className="flex items-center gap-3">
          <p className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-mist">
            {a.mime_type.split('/').pop()} · {fmtSize(a.size_bytes)}
          </p>
          {canDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-rose hover:opacity-80"
              title="Remove attachment"
            >
              remove
            </button>
          )}
        </div>
      </div>
      {kind === 'image' && (
        <img
          src={`${API_BASE}/uploads/${a.stored_path}`}
          alt={a.filename}
          className="rounded-md max-w-full"
        />
      )}
      {kind === 'code' && code && (
        <pre className="overflow-x-auto rounded bg-void p-4 text-sm leading-relaxed text-cream">
          <code>{code}</code>
        </pre>
      )}
      {(kind === 'doc' || (kind === 'code' && code === '')) && (
        <a
          href={`${API_BASE}/uploads/${a.stored_path}`}
          target="_blank"
          rel="noopener"
          className="chip-accent"
        >
          download ↓
        </a>
      )}
    </div>
  );
}
