import os
import asyncio
from typing import Any, Dict, Sequence
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, WordCompleter, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import print_formatted_text as print
from pydantic import BaseModel
from traitlets import List
from .markdown_renderer import render_markdown
import yaml

from agentarena.util.files import find_file_upwards

from .clients import ArenaClient

prod = getattr(os.environ, "ARENA_ENV", "dev") == "prod"


def print_arena_list(arenas):
    print(HTML("<bold><ansiblue><u>Arenas</u></ansiblue></bold>"))
    for arena in arenas:
        print(HTML(f"  {arena['id']} - {arena['name']}"))


def print_contest_list(contests):
    print(HTML("<bold><ansiblue><u>Contests</u></ansiblue></bold>"))
    for contest in contests:
        print(
            HTML(
                f"  {contest['id']} - <ansiblue>{contest['arena']['name']}</ansiblue> - {contest['state']}"
            )
        )


def read_config():
    yamlfile = find_file_upwards("agent-arena-config.yaml")
    assert yamlfile, "Where is my config file?"
    with open(yamlfile, "r") as f:
        yaml_data = yaml.safe_load(f)
    return yaml_data


BASE_COMMANDS = {
    "arena": {
        "description": "load an arena",
        "commands": {
            "load": {
                "description": "load an arena",
                "commands": {
                    "$arena_ids": {
                        "description": "Arena IDs",
                        "commands": {},
                    },
                },
            },
            "start": {
                "description": "start an arena",
                "commands": {
                    "$arena_ids": {
                        "description": "Arena IDs",
                        "commands": {},
                    },
                },
            },
            "stop": {
                "description": "stop an arena",
                "commands": {
                    "$arena_ids": {
                        "description": "Arena IDs",
                        "commands": {},
                    },
                },
            },
        },
    },
    "help": {
        "description": "show this help",
        "commands": {},
    },
    "exit": {
        "description": "exit the program",
        "commands": {},
    },
    "clear": {
        "description": "clear the loaded data",
        "commands": {},
    },
    "arenas": {
        "description": "list all arenas",
        "commands": {},
    },
    "contest": {
        "description": "load a contest",
        "commands": {
            "load": {
                "description": "load a contest",
                "commands": {
                    "$contest_ids": {
                        "description": "Contest IDs",
                        "commands": {},
                    },
                },
            },
            "start": {
                "description": "start a contest",
                "commands": {
                    "$contest_ids": {
                        "description": "Contest IDs",
                        "commands": {},
                    },
                },
            },
            "stop": {
                "description": "stop a contest",
                "commands": {
                    "$contest_ids": {
                        "description": "Contest IDs",
                        "commands": {},
                    },
                },
            },
        },
    },
    "contests": {
        "description": "list all contests",
        "commands": {},
    },
}

BASE_WORDS = [
    "help",
    "exit",
    "clear",
    "arenas",
    "contests",
]

BASE_META = {
    "exit": "exit the program",
    "help": "show this help",
    "contests": "Load contests",
}


class CommandCompleter(Completer):
    def __init__(self, commands: Dict = BASE_COMMANDS):
        self.commands = commands
        self.loaded = {}

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.strip()
        user_input = text.split()
        if len(user_input) == 0:
            yield from [
                Completion(
                    text=word,
                    display_meta=self.commands[word]["description"],
                    start_position=-1,
                )
                for word in self.commands
            ]
        else:
            first_word = user_input[0]
            if first_word in self.commands:
                command_choices = self.expand_commands(
                    self.commands[first_word]["commands"]
                )
                if len(user_input) == 1:
                    # first word matches, no more input, so show the subcommands
                    yield from [
                        Completion(
                            text=word,
                            display_meta=command_choices[word]["description"],
                            start_position=-1,
                        )
                        for word in command_choices
                    ]
                else:
                    # first word matches, we have more input, does it match a subcommand?
                    subcommand = user_input[1]
                    if subcommand in command_choices:
                        subcommands = self.expand_commands(
                            command_choices[subcommand]["commands"]
                        )

                        yield from [
                            Completion(
                                text=word,
                                display_meta=command_choices[subcommand]["description"],
                                start_position=-1,
                            )
                            for word in subcommands
                        ]
                    else:
                        # first word matches, no match on next, show matching
                        yield from [
                            Completion(
                                text=word,
                                display_meta=command_choices[word]["description"],
                                start_position=-1,
                            )
                            for word in command_choices
                            if word.startswith(subcommand)
                        ]
            else:
                # first word doesn't match, try to find a match in the commands
                yield from [
                    Completion(
                        text=key,
                        display_meta=self.commands[key]["description"],
                        start_position=-1,
                    )
                    for key in self.commands
                    if key.startswith(first_word)
                ]

    def expand_commands(self, commands: Dict) -> Dict:
        rv = {}
        for key, value in commands.items():
            if key == "$arena_ids" and "arenas" in self.loaded:
                for a in self.loaded["arenas"]:
                    rv[a["id"]] = {
                        "description": f"Arena {a['name']}",
                        "commands": {},
                    }
            elif key == "$contest_ids" and "contests" in self.loaded:
                for c in self.loaded["contests"]:
                    rv[c["id"]] = {
                        "description": f"Contest {c['arena']['name']}",
                        "commands": {},
                    }
            else:
                rv[key] = value
        return rv

    def add_loaded(self, key: str, value: Any):
        self.loaded[key] = value


