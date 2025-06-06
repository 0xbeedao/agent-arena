TITLE: Initializing Rich Console Object (Python)
DESCRIPTION: This snippet demonstrates how to import the `Console` class from the `rich.console` module and instantiate a `Console` object. This object is the primary interface for controlling rich terminal content.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_4>

LANGUAGE: python
CODE:

```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Installing Rich Python Library
DESCRIPTION: This command installs the Rich library using pip, the standard Python package installer. It's the recommended way to get Rich set up in your Python environment.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_0>

LANGUAGE: shell
CODE:

```
python -m pip install rich
```

----------------------------------------

TITLE: Printing Content with Rich Console (Python)
DESCRIPTION: These examples illustrate various uses of the `console.print` method. It can print lists, apply console markup for styling, pretty-print dictionaries (like `locals()`), and apply direct styles using the `style` argument. It converts objects to strings and supports rich content rendering.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_2>

LANGUAGE: python
CODE:

```
console.print([1, 2, 3])
console.print("[blue underline]Looks like a link")
console.print(locals())
console.print("FOO", style="white on blue")
```

----------------------------------------

TITLE: Installing Rich as Default Traceback Handler
DESCRIPTION: This code installs Rich as the global default traceback handler, ensuring that all subsequent uncaught exceptions are automatically rendered with Rich's enhanced formatting and syntax highlighting. The `show_locals=True` option enables the display of local variables.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/traceback.rst#_snippet_2>

LANGUAGE: Python
CODE:

```
from rich.traceback import install
install(show_locals=True)
```

----------------------------------------

TITLE: Importing Rich's Print Function
DESCRIPTION: This Python statement imports the `print` function from the `rich` library. Once imported, it can be used as a direct drop-in replacement for Python's built-in `print` to automatically apply Rich's enhanced formatting and styling.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/introduction.rst#_snippet_2>

LANGUAGE: Python
CODE:

```
from rich import print
```

----------------------------------------

TITLE: Inspecting Python Objects with Rich Inspect (Python)
DESCRIPTION: This snippet demonstrates how to use the `rich.inspect` function to generate a detailed report on any Python object, such as a class, instance, or builtin. It shows inspecting a list and including its methods in the report.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_8>

LANGUAGE: python
CODE:

```
my_list = ["foo", "bar"]
from rich import inspect
inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Logging with Rich Console in Python
DESCRIPTION: The `console.log()` method provides enhanced logging capabilities, similar to `print()`, but includes timestamps, file/line information, syntax highlighting for Python structures, and pretty printing for collections. The `log_locals` argument can be used to output a table of local variables for debugging purposes.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_9>

LANGUAGE: python
CODE:

```
from rich.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1"},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"}
]

def test_log():
    enabled = False
    context = {
        "foo": "bar"
    }
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)


test_log()
```

----------------------------------------

TITLE: Directly Importing Rich print_json (Python)
DESCRIPTION: This snippet shows how to directly import the `print_json` function from the top-level `rich` module. This provides a convenient shortcut for pretty-printing JSON without needing to instantiate a `Console` object first.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_6>

LANGUAGE: python
CODE:

```
from rich import print_json
```

----------------------------------------

TITLE: Creating and Printing a Basic Table with Rich in Python
DESCRIPTION: This snippet demonstrates the fundamental steps to create and display a table using the Rich library. It initializes a Table object, defines columns with specific styling and justification, adds rows of data, and then prints the formatted table to the console using a Console instance.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/tables.rst#_snippet_0>

LANGUAGE: Python
CODE:

```
from rich.console import Console
from rich.table import Table

table = Table(title="Star Wars Movies")

table.add_column("Released", justify="right", style="cyan", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Box Office", justify="right", style="green")

table.add_row("Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$952,110,690")
table.add_row("May 25, 2018", "Solo: A Star Wars Story", "$393,151,347")
table.add_row("Dec 15, 2017", "Star Wars Ep. V111: The Last Jedi", "$1,332,539,889")
table.add_row("Dec 16, 2016", "Rogue One: A Star Wars Story", "$1,332,439,889")

console = Console()
console.print(table)
```

