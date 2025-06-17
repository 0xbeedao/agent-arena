from io import StringIO

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.formatted_text import to_formatted_text
from rich.console import Console
from rich.markdown import Markdown


def render_markdown(markdown_text: str):
    buf = StringIO()
    md = Markdown(markdown_text)
    console = Console(file=buf, force_terminal=True, color_system="truecolor")
    console.print(md)
    rich_ansi = buf.getvalue()
    pt_doc = to_formatted_text(ANSI(rich_ansi))
    return pt_doc