class ArenaCommander:
    def __init__(self, arena_client: ArenaClient):
        self.arena_client = arena_client
        self.loaded: Dict[str, Dict[str, Any]] = {}
        self.command_completer = CommandCompleter()
        self.session = PromptSession(
            history=FileHistory(".arena-control.history"),
            completer=self.command_completer,
        )
        self.loaded = {}

    async def cmd_arena(self, args: list[str]):
        if not args:
            print(HTML("<bold><ansired>No arena id provided</ansired></bold>"))
            return True
        r = await self.arena_client.get(f"/api/arena/{args[0]}")
        self.loaded["arena"] = r.json()
        return True

    async def cmd_arenas(self, args: list[str]):
        r = await self.arena_client.get("/api/arena")
        arenas = r.json()
        # self.command_completer.update([a["id"] for a in arenas], "arena", False)
        self.command_completer.add_loaded("arenas", arenas)
        print_arena_list(arenas)
        return True

    async def cmd_clear(self, args: list[str]):
        print(HTML("<bold><ansiblue><u>Cleared all loaded data</u></ansiblue></bold>"))
        self.loaded = {}
        return True

    async def cmd_contest(self, args: list[str]):
        if not args:
            print(HTML("<bold><ansired>No contest id provided</ansired></bold>"))
            return True
        r = await self.arena_client.get(f"/api/contest/{args[0]}")
        self.loaded["contest"] = r.json()
        return True

    async def cmd_contests(self, args: list[str]):
        r = await self.arena_client.get("/api/contest")
        contests = r.json()
        # self.command_completer.update([c["id"] for c in contests], "contest", False)
        self.command_completer.add_loaded("contests", contests)
        print_contest_list(contests)
        return True

    async def cmd_exit(self, args: list[str]):
        print(HTML("<bold><ansiblue><u>Exiting...</u></ansiblue></bold>"))
        return False

    async def cmd_help(self, args: list[str]):
        print(HTML("<bold><ansiblue><u>Help</u></ansiblue></bold>"))
        return True

    async def process_command(self, text: str):
        words = text.split()
        if not words:
            return
        cmd = words[0]
        args = words[1:]
        if cmd == "help":
            await self.cmd_help(args)
        elif cmd == "arena":
            await self.cmd_arena(args)
        elif cmd == "arenas":
            await self.cmd_arenas(args)
        elif cmd == "clear":
            await self.cmd_clear(args)
        elif cmd == "contests":
            await self.cmd_contests(args)
        elif cmd == "contest":
            await self.cmd_contest(args)
        elif cmd == "exit":
            await self.cmd_exit(args)
        else:
            print(HTML(f"<ansired>Unknown command: {cmd}</ansired>"))

    async def prompt(self, text: str) -> str:
        prefix = []
        if "arena" in self.loaded:
            arena = self.loaded["arena"]
            prefix.append(f"arena:{arena['id']}")
        if "contest" in self.loaded:
            contest = self.loaded["contest"]
            prefix.append(f"contest:{contest['id']}")
        if text:
            prefix.append(f"{text}>")
        else:
            prefix.append("> ")
        return await self.session.prompt_async(
            "\n".join(prefix),
            completer=self.command_completer,
            complete_while_typing=True,
        )

    async def start(self):
        while True:
            try:
                text = await self.prompt("")
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                print(HTML(f"<ansired>{e}</ansired>"))
                continue
            await self.process_command(text)


async def main():
    config = read_config()
    arena_client = ArenaClient(config["arena"])
    commander = ArenaCommander(arena_client)
    print(HTML("<bold><ansiblue><u>Mister Agent Arena CLI</u></ansiblue></bold>"))
    await commander.start()
    print("GoodBye!")


if __name__ == "__main__":
    asyncio.run(main())
