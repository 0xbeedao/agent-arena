TITLE: Basic Prompt with prompt-toolkit (Python)
DESCRIPTION: This Python snippet demonstrates the simplest usage of `prompt_toolkit` to get input from the user. It calls the `prompt` function with a string message and then prints the returned user input. This mimics the behavior of Python's built-in `input` or `raw_input`. Requires the `prompt_toolkit` library installed.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/getting_started.rst#_snippet_2>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt

text = prompt("Give me some input: ")
print(f"You said: {text}")
```

----------------------------------------

TITLE: Implementing SQLite REPL Main Loop - Python
DESCRIPTION: Contains the core logic for the SQLite REPL application. It establishes a connection to the specified database, initializes a `PromptSession` with configured syntax highlighting (SqlLexer), autocompletion (sql_completer), and styling. The code then enters a loop to repeatedly prompt the user for SQL input, execute the command via the database connection, and print results or any exceptions encountered. It includes basic handling for keyboard interrupts (Ctrl-C) and end-of-file (Ctrl-D) signals.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_9>

LANGUAGE: python
CODE:

```
def main(database):
        connection = sqlite3.connect(database)
        session = PromptSession(
            lexer=PygmentsLexer(SqlLexer), completer=sql_completer, style=style)

        while True:
            try:
                text = session.prompt('> ')
            except KeyboardInterrupt:
                continue  # Control-C pressed. Try again.
            except EOFError:
                break  # Control-D pressed.

            with connection:
                try:
                    messages = connection.execute(text)
                except Exception as e:
                    print(repr(e))
                else:
                    for message in messages:
                        print(message)

        print('GoodBye!')
```

----------------------------------------

TITLE: Simple Input Prompt with prompt_toolkit in Python
DESCRIPTION: Demonstrates the basic usage of the `prompt` function from `prompt_toolkit.shortcuts` to ask the user for text input. It functions similarly to Python's built-in `input` or `raw_input` but provides basic Emacs key bindings. The returned text is then printed to the console.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_0>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt

text = prompt("Give me some input: ")
print(f"You said: {text}")
```

----------------------------------------

TITLE: Getting User Input using Prompt Toolkit - Python
DESCRIPTION: Demonstrates the simplest use of the prompt_toolkit library. It imports the `prompt` function to ask the user for input and then prints the received input. This snippet shows the basic interaction pattern.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/README.rst#_snippet_2>

LANGUAGE: Python
CODE:

```
from prompt_toolkit import prompt

if __name__ == '__main__':
    answer = prompt('Give me some input: ')
    print('You said: %s' % answer)
```

----------------------------------------

TITLE: Read User Input using prompt_toolkit
DESCRIPTION: This Python snippet demonstrates the most basic use of prompt_toolkit's `prompt()` function to read a single line of input from the user and print it back. It is wrapped in a standard `main` function and guarded by `if __name__ == '__main__':`.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_1>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt

def main():
    text = prompt('> ')
    print('You entered:', text)

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Running Simple Full Screen prompt_toolkit Application Python
DESCRIPTION: Creates and runs a minimal full-screen prompt_toolkit application instance. This example shows the basic structure, initializing the `Application` object with `full_screen=True` to use the alternate screen buffer and calling `run()` to start the event loop. It results in a default application message because no layout is specified.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/full_screen_apps.rst#_snippet_0>

LANGUAGE: python
CODE:

```
from prompt_toolkit import Application

app = Application(full_screen=True)
app.run()
```

----------------------------------------

TITLE: Displaying an Input Dialog in Prompt Toolkit
DESCRIPTION: Use the input_dialog function to prompt the user for text input. It displays a title, a text label, and an input field. The .run() method displays the dialog and returns the string entered by the user when they submit the form (usually by pressing Enter). An optional password=True argument can turn this into a password input field.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_1>

LANGUAGE: python
CODE:

```
from prompt_toolkit.shortcuts import input_dialog

text = input_dialog(
    title='Input dialog example',
    text='Please type your name:').run()
```

----------------------------------------

