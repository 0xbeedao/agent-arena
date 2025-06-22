TITLE: Install LLM Tool
DESCRIPTION: Instructions for installing the LLM command-line tool using various package managers: pip, pipx, uv, and Homebrew.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/setup.md#_snippet_0>

LANGUAGE: bash
CODE:

```
pip install llm
```

LANGUAGE: bash
CODE:

```
pipx install llm
```

LANGUAGE: bash
CODE:

```
uv tool install llm
```

LANGUAGE: bash
CODE:

```
brew install llm
```

----------------------------------------

TITLE: Integrate and Use Anthropic Claude with LLM CLI
DESCRIPTION: Instructions for installing the LLM Anthropic plugin, setting up your API key, and running prompts with Anthropic Claude models.
SOURCE: <https://github.com/simonw/llm/blob/main/README.md#_snippet_3>

LANGUAGE: bash
CODE:

```
llm install llm-anthropic
```

LANGUAGE: bash
CODE:

```
llm keys set anthropic
# Paste Anthropic API key here
```

LANGUAGE: bash
CODE:

```
llm -m claude-4-opus 'Impress me with wild facts about turnips'
```

----------------------------------------

TITLE: Install and Use LLM Anthropic Plugin
DESCRIPTION: Steps to install the LLM plugin for Anthropic's Claude, configure the API key, and run a prompt using a Claude model.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/index.md#_snippet_3>

LANGUAGE: bash
CODE:

```
llm install llm-anthropic
llm keys set anthropic
# Paste Anthropic API key here
llm -m claude-4-opus 'Impress me with wild facts about turnips'
```

----------------------------------------

TITLE: Integrate and Use Google Gemini with LLM CLI
DESCRIPTION: Steps to install the LLM Gemini plugin, configure your API key, and execute prompts against Google Gemini models.
SOURCE: <https://github.com/simonw/llm/blob/main/README.md#_snippet_2>

LANGUAGE: bash
CODE:

```
llm install llm-gemini
```

LANGUAGE: bash
CODE:

```
llm keys set gemini
# Paste Gemini API key here
```

LANGUAGE: bash
CODE:

```
llm -m gemini-2.0-flash 'Tell me fun facts about Mountain View'
```

----------------------------------------

TITLE: Access Google Gemini Models via llm-gemini Plugin
DESCRIPTION: The llm-gemini plugin provides support for Google's Gemini models, allowing LLM users to leverage Google's advanced AI capabilities through a dedicated integration.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/directory.md#_snippet_1>

LANGUAGE: APIDOC
CODE:

```
Plugin: llm-gemini
  API Provider: Google
  Models Supported: Gemini models
  Purpose: Provides access to Google's Gemini models.
```

----------------------------------------

TITLE: llm prompt Command Line Interface Reference
DESCRIPTION: Detailed reference for the `llm prompt` command, used to execute prompts with language models, including options for model selection, system prompts, attachments, and output extraction.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/help.md#_snippet_1>

LANGUAGE: bash
CODE:

```
llm 'Capital of France?'
llm 'Capital of France?' -m gpt-4o
llm 'Capital of France?' -s 'answer in Spanish'
llm 'Extract text from this image' -a image.jpg
llm 'Describe' -a https://static.simonwillison.net/static/2024/pelicans.jpg
cat image | llm 'describe image' -a -
cat image | llm 'describe image' --at - image/jpeg
llm 'JavaScript function for reversing a string' -x
```

LANGUAGE: APIDOC
CODE:

```
Usage: llm prompt [OPTIONS] [PROMPT]

  Execute a prompt

Options:
  -s, --system TEXT               System prompt to use
  -m, --model TEXT                Model to use
  -d, --database FILE             Path to log database
  -q, --query TEXT                Use first model matching these strings
  -a, --attachment ATTACHMENT     Attachment path or URL or -
  --at, --attachment-type <TEXT TEXT>...
                                  Attachment with explicit mimetype,
                                  --at image.jpg image/jpeg
  -T, --tool TEXT                 Name of a tool to make available to the model
  --functions TEXT                Python code block or file path defining
                                  functions to register as tools
  --td, --tools-debug             Show full details of tool executions
  --ta, --tools-approve           Manually approve every tool execution
  --cl, --chain-limit INTEGER     How many chained tool responses to allow,
                                  default 5, set 0 for unlimited
  -o, --option <TEXT TEXT>...     key/value options for the model
  --schema TEXT                   JSON schema, filepath or ID
  --schema-multi TEXT             JSON schema to use for multiple results
  -f, --fragment TEXT             Fragment (alias, URL, hash or file path) to
                                  add to the prompt
  --sf, --system-fragment TEXT    Fragment to add to system prompt
  -t, --template TEXT             Template to use
  -p, --param <TEXT TEXT>...      Parameters for template
  --no-stream                     Do not stream output
  -n, --no-log                    Don't log to database
  --log                           Log prompt and response to the database
  -c, --continue                  Continue the most recent conversation.
  --cid, --conversation TEXT      Continue the conversation with the given ID.
  --key TEXT                      API key to use
  --save TEXT                     Save prompt with this template name
  --async                         Run prompt asynchronously
  -u, --usage                     Show token usage
  -x, --extract                   Extract first fenced code block
  --xl, --extract-last            Extract last fenced code block
  -h, --help                      Show this message and exit.
```