----------------------------------------

TITLE: Installing Rich Python Library
DESCRIPTION: This command installs the Rich library from PyPI using pip. It is the standard and recommended way to add Rich to your Python environment, allowing access to its features for rich terminal output.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/introduction.rst#_snippet_0>

LANGUAGE: Bash
CODE:

```
pip install rich
```

----------------------------------------

TITLE: Initializing Rich Console Instance (Python)
DESCRIPTION: This snippet demonstrates how to create a `Console` instance from the `rich.console` module. It's typically created once at the module level to manage terminal output throughout an application.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_0>

LANGUAGE: python
CODE:

```
from rich.console import Console
console = Console()
```

----------------------------------------

TITLE: Applying Basic Bold and Red Style in Rich
DESCRIPTION: This Python snippet demonstrates the fundamental usage of Rich console markup to apply 'bold' and 'red' styles to a specific part of a string. The `print` function from `rich` is used to render the styled text, with the style applying between the opening `[bold red]` and closing `[/bold red]` tags.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/markup.rst#_snippet_1>

LANGUAGE: Python
CODE:

```
from rich import print
print("[bold red]alert![/bold red] Something happened")
```

----------------------------------------

TITLE: Using Rich Print for Styled Output in Python
DESCRIPTION: This Python snippet demonstrates how to use Rich's `print` function, which replaces the built-in `print` to add color and style to terminal output using Rich's markup. It shows basic text styling and emoji support.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_2>

LANGUAGE: python
CODE:

```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Tracking Task Progress with Rich (Python)
DESCRIPTION: This snippet demonstrates the basic usage of Rich's `track` function to create a simple progress bar for iterating over a sequence. The `track` function wraps an iterable, automatically displaying a flicker-free progress bar in the terminal, which is useful for long-running tasks.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_12>

LANGUAGE: python
CODE:

```
from rich.progress import track

for step in track(range(100)):
    do_step(step)
```

----------------------------------------

TITLE: Basic Live Display with Rich Table (Python)
DESCRIPTION: Demonstrates how to use `rich.live.Live` as a context manager to display and dynamically update a `rich.table.Table`. It shows adding rows to the table within a loop, with a delay, and the live display refreshing automatically.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/live.rst#_snippet_0>

LANGUAGE: Python
CODE:

```
import time

from rich.live import Live
from rich.table import Table

table = Table()
table.add_column("Row ID")
table.add_column("Description")
table.add_column("Level")

with Live(table, refresh_per_second=4):  # update 4 times a second to feel fluid
    for row in range(12):
        time.sleep(0.4)  # arbitrary delay
        # update the renderable internally
        table.add_row(f"{row}", f"description {row}", "[red]ERROR")
```

----------------------------------------

TITLE: Printing Current Exception Traceback with Rich Console
DESCRIPTION: This snippet demonstrates how to use `console.print_exception()` within an exception handler to display a Rich-formatted traceback for the currently caught exception. The `show_locals=True` parameter includes local variable values for each frame, aiding in debugging.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/traceback.rst#_snippet_1>

LANGUAGE: Python
CODE:

```
from rich.console import Console
console = Console()

try:
    do_something()
except Exception:
    console.print_exception(show_locals=True)
```

----------------------------------------

TITLE: Creating and Styling Tables with Rich (Python)
DESCRIPTION: This example illustrates how to construct and format flexible tables using Rich's `Table` class. It shows how to define columns with styles and justification, add rows of data, and print the table to the console. Rich tables automatically resize columns and wrap text to fit the terminal width.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_11>

LANGUAGE: python
CODE:

```
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347"
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]"
)