TITLE: Defining Basic Key Bindings in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates how to create a KeyBindings instance and define simple key bindings using the `@bindings.add` decorator. It shows examples for binding a single character ('a') and a control key combination ('c-t'), executing a function when the key is pressed.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_0>

LANGUAGE: python
CODE:

```
from prompt_toolkit.key_binding import KeyBindings

bindings = KeyBindings()

@bindings.add('a')
def _(event):
    " Do something if 'a' has been pressed. "
    ...


@bindings.add('c-t')
def _(event):
    " Do something if Control-T has been pressed. "
    ...
```

----------------------------------------

TITLE: Creating Password Input Prompt (Python)
DESCRIPTION: Shows how to create a password input field using prompt-toolkit where the typed characters are replaced by asterisks (`*`). This is achieved by setting the `is_password=True` flag when calling the `prompt` function, preventing sensitive input from being displayed directly. Requires `prompt_toolkit`.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_35>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt

prompt("Enter password: ", is_password=True)
```

----------------------------------------

TITLE: Using PromptSession with Default History - Python
DESCRIPTION: Demonstrates the standard way to use `prompt_toolkit.shortcuts.PromptSession`. By default, `PromptSession` includes an in-memory history, allowing users to recall previous inputs using arrow keys within the same session.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_19>

LANGUAGE: python
CODE:

```
from prompt_toolkit import PromptSession

session = PromptSession()

while True:
    session.prompt()
```

----------------------------------------

TITLE: Running prompt_toolkit Application in asyncio Python
DESCRIPTION: This snippet demonstrates how to run a prompt_toolkit Application within an existing asyncio event loop. It defines an async main function that creates an Application instance (placeholder ...) and uses the awaitable application.run_async() method to execute it, then runs the main coroutine using asyncio.get_event_loop().run_until_complete(). This is the recommended approach when embedding prompt_toolkit in an asyncio application.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/asyncio.rst#_snippet_0>

LANGUAGE: python
CODE:

```
from prompt_toolkit.application import Application
import asyncio

async def main():
    # Define application.
    application = Application(
        ...
    )

    result = await application.run_async()
    print(result)

asyncio.get_event_loop().run_until_complete(main())
```

----------------------------------------

TITLE: Using Asyncio Coroutine as prompt_toolkit Key Binding Handler Python
DESCRIPTION: This snippet shows how to define a key binding ('x') that executes an asyncio coroutine as its handler. The coroutine performs background tasks, printing 'hello' repeatedly above the prompt using `in_terminal` and pausing with `asyncio.sleep`, allowing the user to continue typing while the task runs.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_9>

LANGUAGE: Python
CODE:

```
from prompt_toolkit.application import in_terminal

@bindings.add('x')
async def print_hello(event):
    """
    Pressing 'x' will print 5 times "hello" in the background above the
    prompt.
    """
    for i in range(5):
        # Print hello above the current prompt.
        async with in_terminal():
            print('hello')

        # Sleep, but allow further input editing in the meantime.
        await asyncio.sleep(1)
```

----------------------------------------

TITLE: PromptSession Asynchronous Call (v3) - Python
DESCRIPTION: This snippet demonstrates the updated method for performing asynchronous prompt calls in prompt_toolkit version 3.0. The dedicated `prompt_async()` method replaces the `prompt()` method with the `async_=True` parameter used in version 2.0.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_4>

LANGUAGE: python
CODE:

```
# For 3.0
result = await PromptSession().prompt_async('Say something: ')
```

----------------------------------------

TITLE: Adding Simple Word Autocompletion with prompt_toolkit in Python
DESCRIPTION: Illustrates how to add basic autocompletion to a prompt using the `WordCompleter`. An instance of `WordCompleter` is created with a list of potential completion words and passed to the `completer` parameter of the `prompt` function. The completer suggests completions for the word immediately preceding the cursor.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_9>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

html_completer = WordCompleter(["<html>", "<body>", "<head>", "<title>"])
text = prompt("Enter HTML: ", completer=html_completer)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Adding Custom Key Bindings to Prompt (Python)
DESCRIPTION: This example demonstrates defining custom key bindings using `KeyBindings` and adding them to the prompt. It includes bindings for printing text using `run_in_terminal` and exiting the application, showing how to handle actions that affect the terminal output or application state.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_26>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.key_binding import KeyBindings

bindings = KeyBindings()

@bindings.add("c-t")
def _(event):
    " Say \"hello\" when `c-t` is pressed. "
    def print_hello():
        print("hello world")
    run_in_terminal(print_hello)

@bindings.add("c-x")
def _(event):
    " Exit when `c-x` is pressed. "
    event.app.exit()

text = prompt("> ", key_bindings=bindings)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Creating a Prompt Session with prompt_toolkit in Python
DESCRIPTION: Shows how to use the `PromptSession` class to create an input session instance. Calling the `prompt` method on this instance allows for multiple input requests while maintaining state, such as input history, between calls. Configuration options can be passed to the session instance or overridden per prompt call.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_1>

LANGUAGE: python
CODE:

```
from prompt_toolkit import PromptSession