----------------------------------------

TITLE: Generate Structured JSON with Pydantic Schema
DESCRIPTION: Learn how to use a Pydantic `BaseModel` to define the expected JSON schema for an LLM response. This ensures the model's output conforms to a predefined structure, making it easier to parse and use in Python applications.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/python-api.md#_snippet_9>

LANGUAGE: python
CODE:

```
import llm, json
from pydantic import BaseModel

class Dog(BaseModel):
    name: str
    age: int

model = llm.get_model("gpt-4o-mini")
response = model.prompt("Describe a nice dog", schema=Dog)
dog = json.loads(response.text())
print(dog)
# {"name":"Buddy","age":3}
```

----------------------------------------

TITLE: Setting OpenAI API Key for LLM
DESCRIPTION: Instructions on how to set the OpenAI API key using the `llm keys set` command to access OpenAI's `ada-002` embedding model.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/changelog.md#_snippet_83>

LANGUAGE: CLI
CODE:

```
llm keys set openai
```

----------------------------------------

TITLE: Example of an Interactive llm Chat Session
DESCRIPTION: This example illustrates the user experience within an active `llm chat` session. It details the commands available for session control (e.g., `exit`, `!multi`, `!edit`, `!fragment`) and provides a sample interaction where a user asks a joke and the model responds.
SOURCE: <https://github.com/simonw/llm/blob/main/README.md#_snippet_7>

LANGUAGE: default
CODE:

```
Chatting with gpt-4.1
Type 'exit' or 'quit' to exit
Type '!multi' to enter multiple lines, then '!end' to finish
Type '!edit' to open your default editor and modify the prompt.
Type '!fragment <my_fragment> [<another_fragment> ...]' to insert one or more fragments
> Tell me a joke about a pelican
Why don't pelicans like to tip waiters?

Because they always have a big bill!
```

----------------------------------------

TITLE: Chaining Prompts in LLM Conversations with Tools
DESCRIPTION: Shows how to use the `conversation.chain()` method multiple times within a tool-enabled conversation. This allows for complex, multi-step interactions where the model can leverage the provided tools across different prompts while maintaining conversational context.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/python-api.md#_snippet_31>

LANGUAGE: python
CODE:

```
print(conversation.chain(
    "Convert panda to uppercase and reverse it"
).text())
print(conversation.chain(
    "Same with pangolin"
).text())
```

----------------------------------------

TITLE: Extract People from Image Attachment using LLM
DESCRIPTION: This command illustrates how to extract 'people' data from an image file using `llm`. It specifies the 'people' template, provides a URL to an image as an attachment (`-a`), and explicitly uses the 'gpt-4o' model (`-m`).
SOURCE: <https://github.com/simonw/llm/blob/main/docs/schemas.md#_snippet_12>

LANGUAGE: bash
CODE:

```
llm -t people -a https://static.simonwillison.net/static/2025/onion-zuck.jpg -m gpt-4o
```

----------------------------------------

TITLE: Registering Python Functions as LLM Tools
DESCRIPTION: This snippet demonstrates how to register standard Python functions as tools for the LLM library using the `register_tools` hook. It shows how to define functions like `upper` and `count_char` and make them available, including specifying a custom tool name.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/plugin-hooks.md#_snippet_4>

LANGUAGE: python
CODE:

```
import llm

def upper(text: str) -> str:
    """Convert text to uppercase."""
    return text.upper()

def count_char(text: str, character: str) -> int:
    """Count the number of occurrences of a character in a word."""
    return text.count(character)

@llm.hookimpl
def register_tools(register):
    register(upper)
    # Here the name= argument is used to specify a different name for the tool:
    register(count_char, name="count_character_in_word")
```

----------------------------------------

TITLE: Calculate Embedding with llm embed using OpenAI Model
DESCRIPTION: Demonstrates how to calculate an embedding for a string using the `llm embed` command with a specified OpenAI model. Requires an OpenAI API key to be set.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/embeddings/cli.md#_snippet_0>

LANGUAGE: bash
CODE:

```
llm embed -c 'This is some content' -m 3-small
```

----------------------------------------

TITLE: Install LLM CLI Tool
DESCRIPTION: Instructions for installing the LLM command-line interface using various popular package managers like pip, Homebrew, pipx, or uv.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/index.md#_snippet_0>

LANGUAGE: bash
CODE:

```
pip install llm
```

LANGUAGE: bash
CODE:

```
brew install llm
```

LANGUAGE: bash
CODE:

```
pipx install llm
```

LANGUAGE: bash
CODE:

```
uv tool install llm
```

----------------------------------------

TITLE: Define and Execute Tools with LLM Python API
DESCRIPTION: Explains how to define Python functions as tools for the LLM model, retrieve tool calls from the response, and execute them. It also covers using `model.chain()` for automatic tool execution and streaming responses from a chain of operations.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/python-api.md#_snippet_3>

LANGUAGE: python
CODE:

```
import llm

def upper(text: str) -> str:
    """Convert text to uppercase."""
    return text.upper()

model = llm.get_model("gpt-4.1-mini")
response = model.prompt("Convert panda to upper", tools=[upper])
tool_calls = response.tool_calls()
# [ToolCall(name='upper', arguments={'text': 'panda'}, tool_call_id='...')]
```

LANGUAGE: python
CODE:

```
tool_results = response.execute_tool_calls()
# [ToolResult(name='upper', output='PANDA', tool_call_id='...')]
```

LANGUAGE: python
CODE:

```
chain_response = model.chain(
    "Convert panda to upper",
    tools=[upper],
)
print(chain_response.text())
# The word "panda" converted to uppercase is "PANDA".
```

LANGUAGE: python
CODE:

```
for chunk in model.chain(
    "Convert panda to upper",
    tools=[upper],
):
    print(chunk, end="", flush=True)
```

LANGUAGE: python
CODE:

```
chain = model.chain(
    "Convert panda to upper",
    tools=[upper],
)
for response in chain.responses():
    print(response.prompt)
    for chunk in response:
        print(chunk, end="", flush=True)
```

----------------------------------------

TITLE: Define Schema for Extracting People from News Articles
DESCRIPTION: Presents a multi-line schema definition using LLM's concise schema language, designed to extract specific details about individuals mentioned in news articles. The schema includes fields for `name`, `organization`, `role`, `learned` (what was learned about them), `article_headline`, and `article_date` (in YYYY-MM-DD format), with descriptions guiding the model's extraction process.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/schemas.md#_snippet_3>

LANGUAGE: LLM Schema DSL
CODE:

```
name: the person's name
organization: who they represent
role: their job title or role
learned: what we learned about them from this story
article_headline: the headline of the story
article_date: the publication date in YYYY-MM-DD
```

----------------------------------------

TITLE: Save and Use Stored LLM API Keys
DESCRIPTION: Explains how to save API keys using the 'llm keys set' command for automatic use in subsequent commands, how to list stored keys, and where the 'keys.json' file is located.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/setup.md#_snippet_5>

LANGUAGE: bash
CODE:

```
llm keys set openai
```

LANGUAGE: bash
CODE:

```
llm "Five ludicrous names for a pet lobster"
```

LANGUAGE: bash
CODE:

```
llm keys
```

LANGUAGE: bash
CODE:

```
llm keys path
```

----------------------------------------

TITLE: Extracting Structured Data from Articles with LLM and Multi-Schema
DESCRIPTION: Demonstrates how to use the `llm` command-line tool to extract structured information, specifically people's names, organizations, roles, and what was learned about them, from a web article. It pipes the content of a URL through `uvx strip-tags` to `llm`, providing a multi-line schema definition and a system prompt. The output is a JSON array of items, each representing an extracted person. An example of the JSON output is:

```json
{
  "items": [
    {
      "name": "William Alsup",
      "organization": "U.S. District Court",
      "role": "Judge",
      "learned": "He ruled that the mass firings of probationary employees were likely unlawful and criticized the authority exercised by the Office of Personnel Management.",
      "article_headline": "Judge finds mass firings of federal probationary workers were likely unlawful",
      "article_date": "2025-02-26"
    },
    {
      "name": "Everett Kelley",
      "organization": "American Federation of Government Employees",
      "role": "National President",
      "learned": "He hailed the court's decision as a victory for employees who were illegally fired.",
      "article_headline": "Judge finds mass firings of federal probationary workers were likely unlawful",
      "article_date": "2025-02-26"
    }
  ]
}
```

SOURCE: <https://github.com/simonw/llm/blob/main/docs/schemas.md#_snippet_5>

LANGUAGE: bash
CODE:

```
curl 'https://apnews.com/article/trump-federal-employees-firings-a85d1aaf1088e050d39dcf7e3664bb9f' | \
  uvx strip-tags | \
  llm --schema-multi "
name: the person's name
organization: who they represent
role: their job title or role
learned: what we learned about them from this story
article_headline: the headline of the story
article_date: the publication date in YYYY-MM-DD
" --system 'extract people mentioned in this article'
```

----------------------------------------

TITLE: Use LLM API Keys from Environment Variables
DESCRIPTION: Describes how LLM can read API keys from environment variables (e.g., OPENAI_API_KEY) and how to explicitly use them with the '--key' option, prioritizing them over stored keys.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/setup.md#_snippet_7>

LANGUAGE: bash
CODE:

```
llm 'my prompt' --key $OPENAI_API_KEY
```

----------------------------------------

TITLE: Execute Python Functions as Tools with LLM
DESCRIPTION: Demonstrates how to enable LLM models to execute Python functions as tools. This functionality is available via both the command-line interface and the Python API, allowing models to perform computations by calling defined Python functions.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/changelog.md#_snippet_19>

LANGUAGE: bash
CODE:

```
llm --functions '
def multiply(x: int, y: int) -> int:
    """Multiply two numbers."""
    return x * y
' 'what is 34234 * 213345'
```

LANGUAGE: python
CODE:

```
import llm

def multiply(x: int, y: int) -> int:
    """Multiply two numbers."""
    return x * y

model = llm.get_model("gpt-4.1-mini")
response = model.chain(
    "What is 34234 * 213345?",
    tools=[multiply]
)
print(response.text())
```

----------------------------------------

TITLE: Generate and Execute Shell Commands with llm-cmd
DESCRIPTION: The llm-cmd plugin accepts a natural language prompt for a shell command. It generates the command, populates it in the user's shell for review and editing, and allows execution or cancellation. This streamlines command-line interaction by leveraging LLM for command generation.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/directory.md#_snippet_27>

LANGUAGE: Shell
CODE:

```
llm-cmd (followed by a prompt, e.g., 'create a directory named my_project')
```

----------------------------------------

TITLE: Enabling JSON Output for OpenAI Models in LLM
DESCRIPTION: Shows how to configure OpenAI models in LLM to return output as a valid JSON object using the `-o json_object 1` option, useful for structured data generation.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/changelog.md#_snippet_70>

LANGUAGE: Shell
CODE:

```
llm -m gpt-4-turbo -o json_object 1 '{"prompt": "Generate a JSON object with a \"name\" and \"age\" field."}'
```

----------------------------------------

TITLE: Embed and Search Binary Data with LLM CLIP
DESCRIPTION: LLM's embedding feature now supports binary data, enabling multimodal models like CLIP to embed images and text into a shared vector space. This allows for semantic search of images based on text queries. The example demonstrates installing the `llm-clip` plugin, embedding JPEGs, and then searching for specific content.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/changelog.md#_snippet_80>

LANGUAGE: bash
CODE:

```
llm install llm-clip
llm embed-multi photos --files photos/ '*.jpg' --binary -m clip
```

LANGUAGE: bash
CODE:

```
llm similar photos -c 'raccoon'
```

LANGUAGE: json
CODE:

```
{"id": "IMG_4801.jpeg", "score": 0.28125139257127457, "content": null, "metadata": null}
{"id": "IMG_4656.jpeg", "score": 0.26626441704164294, "content": null, "metadata": null}
{"id": "IMG_2944.jpeg", "score": 0.2647445926996852, "content": null, "metadata": null}
...
```

----------------------------------------

TITLE: Implementing a Custom Embedding Model Plugin with Sentence-Transformers
DESCRIPTION: This Python code demonstrates how to create an LLM plugin that integrates a new embedding model using the `sentence-transformers` library. It includes the `register_embedding_models` hook to register the model and the `SentenceTransformerModel` class, which extends `llm.EmbeddingModel` and implements the `embed_batch` method for processing text batches.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/embeddings/writing-plugins.md#_snippet_0>

LANGUAGE: python
CODE:

```
import llm
from sentence_transformers import SentenceTransformer


@llm.hookimpl
def register_embedding_models(register):
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    register(SentenceTransformerModel(model_id, model_id), aliases=("all-MiniLM-L6-v2",))


class SentenceTransformerModel(llm.EmbeddingModel):
    def __init__(self, model_id, model_name):
        self.model_id = model_id
        self.model_name = model_name
        self._model = None

    def embed_batch(self, texts):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        results = self._model.encode(texts)
        return (list(map(float, result)) for result in results)
```

----------------------------------------

TITLE: llm keys Command Line Interface Reference
DESCRIPTION: Reference for the `llm keys` command, used to manage API keys for different models, including listing, getting, setting, and showing the key file path.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/help.md#_snippet_3>

LANGUAGE: APIDOC
CODE:

```
Usage: llm keys [OPTIONS] COMMAND [ARGS]...

  Manage stored API keys for different models

Options:
  -h, --help  Show this message and exit.

Commands:
  list*  List names of all stored keys
  get    Return the value of a stored key
  path   Output the path to the keys.json file
  set    Save a key in the keys.json file
```

----------------------------------------

TITLE: Pass multiple image attachments to llm using file paths
DESCRIPTION: Attaches multiple images to a single prompt using the `-a` option with file paths. This is useful for providing multiple visual contexts to multi-modal models.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/usage.md#_snippet_9>

LANGUAGE: bash
CODE:

```
llm "extract text" -a image1.jpg -a image2.jpg
```

----------------------------------------

TITLE: Register Synchronous and Asynchronous LLM Language Models with Alias
DESCRIPTION: This example demonstrates how to register both synchronous and asynchronous versions of a language model, along with an alias, using the `register_models` hook. It shows the structure for an `AsyncModel` and how to pass multiple models and aliases to the register function.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/plugin-hooks.md#_snippet_2>

LANGUAGE: Python
CODE:

```
class AsyncHelloWorld(llm.AsyncModel):
    model_id = "helloworld"

    async def execute(self, prompt, stream, response):
        return ["hello world"]

@llm.hookimpl
def register_models(register):
    register(HelloWorld(), AsyncHelloWorld(), aliases=("hw",))
```

----------------------------------------

TITLE: Generate Structured JSON Output with Inline Schema using llm
DESCRIPTION: Demonstrates how to pass a full JSON schema directly to the 'llm' command using the '--schema' option to enforce structured JSON output from a language model. It specifies the model 'gpt-4o-mini' and a prompt to invent two dogs, ensuring the output adheres to the defined 'dogs' array structure.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/usage.md#_snippet_26>

