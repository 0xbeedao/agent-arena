import asyncio
import os
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import yaml
from nats.aio.msg import Msg
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import TextArea

from agentarena.util.files import find_file_upwards

from .clients import ArenaClient
from .clients import MessageBrokerClient
from .clients import ParticipantClient
from .clients import SchedulerClient
from .markdown_renderer import render_markdown

VERSION = "0.0.1"

prod = getattr(os.environ, "ARENA_ENV", "dev") == "prod"

CAPTURE_THE_FLAG_RULES = "Capture the flag. No fighting. Players move up to 2 spaces, if running, but may trip or be vulnerable when doing so. Players may only grab the flag or place it on the base from one space away."


async def prompt_int(
    prompt: str,
    min_value: int = 0,
    max_value: int = 1000,
    default: int = 5,
    words: List[str] = [],
) -> int:
    parsed_val = None
    if len(words) == 0:
        words.append(str(default))
        words.append(str(min_value))
        if default != 0:
            for ix in range(1, 10):
                words.append(str(ix * default))
    session = PromptSession(completer=WordCompleter(words))
    while parsed_val is None:
        raw = await session.prompt_async(f"{prompt}: ")
        if raw == "":
            return default
        try:
            parsed_val = int(raw)
        except ValueError:
            print(HTML(f"<ansired>Invalid {prompt.lower()}</ansired>"))
        if parsed_val is not None and parsed_val < 1:
            print(HTML(f"<ansired>{prompt.lower()} must be greater than 0</ansired>"))
        if parsed_val is not None and parsed_val > max_value:
            print(
                HTML(
                    f"<ansired>{prompt.lower()} must be less than {max_value}</ansired>"
                )
            )
    return parsed_val


async def prompt_str(
    prompt: str, default: Optional[str] = None, words: List[str] = []
) -> Optional[str]:
    if len(words) == 0 and default:
        words.append(default)
    session = PromptSession(completer=WordCompleter(words))
    raw = await session.prompt_async(f"{prompt}: ")
    if raw == "":
        return default
    return raw


def print_title(title, error=False, success=False, info=False):
    if error:
        print(HTML(f"<bold><ansired>{title}</ansired></bold>"))
    elif success:
        print(HTML(f"<ansigreen>{title}</ansigreen>"))
    elif info:
        print(HTML(f"<bold><ansiblue><u>{title}</u></ansiblue></bold>"))
    else:
        print(HTML(f"<bold>{title}</bold>"))


def print_arena_list(arenas):
    print_title("Arenas", info=True)
    for arena in arenas:
        print(HTML(f"  {arena['id']} - {arena['name']}"))


def print_contest_list(contests):
    print_title("Contests", info=True)
    for contest in contests:
        print(
            HTML(
                f"  {contest['id']} - <ansiblue>{contest['arena']['name']}</ansiblue> - {contest['state']}"
            )
        )


def print_job_list(jobs):
    print_title("Jobs", info=True)
    for job in jobs:
        print(HTML(f"  {job['id']} - {job['channel']} - {job['state']}"))


def print_generate_job_list(jobs):
    print_title("Generate Jobs", info=True)
    for job in jobs:
        print(
            HTML(
                f"  {job['id']} - {job['job_id']} - {job['model']} - {job['prompt_type']} - {job['state']}"
            )
        )


def print_participant_list(participants):
    print_title("participants", info=True)
    for participant in participants:
        strat = participant.get("strategy")
        strat_str = f" (strategy: {strat['name']})" if strat else ""
        print(
            HTML(
                f"  {participant['id']} - {participant['name']}{strat_str} (participant: {participant['participant_id']})"
            )
        )