console.print(table)
```

----------------------------------------

TITLE: Listing Directory Contents with Rich Columns in Python
DESCRIPTION: This Python script demonstrates how to use the `rich.columns.Columns` class to display directory contents in a columnar format, mimicking the `ls` command. It takes a directory path as a command-line argument, lists its contents using `os.listdir`, and then renders them using `Columns` with `equal=True` and `expand=True` for even distribution across the console.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/columns.rst#_snippet_0>

LANGUAGE: Python
CODE:

```
import os
import sys

from rich import print
from rich.columns import Columns

if len(sys.argv) < 2:
    print("Usage: python columns.py DIRECTORY")
else:
    directory = os.listdir(sys.argv[1])
    columns = Columns(directory, equal=True, expand=True)
    print(columns)
```

----------------------------------------

TITLE: Installing Rich Pretty Printing in Python REPL
DESCRIPTION: This Python code snippet integrates Rich's pretty printing functionality into the Python REPL. Once `pretty.install()` is called, any data structures displayed in the REPL will be automatically formatted and syntax-highlighted by Rich.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_3>

LANGUAGE: python
CODE:

```
from rich import pretty
pretty.install()
```

----------------------------------------

TITLE: Logging Messages with Rich Console (Python)
DESCRIPTION: This snippet demonstrates the `console.log` method, which is similar to `print` but adds debugging features like timestamps and source file/line information. It's useful for tracking application flow and state.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_3>

LANGUAGE: python
CODE:

```
console.log("Hello, World!")
```

----------------------------------------

TITLE: Automatic Rich Repr Generation with @rich.repr.auto Decorator in Python
DESCRIPTION: This snippet shows how to automatically generate a Rich representation for a class using the `@rich.repr.auto` decorator. When applied, Rich infers the repr from the class's `__init__` parameters, simplifying the process of creating custom representations without explicit `__rich_repr__` implementation, and also generates a standard `__repr__`.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/pretty.rst#_snippet_14>

LANGUAGE: Python
CODE:

```
import rich.repr

@rich.repr.auto
class Bird:
    def __init__(self, name, eats=None, fly=True, extinct=False):
        self.name = name
        self.eats = list(eats) if eats else []
        self.fly = fly
        self.extinct = extinct


BIRDS = {
    "gull": Bird("gull", eats=["fish", "chips", "ice cream", "sausage rolls"]),
    "penguin": Bird("penguin", eats=["fish"], fly=False),
    "dodo": Bird("dodo", eats=["fruit"], fly=False, extinct=True)
}
from rich import print
print(BIRDS)
```

----------------------------------------

TITLE: Rendering Markdown Content with Rich in Python
DESCRIPTION: This Python snippet shows how to render a Markdown file (README.md) to the terminal using rich.markdown.Markdown. It reads the content of the Markdown file, constructs a Markdown object, and then prints it to the console, translating Markdown formatting into terminal-friendly output.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_17>

LANGUAGE: python
CODE:

```
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

----------------------------------------

TITLE: Creating a Basic Rich Panel
DESCRIPTION: This snippet demonstrates how to create a basic panel using `rich.panel.Panel` to draw a border around text. It imports `print` and `Panel` from the `rich` library and then prints a panel containing the string 'Hello, [red]World!'.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/panel.rst#_snippet_0>

LANGUAGE: Python
CODE:

```
from rich import print
from rich.panel import Panel
print(Panel("Hello, [red]World!"))
```

----------------------------------------

TITLE: Wrapping File-like Objects for Progress Display in Python
DESCRIPTION: This snippet demonstrates using `rich.progress.wrap_file` to add a progress bar to an already open file-like object, such as a network response. It requires specifying the total size of the content to be read. The example simulates reading data from a URL with a delay, showing progress as bytes are consumed.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/progress.rst#_snippet_11>

LANGUAGE: Python
CODE:

```
from time import sleep
    from urllib.request import urlopen

    from rich.progress import wrap_file

    response = urlopen("https://www.textualize.io")
    size = int(response.headers["Content-Length"])

    with wrap_file(response, size) as file:
        for line in file:
            print(line.decode("utf-8"), end="")
            sleep(0.1)
```

----------------------------------------

TITLE: Safely Formatting Dynamic Strings with Rich Markup Escape
DESCRIPTION: This Python function demonstrates the safe way to handle dynamic string formatting with Rich by using `rich.markup.escape`. By applying `escape()` to the `name` parameter, any potential markup tags within the input string are neutralized, preventing unintended styling or markup injection when printed by `console.print`.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/markup.rst#_snippet_8>

LANGUAGE: Python
CODE:

```
from rich.markup import escape
def greet(name):
    console.print(f"Hello {escape(name)}!")
```

----------------------------------------

TITLE: Rendering Markdown Content with Rich in Python
DESCRIPTION: This snippet demonstrates how to use the Rich library to render a multi-line Markdown string to the console. It initializes a `Console` object and a `Markdown` object, then prints the Markdown content, showcasing Rich's ability to format text and syntax highlight code blocks.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/markdown.rst#_snippet_0>

LANGUAGE: Python
CODE:

```
MARKDOWN = """
# This is an h1

Rich can do a pretty *decent* job of rendering markdown.

1. This is a list item
2. This is another list item
"""
from rich.console import Console
from rich.markdown import Markdown

console = Console()
md = Markdown(MARKDOWN)
console.print(md)
```

----------------------------------------

TITLE: Configuring RichHandler for Traceback Formatting in Python
DESCRIPTION: This example illustrates how to configure `RichHandler` to use Rich's enhanced traceback formatting by setting `rich_tracebacks=True`. It demonstrates logging an exception with the improved traceback, providing more context.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/logging.rst#_snippet_3>

LANGUAGE: Python
CODE:

```
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")
try:
    print(1 / 0)
except Exception:
    log.exception("unable print!")
```

----------------------------------------

TITLE: Installing Rich Pretty Printing in Python REPL
DESCRIPTION: This Python code snippet installs Rich's pretty printing functionality into the current Python REPL session. After execution, Python data structures will be automatically pretty-printed with syntax highlighting for improved readability.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/introduction.rst#_snippet_5>

LANGUAGE: Python
CODE:

```
from rich import pretty
pretty.install()
```

----------------------------------------

TITLE: String Prompt with Default Value using `rich.prompt.Prompt.ask` (Python)
DESCRIPTION: Shows how to assign a default value to `rich.prompt.Prompt.ask`. If the user submits an empty response, the specified default value is automatically returned.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/prompt.rst#_snippet_1>

LANGUAGE: Python
CODE:

```
from rich.prompt import Prompt
name = Prompt.ask("Enter your name", default="Paul Atreides")
```

----------------------------------------

TITLE: Managing Multiple Progress Tasks with Context Manager
DESCRIPTION: This example shows how to manage multiple concurrent tasks using the `rich.progress.Progress` class as a context manager. It initializes three distinct tasks with different descriptions and colors, then continuously updates their progress using `advance` until all tasks are marked as finished. This approach ensures proper display start and stop.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/progress.rst#_snippet_2>

LANGUAGE: Python
CODE:

```
import time

from rich.progress import Progress

with Progress() as progress:

    task1 = progress.add_task("[red]Downloading...", total=1000)
    task2 = progress.add_task("[green]Processing...", total=1000)
    task3 = progress.add_task("[cyan]Cooking...", total=1000)

    while not progress.finished:
        progress.update(task1, advance=0.5)
        progress.update(task2, advance=0.3)
        progress.update(task3, advance=0.9)
        time.sleep(0.02)
```

----------------------------------------