LANGUAGE: bash
CODE:

```
llm --schema '{
  "type": "object",
  "properties": {
    "dogs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "bio": {
            "type": "string"
          }
        }
      }
    }
  }
}' -m gpt-4o-mini 'invent two dogs'
```

----------------------------------------

TITLE: Install llm-gpt4all Plugin for Local Models
DESCRIPTION: This command installs the `llm-gpt4all` plugin, which provides access to 17 models from the GPT4All project. This enables LLM to use local models directly on your machine.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/other-models.md#_snippet_0>

LANGUAGE: bash
CODE:

```
llm install llm-gpt4all
```

----------------------------------------

TITLE: Define JSON Schema with Python Dictionary
DESCRIPTION: Explore how to directly pass a Python dictionary representing a JSON schema to the `model.prompt()` method. This provides granular control over the structure and types of the LLM's generated output.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/python-api.md#_snippet_10>

LANGUAGE: python
CODE:

```
response = model.prompt("Describe a nice dog", schema={
    "properties": {
        "name": {"title": "Name", "type": "string"},
        "age": {"title": "Age", "type": "integer"}
    },
    "required": ["name", "age"],
    "title": "Dog",
    "type": "object"
})
```

----------------------------------------

TITLE: Specify Output Schemas for LLM Prompts (CLI)
DESCRIPTION: Demonstrates various command-line options for providing JSON schemas or concise schema specifications to guide the LLM model's output.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/changelog.md#_snippet_39>

LANGUAGE: Bash
CODE:

```
llm prompt --schema '{JSON schema goes here}'
```

LANGUAGE: Bash
CODE:

```
llm prompt --schema 'name, bio, age int'
```

----------------------------------------

TITLE: Running Prompt with Specific LLM Model (Bash)
DESCRIPTION: This command executes a text prompt against a specified LLM model using the -m or --model option. It demonstrates how to interact with a newly installed or chosen model for generating responses.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/installing-plugins.md#_snippet_4>

LANGUAGE: bash
CODE:

```
llm -m orca-mini-3b-gguf2-q4_0 'What is the capital of France?'
```

----------------------------------------

TITLE: Upgrade LLM Tool
DESCRIPTION: Commands to upgrade the LLM tool to its latest version using pip, pipx, uv, or Homebrew. Includes a fallback method for Homebrew if the latest version isn't immediately available.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/setup.md#_snippet_1>

LANGUAGE: bash
CODE:

```
pip install -U llm
```

LANGUAGE: bash
CODE:

```
pipx upgrade llm
```

LANGUAGE: bash
CODE:

```
uv tool upgrade llm
```

LANGUAGE: bash
CODE:

```
brew upgrade llm
```

LANGUAGE: bash
CODE:

```
llm install -U llm
```

----------------------------------------

TITLE: Continue LLM Chat Conversation with Previous Context
DESCRIPTION: This command continues the most recent chat conversation using the `-c` or `--continue` option. It automatically includes the previous prompts and responses in the new request, allowing the model to maintain conversational context.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/changelog.md#_snippet_112>

LANGUAGE: bash
CODE:

```
llm "What do you think of snacks?" -c
```

----------------------------------------

TITLE: Retrieve Similar Items by Existing Item ID
DESCRIPTION: Shows how to use the `collection.similar_by_id()` method to find items most similar to an existing item in the collection, identified by its ID. The item itself is excluded from the results.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/embeddings/python-api.md#_snippet_14>

LANGUAGE: python
CODE:

```
for entry in collection.similar_by_id("cat"):
    print(entry.id, entry.score)
```

----------------------------------------

TITLE: Configure Model Behavior with Options
DESCRIPTION: See how to pass model-specific options, such as `temperature`, as keyword arguments directly to the `model.prompt()` method. This allows fine-tuning the LLM's generation parameters.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/python-api.md#_snippet_14>

LANGUAGE: python
CODE:

```
model = llm.get_model()
print(model.prompt("Names for otters", temperature=0.2))
```

----------------------------------------

TITLE: Find Similar Embeddings with `llm similar` Command
DESCRIPTION: The `llm similar` command allows users to find the top N most similar IDs within a specified collection using cosine similarity. It can compare against new content provided directly or against an existing stored ID, offering options for input source, number of results, and output format.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/help.md#_snippet_51>

LANGUAGE: Shell
CODE:

```
Usage: llm similar [OPTIONS] COLLECTION [ID]

  Return top N similar IDs from a collection using cosine similarity.

  Example usage:

      llm similar my-collection -c "I like cats"

  Or to find content similar to a specific stored ID:

      llm similar my-collection 1234

Options:
  -i, --input PATH      File to embed for comparison
  -c, --content TEXT    Content to embed for comparison
  --binary              Treat input as binary data
  -n, --number INTEGER  Number of results to return
  -p, --plain           Output in plain text format
  -d, --database FILE
  --prefix TEXT         Just IDs with this prefix
  -h, --help            Show this message and exit.
```

----------------------------------------

