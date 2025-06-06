TITLE: Running a Textual App Instance in Python
DESCRIPTION: This code shows how to instantiate and run a Textual application. Calling `app.run()` puts the terminal into application mode, allowing Textual to manage user input and screen updates. It's the standard entry point for launching a Textual UI.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_1>

LANGUAGE: python
CODE:

```
from textual.app import App

class MyApp(App):
    pass

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

----------------------------------------

TITLE: Using Textual Log Function for Output (Python)
DESCRIPTION: This example demonstrates how to use the `textual.log` function within an `on_mount` event handler to output different types of data. It shows logging simple strings, local variables, key-value pairs, and Rich renderables like `self.tree` to the devtools console.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_18>

LANGUAGE: python
CODE:

```
def on_mount(self) -> None:
    log("Hello, World")  # simple string
    log(locals())  # Log local variables
    log(children=self.children, pi=3.141592)  # key/values
    log(self.tree)  # Rich renderables
```

----------------------------------------

TITLE: Installing Textual via PyPI
DESCRIPTION: Installs the core Textual library using pip, the Python package installer. This is the standard method for getting Textual.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/getting_started.md#_snippet_0>

LANGUAGE: Bash
CODE:

```
pip install textual
```

----------------------------------------

TITLE: Creating a Basic Textual App Class in Python
DESCRIPTION: This snippet demonstrates the simplest way to define a Textual application by subclassing `textual.app.App`. It serves as the foundational structure for any Textual application, providing the necessary inheritance for app functionality.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_0>

LANGUAGE: python
CODE:

```
from textual.app import App

class MyApp(App):
    pass
```

----------------------------------------

TITLE: Implementing Reactive Attributes in Textual Python
DESCRIPTION: This snippet demonstrates adding reactive attributes (`start_time`, `time`) to a Textual widget (`TimeDisplay`). It shows how to initialize them, use `set_interval` in `on_mount` to periodically update a reactive attribute (`time`), and implement a `watch_time` method that automatically updates the widget's display whenever the `time` attribute changes.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_10>

LANGUAGE: python
CODE:

```
from textual.reactive import reactive
from textual.widget import Widget
from time import monotonic

class TimeDisplay(Widget):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)

    def on_mount(self) -> None:
        """Called when the widget is added to the app."""
        self.set_interval(1 / 60, self.update_time)

    def update_time(self) -> None:
        """Method to update the time attribute."""
        self.time = monotonic() - self.start_time

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02.0f}:{minutes:02.0f}:{seconds:05.2f}")

# Example usage (simplified, assumes a Textual App context)
# app = App()
# app.mount(TimeDisplay())
# app.run()
```

----------------------------------------

TITLE: Performing Batch Updates - Textual Python
DESCRIPTION: This snippet demonstrates the use of the `self.app.batch_update()` context manager to prevent screen updates until the block exits. This is crucial for operations like removing and mounting multiple widgets (e.g., `MarkdownBlock` content) to avoid visual flicker and ensure a smooth, instant update experience.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-12-0.md#_snippet_2>

LANGUAGE: python
CODE:

```
with self.app.batch_update():
    await self.query("MarkdownBlock").remove()
    await self.mount_all(output)
```

----------------------------------------

TITLE: Defining Input.Changed Message Class in Textual Python
DESCRIPTION: This snippet shows the definition of the `Changed` message class nested within the `Input` widget class in Textual. This structure establishes a namespace for the message, leading to handler names like `on_input_changed`.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/events.md#_snippet_0>

LANGUAGE: Python
CODE:

```
class Input(Widget):
    ...
    class Changed(Message):
        """Posted when the value changes."""
        ...
```

----------------------------------------

TITLE: Running a Blocking Background Task in Textual (Incorrect)
DESCRIPTION: This snippet demonstrates an attempt to run a long-running operation in the background using `asyncio.create_task`. Although `_do_long_operation` is an `async` function (coroutine), it still uses `time.sleep`, which is a blocking call. This causes the Textual application's event loop to freeze and the UI to become unresponsive during the operation, highlighting the importance of using `await` with asynchronous I/O operations.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/responsive-app-background-task.md#_snippet_1>

LANGUAGE: Python
CODE:

```
import time
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Container