# Create prompt object.
session = PromptSession()

# Do multiple input calls.
text1 = session.prompt()
text2 = session.prompt()
```

----------------------------------------

TITLE: Create a REPL Loop with PromptSession
DESCRIPTION: This Python snippet introduces `PromptSession` to create a continuous loop for the REPL. It handles `KeyboardInterrupt` (Ctrl+C) to continue the loop and `EOFError` (Ctrl+D) to break the loop and exit, providing a basic interactive session experience with history.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_2>

LANGUAGE: python
CODE:

```
from prompt_toolkit import PromptSession

def main():
    session = PromptSession()

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            print('You entered:', text)
    print('GoodBye!')

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Creating Custom Validator Class - Python
DESCRIPTION: Demonstrates creating a custom input validator by inheriting from `Validator` and implementing the `validate` method. It checks if the input text is purely numeric and raises a `ValidationError` with a custom message and cursor position if not.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_16>

LANGUAGE: python
CODE:

```
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

class NumberValidator(Validator):
    def validate(self, document):
        text = document.text

        if text and not text.isdigit():
            i = 0

            # Get index of first non numeric character.
            # We want to move the cursor here.
            for i, c in enumerate(text):
                if not c.isdigit():
                    break

            raise ValidationError(
                message="This input contains non-numeric characters",
                cursor_position=i
            )

number = int(prompt("Give a number: ", validator=NumberValidator()))
print(f"You said: {number}")
```

----------------------------------------

TITLE: Creating Basic Custom Completer Class - Python
DESCRIPTION: Demonstrates the minimum implementation for a custom completer by inheriting from `Completer` and overriding the `get_completions` generator method. It yields a simple completion with a start position.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_11>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion

class MyCustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        yield Completion("completion", start_position=0)

text = prompt("> ", completer=MyCustomCompleter())
```

----------------------------------------

TITLE: Defining SQL Keywords for Completion - Python
DESCRIPTION: Defines a comprehensive list of SQL keywords using `WordCompleter` from `prompt_toolkit.completion`. This list serves as the source for autocompletion suggestions provided to the user as they type SQL commands in the REPL, enhancing usability. The completer is configured to ignore case.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_7>

LANGUAGE: python
CODE:

```
'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
        'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
        'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
        'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
        'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
        'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
        'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
        'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
        'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
        'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
        'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
        'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
        'without'], ignore_case=True)
```

----------------------------------------

TITLE: Displaying a Yes/No Confirmation Dialog in Prompt Toolkit
DESCRIPTION: Use the yes_no_dialog function to present a simple confirmation prompt to the user. It displays a title, a text label, and 'Yes'/'No' buttons. The .run() method displays the dialog and returns a boolean value (True for Yes, False for No) based on the user's selection.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_2>

LANGUAGE: python
CODE:

```
from prompt_toolkit.shortcuts import yes_no_dialog

result = yes_no_dialog(
    title='Yes/No dialog example',
    text='Do you want to confirm?').run()