TITLE: Configure OpenAI and Run Basic Prompts
DESCRIPTION: Demonstrates how to set up your OpenAI API key and execute various types of prompts, including text generation, image text extraction, and using system prompts with file input.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/index.md#_snippet_1>

LANGUAGE: bash
CODE:

```
# Paste your OpenAI API key into this
llm keys set openai

# Run a prompt (with the default gpt-4o-mini model)
llm "Ten fun names for a pet pelican"

# Extract text from an image
llm "extract text" -a scanned-document.jpg

# Use a system prompt against a file
cat myfile.py | llm -s "Explain this code"
```

----------------------------------------

TITLE: Interact with OpenAI Models using LLM CLI
DESCRIPTION: Demonstrates how to set up your OpenAI API key and run various types of prompts, including basic text generation, image text extraction, and using system prompts with file input.
SOURCE: <https://github.com/simonw/llm/blob/main/README.md#_snippet_1>

LANGUAGE: bash
CODE:

```
# Paste your OpenAI API key into this
llm keys set openai
```

LANGUAGE: bash
CODE:

```
# Run a prompt (with the default gpt-4o-mini model)
llm "Ten fun names for a pet pelican"
```

LANGUAGE: bash
CODE:

```
# Extract text from an image
llm "extract text" -a scanned-document.jpg
```

LANGUAGE: bash
CODE:

```
# Use a system prompt against a file
cat myfile.py | llm -s "Explain this code"
```

----------------------------------------

TITLE: Start Interactive Chat Session with LLM
DESCRIPTION: The `llm chat` command initiates an ongoing conversation with a language model directly in the terminal, offering significant performance improvements for local models by avoiding repeated loading. Users can interact, ask questions, and receive responses, with sessions automatically logged for later review.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/changelog.md#_snippet_79>

LANGUAGE: bash
CODE:

```
llm chat -m mlc-chat-Llama-2-13b-chat-hf-q4f16_1
Type 'exit' or 'quit' to exit
Type '!multi' to enter multiple lines, then '!end' to finish
Type '!edit' to open your default editor and modify the prompt.
> Who are you?
Hello! I'm just an AI, here to assist you with any questions you may have.
My name is LLaMA, and I'm a large language model trained to provide helpful
and informative responses to a wide range of questions and topics. I'm here
to help you find the information you need, while ensuring a safe and
respectful conversation. Please feel free to ask me anything, and I'll do my
best to provide a helpful and accurate response.
> Tell me a joke about otters
Sure, here's a joke about otters:

Why did the otter go to the party?

Because he heard it was a "whale" of a time!

(Get it? Whale, like a big sea mammal, but also a "wild" or "fun" time.
Otters are known for their playful and social nature, so it's a lighthearted
and silly joke.)

I hope that brought a smile to your face! Do you have any other questions or
topics you'd like to discuss?
> exit
```

----------------------------------------

TITLE: Load GitHub Repositories and Issues as Fragments with llm-fragments-github
DESCRIPTION: The llm-fragments-github plugin enables loading entire GitHub repositories as fragments for LLM, allowing users to prompt against the codebase. It also supports fetching specific GitHub issue threads as Markdown, making it useful for summarizing discussions or understanding context from issues.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/directory.md#_snippet_21>

LANGUAGE: Shell
CODE:

```
llm -f github:simonw/files-to-prompt 'explain this code'
```

LANGUAGE: Shell
CODE:

```
llm -f issue:https://github.com/simonw/llm-fragments-github/issues/3
```

----------------------------------------

TITLE: Execute Basic Prompts with LLM Python API
DESCRIPTION: Demonstrates how to run a prompt against a specified LLM model using the Python API, including lazy loading of responses and alternative key configuration methods. It also shows how to list available models via the command line.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/python-api.md#_snippet_0>

LANGUAGE: python
CODE:

```
import llm

model = llm.get_model("gpt-4o-mini")
# key= is optional, you can configure the key in other ways
response = model.prompt(
    "Five surprising names for a pet pelican",
    key="sk-..."
)
print(response.text())
```

LANGUAGE: python
CODE:

```
print(llm.get_model().prompt("Five surprising names for a pet pelican"))
```

LANGUAGE: bash
CODE:

```
llm models
```

----------------------------------------

TITLE: llm embed-multi Command Overview and Options
DESCRIPTION: The `llm embed-multi` command allows embedding multiple strings efficiently, leveraging model batching capabilities. It supports various input sources (CSV, TSV, JSON files, SQLite queries, directories with glob patterns) and offers options for model selection, database specification, content storage, ID prefixing, content prepending, and batch sizing.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/embeddings/cli.md#_snippet_14>

LANGUAGE: APIDOC
CODE:

```
llm embed-multi:
  description: Embed multiple strings at once, leveraging model batching.
  input_sources:
    - CSV, TSV, JSON, newline-delimited JSON file
    - SQLite database with SQL query
    - Directories with glob patterns
  options:
    - -m model_id (string): Specify the embedding model to use.
    - -d database.db (string): Specify a different database file.
    - --store (boolean): Store original content in the embeddings table.
    - --prefix (string): Prepend a prefix to the stored ID.
    - --prepend (string): Prepend a string to content before embedding (e.g., 'search_document: ').
    - --batch-size SIZE (integer): Process embeddings in batches.
```

