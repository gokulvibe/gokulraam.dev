import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import Placeholder from '@tiptap/extension-placeholder';
import { Markdown } from 'tiptap-markdown';

import { useEffect, useRef, useState } from 'react';
import { til } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';
import EditorToolbar from './EditorToolbar';

interface Props {
  postId: number;
  initialMd: string;
  initialHtml: string;
}

// ─── Local-storage autosave ─────────────────────────────────────
//
// While the editor is open and dirty we periodically stash the current
// markdown to localStorage. If the user reloads, navigates away and back, or
// crashes their browser, the next time the editor mounts we offer to restore.
// Once a real save lands, we drop the local copy.

const AUTOSAVE_INTERVAL_MS = 5000;
const draftKey = (id: number) => `til.draft.${id}`;

interface LocalDraft {
  md: string;
  savedAt: number;
}

function readDraft(id: number): LocalDraft | null {
  try {
    const raw = localStorage.getItem(draftKey(id));
    return raw ? (JSON.parse(raw) as LocalDraft) : null;
  } catch {
    return null;
  }
}
function writeDraft(id: number, md: string) {
  try {
    localStorage.setItem(draftKey(id), JSON.stringify({ md, savedAt: Date.now() } satisfies LocalDraft));
  } catch {
    /* quota / disabled — fine */
  }
}
function clearDraft(id: number) {
  try { localStorage.removeItem(draftKey(id)); } catch { /* ignore */ }
}

export default function EditableBody({ postId, initialMd, initialHtml }: Props) {
  const isAdmin = useIsAdmin();
  const [editing, setEditing] = useState(false);
  const [html, setHtml] = useState(initialHtml);
  const [md, setMd] = useState(initialMd);
  const [status, setStatus] = useState('');
  const [autosavedAt, setAutosavedAt] = useState<number | null>(null);
  const autosaveTimer = useRef<number | null>(null);

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
      Link.configure({ openOnClick: false, autolink: true }),
      Image,
      Placeholder.configure({
        placeholder: 'Write your note. Toolbar above for headings, lists, code, and links. ⌘S to save.',
      }),
      Markdown.configure({
        html: false,
        tightLists: true,
        bulletListMarker: '-',
        linkify: true,
        breaks: false,
      }),
    ],
    content: md ?? '',
  });

  // On mount as admin: if a local draft exists for this post AND it differs
  // from the server's body, offer to restore. We only nudge once per session.
  useEffect(() => {
    if (!isAdmin) return;
    const draft = readDraft(postId);
    if (!draft || !draft.md) return;
    if (draft.md.trim() === (initialMd ?? '').trim()) {
      // Stale draft matches server — drop it silently.
      clearDraft(postId);
      return;
    }
    const ageMin = Math.round((Date.now() - draft.savedAt) / 60000);
    const restore = confirm(
      `Found an unsaved draft for this post (${ageMin} min old).\n\nRestore it?\n\n` +
      `OK = open the editor with your draft.\nCancel = discard the draft and use the saved version.`
    );
    if (restore) {
      setMd(draft.md);
      editor?.commands.setContent(draft.md);
      setEditing(true);
    } else {
      clearDraft(postId);
    }
    // We deliberately don't depend on `editor` to avoid re-firing when it
    // becomes available later — the setContent in the truthy branch is gated
    // on editor existing the first time around. If it's null we just set md
    // and let the next mount pick it up.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postId, isAdmin]);

  function getCurrentMd(): string {
    if (!editor) return '';
    // @ts-expect-error tiptap-markdown adds this storage
    return editor.storage.markdown.getMarkdown() as string;
  }

  function start() {
    if (!isAdmin) return;
    editor?.commands.setContent(md ?? '');
    setEditing(true);
  }

  async function save() {
    if (!editor) return;
    const next = getCurrentMd();
    setStatus('saving…');
    try {
      const updated = await til.update(postId, { body_md: next });
      setMd(updated.body_md);
      setHtml(updated.body_html);
      setStatus('');
      setEditing(false);
      clearDraft(postId);
    } catch {
      setStatus('save failed');
    }
  }

  function cancel() {
    if (!editor) return;
    const current = getCurrentMd();
    if (current.trim() !== (md ?? '').trim()) {
      if (!confirm('Discard your unsaved changes?')) return;
    }
    editor.commands.setContent(md ?? '');
    setEditing(false);
    setStatus('');
    clearDraft(postId);
  }

  // ⌘S / Ctrl+S → save. Only fires while editor is active to avoid hijacking
  // the browser's save-page shortcut on read-only views.
  useEffect(() => {
    if (!editing) return;
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        void save();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editing, editor]);

  // Autosave to localStorage every 5s while editing.
  useEffect(() => {
    if (!editing || !editor) {
      if (autosaveTimer.current) {
        window.clearInterval(autosaveTimer.current);
        autosaveTimer.current = null;
      }
      return;
    }
    autosaveTimer.current = window.setInterval(() => {
      const current = getCurrentMd();
      if (current.trim() === (md ?? '').trim()) return;  // not dirty
      writeDraft(postId, current);
      setAutosavedAt(Date.now());
    }, AUTOSAVE_INTERVAL_MS);
    return () => {
      if (autosaveTimer.current) {
        window.clearInterval(autosaveTimer.current);
        autosaveTimer.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editing, editor, postId, md]);

  // Confirm before unloading the tab with unsaved changes.
  useEffect(() => {
    if (!editing) return;
    function beforeUnload(e: BeforeUnloadEvent) {
      const current = getCurrentMd();
      if (current.trim() === (md ?? '').trim()) return;
      e.preventDefault();
      e.returnValue = '';
    }
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editing, md]);

  if (!isAdmin || !editing) {
    return (
      <div
        className={isAdmin ? 'editable editable--admin' : ''}
        onClick={start}
        title={isAdmin ? 'Click to edit body' : undefined}
      >
        <div className="prose" dangerouslySetInnerHTML={{ __html: html || '<p class="text-mist italic">No content yet — click to write.</p>' }} />
        {isAdmin && <span className="editable__pencil" aria-hidden>✏</span>}
      </div>
    );
  }

  return (
    <div
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <EditorToolbar editor={editor} />
      <div className="tt-editor">
        <EditorContent editor={editor} />
      </div>
      <div className="editable-row">
        <button type="button" className="save" onClick={save} title="Save (⌘S)">
          save body <kbd className="ml-1 opacity-70">⌘S</kbd>
        </button>
        <button type="button" className="cancel" onClick={cancel}>
          cancel
        </button>
        {status && <span className="editable-row__status">{status}</span>}
        {!status && autosavedAt && (
          <span className="editable-row__status" title="Saved locally to your browser">
            autosaved · {new Date(autosavedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        )}
      </div>
    </div>
  );
}