class BlockingApp(App):
    BINDINGS = [
        ("c", "change_color", "Change Color"),
        ("l", "load", "Load Data")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Container():
            yield Button("Change Color", id="change_color")
            yield Button("Load Data", id="load_data")
            yield Label("Ready", id="status_label")

    def action_change_color(self) -> None:
        self.query_one("#status_label").update("Color changed!")
        self.screen.styles.background = "blue" if self.screen.styles.background == "red" else "red"

    async def _do_long_operation(self) -> None:
        # This is the blocking part, using time.sleep
        self.query_one("#status_label").update("Starting long operation...")
        time.sleep(5) # This blocks the event loop
        self.query_one("#status_label").update("Long operation finished.")

    def action_load(self) -> None:
        self.query_one("#status_label").update("Loading data...")
        # Create a task to run the long operation concurrently
        asyncio.create_task(self._do_long_operation())

if __name__ == "__main__":
    app = BlockingApp()
    app.run()
```

----------------------------------------

TITLE: Calculator Example in Textual
DESCRIPTION: This example demonstrates a calculator application built with Textual, showcasing its ability to create interactive terminal applications. It includes both the Python code for the application logic and the CSS for styling.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/index.md#_snippet_1>

LANGUAGE: Python
CODE:

```
--8<-- "examples/calculator.py"
```

----------------------------------------

TITLE: Installing Textual and Development Tools via pip
DESCRIPTION: This command installs the Textual framework and its development tools (`textual-dev`) using pip, the Python package installer. `textual-dev` provides additional utilities for debugging and development.
SOURCE: <https://github.com/textualize/textual/blob/main/README.md#_snippet_1>

LANGUAGE: Bash
CODE:

```
pip install textual textual-dev
```

----------------------------------------

TITLE: Running a Textual Application (Python)
DESCRIPTION: This standard Python entry point creates an instance of the `MotherApp` and starts the Textual application. It's the main execution block for launching the TUI.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_8>

LANGUAGE: Python
CODE:

```
if __name__ == "__main__":
    app = MotherApp()
    app.run()
```

----------------------------------------

TITLE: Combining Multiple Input Validators - Python
DESCRIPTION: This snippet demonstrates how to integrate multiple built-in and custom validators with the `Input` widget. It also shows how to handle `Input.Changed` and `Input.Submitted` events to update the UI based on the `validation_result` and how to implement a custom `Validator` class.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/widgets/input.md#_snippet_3>

LANGUAGE: Python
CODE:

```
--8<-- "docs/examples/widgets/input_validation.py"
```

----------------------------------------

TITLE: Custom Widget with Render Method in Textual (Python)
DESCRIPTION: This code defines a custom widget class named `Hello` that extends the base `Widget` class. It overrides the `render` method to return a Textual `Text` object containing a formatted greeting string. The greeting string uses Textual's markup to style the word 'World' in bold.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_0>

LANGUAGE: Python
CODE:

```
class Hello(Widget):
    
```

----------------------------------------

TITLE: ByteEditor: Handling Input Changes and Updating BitSwitches (byte03.py)
DESCRIPTION: This code snippet demonstrates how to update the switches if the user edits the decimal value. Since the switches are children of `ByteEditor` they can be updated by setting their attributes directly. This is an example of attributes down. When the user edits the input, the Input widget sends a `Changed` event, which is handled with `on_input_changed` by setting `self.value`, which is a reactive value added to `ByteEditor`. If the value has changed, Textual will call `watch_value` which sets the value of each of the eight switches.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_30>

LANGUAGE: python
CODE:

```
class BitSwitch(Widget):
    
```

----------------------------------------

TITLE: Sending Prompt to LLM with Threaded Worker in Textual (Python)
DESCRIPTION: This method, decorated as a threaded Textual worker, sends the user's prompt to the LLM. It processes the LLM's response in chunks, incrementally updating the `Response` widget's content to create a streaming text effect, ensuring the UI remains responsive.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_7>

LANGUAGE: Python
CODE:

```
    @work(thread=True)
    def send_prompt(self, prompt: str, response: Response) -> None:
        response_content = ""
        llm_response = self.model.prompt(prompt, system=SYSTEM)
        for chunk in llm_response:
            response_content += chunk
            self.call_from_thread(response.update, response_content)
```

----------------------------------------

TITLE: Implementing a Non-Blocking Background Task in Textual (Correct)
DESCRIPTION: This snippet shows the corrected approach for running a long-running operation asynchronously in a Textual application. By replacing `time.sleep` with `await asyncio.sleep`, the operation becomes non-blocking, allowing the Textual UI to remain responsive. It illustrates how to properly use `await` within a coroutine to yield control back to the event loop, enabling concurrent execution of other tasks while the long operation is in progress.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/responsive-app-background-task.md#_snippet_2>

LANGUAGE: Python
CODE:

```
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Container

class NonBlockingApp(App):
    BINDINGS = [
        ("c", "change_color", "Change Color"),
        ("l", "load", "Load Data")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Container():
            yield Button("Change Color", id="change_color")
            yield Button("Load Data", id="load_data")
            yield Label("Ready", id="status_label")

    def action_change_color(self) -> None:
        self.query_one("#status_label").update("Color changed!")
        self.screen.styles.background = "blue" if self.screen.styles.background == "red" else "red"

    async def _do_long_operation(self) -> None:
        # 1. We create a label that tells the user that we are starting our time-consuming operation.
        self.query_one("#status_label").update("Starting long operation...")
        # 2. We `await` the time-consuming operation so that the application remains responsive.
        await asyncio.sleep(5) # This is the non-blocking change
        # 3. We create a label that tells the user that the time-consuming operation has been concluded.
        self.query_one("#status_label").update("Long operation finished.")

    def action_load(self) -> None:
        self.query_one("#status_label").update("Loading data...")
        asyncio.create_task(self._do_long_operation())

if __name__ == "__main__":
    app = NonBlockingApp()
    app.run()
```

----------------------------------------

TITLE: Handling Custom Messages in Textual Main Screen Python
DESCRIPTION: This Python snippet illustrates how the Main screen listens for and reacts to the Activity.Moved message emitted by an Activity widget. Upon receiving the message, it calls save_activity_list(), demonstrating a decoupled way to trigger screen-level actions based on child widget events.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/on-dog-food-the-original-metaverse-and-not-being-bored.md#_snippet_3>

LANGUAGE: Python
CODE:

```
    def on_activity_moved( self, _: Activity.Moved ) -> None:
        """React to an activity being moved."""
        self.save_activity_list()
```

----------------------------------------

TITLE: BitSwitch: Sending Custom Messages on Switch Change (byte02.py)
DESCRIPTION: This code snippet demonstrates how to extend the `ByteEditor` widget so that clicking any of the 8 `BitSwitch` widgets updates the decimal value. It adds a custom message to `BitSwitch` that is caught in the `ByteEditor`. The `BitSwitch` widget now has an `on_switch_changed` method which will handle a `Switch.Changed` message, sent when the user clicks a switch. This is used to store the new value of the bit, and sent a new custom message, `BitSwitch.BitChanged`.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_29>

LANGUAGE: python
CODE:

```
class BitSwitch(Widget):
    
```

----------------------------------------

TITLE: Binding Textual Actions to Keys (Python)
DESCRIPTION: This example demonstrates how to bind Textual actions to specific keyboard keys using the `BINDINGS` class attribute. Pressing 'r', 'g', or 'b' will trigger the `set_background` action with the corresponding color, providing an alternative input method to links for executing actions.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/actions.md#_snippet_3>

LANGUAGE: python
CODE:

```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class ActionsApp(App):
    BINDINGS = [
        ("r", "set_background('red')", "Set Red Background"),
        ("g", "set_background('green')", "Set Green Background"),
        ("b", "set_background('blue')", "Set Blue Background"),
    ]

    def action_set_background(self, color: str) -> None:
        self.screen.styles.background = color

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Static("Press 'r', 'g', or 'b' to change background.")

if __name__ == "__main__":
    ActionsApp().run()
```

----------------------------------------

TITLE: Posting Messages (Textual 0.14.0+) - Python
DESCRIPTION: This snippet shows the simplified message posting in Textual 0.14.0 and later. The `await` keyword is no longer required for `post_message`, and the `sender` argument is automatically handled by the framework, reducing boilerplate.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-14-0.md#_snippet_1>

LANGUAGE: Python
CODE:

```
self.post_message(self.Change(item=self.item))
```

----------------------------------------

TITLE: World Clock App with Data Binding - Python
DESCRIPTION: This Python code demonstrates data binding in a Textual application. It binds the app's `time` reactive attribute to the `time` attribute of the `WorldClock` widgets, eliminating the need for a separate watcher to update the clocks.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_24>

LANGUAGE: python
CODE:

```
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import pytz
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class TimeDisplay(Static):
    
```

----------------------------------------

TITLE: Handling Button Presses for Animation Control in Textual (Python)
DESCRIPTION: This Python snippet demonstrates how to handle button press events in a Textual application. It dynamically calls methods on widgets based on button IDs to pause or resume animations and updates the disabled state of the buttons to reflect the current interaction, ensuring only one button is active at a time. It relies on Textual's `query` method and attribute introspection.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_9>

LANGUAGE: python
CODE:

```
                getattr(widget, pressed_id)()  # (5)!

            for button in self.query(Button):  # (6)!
                if button.id == pressed_id:
                    button.disabled = True
                else:
                    button.disabled = False


    LiveDisplayApp().run()
```

----------------------------------------

TITLE: Awaiting Widget Mounting for Immediate Interaction in Textual Python
DESCRIPTION: This snippet provides the solution to the asynchronous mounting problem. By making the event handler `async` and `await`ing `self.mount(Welcome())`, it ensures that the `Welcome` widget and its children (like the Button) are fully mounted and available in the DOM before attempting to query and modify them, preventing `NoMatches` exceptions.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_4>

LANGUAGE: python
CODE:

```
from textual.app import App
from textual.widgets import Button, Welcome


class WelcomeApp(App):
    async def on_key(self) -> None:
        await self.mount(Welcome())
        self.query_one(Button).label = "YES!"


if __name__ == "__main__":
    app = WelcomeApp()
    app.run()
```

----------------------------------------

TITLE: Defining a Widget with Scoped CSS in Textual (Python)
DESCRIPTION: This Python snippet defines a `MyWidget` class inheriting from `Widget` and demonstrates the use of `DEFAULT_CSS` to apply styles. Prior to Textual 0.38.0, the `Label` rule would style all `Label` widgets globally. With 0.38.0, the CSS is automatically scoped to only affect `Label` instances within `MyWidget`, preventing unintended global style impacts. The `compose` method yields two `Label` instances.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-38-0.md#_snippet_0>

LANGUAGE: python
CODE:

```
class MyWidget(Widget):
    DEFAULT_CSS = """
    MyWidget {
        height: auto;
        border: magenta;
    }
    Label {
        border: solid green;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("foo")
        yield Label("bar")
```

----------------------------------------

TITLE: Defining Custom Messages (Textual 0.14.0+) - Python
DESCRIPTION: This code defines a custom `Changed` message class for `MyWidget` in Textual 0.14.0 and later. The `sender` argument is no longer required in the `__init__` method, simplifying message class definitions as the framework handles it automatically.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-14-0.md#_snippet_3>

LANGUAGE: Python
CODE:

```
class MyWidget(Widget):

    class Changed(Message):
        """My widget change event."""
        def __init__(self, item_index:int) -> None:
            self.item_index = item_index
            super().__init__()
```

----------------------------------------

TITLE: Handling Button Presses with Textual (Python)
DESCRIPTION: This method serves as the event handler for button press events in the Textual application. It determines which button was pressed based on its ID, retrieves the associated `TimeDisplay` widget, and invokes the corresponding action (`start`, `stop`, or `reset`). It also manages a CSS class ('started') on the parent widget to visually indicate the stopwatch's state.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_11>

LANGUAGE: Python
CODE:

```
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)
        if button_id == "start":
            time_display.start()
            self.add_class("started")
        elif button_id == "stop":
            time_display.stop()
            self.remove_class("started")
        elif button_id == "reset":
            time_display.reset()
```

----------------------------------------

TITLE: Safe Markup Variable Substitution with Content.from_markup - Textual Python
DESCRIPTION: This snippet demonstrates the recommended and secure way to insert variables into Textual markup using the Content.from_markup method. By passing variables as keyword arguments, Textual intelligently handles the substitution, ensuring that any square brackets within the variable's value are treated as literal text rather than markup, thereby preventing styling conflicts and maintaining display integrity.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_29>

LANGUAGE: python
CODE:

```
return Content.from_markup("hello [bold]$name[/bold]!", name=name)
```

----------------------------------------

TITLE: Implementing TimeDisplay Widget in Textual (Python)
DESCRIPTION: This snippet defines the `TimeDisplay` widget, a `Static` subclass in Textual, used to display elapsed time. It leverages Textual's reactive attributes and `set_interval` to automatically update the displayed time, with `on_mount` setting up a timer, `update_time` calculating the current time, and `watch_time` rendering the time string when the `time` attribute changes.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_2>

LANGUAGE: Python
CODE:

```
from time import monotonic

from textual.reactive import reactive
from textual.widgets import Static


class TimeDisplay(Static):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update time to current."""
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")
```

----------------------------------------

TITLE: Handling Asynchronous Widget Mounting Issues in Textual Python
DESCRIPTION: This snippet demonstrates a common issue when dynamically mounting widgets in Textual. It attempts to query and modify a child widget (Button) immediately after calling `self.mount(Welcome())` without awaiting, which often leads to a `NoMatches` exception because the widget has not yet been fully mounted and rendered.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_3>

LANGUAGE: python
CODE:

```
from textual.app import App
from textual.widgets import Button, Welcome


class WelcomeApp(App):
    def on_key(self) -> None:
        self.mount(Welcome())
        self.query_one(Button).label = "YES!" # (1)!


if __name__ == "__main__":
    app = WelcomeApp()
    app.run()
```

----------------------------------------

TITLE: Launching Textual Markup Playground (Python)
DESCRIPTION: This command launches the interactive Textual markup playground, allowing users to experiment with content markup and see live results. It's executed directly from the command line using Python's module execution feature.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_0>

LANGUAGE: bash
CODE:

```
python -m textual.markup
```

----------------------------------------

TITLE: Displaying Full Help Documentation with Rich Inspect (Python)
DESCRIPTION: This snippet illustrates how to use `rich.inspect` with both `methods=True` and `help=True` to display the full, unabbreviated documentation for an object's attributes and methods. This is useful for in-depth understanding.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/rich-inspect.md#_snippet_2>

LANGUAGE: Python
CODE:

```
>>> inspect(text_file, methods=True, help=True)
```

----------------------------------------

TITLE: Creating a Real-time Clock Application with Textual Python
DESCRIPTION: This Textual application displays the current time using the `Digits` widget. It updates the time every second by querying the widget and formatting the `datetime.now().time()` output. The CSS aligns the display to the center.
SOURCE: <https://github.com/textualize/textual/blob/main/README.md#_snippet_0>

LANGUAGE: Python
CODE:

```
"""
An App to show the current time.
"""

from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Digits


class ClockApp(App):
    CSS = """
    Screen { align: center middle; }
    Digits { width: auto; }
    """

    def compose(self) -> ComposeResult:
        yield Digits("")

    def on_ready(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        clock = datetime.now().time()
        self.query_one(Digits).update(f"{clock:%T}")


if __name__ == "__main__":
    app = ClockApp()
    app.run()
```

----------------------------------------

TITLE: Handling Button Events and Toggling CSS Classes (Python)
DESCRIPTION: Implements an `on_button_pressed` event handler in Textual to respond to button clicks. It demonstrates how to add or remove the "started" CSS class on a widget using `add_class()` and `remove_class()` methods to dynamically change its appearance based on user interaction.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_9>

LANGUAGE: python
CODE:

```
# stopwatch04.py

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button, Header, Footer, Static

class Stopwatch(Static):
    """A stopwatch widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the stopwatch."""
        yield Static("00:00:00.00", id="time")
        with Container(id="buttons"):
            yield Button("Start", id="start", variant="success")
            yield Button("Stop", id="stop", variant="error")
            yield Button("Reset", id="reset")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when a button is pressed."""
        button_id = event.button.id
        if button_id == "start":
            self.add_class("started")
        elif button_id == "stop":
            self.remove_class("started")


class StopwatchApp(App):
    """Textual app for the Stopwatch."""

    CSS_PATH = "stopwatch04.tcss"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Container(
            Stopwatch(),
            Stopwatch(),
            Stopwatch(),
            id="stopwatches",
        )


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()

```

----------------------------------------

TITLE: Applying Margin Styles in CSS
DESCRIPTION: This snippet demonstrates various ways to apply margin to a widget using CSS. It shows shorthand notations for setting uniform margin, vertical/horizontal margins, and individual margins for all four sides (top, right, bottom, left). It also includes examples for setting margin on each side independently using `margin-top`, `margin-right`, `margin-bottom`, and `margin-left`.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/styles/margin.md#_snippet_1>

LANGUAGE: CSS
CODE:

```
/* Set margin of 1 around all edges */
margin: 1;
/* Set margin of 2 on the top and bottom edges, and 4 on the left and right */
margin: 2 4;
/* Set margin of 1 on the top, 2 on the right,
                 3 on the bottom, and 4 on the left */
margin: 1 2 3 4;

margin-top: 1;
margin-right: 2;
margin-bottom: 3;
margin-left: 4;
```

----------------------------------------

TITLE: Setting Widget Padding in Python
DESCRIPTION: This snippet illustrates how to programmatically set padding for a Textual widget using its `styles.padding` attribute in Python. It demonstrates setting uniform padding with a single integer, vertical and horizontal padding with a 2-integer tuple, and distinct padding for all four edges (top, right, bottom, left) with a 4-integer tuple. Note that individual padding properties like `padding-top` are not directly settable via the Python API.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/styles/padding.md#_snippet_1>

LANGUAGE: Python
CODE:

```
# Set padding of 1 around all edges
widget.styles.padding = 1
# Set padding of 2 on the top and bottom edges, and 4 on the left and right
widget.styles.padding = (2, 4)
# Set padding of 1 on top, 2 on the right, 3 on the bottom, and 4 on the left
widget.styles.padding = (1, 2, 3, 4)
```

----------------------------------------

TITLE: Custom Widget with CSS Styling in Textual (Python)
DESCRIPTION: This code defines a Textual app that includes a custom widget (`Hello`) and applies CSS styling to it. The CSS targets the `Hello` widget and sets its background color to green.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_1>

LANGUAGE: Python
CODE:

```
class Hello(Widget):
    
```

----------------------------------------

TITLE: Implementing Thread Workers with urllib.request in Textual (Python)
DESCRIPTION: This example illustrates the use of thread workers in Textual for non-asynchronous operations, specifically fetching weather data using urllib.request. It shows how to use the @work(thread=True) decorator and how to check for cancellation manually within a thread worker using get_current_worker to ensure graceful exit, as direct cancellation like coroutines is not possible.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/workers.md#_snippet_1>

LANGUAGE: python
CODE:

```
import urllib.request
import json
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.worker import work, get_current_worker, WorkerState

class WeatherAppThread(App):
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Button("Get Weather (Thread)", id="get_weather_thread")
        yield Label("Weather: N/A", id="weather_label_thread")

    @work(thread=True, exclusive=True)
    def get_weather_data_thread(self) -> str:
        worker = get_current_worker()
        try:
            with urllib.request.urlopen("https://api.weather.gov/points/39.7456,-97.0892") as url:
                if worker.is_cancelled: # Manual cancellation check
                    return "Cancelled"
                data = json.loads(url.read().decode())
                if worker.is_cancelled: # Manual cancellation check
                    return "Cancelled"
                city = data["properties"]["relativeLocation"]["properties"]["city"]
                # Simulate some work
                for _ in range(2):
                    if worker.is_cancelled:
                        return "Cancelled"
                    self.call_from_thread(lambda: self.log("Working...")) # Call UI from thread
                    import time
                    time.sleep(0.1)
                return city
        except Exception as e:
            self.call_from_thread(lambda: self.log(f"Thread worker error: {e}"))
            raise

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "get_weather_thread":
            self.run_worker(self.get_weather_data_thread(), exit_on_error=False)

    def on_worker_state_changed(self, event: WorkerState.StateChanged) -> None:
        self.log(f"Thread Worker {event.worker.name} changed state to {event.state.name}")
        if event.state == WorkerState.SUCCESS:
            self.query_one("#weather_label_thread", Label).update(f"Weather: {event.worker.result}")
        elif event.state == WorkerState.ERROR:
            self.query_one("#weather_label_thread", Label).update(f"Error: {event.worker.error}")
        elif event.state == WorkerState.CANCELLED:
            self.query_one("#weather_label_thread", Label).update("Weather: Cancelled")

if __name__ == "__main__":
    app = WeatherAppThread()
    app.run()
```

----------------------------------------

TITLE: Declaring Threaded Workers in Textual Python
DESCRIPTION: This snippet demonstrates how to define a threaded worker function in Textual applications by applying the @work(thread=True) decorator. This ensures the decorated function executes in a separate thread, preventing the main UI thread from blocking during long-running operations. It is required for Textual versions 0.31.0 and later to explicitly declare threaded workers.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/FAQ.md#_snippet_3>

LANGUAGE: Python
CODE:

```
@work(thread=True)
def run_in_background():
    ...
```

----------------------------------------

TITLE: Dispatching Button Press Events with the @on Decorator in Textual Python
DESCRIPTION: This snippet showcases the new `@on` decorator introduced in Textual 0.23.0 for more granular event dispatching. It allows specific methods to handle `Button.Pressed` events based on CSS selectors (e.g., `#id` for ID, `.class` for class names), eliminating the need for large `if` statements within a single handler. This approach enhances code readability and maintainability. It requires the `textual` library and the `@on` decorator.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-23-0.md#_snippet_1>

LANGUAGE: Python
CODE:

```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Container
from textual.on import on

class MyButtonApp(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Container():
            yield Button("Bell", id="bell")
            yield Button("Toggle Dark", classes="toggle dark")
            yield Button("Quit", id="quit")
            yield Label("Press a button!")

    @on(Button.Pressed, "#bell")
    def handle_bell_button(self) -> None:
        """Handles the bell button pressed event."""
        self.query_one(Label).update("Bell button pressed!")

    @on(Button.Pressed, ".toggle.dark")
    def handle_toggle_dark_button(self) -> None:
        """Handles the toggle dark button pressed event."""
        self.query_one(Label).update("Toggle Dark button pressed!")

    @on(Button.Pressed, "#quit")
    def handle_quit_button(self) -> None:
        """Handles the quit button pressed event."""
        self.query_one(Label).update("Quit button pressed!")
        self.exit()

if __name__ == "__main__":
    app = MyButtonApp()
    app.run()
```

----------------------------------------

TITLE: Writing a Basic Snapshot Test with snap_compare in Python
DESCRIPTION: This snippet demonstrates how to write a basic snapshot test in Textual by injecting the `snap_compare` fixture into a test function. It asserts the comparison of a Textual app's output, specified by its file path, against a saved snapshot. The `snap_compare` fixture supports additional arguments, such as `press`, for simulating user interactions.
SOURCE: <https://github.com/textualize/textual/blob/main/notes/snapshot_testing.md#_snippet_0>

LANGUAGE: Python
CODE:

```
def test_grid_layout_basic_overflow(snap_compare):
    assert snap_compare("docs/examples/guide/layout/grid_layout2.py")
```

----------------------------------------

TITLE: Creating a Determinate Progress Bar with Rich's `track` function (Python)
DESCRIPTION: This snippet demonstrates how to create a determinate progress bar using Rich's `track` function. It simulates a task with a known number of steps (20 in this case) and updates the progress bar as each step is completed. The `time.sleep` call simulates work being done.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_0>

LANGUAGE: Python
CODE:

```
import time
from rich.progress import track

for _ in track(range(20), description="Processing..."):
    time.sleep(0.5)  # Simulate work being done
```

----------------------------------------

TITLE: Defining a Custom Textual Widget (Python)
DESCRIPTION: This Python snippet defines a simple custom widget class named `Alert` that inherits from `textual.widgets.Static`. This custom widget is later used to demonstrate how Textual CSS type selectors can target specific widget classes.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_4>

LANGUAGE: python
CODE:

```
from textual.widgets import Static

class Alert(Static):
    pass
```

----------------------------------------

TITLE: Applying Column Span in Textual Grid Layout (Python/CSS)
DESCRIPTION: This snippet demonstrates how to make a grid cell span multiple columns using Textual's CSS. It assigns an ID to a widget in Python's `compose` method and then applies `column-span: 2;` and `tint: magenta 40%;` in the TUI CSS to expand the widget horizontally and highlight it.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_10>

LANGUAGE: python
CODE:

```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

class GridApp(App):
    CSS_PATH = "grid_layout5_col_span.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Static("One")
            yield Static("Two", id="two")
            yield Static("Three")
            yield Static("Four")
            yield Static("Five")
            yield Static("Six")
        yield Footer()

if __name__ == "__main__":
    app = GridApp()
    app.run()
```

LANGUAGE: css
CODE:

```
Screen {
    layout: grid;
    grid-size: 3 2;
}

#two {
    column-span: 2;
    tint: magenta 40%;
}
```

----------------------------------------

TITLE: Defining a Textual App with Custom Arguments in Python
DESCRIPTION: This snippet illustrates how to define a Textual `App` class (`Greetings`) that accepts custom arguments (`greeting` and `to_greet`) by overriding the `__init__` method. These arguments are stored as instance attributes and then used within the `compose` method to dynamically generate the UI content.
SOURCE: <https://github.com/textualize/textual/blob/main/questions/pass-args-to-app.question.md#_snippet_0>

LANGUAGE: python
CODE:

```
from textual.app import App, ComposeResult
from textual.widgets import Static

class Greetings(App[None]):

    def __init__(self, greeting: str="Hello", to_greet: str="World") -> None:
        self.greeting = greeting
        self.to_greet = to_greet
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(f"{self.greeting}, {self.to_greet}")
```

----------------------------------------

TITLE: Defining Equivalent Textual Message Handlers (Python)
DESCRIPTION: This snippet illustrates the equivalence between defining a Textual message handler using the `@on` decorator and using the `on_` naming convention. Both methods achieve the same result of handling a `Button.Pressed` event.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/guide/events.md#_snippet_2>

LANGUAGE: python
CODE:

```
@on(Button.Pressed)
def handle_button_pressed(self):
    ...

def on_button_pressed(self):
    ...
```

----------------------------------------

TITLE: Handling User Input Submission in Textual Python
DESCRIPTION: This asynchronous event handler is triggered when a user submits text in the `Input` widget. It clears the input, adds the user's prompt to the chat view, mounts a new `Response` widget for the LLM's reply, anchors it to the bottom, and then calls `send_prompt` to process the input.
SOURCE: <https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_6>

LANGUAGE: Python
CODE:

```
    @on(Input.Submitted)
    async def on_input(self, event: Input.Submitted) -> None:
        chat_view = self.query_one("#chat-view")
        event.input.clear()
        await chat_view.mount(Prompt(event.value))
        await chat_view.mount(response := Response())
        response.anchor()
        self.send_prompt(event.value, response)
```