def print_strategy_list(strategies):
    print_title("Strategies", info=True)
    for strat in strategies:
        prompt_count = len(strat.get("prompts", []))
        print(
            HTML(
                f"  {strat['id']} - {strat['name']} ({strat['role']}) | {strat['personality']} | {strat['description']} | prompts: {prompt_count}"
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
                    "latest": {
                        "description": "load the latest arena",
                        "commands": {},
                    },
                    "$arena_ids": {
                        "description": "Arena IDs",
                        "commands": {},
                    },
                },
            },
            "create": {"description": "create an arena", "commands": {}},
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
        "description": "Contest Control",
        "commands": {
            "create": {
                "description": "create a contest",
                "commands": {},
            },
            "load": {
                "description": "load a contest",
                "commands": {
                    "latest": {
                        "description": "load the latest contest",
                        "commands": {},
                    },
                    "$contest_ids": {
                        "description": "Contest IDs",
                        "commands": {},
                    },
                },
            },
            "start": {
                "description": "start a contest",
                "commands": {
                    "latest": {
                        "description": "Start the latest contest",
                        "commands": {},
                    },
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
    "listen": {
        "description": "listen to a channel",
        "commands": {
            "all": {
                "description": "listen to all channels",
            },
            "most": {
                "description": "listen to all non-system messages",
            },
            "none": {
                "description": "listen to no channels",
            },
            "arena": {
                "description": "listen to the arena channel",
                "commands": {},
            },
            "actor": {
                "description": "listen to the actor channel",
                "commands": {},
            },
            "scheduler": {
                "description": "listen to the scheduler channel",
                "commands": {},
            },
        },
    },
    "jobs": {
        "description": "list all jobs",
        "commands": {},
    },
    "job": {
        "description": "Job Control",
        "commands": {
            "create": {
                "description": "create a job",
                "commands": {},
            },
            "load": {
                "description": "load a job by id",
                "commands": {
                    "latest": {
                        "description": "load the latest job",
                        "commands": {},
                    },
                    "$job_ids": {
                        "description": "Job IDs",
                        "commands": {},
                    },
                },
            },
        },
    },
    "generatejob": {
        "description": "Generate Job Control",
        "commands": {
            "load": {
                "description": "load a generate job by id",
                "commands": {
                    "latest": {
                        "description": "load the latest generate job",
                        "commands": {},
                    },
                    "$generatejob_ids": {
                        "description": "Generate Job IDs",
                        "commands": {},
                    },
                },
            },
            "repeat": {
                "description": "repeat a generate job",
                "commands": {
                    "latest": {
                        "description": "repeat the latest job",
                        "commands": {},
                    },
                    "$job_ids": {
                        "description": "Generate Job IDs",
                        "commands": {},
                    },
                },
            },
        },
    },
    "generatejobs": {
        "description": "list all generate jobs",
        "commands": {},
    },
    "participant": {
        "description": "Participant Control",
        "commands": {
            "create": {
                "description": "create a participant",
                "commands": {},
            },
            "load": {
                "description": "load a participant by id",
                "commands": {},
            },
        },
    },
    "participants": {
        "description": "list all participants",
        "commands": {},
    },
    "strategy": {
        "description": "Strategy Control",
        "commands": {
            "create": {
                "description": "create a strategy",
                "commands": {},
            },
            "load": {
                "description": "load a strategy by id",
                "commands": {},
            },
        },
    },
    "strategies": {
        "description": "list all strategies",
        "commands": {},
    },
}


class CommandCompleter(Completer):
    def __init__(self, commands: Dict = BASE_COMMANDS):
        self.commands = commands
        self.loaded = {}

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        words = text_before_cursor.lstrip().split()
        word_before_cursor = document.get_word_before_cursor()

        if not words or (len(words) == 1 and not text_before_cursor.endswith(" ")):
            # First word completion
            for word in self.commands:
                if word.startswith(word_before_cursor):
                    yield Completion(
                        text=word,
                        display_meta=self.commands[word]["description"],
                        start_position=-len(word_before_cursor),
                    )
            return

        if text_before_cursor.endswith(" "):
            # Start suggesting next command part
            path = words
            word_to_complete = ""
        else:
            # Complete current command part
            path = words[:-1]
            word_to_complete = words[-1]

        current_level_commands = self.commands
        for part in path:
            expanded_commands = self.expand_commands(current_level_commands)
            # Find a match for the path part in the expanded commands
            match_found = False
            for cmd_key, cmd_val in expanded_commands.items():
                if cmd_key == part:
                    current_level_commands = cmd_val.get("commands", {})
                    match_found = True
                    break
            if not match_found:
                return  # Invalid command path

        command_choices = self.expand_commands(current_level_commands)

        for word, details in command_choices.items():
            if word.startswith(word_to_complete):
                yield Completion(
                    text=word,
                    display_meta=details.get("description", ""),
                    start_position=-len(word_to_complete),
                )

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
            elif key == "$job_ids" and "jobs" in self.loaded:
                for j in self.loaded["jobs"]:
                    rv[j["id"]] = {
                        "description": f"Job {j['channel']} {j['url']}",
                        "commands": {},
                    }
            elif key == "$generatejob_ids" and "generatejobs" in self.loaded:
                for j in self.loaded["generatejobs"]:
                    rv[j["id"]] = {
                        "description": f"Generate Job {j['job_id']} {j['model']}",
                        "commands": {},
                    }
            else:
                rv[key] = value
        return rv

    def add_loaded(self, key: str, value: Any):
        self.loaded[key] = value


class ArenaCommander:
    def __init__(self, config: Dict[str, Any]):
        self.arena_client = ArenaClient(config["arena"])
        self.message_broker = MessageBrokerClient(config["messagebroker"])
        self.participant_client = ParticipantClient(config["actor"])
        self.scheduler_client = SchedulerClient(config["scheduler"])
        self.config = config
        self.loaded: Dict[str, Dict[str, Any]] = {}
        self.command_completer = CommandCompleter()
        self.session = PromptSession(
            history=FileHistory(".arena-control.history"),
            completer=self.command_completer,
        )
        self.loaded = {}
        self.subscriptions = {}

    async def subscribe(self, channel: str):
        if channel not in self.subscriptions:
            self.subscriptions[channel] = await self.message_broker.subscribe(
                channel, self.on_message
            )
        return self.subscriptions[channel]

    async def unsubscribe(self, channel: str):
        if channel in self.subscriptions:
            await self.subscriptions[channel].unsubscribe()
            del self.subscriptions[channel]

    async def on_message(self, msg: Msg):
        # actor.llm.id.job_id.state
        parts = msg.subject.split(".")
        if parts[1] == "llm" and len(parts) == 5:
            id = parts[2]
            job_id = parts[3]
            job_state = parts[4]
            if job_state == "start":
                print_title(f"Generation job {job_id} started", success=True)
            elif job_state == "complete":
                print_title(f"Generation job {job_id} completed", success=True)
                await self.unsubscribe(f"actor.llm.{id}.*.*")
                r = await self.participant_client.get(f"/api/generatejob/{id}")
                data = r.json()
                self.add_loaded("generatejob", data)
                r = await self.participant_client.get(f"/api/generatejob/{id}.md")
                print(render_markdown(r.content.decode("utf-8")))
            elif job_state == "fail":
                print_title(f"Generation job {job_id} failed", error=True)
                await self.unsubscribe(f"actor.llm.{id}.>")
        else:
            print_title(f"Message: {msg.subject}", info=True)

    def add_loaded(self, key: str, value: Any):
        self.loaded[key] = value
        self.command_completer.add_loaded(key, value)

    def clean_id(self, id: str, key: str) -> str:
        id = id.strip() if id else ""
        if id == "latest":
            possibles = self.loaded.get(key, [])
            assert isinstance(possibles, list), f"{key} must be a list"
            if len(possibles) == 0:
                print_title(f"No {key} loaded", error=True)
                return ""
            sorted_possibles = sorted(possibles, key=lambda x: x.get("created_at", 0))
            id = sorted_possibles[-1]["id"]
        return id

    async def cmd_arena(self, args: list[str]):
        arena_id = None
        if len(args) == 0:
            arena = self.loaded.get("arena", None)
            arena_id = arena["id"] if arena else None
            if not arena_id:
                print_title("No arena id provided", error=True)
                return True
            args = ["load", arena_id]

        cmd = args.pop(0)

        if cmd == "load":
            arena_id = await self.cmd_arena_load(args)
        elif cmd == "create":
            arena_id = await self.cmd_arena_create(args)
        else:
            arena_id = cmd

        if arena_id:
            arena_id = self.clean_id(arena_id, "arenas")

        if arena_id and arena_id != "":
            body = await self.arena_client.get(f"/api/arena/{arena_id}.md")
            print(render_markdown(body.content.decode("utf-8")))

        return True

    async def cmd_arena_create(self, args: list[str]):
        data = {}
        print_title("Create Arena", info=True)
        data["name"] = await prompt_str("Name")
        if not data["name"]:
            return False
        data["description"] = await prompt_str(
            "Description", default=f"A new arena named {data['name']}"
        )
        data["height"] = await prompt_int(
            "Height", min_value=1, max_value=1000, default=10
        )
        data["width"] = await prompt_int(
            "Width", min_value=1, max_value=1000, default=10
        )

        data["rules"] = await self.session.prompt_async(
            "Rules",
            default=CAPTURE_THE_FLAG_RULES,
        )
        winning_condition = await prompt_str(
            "Winning Condition",
            default="First player to bring the flag to the base wins",
        )
        data["winning_condition"] = winning_condition
        data["max_random_features"] = await prompt_int(
            "Max Random Features", min_value=0, max_value=20, default=5
        )
        data["features"] = []
        num_features = await prompt_int(
            "Number of features", min_value=0, max_value=20, default=0
        )
        for i in range(num_features):
            feature = {}
            feature["name"] = await prompt_str(
                f"Feature {i+1} name", default="base", words=["base", "flag"]
            )
            feature["description"] = await prompt_str(
                f"Feature {i+1} description",
                default=f"The flag the players are seeking to capture",
                words=[
                    "The flag the players are seeking to capture",
                    "The Scoring Base",
                ],
            )
            feature["position"] = await prompt_str(
                f"Feature {i+1} position",
                default=f"5,5",
                words=["5,5", "1,5"],
            )
            feature["origin"] = "required"
            data["features"].append(feature)
        r = await self.arena_client.post("/api/arena", data)
        r.raise_for_status()
        data = r.json()
        self.loaded["arena"] = data
        print_title(f"Arena {data['name']} created", success=True)
        return data["id"]

    async def cmd_arena_load(self, args: list[str]):
        if not args:
            print_title("No arena id provided", error=True)
            return None
        arena_id = self.clean_id(args[0], "arenas")
        r = await self.arena_client.get(f"/api/arena/{arena_id}")
        r.raise_for_status()
        self.loaded["arena"] = r.json()
        return arena_id

    async def cmd_arena_start(self, args: list[str]):
        arena_id = None
        if len(args) > 0:
            arena_id = args[0]
        else:
            arena = self.loaded.get("arena", None)
            arena_id = arena["id"] if arena else None
        if not arena_id:
            print_title("No arena id provided", error=True)
            return True
        r = await self.arena_client.post(f"/api/arena/{arena_id}/start", {})
        r.raise_for_status()
        return arena_id

    async def cmd_arenas(self, args: list[str]):
        r = await self.arena_client.get("/api/arena")
        arenas = r.json()
        # self.command_completer.update([a["id"] for a in arenas], "arena", False)
        self.add_loaded("arenas", arenas)
        print_arena_list(arenas)
        return True

    async def cmd_clear(self, args: list[str]):
        print_title("Cleared all loaded data", info=True)
        self.loaded = {}
        return True

    async def cmd_contest(self, args: list[str]):
        contest_id = None
        if len(args) == 0:
            contest = self.loaded.get("contest", None)
            contest_id = contest["id"] if contest else None
            if not contest_id:
                print_title("No contest id provided", error=True)
                return True
            args = ["load", contest_id]

        cmd = args.pop(0)

        if cmd == "load":
            contest_id = await self.cmd_contest_load(args)
        elif cmd == "start":
            contest_id = await self.cmd_contest_start(args)
        else:
            contest_id = cmd

        if contest_id and isinstance(contest_id, str):
            contest_id = self.clean_id(contest_id, "contests")

        if contest_id and contest_id != "":
            body = await self.arena_client.get(f"/api/contest/{contest_id}.md")
            print(render_markdown(body.content.decode("utf-8")))

        return True

    async def cmd_contest_load(self, args: list[str]):
        if not args:
            print_title("No contest id provided", error=True)
            return None
        contest_id = self.clean_id(args[0], "contests")
        r = await self.arena_client.get(f"/api/contest/{contest_id}")
        r.raise_for_status()
        self.loaded["contest"] = r.json()

        return contest_id

    async def cmd_contest_start(self, args: list[str]):
        contest_id = None
        if len(args) > 0:
            contest_id = args[0]
        else:
            contest = self.loaded.get("contest", None)
            contest_id = contest["id"] if contest else None
        if not contest_id:
            print_title("No contest id provided", error=True)
            return True
        r = await self.arena_client.post(f"/api/contest/{contest_id}/start", {})
        r.raise_for_status()
        return contest_id

    async def cmd_contests(self, args: list[str]):
        r = await self.arena_client.get("/api/contest")
        contests = r.json()
        # self.command_completer.update([c["id"] for c in contests], "contest", False)
        self.add_loaded("contests", contests)
        print_contest_list(contests)
        return True

    async def cmd_exit(self, args: list[str]):
        print_title("Exiting...", info=True)
        return False

    async def cmd_generatejob(self, args: list[str]):
        job_id = None
        if len(args) == 0:
            job = self.loaded.get("generatejob", None)
            job_id = job["id"] if job else None
            if not job_id:
                print_title("No generate job id provided", error=True)
                return True
            args = ["load", job_id]

        cmd = args.pop(0)
        show_md = True

        if cmd == "load":
            job_id = await self.cmd_generatejob_load(args)
        elif cmd == "repeat":
            job_id = await self.cmd_generatejob_repeat(args)
            show_md = False
        else:
            job_id = cmd

        if show_md:
            if job_id:
                job_id = self.clean_id(job_id, "generatejobs")

            if job_id and job_id != "":
                body = await self.participant_client.get(
                    f"/api/generatejob/{job_id}.md"
                )
                print(render_markdown(body.content.decode("utf-8")))

        return True

    async def cmd_generatejob_load(self, args: list[str]):
        if not args:
            job = self.loaded.get("generatejob", None)
            if not job:
                print_title("No generate job id provided", error=True)
                return None
            job_id = job["id"]
            args = [job_id]

        job_id = self.clean_id(args[0], "generatejobs")
        r = await self.participant_client.get(f"/api/generatejob/{job_id}")
        r.raise_for_status()
        self.loaded["generatejob"] = r.json()
        return job_id

    async def cmd_generatejob_repeat(self, args: list[str]):
        if not args:
            job = self.loaded.get("generatejob", None)
            if not job:
                print_title("No generate job id provided", error=True)
                return None
            job_id = job["id"]
            args = [job_id]

        job_id = self.clean_id(args[0], "generatejobs")
        r = await self.participant_client.get(f"/api/generatejob/{job_id}")
        r.raise_for_status()
        self.loaded["generatejob"] = r.json()
        words = []
        meta = {}
        for m in self.config["llm"]:
            words.append(m["name"])
            meta[m["name"]] = m["key"]
        words = sorted(words)
        model = await prompt_str(
            "Model",
            default=self.loaded["generatejob"]["model"],
            words=words,
        )
        model_id = meta.get(model, None)
        if not model_id:
            print_title(f"Invalid model: {model}", error=True)
            return None

        r = await self.participant_client.post(
            f"/api/generatejob/repeat", {"original_id": job_id, "model": model_id}
        )
        r.raise_for_status()
        data = r.json()
        self.loaded["generatejob"] = data
        print_title(f"Generate job cloned, new ID is: {data['id']}", success=True)
        gen_id = data["id"]
        channel = f"actor.llm.{gen_id}.>"
        await self.subscribe(channel)
        print(f"Waiting for job to complete... {channel}")

        return gen_id

    async def cmd_generatejobs(self, args: list[str]):
        r = await self.participant_client.get("/api/generatejob")
        jobs = r.json()
        self.add_loaded("generatejobs", jobs)
        print_generate_job_list(jobs)
        return True

    async def cmd_help(self, args: list[str]):
        print_title("Help", info=True)
        return True

    async def cmd_job(self, args: list[str]):
        job_id = None
        if len(args) == 0:
            job = self.loaded.get("job", None)
            job_id = job["id"] if job else None
            if not job_id:
                print_title("No job id provided", error=True)
                return True
            args = ["load", job_id]

        cmd = args.pop(0)

        if cmd == "load":
            job_id = await self.cmd_job_load(args)
        elif cmd == "create":
            job_id = await self.cmd_job_create(args)
        else:
            job_id = cmd

        if job_id:
            job_id = self.clean_id(job_id, "jobs")

        if job_id and job_id != "":
            body = await self.scheduler_client.get(f"/api/job/{job_id}.md")
            print(render_markdown(body.content.decode("utf-8")))

        return True

    async def cmd_job_load(self, args: list[str]):
        if not args:
            print_title("No job id provided", error=True)
            return None
        job_id = self.clean_id(args[0], "jobs")
        r = await self.scheduler_client.get(f"/api/job/{job_id}")
        r.raise_for_status()
        self.loaded["job"] = r.json()
        return job_id

    async def cmd_job_create(self, args: list[str]):
        data = {}
        print_title("Create Job", info=True)
        data["channel"] = await prompt_str("Channel", default="default")
        data["method"] = await prompt_str(
            "Method", default="POST", words=["POST", "GET", "PUT", "DELETE"]
        )
        data["url"] = await prompt_str(
            "URL", default="http://localhost:8000/api/debug/health"
        )
        data["priority"] = await prompt_int("Priority", default=50)
        data["data"] = await prompt_str("Data (json)", default="{}")

        r = await self.scheduler_client.post("/api/job", data)
        r.raise_for_status()
        data = r.json()
        self.loaded["job"] = data
        print_title(f"Job {data['id']} created", success=True)
        return data["id"]

    async def cmd_jobs(self, args: list[str]):
        r = await self.scheduler_client.get("/api/job")
        jobs = r.json()
        self.add_loaded("jobs", jobs)
        print_job_list(jobs)
        return True

    async def cmd_listen(self, args: list[str]):
        if not args:
            print_title("No channel provided", error=True)
            return True
        if len(args) == 0:
            print_title("No channel provided", error=True)
            return True
        channel = args[0]
        if channel == "":
            print_title("No channel provided", error=True)
            return True
        if channel == "all":
            await self.subscribe("arena.>")
            await self.subscribe("actor.>")
            await self.subscribe("scheduler.>")
        elif channel == "most":
            await self.subscribe("arena.>")
            await self.subscribe("actor.>")
        elif channel == "none":
            await self.unsubscribe("arena.>")
            await self.unsubscribe("actor.>")
            await self.unsubscribe("scheduler.>")
        elif channel == "arena":
            await self.subscribe("arena.>")
        elif channel == "actor":
            await self.subscribe("actor.>")
        elif channel == "scheduler":
            await self.subscribe("scheduler.>")
        else:
            await self.subscribe(channel)
        return True

    async def cmd_participant(self, args: list[str]):
        participant_id = None
        if len(args) == 0:
            participant = self.loaded.get("participant", None)
            participant_id = participant["id"] if participant else None
            if not participant_id:
                print_title("No participant id provided", error=True)
                return True
            args = ["load", participant_id]
        cmd = args.pop(0)
        if cmd == "load":
            participant_id = await self.cmd_participant_load(args)
        elif cmd == "create":
            participant_id = await self.cmd_participant_create(args)
        else:
            participant_id = cmd
        if participant_id:
            r = await self.participant_client.get(f"/api/agent/{participant_id}")
            r.raise_for_status()
            data = r.json()
            self.loaded["participant"] = data
            print_title(f"Loaded participant {data['name']}", success=True)
            print_participant_list([data])
        return True

    async def cmd_participant_create(self, args: list[str]):
        data = {}
        print_title("Create participant", info=True)
        data["name"] = await prompt_str("Name")
        if not data["name"]:
            return False
        data["participant_id"] = await prompt_str("Participant ID")
        data["model"] = await prompt_str("Model", default="gpt-3.5-turbo")
        # Fetch strategies for selection
        strat_resp = await self.participant_client.get("/api/strategy")
        strategies = strat_resp.json()
        print_title("Available Strategies", info=True)
        for s in strategies:
            print(HTML(f"  {s['id']} - {s['name']} ({s['role']})"))
        strat_ids = [s["id"] for s in strategies]
        data["strategy_id"] = await prompt_str("Strategy ID", words=strat_ids)
        if data["strategy_id"] not in strat_ids:
            print_title("Invalid strategy id", error=True)
            return False
        r = await self.participant_client.post("/api/agent", data)
        r.raise_for_status()
        data = r.json()
        self.loaded["participant"] = data
        print_title(f"participant {data['name']} created", success=True)
        return data["id"]

    async def cmd_participant_load(self, args: list[str]):
        if not args:
            print_title("No participant id provided", error=True)
            return None
        r = await self.participant_client.get(f"/api/agent/{args[0]}")
        r.raise_for_status()
        self.loaded["participant"] = r.json()
        return args[0]

    async def cmd_participants(self, args: list[str]):
        r = await self.participant_client.get("/api/agent")
        participants = r.json()
        self.add_loaded("participants", participants)
        print_participant_list(participants)
        return True

    async def cmd_strategy(self, args: list[str]):
        strategy_id = None
        if len(args) == 0:
            strategy = self.loaded.get("strategy", None)
            strategy_id = strategy["id"] if strategy else None
            if not strategy_id:
                print_title("No strategy id provided", error=True)
                return True
            args = ["load", strategy_id]
        cmd = args.pop(0)
        if cmd == "load":
            strategy_id = await self.cmd_strategy_load(args)
        elif cmd == "create":
            strategy_id = await self.cmd_strategy_create(args)
        else:
            strategy_id = cmd
        if strategy_id:
            r = await self.participant_client.get(f"/api/strategy/{strategy_id}")
            r.raise_for_status()
            data = r.json()
            self.loaded["strategy"] = data
            print_title(f"Loaded strategy {data['name']}", success=True)
            print_strategy_list([data])
        return True

    async def cmd_strategy_create(self, args: list[str]):
        data = {}
        print_title("Create Strategy", info=True)
        data["name"] = await prompt_str("Name")
        if not data["name"]:
            return False
        data["personality"] = await prompt_str("Personality")
        data["description"] = await prompt_str("Description")
        # Role selection
        role_types = ["PLAYER", "ARENA", "JUDGE", "ANNOUNCER"]
        data["role"] = await prompt_str("Role", default="PLAYER", words=role_types)
        if data["role"] not in role_types:
            print_title("Invalid role type", error=True)
            return False
        # Prompts
        data["prompts"] = []
        add_more = True
        while add_more:
            prompt_key = await prompt_str("Prompt Key (e.g. ARENA_GENERATE_FEATURES)")
            prompt_text = await prompt_str("Prompt Text (jinja template or text)")
            if prompt_key and prompt_text:
                data["prompts"].append({"key": prompt_key, "prompt": prompt_text})
            more = await prompt_str(
                "Add another prompt? (y/n)", default="n", words=["y", "n"]
            )
            add_more = more and more.lower().startswith("y")
        r = await self.participant_client.post("/api/strategy", data)
        r.raise_for_status()
        data = r.json()
        self.loaded["strategy"] = data
        print_title(f"Strategy {data['name']} created", success=True)
        return data["id"]

    async def cmd_strategy_load(self, args: list[str]):
        if not args:
            print_title("No strategy id provided", error=True)
            return None
        r = await self.participant_client.get(f"/api/strategy/{args[0]}")
        r.raise_for_status()
        self.loaded["strategy"] = r.json()
        return args[0]

    async def cmd_strategies(self, args: list[str]):
        r = await self.participant_client.get("/api/strategy")
        strategies = r.json()
        self.add_loaded("strategies", strategies)
        print_strategy_list(strategies)
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
        elif cmd == "participant":
            await self.cmd_participant(args)
        elif cmd == "participants":
            await self.cmd_participants(args)
        elif cmd == "strategy":
            await self.cmd_strategy(args)
        elif cmd == "strategies":
            await self.cmd_strategies(args)
        elif cmd == "clear":
            await self.cmd_clear(args)
        elif cmd == "contests":
            await self.cmd_contests(args)
        elif cmd == "contest":
            await self.cmd_contest(args)
        elif cmd == "listen":
            await self.cmd_listen(args)
        elif cmd == "jobs":
            await self.cmd_jobs(args)
        elif cmd == "job":
            await self.cmd_job(args)
        elif cmd == "generatejobs":
            await self.cmd_generatejobs(args)
        elif cmd == "generatejob":
            await self.cmd_generatejob(args)
        elif cmd == "exit":
            await self.cmd_exit(args)
        else:
            print_title(f"Unknown command: {cmd}", error=True)

    async def prompt(self, text: str = "> ") -> str:
        keys = self.loaded.keys()
        sorted_keys = sorted(keys)
        for key in sorted_keys:
            value = self.loaded[key]
            if isinstance(value, list):
                print(HTML(f"<ansiblue>{key}:</ansiblue> {len(value)}"))
            else:
                print(HTML(f"<ansiblue>{key}:</ansiblue> {value['id']}"))
        return await self.session.prompt_async(
            text,
            completer=self.command_completer,
            complete_while_typing=True,
        )

    async def start(self):
        while True:
            try:
                text = await self.prompt()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                print_title(f"{e}", error=True)
                continue
            await self.process_command(text)


async def main():
    config = read_config()
    commander = ArenaCommander(config)
    print_container(
        Frame(
            TextArea(
                text=f"Version: {VERSION} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ),
            title="Mister Agent Control",
        )
    )

    await commander.start()
    print("GoodBye!")


if __name__ == "__main__":
    asyncio.run(main())