```

----------------------------------------

TITLE: Combining Filters with Operators - prompt_toolkit Python
DESCRIPTION: Demonstrates combining `prompt_toolkit` filters using the negation (`~`) and logical OR (`|`) operators (`&` for AND is also supported) to create more complex conditional filters. The examples show how these compound filters are applied in key bindings to activate based on combined criteria, such as 'not searching' or 'searching OR has selection'.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/filters.rst#_snippet_4>

LANGUAGE: python
CODE:

```
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import has_selection, has_search

kb = KeyBindings()

@kb.add('c-t', filter=~is_searching)
def _(event):
    " Do something, but not while searching. "
    pass

@kb.add('c-t', filter=has_search | has_selection)
def _(event):
    " Do something, but only when searching or when there is a selection. "
    pass
```

----------------------------------------

TITLE: Add Syntax Highlighting to REPL Input
DESCRIPTION: This Python snippet integrates Pygments SQL lexer to add syntax highlighting to the user input within the REPL loop. It uses `PygmentsLexer` to wrap the `SqlLexer` and passes it to the `PromptSession` constructor.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_3>

LANGUAGE: python
CODE:

```
from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer

def main():
    session = PromptSession(lexer=PygmentsLexer(SqlLexer))

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            print('You entered:', text)
    print('GoodBye!')

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Adding Conditional Key Bindings to Prompt (Python)
DESCRIPTION: This snippet shows how to make a custom key binding active only when a specific condition is met. It uses the `@Condition` decorator and passes the condition filter to the `@bindings.add` method.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_27>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
import datetime

bindings = KeyBindings()

@Condition
def is_active():
    " Only activate key binding on the second half of each minute. "
    return datetime.datetime.now().second > 30

@bindings.add("c-t", filter=is_active)
def _(event):
    # ...
    pass

prompt("> ", key_bindings=bindings)
```

----------------------------------------

TITLE: Initializing NestedCompleter with Dictionary - Python
DESCRIPTION: Shows how to create a hierarchical completer from a nested dictionary where `None` indicates no further nesting. It then uses this completer with the `prompt` function to get user input.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_10>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter

completer = NestedCompleter.from_nested_dict({
    "show": {
        "version": None,
        "clock": None,
        "ip": {
            "interface": {"brief"}
        }
    },
    "exit": None,
})

text = prompt("# ", completer=completer)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Using Filter in Key Binding - prompt_toolkit Python
DESCRIPTION: Explains how to use a `prompt_toolkit` filter, such as `is_searching`, within the `filter` parameter of the `@kb.add` decorator on a `KeyBindings` instance. This ensures that the associated key binding (`c-t`) only triggers the decorated function when the filter evaluates to `True`, enabling conditional key press handling.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/filters.rst#_snippet_2>

LANGUAGE: python
CODE:

```
from prompt_toolkit.key_binding import KeyBindings

kb = KeyBindings()

@kb.add('c-t', filter=is_searching)
def _(event):
    # Do, something, but only when searching.
    pass
```

----------------------------------------

TITLE: Displaying a Checkbox List Dialog in Prompt Toolkit
DESCRIPTION: Use the checkboxlist_dialog function to display a dialog with a list of choices where the user can select multiple options, presented as checkboxes. Choices are provided as a list of tuples (return value, display text). The .run() method displays the dialog and returns a list of values corresponding to the selected checkbox options.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_5>

LANGUAGE: python
CODE:

```
from prompt_toolkit.shortcuts import checkboxlist_dialog

results_array = checkboxlist_dialog( 
    title="CheckboxList dialog", 
    text="What would you like in your breakfast ?",
    values=[ 
        ("eggs", "Eggs"),
        ("bacon", "Bacon"),
        ("croissants", "20 Croissants"),
        ("daily", "The breakfast of the day")
    ] 
).run()
```

----------------------------------------

TITLE: Attaching a Filter to a Key Binding in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates how to make a key binding conditional by attaching a Filter, specifically a Condition instance. The key binding ('c-t') will only be active and trigger its associated function if the `is_active` condition function returns `True` when evaluated.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_5>

LANGUAGE: python
CODE:

```
from prompt_toolkit.filters import Condition
import datetime

@Condition
def is_active():
    " Only activate key binding on the second half of each minute. "
    return datetime.datetime.now().second > 30

