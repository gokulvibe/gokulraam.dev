import type { Editor } from '@tiptap/react';

interface Props {
  editor: Editor | null;
}

export default function EditorToolbar({ editor }: Props) {
  if (!editor) return null;

  const tool = (props: {
    label: string;
    title?: string;
    onClick: () => void;
    active?: boolean;
    disabled?: boolean;
  }) => (
    <button
      type="button"
      className={`tt-tool ${props.active ? 'is-active' : ''}`}
      onClick={props.onClick}
      disabled={props.disabled}
      title={props.title ?? props.label}
    >
      {props.label}
    </button>
  );

  return (
    <div className="tt-toolbar" role="toolbar" aria-label="Editor formatting">
      {tool({
        label: 'H1',
        onClick: () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
        active: editor.isActive('heading', { level: 1 }),
      })}
      {tool({
        label: 'H2',
        onClick: () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
        active: editor.isActive('heading', { level: 2 }),
      })}
      {tool({
        label: 'H3',
        onClick: () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
        active: editor.isActive('heading', { level: 3 }),
      })}

      <span className="tt-divider" />

      {tool({
        label: 'B',
        title: 'Bold (⌘B)',
        onClick: () => editor.chain().focus().toggleBold().run(),
        active: editor.isActive('bold'),
      })}
      {tool({
        label: 'I',
        title: 'Italic (⌘I)',
        onClick: () => editor.chain().focus().toggleItalic().run(),
        active: editor.isActive('italic'),
      })}
      {tool({
        label: 'S',
        title: 'Strikethrough',
        onClick: () => editor.chain().focus().toggleStrike().run(),
        active: editor.isActive('strike'),
      })}

      <span className="tt-divider" />

      {tool({
        label: '• list',
        onClick: () => editor.chain().focus().toggleBulletList().run(),
        active: editor.isActive('bulletList'),
      })}
      {tool({
        label: '1. list',
        onClick: () => editor.chain().focus().toggleOrderedList().run(),
        active: editor.isActive('orderedList'),
      })}
      {tool({
        label: '" quote',
        onClick: () => editor.chain().focus().toggleBlockquote().run(),
        active: editor.isActive('blockquote'),
      })}

      <span className="tt-divider" />

      {tool({
        label: '< code >',
        title: 'Inline code',
        onClick: () => editor.chain().focus().toggleCode().run(),
        active: editor.isActive('code'),
      })}
      {tool({
        label: '{ block }',
        title: 'Code block',
        onClick: () => editor.chain().focus().toggleCodeBlock().run(),
        active: editor.isActive('codeBlock'),
      })}

      <span className="tt-divider" />

      {tool({
        label: '⌘ link',
        onClick: () => {
          const prev = editor.getAttributes('link').href as string | undefined;
          const url = window.prompt('URL', prev ?? 'https://');
          if (url === null) return;
          if (url === '') {
            editor.chain().focus().unsetLink().run();
            return;
          }
          editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
        },
        active: editor.isActive('link'),
      })}
      {tool({
        label: '⌥ image',
        onClick: () => {
          const url = window.prompt('Image URL');
          if (url) editor.chain().focus().setImage({ src: url }).run();
        },
      })}
      {tool({
        label: '— rule',
        onClick: () => editor.chain().focus().setHorizontalRule().run(),
      })}

      <span className="tt-divider" />

      {tool({
        label: '↶ undo',
        onClick: () => editor.chain().focus().undo().run(),
        disabled: !editor.can().undo(),
      })}
      {tool({
        label: '↷ redo',
        onClick: () => editor.chain().focus().redo().run(),
        disabled: !editor.can().redo(),
      })}
    </div>
  );
}
