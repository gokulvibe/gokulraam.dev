from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin


_md = (
    MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
    .enable(["table", "strikethrough"])
    .use(front_matter_plugin)
)


def render_markdown(text: str) -> str:
    return _md.render(text or "")