@bindings.add('c-t', filter=is_active)
def _(event):
    # ...
    pass
```

----------------------------------------

TITLE: Displaying a Radio List Dialog in Prompt Toolkit
DESCRIPTION: Use the radiolist_dialog function to display a dialog with a list of mutually exclusive choices, presented as radio buttons. Choices are provided as a list of tuples, where each tuple contains the return value (first element) and the text to display (second element). The .run() method displays the dialog and returns the value associated with the selected radio option.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_4>

LANGUAGE: python
CODE:

```
from prompt_toolkit.shortcuts import radiolist_dialog

result = radiolist_dialog( 
    title="RadioList dialog", 
    text="Which breakfast would you like ?", 
    values=[ 
        ("breakfast1", "Eggs and beacon"), 
        ("breakfast2", "French breakfast"), 
        ("breakfast3", "Equestrian breakfast") 
    ] 
).run()
```

----------------------------------------

TITLE: Displaying a Button Dialog in Prompt Toolkit
DESCRIPTION: Use the button_dialog function to offer the user choices represented by buttons. Buttons are defined as a list of tuples, where each tuple contains the button's label (string) and the value to be returned if that button is clicked. The .run() method displays the dialog and returns the value associated with the selected button.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_3>

LANGUAGE: python
CODE:

```
from prompt_toolkit.shortcuts import button_dialog

result = button_dialog(
    title='Button dialog example',
    text='Do you want to confirm?',
    buttons=[
        ('Yes', True),
        ('No', False),
        ('Maybe...', None)
    ],
).run()
```

----------------------------------------

TITLE: Conditionally Enabling/Disabling Key Binding Sets in prompt_toolkit Python
DESCRIPTION: This snippet shows how to wrap an entire set of KeyBindings (`my_bindings`) within a ConditionalKeyBindings object. The wrapped bindings will only be active if the provided filter (`is_active` condition) evaluates to `True`.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_6>

LANGUAGE: python
CODE:

```
from prompt_toolkit.key_binding import ConditionalKeyBindings
import datetime

@Condition
def is_active():
    " Only activate key binding on the second half of each minute. "
    return datetime.datetime.now().second > 30

bindings = ConditionalKeyBindings(
    key_bindings=my_bindings,
    filter=is_active)

```

----------------------------------------

TITLE: Displaying a Message Dialog in Prompt Toolkit
DESCRIPTION: Use the message_dialog function to display a simple message box with a title and text. The .run() method is called to display the dialog and block until the user dismisses it (usually by pressing Enter). This dialog does not return a value.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_0>

LANGUAGE: python
CODE:

```
from prompt_toolkit.shortcuts import message_dialog

message_dialog(
    title='Example dialog window',
    text='Do you want to continue?\nPress ENTER to quit.').run()
```

----------------------------------------

TITLE: Adding Pygments Syntax Highlighting to prompt_toolkit in Python
DESCRIPTION: Illustrates how to enable syntax highlighting by providing a `lexer` parameter to the `prompt` function. This example uses an `HtmlLexer` from Pygments, wrapped in `PygmentsLexer`, to apply highlighting based on HTML syntax rules. The default prompt_toolkit style includes the default Pygments colorscheme.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_2>

LANGUAGE: python
CODE:

```
from pygments.lexers.html import HtmlLexer
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.lexers import PygmentsLexer

text = prompt("Enter HTML: ", lexer=PygmentsLexer(HtmlLexer))
print(f"You said: {text}")
```

----------------------------------------

TITLE: Enabling Mouse Support in Prompt (Python)
DESCRIPTION: Shows how to enable limited mouse support for a prompt-toolkit input field. This includes functionality for positioning the cursor, scrolling in multiline inputs, and clicking in the autocompletion menu. Mouse support is activated by passing the `mouse_support=True` option to the `prompt` function. Requires `prompt_toolkit`.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_33>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt

prompt("What is your name: ", mouse_support=True)
```

----------------------------------------

TITLE: Using PromptSession with Auto-suggestion from History (Python)
DESCRIPTION: This snippet demonstrates how to use `PromptSession` with `AutoSuggestFromHistory` to provide suggestions to the user based on previous inputs stored in an `InMemoryHistory`. A loop continuously prompts the user, retrieves input, and prints it back.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_21>