----------------------------------------

TITLE: Manage LLM Prompt Templates
DESCRIPTION: Provides commands for managing stored prompt templates, including listing, editing, showing, and locating the templates directory. This helps in organizing and reusing prompts.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/help.md#_snippet_23>

LANGUAGE: Shell
CODE:

```
Usage: llm templates [OPTIONS] COMMAND [ARGS]...

  Manage stored prompt templates

Options:
  -h, --help  Show this message and exit.

Commands:
  list*    List available prompt templates
  edit     Edit the specified prompt template using the default $EDITOR
  loaders  Show template loaders registered by plugins
  path     Output the path to the templates directory
  show     Show the specified prompt template
```

----------------------------------------

TITLE: Install LLM CLI Tool
DESCRIPTION: Instructions for installing the LLM command-line tool using various package managers like pip, Homebrew, pipx, and uv.
SOURCE: <https://github.com/simonw/llm/blob/main/README.md#_snippet_0>

LANGUAGE: bash
CODE:

```
pip install llm
```

LANGUAGE: bash
CODE:

```
brew install llm
```

LANGUAGE: bash
CODE:

```
pipx install llm
```

LANGUAGE: bash
CODE:

```
uv tool install llm
```

----------------------------------------

TITLE: Provide Context with Prompt Fragments
DESCRIPTION: Understand how to pass `fragments` and `system_fragments` lists to the `model.prompt()` method. This allows injecting external document content or system-level instructions to guide the LLM's response.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/python-api.md#_snippet_13>

LANGUAGE: python
CODE:

```
response = model.prompt(
    "What do these documents say about dogs?",
    fragments=[
        open("dogs1.txt").read(),
        open("dogs2.txt").read()
    ],
    system_fragments=[
        "You answer questions like Snoopy"
    ]
)
```

----------------------------------------

TITLE: Define and Use LLM Templates with Custom Named Variables
DESCRIPTION: This snippet demonstrates how to create a custom `llm` template using YAML that accepts named variables like `$ingredients` and `$country`. It then shows how to execute this template from the command line, passing values for these variables using the `-p/--param` option. This allows for dynamic and reusable prompts.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/templates.md#_snippet_16>

LANGUAGE: YAML
CODE:

```
prompt: |
    Suggest a recipe using ingredients: $ingredients

    It should be based on cuisine from this country: $country
```

LANGUAGE: Bash
CODE:

```
llm -t recipe -p ingredients 'sausages, milk' -p country Germany
```

----------------------------------------

TITLE: Pass single image attachment to llm using a URL
DESCRIPTION: Includes an image attachment in a prompt using the `-a` option with a URL. Multi-modal models can then process the image alongside the text prompt.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/usage.md#_snippet_8>

LANGUAGE: bash
CODE:

```
llm "describe this image" -a https://static.simonwillison.net/static/2024/pelicans.jpg
```

----------------------------------------

TITLE: Configure Capabilities for OpenAI Compatible LLM Models
DESCRIPTION: OpenAI compatible models, configured via `extra-openai-models.yaml`, now support additional options to declare their capabilities: `supports_schema` for schema generation, `vision` for image attachments, and `audio` for audio processing.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/changelog.md#_snippet_35>

LANGUAGE: APIDOC
CODE:

```
Model Configuration Options for `extra-openai-models.yaml`:
  "supports_schema": boolean (default: false) - Indicates if the model supports schema generation.
  "vision": boolean (default: false) - Indicates if the model supports vision capabilities (e.g., image attachments).
  "audio": boolean (default: false) - Indicates if the model supports audio capabilities.
```

----------------------------------------

TITLE: Implement Asynchronous execute Method with API Key for LLM AsyncKeyModel
DESCRIPTION: This example shows how to define the `async def execute()` method for an `llm.AsyncKeyModel`. It combines asynchronous execution with the ability to receive an API key, making it suitable for async models that require authentication.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/advanced-model-plugins.md#_snippet_3>

LANGUAGE: Python
CODE:

```
class MyAsyncModel(llm.AsyncKeyModel):
    ...
    async def execute(
        self, prompt, stream, response, conversation=None, key=None
    ) -> AsyncGenerator[str, None]:
```

----------------------------------------

TITLE: Embed Multiple Strings with `llm embed-multi` Command
DESCRIPTION: The `llm embed-multi` command facilitates storing embeddings for multiple strings simultaneously within a specified collection. It supports diverse input formats including CSV, TSV, JSON, JSONL files, SQL queries against SQLite databases, and files from directories matching glob patterns.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/help.md#_snippet_50>

LANGUAGE: Shell
CODE:

```
Usage: llm embed-multi [OPTIONS] COLLECTION [INPUT_PATH]

  Store embeddings for multiple strings at once in the specified collection.

  Input data can come from one of three sources:

  1. A CSV, TSV, JSON or JSONL file:
     - CSV/TSV: First column is ID, remaining columns concatenated as content
     - JSON: Array of objects with "id" field and content fields
     - JSONL: Newline-delimited JSON objects

     Examples:
       llm embed-multi docs input.csv
       cat data.json | llm embed-multi docs -
       llm embed-multi docs input.json --format json

  2. A SQL query against a SQLite database:
     - First column returned is used as ID
     - Other columns concatenated to form content

     Examples:
       llm embed-multi docs --sql "SELECT id, title, body FROM posts"
       llm embed-multi docs --attach blog blog.db --sql "SELECT id, content FROM blog.posts"

  3. Files in directories matching glob patterns:
     - Each file becomes one embedding
     - Relative file paths become IDs

     Examples:
       llm embed-multi docs --files docs '**/*.md'
       llm embed-multi images --files photos '*.jpg' --binary
       llm embed-multi texts --files texts '*.txt' --encoding utf-8 --encoding latin-1

Options:
  --format [json|csv|tsv|nl]   Format of input file - defaults to auto-detect
  --files <DIRECTORY TEXT>...  Embed files in this directory - specify directory
                               and glob pattern
  --encoding TEXT              Encodings to try when reading --files
  --binary                     Treat --files as binary data
  --sql TEXT                   Read input using this SQL query
  --attach <TEXT FILE>...      Additional databases to attach - specify alias
                               and file path
  --batch-size INTEGER         Batch size to use when running embeddings
  --prefix TEXT                Prefix to add to the IDs
  -m, --model TEXT             Embedding model to use
  --prepend TEXT               Prepend this string to all content before
                               embedding
  --store                      Store the text itself in the database
  -d, --database FILE
  -h, --help                   Show this message and exit.
```

----------------------------------------

TITLE: Generate Single Structured JSON Output with LLM Schema
DESCRIPTION: Demonstrates how to use the `llm --schema` command-line tool to prompt a Large Language Model to generate a single JSON object conforming to a specified concise schema. This example invents a 'cool dog' with `name` (string), `age` (integer), and `one_sentence_bio` (string) fields.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/schemas.md#_snippet_0>

LANGUAGE: bash
CODE:

```
llm --schema 'name, age int, one_sentence_bio' 'invent a cool dog'
```

LANGUAGE: json
CODE:

```
{
  "name": "Ziggy",
  "age": 4,
  "one_sentence_bio": "Ziggy is a hyper-intelligent, bioluminescent dog who loves to perform tricks in the dark and guides his owner home using his glowing fur."
}
```

----------------------------------------

TITLE: Truncate Text to Desired Token Count with ttok
DESCRIPTION: Illustrates using `ttok` to truncate input text to a specified number of OpenAI tokens, useful for fitting large documents into LLM context windows.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/related-tools.md#_snippet_2>

LANGUAGE: bash
CODE:

```
ttok This is too many tokens -t 3
```

----------------------------------------

TITLE: Complete LLM Plugin for Markov Chain Model in Python
DESCRIPTION: This comprehensive snippet provides the full Python code for an `llm` plugin that integrates a Markov chain model. It includes the `register_models` hook, the `build_markov_table` function for training, the `generate` function, and the `Markov` class with its `execute` method, demonstrating how to process user prompts to generate text.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/tutorial-model-plugin.md#_snippet_15>

LANGUAGE: Python
CODE:

```
import llm
import random

@llm.hookimpl
def register_models(register):
    register(Markov())

def build_markov_table(text):
    words = text.split()
    transitions = {}
    # Loop through all but the last word
    for i in range(len(words) - 1):
        word = words[i]
        next_word = words[i + 1]
        transitions.setdefault(word, []).append(next_word)
    return transitions

def generate(transitions, length, start_word=None):
    all_words = list(transitions.keys())
    next_word = start_word or random.choice(all_words)
    for i in range(length):
        yield next_word
        options = transitions.get(next_word) or all_words
        next_word = random.choice(options)

class Markov(llm.Model):
    model_id = "markov"

    def execute(self, prompt, stream, response, conversation):
        text = prompt.prompt
        transitions = build_markov_table(text)
        for word in generate(transitions, 20):
            yield word + ' '
```

----------------------------------------

TITLE: Integrate Mistral AI Language and Embedding Models with llm-mistral
DESCRIPTION: The llm-mistral plugin enables interaction with Mistral AI's language and embedding models through their official API. It extends the LLM framework to support Mistral's offerings for text generation and embeddings.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/plugins/directory.md#_snippet_0>

LANGUAGE: APIDOC
CODE:

```
Plugin: llm-mistral
  API Provider: Mistral AI
  Models Supported: Language and embedding models
  Purpose: Integrates Mistral AI's API for LLM interactions.
```

----------------------------------------

TITLE: Generate Multiple Items with LLM's DSL
DESCRIPTION: Learn to use `llm.schema_dsl()` with the `multi=True` parameter to instruct the LLM to generate a list of items, each conforming to the specified schema. Useful for generating multiple structured entities.
SOURCE: <https://github.com/simonw/llm/blob/main/docs/python-api.md#_snippet_12>

LANGUAGE: python
CODE:

```
print(model.prompt(
    "Describe 3 nice dogs with surprising names",
    schema=llm.schema_dsl("name, age int, bio", multi=True)
))
```