TITLE: Printing Basic Text with Rich Console (Python)
DESCRIPTION: This snippet shows how to use the `print` method of the `Console` object to output text to the terminal. It functions similarly to the built-in `print` function but includes Rich's word-wrapping capabilities.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_5>

LANGUAGE: python
CODE:

```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Defining and Applying Custom Rich Style Themes in Python
DESCRIPTION: This snippet demonstrates how to create a custom `Theme` object with named styles (e.g., 'info', 'warning', 'danger') and apply it to a `Console` instance. It shows how to print text using these defined styles, either via the `style` parameter or inline markup, centralizing style definitions for easier maintenance.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/style.rst#_snippet_10>

LANGUAGE: Python
CODE:

```
from rich.console import Console
from rich.theme import Theme
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red"
})
console = Console(theme=custom_theme)
console.print("This is information", style="info")
console.print("[warning]The pod bay doors are locked[/warning]")
console.print("Something terrible happened!", style="danger")
```

----------------------------------------

TITLE: Yes/No Confirmation Prompt with `rich.prompt.Confirm.ask` (Python)
DESCRIPTION: Illustrates the use of `rich.prompt.Confirm.ask` for posing simple yes/no questions to the user. This specialized prompt returns a boolean value (`True` for yes, `False` for no) based on the user's response.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/prompt.rst#_snippet_4>

LANGUAGE: Python
CODE:

```
from rich.prompt import Confirm
is_rich_great = Confirm.ask("Do you like rich?")
assert is_rich_great
```

----------------------------------------

TITLE: Customizing Console Output with `__rich__` Method (Python)
DESCRIPTION: This snippet demonstrates how to implement the `__rich__` method in a Python class. This method, accepting no arguments, allows an object to define its rich console representation by returning a renderable object, such as a string with console markup. When an instance of `MyObject` is printed, it will render as 'MyObject()' in bold cyan.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/protocol.rst#_snippet_0>

LANGUAGE: Python
CODE:

```
class MyObject:
    def __rich__(self) -> str:
        return "[bold cyan]MyObject()"
```

----------------------------------------

TITLE: Inspecting a Rich Color Object in Python
DESCRIPTION: This snippet demonstrates how to use the `rich.inspect` function to generate a detailed report on a `rich.color.Color` object. It shows the object's attributes and methods, which is useful for debugging and understanding object structure. The `methods=True` argument ensures that callable methods are also included in the report.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/introduction.rst#_snippet_9>

LANGUAGE: python
CODE:

```
from rich import inspect
from rich.color import Color
color = Color.parse("red")
inspect(color, methods=True)
```

----------------------------------------

TITLE: Displaying a Basic Status Message with Rich (Python)
DESCRIPTION: This Python snippet shows how to use `console.status` as a context manager. It displays "Working..." with a default spinner animation while the `do_work()` function (a placeholder for actual work) executes, automatically stopping the status display upon exiting the block.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_11>

LANGUAGE: Python
CODE:

```
with console.status("Working..."):
    do_work()
```

----------------------------------------

TITLE: Displaying Progress with Rich Status Spinner in Python
DESCRIPTION: This snippet uses rich.console.Console.status to display a dynamic spinner animation and a message while a series of tasks are being processed. It's useful when exact progress calculation is difficult, providing visual feedback without blocking console interaction. The sleep(1) simulates work for each task.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_13>

LANGUAGE: python
CODE:

```
from time import sleep
from rich.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:
        task = tasks.pop(0)
        sleep(1)
        console.log(f"{task} complete")
```

----------------------------------------

TITLE: Setting Up Basic Rich Logger in Python
DESCRIPTION: This snippet demonstrates the basic setup for integrating Rich's `RichHandler` with Python's standard `logging` module. It configures a logger to output messages with Rich's formatting and colorization, showing a simple info message.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/logging.rst#_snippet_0>

LANGUAGE: Python
CODE:

```
import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")
log.info("Hello, World!")
```

----------------------------------------

TITLE: Applying Syntax Highlighting with Rich in Python
DESCRIPTION: This Python snippet utilizes rich.syntax.Syntax and the pygments library to apply syntax highlighting to a given Python code string. It configures the syntax object with the language ("python"), a theme ("monokai"), and line numbers, then prints the beautifully formatted code to the console.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_18>

LANGUAGE: python
CODE:

```
from rich.console import Console
from rich.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

