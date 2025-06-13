import os
import asyncio
from typing import Sequence
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import print_formatted_text as print
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


class UpdatableWordCompleter:
    def __init__(self, words: Sequence[str] = BASE_WORDS, meta: dict = BASE_META):
        self.words = words
        self.meta = meta
        self.completer = WordCompleter(self._get_words, meta_dict=self.meta)

    def _get_words(self) -> Sequence[str]:
        return self.words

    def get_context(self, text: str) -> str:
        if text[0].isdigit() or len(text.split("-")) > 2:
            if text in self.meta:
                return self.meta[text].split("-")[-1].strip()
        return ""

    def update(self, updated, context="", replace=True):
        if context:
            for word in updated:
                self.meta[word] = f"{word} - {context}"

        if replace:
            self.words = BASE_WORDS + updated
        else:
            unique = [x for x in updated if x not in self.words]
            existing = [x for x in self.words]
            self.words = existing + unique
        self.completer = WordCompleter(self._get_words, meta_dict=self.meta)


async def main():
    config = read_config()
    arena_client = ArenaClient(config["arena"])
    command_completer = UpdatableWordCompleter()
    session = PromptSession(
        history=FileHistory(".arena-control.history"),
        completer=command_completer.completer,
    )
    current_contest = None
    current_arena = None
    print(HTML("<bold><ansiblue><u>Mister Agent Arena CLI</u></ansiblue></bold>"))

    while True:
        try:
            text = await session.prompt_async("> ")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            print(HTML(f"<ansired>{e}</ansired>"))
            break
        else:
            if text == "help":
                print("Help")
            elif text == "exit":
                break
            elif text == "clear":
                print("Clear")
            elif text == "arenas":
                r = await arena_client.get("/api/arena")
                arenas = r.json()
                command_completer.update([a["id"] for a in arenas], "arena", False)
                print_arena_list(arenas)
            elif text == "contests":
                r = await arena_client.get("/api/contest")
                contests = r.json()
                command_completer.update([c["id"] for c in contests], "contest", False)
                print_contest_list(contests)
            elif text:
                context = command_completer.get_context(text)
                if context == "arena":
                    r = await arena_client.get(f"/api/arena/{text}")
                    current_arena = r.json()
                    arena_md = await arena_client.get(f"/api/arena/{text}.md")
                    print(render_markdown(arena_md.content.decode("utf-8")))
                if context == "contest":
                    r = await arena_client.get(f"/api/contest/{text}")
                    current_contest = r.json()
                    contest_md = await arena_client.get(f"/api/contest/{text}.md")
                    print(render_markdown(contest_md.content.decode("utf-8")))
                else:
                    print(HTML(f"<ansired>Unknown command: {text} {context}</ansired>"))

    print("GoodBye!")


if __name__ == "__main__":
    asyncio.run(main())
