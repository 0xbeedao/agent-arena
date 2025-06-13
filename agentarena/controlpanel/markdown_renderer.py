from io import StringIO
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit.formatted_text import ANSI, to_formatted_text
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout import Layout
from prompt_toolkit import Application


def render_markdown(markdown_text: str):
    buf = StringIO()
    md = Markdown(markdown_text)
    console = Console(file=buf, force_terminal=True, color_system="truecolor")
    console.print(md)
    rich_ansi = buf.getvalue()
    pt_doc = to_formatted_text(ANSI(rich_ansi))
    return pt_doc