----------------------------------------

TITLE: Printing with Rich Console Markup and Pretty Formatting
DESCRIPTION: This Python code demonstrates using Rich's `print` function to output text with inline console markup for styling (e.g., italic red) and to pretty-print a Python object (`locals()`), making complex data structures more readable in the terminal.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/introduction.rst#_snippet_3>

LANGUAGE: Python
CODE:

```
print("[italic red]Hello[/italic red] World!", locals())
```

----------------------------------------

TITLE: Applying Global Style with Rich Console (Python)
DESCRIPTION: This snippet illustrates how to apply a global style to the entire output of the `console.print` method using the `style` keyword argument. The example sets the text to be bold and red.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_6>

LANGUAGE: python
CODE:

```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Writing Console Output to a File in Rich (Python)
DESCRIPTION: This snippet demonstrates how to redirect Rich console output to a file. It initializes a `Console` instance with a file object, allowing all subsequent `console` methods (like `console.rule`) to write to the specified file instead of the terminal. It also notes that `width` might need explicit setting.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_22>

LANGUAGE: Python
CODE:

```
from rich.console import Console
from datetime import datetime

with open("report.txt", "wt") as report_file:
    console = Console(file=report_file)
    console.rule(f"Report Generated {datetime.now().ctime()}")
```

----------------------------------------

TITLE: Styling an Error Console in Rich Python
DESCRIPTION: This code builds upon the error console concept by also applying a visual style to it. By setting `stderr=True` and `style='bold red'`, all messages printed to `error_console` will appear in bold red, making error messages immediately distinct.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_21>

LANGUAGE: Python
CODE:

```
error_console = Console(stderr=True, style="bold red")
```

----------------------------------------

TITLE: Pretty Printing JSON via Command Line (Bash)
DESCRIPTION: This snippet provides a command-line example for pretty-printing a JSON file (`cats.json`) using Rich's built-in module. This is useful for quick inspection of JSON data directly from the terminal.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_7>

LANGUAGE: bash
CODE:

```
python -m rich.json cats.json
```

----------------------------------------

TITLE: Creating a Basic Rich Tree
DESCRIPTION: This snippet demonstrates the basic instantiation and printing of a `rich.tree.Tree` object. It initializes a tree with a root label 'Rich Tree' and then prints it to the console, showing only the root.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/tree.rst#_snippet_1>

LANGUAGE: Python
CODE:

```
from rich.tree import Tree
from rich import print