LANGUAGE: python
CODE:

```
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

session = PromptSession()

while True:
    text = session.prompt("> ", auto_suggest=AutoSuggestFromHistory())
    print(f"You said: {text}")
```

----------------------------------------

TITLE: Displaying Progress for Generator with Total in prompt_toolkit Python
DESCRIPTION: Explains how to provide the total number of items explicitly using the `total` parameter when the iterable itself cannot determine its length (e.g., a generator). This allows the progress bar to display completion percentage and estimated time. Requires `prompt_toolkit` and `time`.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_1>

LANGUAGE: python
CODE:

```
def some_iterable():
    yield ...

with ProgressBar() as pb:
    for i in pb(some_iterable(), total=1000):
        time.sleep(.01)
```

----------------------------------------

TITLE: Printing HTML fg/bg Attributes with prompt_toolkit
DESCRIPTION: Demonstrates setting both foreground (`fg`) and background (`bg`) colors for text within an HTML tag using attributes, supporting both ANSI and named colors.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_4>

LANGUAGE: python
CODE:

```
# Colors from the ANSI palette.
print_formatted_text(HTML('<aaa fg="ansiwhite" bg="ansigreen">White on green</aaa>'))
```

----------------------------------------

TITLE: Printing HTML Color Tags with prompt_toolkit
DESCRIPTION: Shows how to use the `HTML` class to specify foreground colors using tag names, including ANSI palette colors (e.g., `<ansired>`) and named colors (e.g., `<skyblue>`).
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_3>

LANGUAGE: python
CODE:

```
# Colors from the ANSI palette.
print_formatted_text(HTML('<ansired>This is red</ansired>'))
print_formatted_text(HTML('<ansigreen>This is green</ansigreen>'))

# Named colors (256 color palette, or true color, depending on the output).
print_formatted_text(HTML('<skyblue>This is sky blue</skyblue>'))
print_formatted_text(HTML('<seagreen>This is sea green</seagreen>'))
print_formatted_text(HTML('<violet>This is violet</violet>'))
```

----------------------------------------

TITLE: Initializing Prompt with Default Value (Python)
DESCRIPTION: Demonstrates a basic interactive prompt using prompt-toolkit. It sets a default value for the input field by retrieving the current user's name using `getpass.getuser()` from the standard library's `getpass` module. Requires `prompt_toolkit` and `getpass`.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_32>

LANGUAGE: python
CODE:

```
from prompt_toolkit import prompt
import getpass

prompt("What is your name: ", default=f"{getpass.getuser()}")
```

----------------------------------------

TITLE: Style the Completion Menu Appearance
DESCRIPTION: This Python snippet demonstrates how to customize the appearance of the auto-completion menu. It creates a `prompt_toolkit.styles.Style` instance with specific rules for 'completion-menu' and 'scrollbar' elements and passes the style to the `PromptSession` constructor.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_5>

LANGUAGE: python
CODE:

```
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

sql_completer = WordCompleter([
    'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
    'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
    'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
    'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
    'current_time', 'current_timestamp', 'database', 'default',
    'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
    'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
    'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
    'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
    'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
    'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
    'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
    'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
    'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
    'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
    'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
    'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
    'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
    'without'], ignore_case=True)

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})

def main():
   session = PromptSession(
       lexer=PygmentsLexer(SqlLexer), completer=sql_completer, style=style)

   while True:
       try:
           text = session.prompt('> ')
       except KeyboardInterrupt:
           continue
       except EOFError:
           break
       else:
           print('You entered:', text)
   print('GoodBye!')

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Adding Global Key Binding to Exit Application - Python
DESCRIPTION: Illustrates how to register a global key binding (Ctrl-Q) to exit the prompt_toolkit application. It uses the `@kb.add('c-q')` decorator on a function that receives an event object. The handler function calls `event.app.exit()` to terminate the application's main loop, optionally returning a value.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/full_screen_apps.rst#_snippet_4>

LANGUAGE: python
CODE:

```
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings

kb = KeyBindings()

@kb.add('c-q')
def exit_(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `Application.run()` call. 
    """
    event.app.exit()

app = Application(key_bindings=kb, full_screen=True)
app.run()
```

----------------------------------------

TITLE: Merging Key Binding Sets in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates how to combine multiple KeyBindings instances into a single set using the `merge_key_bindings` function. This is useful for organizing key bindings from different parts of an application.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_7>

LANGUAGE: python
CODE:

```
from prompt_toolkit.key_binding import merge_key_bindings

bindings = merge_key_bindings([
    bindings1,
    bindings2,
])
```

----------------------------------------

TITLE: Merging Multiple prompt_toolkit Styles in Python
DESCRIPTION: This snippet illustrates how to combine multiple existing prompt_toolkit.styles.Style objects into a single, merged style. It demonstrates using the prompt_toolkit.styles.merge_styles function to combine several individual Style objects (style1, style2, style3) into a single, new Style object. This is useful for layering or combining different style definitions from various sources or components within an application.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_8>

LANGUAGE: python
CODE:

```
from prompt_toolkit.styles import merge_styles

style = merge_styles([
    style1,
    style2,
    style3
])
```

----------------------------------------

TITLE: Adding Key Bindings and Toolbar to prompt_toolkit Progress Bar Python
DESCRIPTION: Demonstrates how to pass a `KeyBindings` object to the `ProgressBar` to add custom keyboard shortcuts and how to display information using the `bottom_toolbar` parameter. It also shows using `patch_stdout` to ensure `print` statements appear correctly above the progress bar and how to use key bindings to control the progress (e.g., stopping it). Requires `prompt_toolkit`, its key bindings, HTML, stdout patching, `os`, `time`, and `signal`.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_6>

LANGUAGE: python
CODE:

```
from prompt_toolkit import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import ProgressBar

import os
import time
import signal

bottom_toolbar = HTML(' <b>[f]<\/b> Print "f" <b>[x]<\/b> Abort.')

# Create custom key bindings first.
kb = KeyBindings()
cancel = [False]

@kb.add('f')
def _(event):
        print('You pressed `f`.')

@kb.add('x')
def _(event):
        " Send Abort (control-c) signal. "
        cancel[0] = True
        os.kill(os.getpid(), signal.SIGINT)

# Use `patch_stdout`, to make sure that prints go above the
# application.
with patch_stdout():
        with ProgressBar(key_bindings=kb, bottom_toolbar=bottom_toolbar) as pb:
            for i in pb(range(800)):
                time.sleep(.01)

                # Stop when the cancel flag has been set.
                if cancel[0]:
                    break
```

----------------------------------------

TITLE: Add Auto-completion for SQL Keywords
DESCRIPTION: This Python snippet adds auto-completion functionality to the REPL using `prompt_toolkit.completion.WordCompleter`. It defines a list of SQLite keywords and passes the resulting `WordCompleter` instance to the `PromptSession` constructor.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_4>

LANGUAGE: python
CODE:

```
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer

sql_completer = WordCompleter([
    'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
    'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
    'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
    'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
    'current_time', 'current_timestamp', 'database', 'default',
    'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
    'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
    'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
    'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
    'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
    'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
    'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
    'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
    'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
    'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
    'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
    'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
    'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
    'without'], ignore_case=True)

def main():
    session = PromptSession(
        lexer=PygmentsLexer(SqlLexer), completer=sql_completer)

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            print('You entered:', text)
    print('GoodBye!')

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Printing HTML Basic Tags with prompt_toolkit
DESCRIPTION: Illustrates how to use the `prompt_toolkit.formatted_text.HTML` class to print text formatted using basic HTML-like tags such as `<b>`, `<i>`, and `<u>` for bold, italic, and underline.
SOURCE: <https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_2>

LANGUAGE: python
CODE:

```
from prompt_toolkit import print_formatted_text, HTML

print_formatted_text(HTML('<b>This is bold</b>'))
print_formatted_text(HTML('<i>This is italic</i>'))
print_formatted_text(HTML('<u>This is underlined</u>'))
```
