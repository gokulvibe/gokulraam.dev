import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import Placeholder from '@tiptap/extension-placeholder';
import { Markdown } from 'tiptap-markdown';

import { useState } from 'react';
import { til } from '@/lib/api';
import { useIsAdmin } from './useIsAdmin';
import EditorToolbar from './EditorToolbar';

interface Props {
  postId: number;
  initialMd: string;
  initialHtml: string;
}

export default function EditableBody({ postId, initialMd, initialHtml }: Props) {
  const isAdmin = useIsAdmin();
  const [editing, setEditing] = useState(false);
  const [html, setHtml] = useState(initialHtml);
  const [md, setMd] = useState(initialMd);
  const [status, setStatus] = useState('');

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
      Link.configure({ openOnClick: false, autolink: true }),
      Image,
      Placeholder.configure({
        placeholder: 'Write your note. Toolbar above for headings, lists, code, and links.',
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

  function start() {
    if (!isAdmin) return;
    editor?.commands.setContent(md ?? '');
    setEditing(true);
  }

  async function save() {
    if (!editor) return;
    // @ts-expect-error tiptap-markdown adds this storage
    const next = editor.storage.markdown.getMarkdown() as string;
    setStatus('saving…');
    try {
      const updated = await til.update(postId, { body_md: next });
      setMd(updated.body_md);
      setHtml(updated.body_html);
      setStatus('');
      setEditing(false);
    } catch {
      setStatus('save failed');
    }
  }

  function cancel() {
    editor?.commands.setContent(md ?? '');
    setEditing(false);
    setStatus('');
  }

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
    <div>
      <EditorToolbar editor={editor} />
      <div className="tt-editor">
        <EditorContent editor={editor} />
      </div>
      <div className="editable-row">
        <button type="button" className="save" onClick={save}>
          save body
        </button>
        <button type="button" className="cancel" onClick={cancel}>
          cancel
        </button>
        {status && <span className="editable-row__status">{status}</span>}
      </div>
    </div>
  );
}