tree = Tree("Rich Tree")
print(tree)
```

----------------------------------------

TITLE: Basic String Prompt with `rich.prompt.Prompt.ask` (Python)
DESCRIPTION: Illustrates the fundamental usage of `rich.prompt.Prompt.ask` to obtain a string input from the user. The prompt message can incorporate console markup and emoji codes for enhanced presentation.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/prompt.rst#_snippet_0>

LANGUAGE: Python
CODE:

```
from rich.prompt import Prompt
name = Prompt.ask("Enter your name")
```

----------------------------------------

TITLE: String Prompt with Predefined Choices using `rich.prompt.Prompt.ask` (Python)
DESCRIPTION: Demonstrates how to restrict user input to a list of predefined choices using `rich.prompt.Prompt.ask`. The prompt will repeatedly ask for input until a valid choice from the list is provided, and a default value can also be set.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/prompt.rst#_snippet_2>

LANGUAGE: Python
CODE:

```
from rich.prompt import Prompt
name = Prompt.ask("Enter your name", choices=["Paul", "Jessica", "Duncan"], default="Paul")
```

----------------------------------------

TITLE: Enabling Line Numbers for Rich Syntax Highlighting in Python
DESCRIPTION: This snippet demonstrates how to enable line numbers when highlighting code using `rich.syntax.Syntax.from_path`. By setting `line_numbers=True`, Rich will render a column displaying line numbers alongside the code. It builds upon the `from_path` constructor.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/syntax.rst#_snippet_2>

LANGUAGE: python
CODE:

```
syntax = Syntax.from_path("syntax.py", line_numbers=True)
```

----------------------------------------

TITLE: Capturing Console Output with `StringIO` in Rich (Python)
DESCRIPTION: This snippet demonstrates an alternative method for capturing console output by setting the `Console`'s `file` argument to an `io.StringIO` object. After printing, the captured string can be retrieved from the `StringIO` buffer using `console.file.getvalue()`, which is recommended for unit testing.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_24>

LANGUAGE: Python
CODE:

```
from io import StringIO
from rich.console import Console
console = Console(file=StringIO())
console.print("[bold red]Hello[/] World")
str_output = console.file.getvalue()
```

----------------------------------------

TITLE: Importing and Using Rich's pprint Method (Python)
DESCRIPTION: This snippet demonstrates how to import the `pprint` function from `rich.pretty` and then use it to pretty print the `locals()` dictionary, which contains all local symbols. This showcases the basic usage of the `pprint` method.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/pretty.rst#_snippet_1>

LANGUAGE: Python
CODE:

```
from rich.pretty import pprint
pprint(locals())
```

----------------------------------------

TITLE: Getting User Input with Rich Console in Python
DESCRIPTION: This code shows how to use the `Console.input` method, which functions similarly to Python's built-in `input` but allows for rich-styled prompts. The example uses inline styling and an emoji for a colorful prompt.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_17>

LANGUAGE: Python
CODE:

```
from rich.console import Console
console = Console()
console.input("What is [i]your[/i] [bold red]name[/]? :smiley: ")
```

----------------------------------------

TITLE: Using Rich Markup for Inline Styling (Python)
DESCRIPTION: This snippet demonstrates the use of Rich's special markup, similar to BBCode, for fine-grained inline styling within a printed string. It shows examples of bold, underline, and italic styles.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_7>

LANGUAGE: python
CODE:

```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Creating and Applying Styles with Rich Style Class
DESCRIPTION: Shows how to explicitly create a Style object with specific attributes (color, blink, bold) and then apply it to text using console.print, offering an alternative to style strings.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/style.rst#_snippet_7>

LANGUAGE: Python
CODE:

```
from rich.style import Style
danger_style = Style(color="red", blink=True, bold=True)
console.print("Danger, Will Robinson!", style=danger_style)
```

----------------------------------------

TITLE: Pretty Printing JSON with Rich Console (Python)
DESCRIPTION: This example shows how to use the `console.print_json` method to pretty-print a JSON string to the terminal. This method automatically formats and styles the JSON for readability.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_4>

LANGUAGE: python
CODE:

```
console.print_json('[false, true, null, "foo"]')
```

----------------------------------------

TITLE: Syntax Highlighting from File Path with Rich in Python
DESCRIPTION: This example shows how to use the `Syntax.from_path` alternative constructor to load and highlight code directly from a file. This method automatically detects the file type for highlighting. It requires `rich.console.Console` and `rich.syntax.Syntax`.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/syntax.rst#_snippet_1>

LANGUAGE: python
CODE:

```
from rich.console import Console
from rich.syntax import Syntax

console = Console()
syntax = Syntax.from_path("syntax.py")
console.print(syntax)
```

----------------------------------------

TITLE: Basic Syntax Highlighting with Rich in Python
DESCRIPTION: This snippet demonstrates how to perform basic syntax highlighting using the `rich.syntax.Syntax` object. It reads code from a file, creates a `Syntax` object, and prints it to the console. It requires `rich.console.Console` and `rich.syntax.Syntax`.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/syntax.rst#_snippet_0>

LANGUAGE: python
CODE:

```
from rich.console import Console
from rich.syntax import Syntax

console = Console()
with open("syntax.py", "rt") as code_file:
    syntax = Syntax(code_file.read(), "python")
console.print(syntax)
```

----------------------------------------

TITLE: Installing Rich with Jupyter Dependencies
DESCRIPTION: This command installs the Rich library along with additional dependencies specifically required for its integration and optimal use within Jupyter environments, ensuring full functionality in notebooks.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/introduction.rst#_snippet_1>

LANGUAGE: Bash
CODE:

```
pip install "rich[jupyter]"
```

----------------------------------------

TITLE: Drawing a Styled Rule with Rich Console (Python)
DESCRIPTION: This code uses the `console.rule` method to draw a horizontal line with an optional title. The title "[bold red]Chapter 2" applies Rich's styling syntax to make the text bold and red, effectively creating a visual section divider.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/console.rst#_snippet_9>

LANGUAGE: Python
CODE:

```
console.rule("[bold red]Chapter 2")
```

----------------------------------------

TITLE: Demonstrating Rich REPL Pretty Printing
DESCRIPTION: This Python code demonstrates the automatic pretty printing feature of Rich in the REPL. After `pretty.install()` is called, simple data structures like lists are automatically formatted and syntax-highlighted upon evaluation.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/introduction.rst#_snippet_6>

LANGUAGE: Python
CODE:

```
["Rich and pretty", True]
```

----------------------------------------

TITLE: Unsafe Dynamic String Formatting with Rich
DESCRIPTION: This Python function demonstrates a potential vulnerability when dynamically formatting strings for Rich's `console.print`. Without proper escaping, malicious input for the `name` parameter could inject unwanted markup tags, leading to unexpected styling or behavior.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/markup.rst#_snippet_7>

LANGUAGE: Python
CODE:

```
def greet(name):
    console.print(f"Hello {name}!")
```

----------------------------------------

TITLE: Creating a Transient Rich Progress Bar in Python
DESCRIPTION: This snippet demonstrates how to create a `rich.progress.Progress` bar that disappears from the terminal upon completion or exit. By setting `transient=True` in the constructor, the progress display is automatically removed, providing a cleaner terminal output. It shows adding a task and performing work.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/progress.rst#_snippet_4>

LANGUAGE: Python
CODE:

```
with Progress(transient=True) as progress:
    task = progress.add_task("Working", total=100)
    do_work(task)
```

----------------------------------------

TITLE: Inserting Emojis in Rich Console (Python)
DESCRIPTION: This snippet demonstrates how to embed emojis directly into console output using Rich. By enclosing the emoji's shortcode name within two colons (e.g., `:smiley:`), the `console.print()` method will render the corresponding emoji character.
SOURCE: <https://github.com/textualize/rich/blob/master/README.md#_snippet_10>

LANGUAGE: python
CODE:

```
>>> console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")
😃 🧛 💩 👍 🦝
```

----------------------------------------

TITLE: Creating a Grid Layout with Rich Table (Python)
DESCRIPTION: Illustrates using `rich.table.Table.grid` as a layout tool to position content. It creates a grid, adds two columns (one left-aligned, one right-aligned), and then adds a row with two pieces of text, effectively aligning them to the left and right edges of the terminal.
SOURCE: <https://github.com/textualize/rich/blob/master/docs/source/tables.rst#_snippet_6>

LANGUAGE: Python
CODE:

```
from rich import print
from rich.table import Table

grid = Table.grid(expand=True)
grid.add_column()
grid.add_column(justify="right")
grid.add_row("Raising shields", "[bold magenta]COMPLETED [green]:heavy_check_mark:")

print(grid)
```
