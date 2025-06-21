import asyncio
import os
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import yaml
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import print_container, input_dialog
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import TextArea

from agentarena.util.files import find_file_upwards

from .clients import ParticipantClient
from .clients import ArenaClient
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


def _print_list_generic(title: str, items: List[Dict[str, Any]], formatter: callable):
    print_title(title, info=True)
    if not items:
        print(HTML("  <em>No items to display.</em>"))
        return
    for item in items:
        print(HTML(formatter(item)))


def print_arena_list(arenas: List[Dict[str, Any]]):
    _print_list_generic("Arenas", arenas, lambda a: f"  {a['id']} - {a['name']}")


def print_contest_list(contests: List[Dict[str, Any]]):
    _print_list_generic(
        "Contests",
        contests,
        lambda c: f"  {c['id']} - <ansiblue>{c['arena']['name']}</ansiblue> - {c['state']}",
    )


def print_job_list(jobs: List[Dict[str, Any]]):
    _print_list_generic(
        "Jobs", jobs, lambda j: f"  {j['id']} - {j['channel']} - {j['state']}"
    )


def print_generate_job_list(jobs: List[Dict[str, Any]]):
    _print_list_generic(
        "Generate Jobs",
        jobs,
        lambda j: f"  {j['id']} - {j['job_id']} - {j['model']} - {j['state']}",
    )


def print_participant_list(participants: List[Dict[str, Any]]):
    def _format_participant(p: Dict[str, Any]) -> str:
        strat = p.get("strategy")
        strat_str = f" (strategy: {strat['name']})" if strat else ""
        return f"  {p['id']} - {p['name']}{strat_str} (participant: {p['participant_id']})"

    _print_list_generic("Participants", participants, _format_participant)


def print_strategy_list(strategies: List[Dict[str, Any]]):
    def _format_strategy(s: Dict[str, Any]) -> str:
        prompt_count = len(s.get("prompts", []))
        return f"  {s['id']} - {s['name']} ({s['role']}) | {s['personality']} | {s['description']} | prompts: {prompt_count}"

    _print_list_generic("Strategies", strategies, _format_strategy)


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
    "generatejobs": {
        "description": "list all generate jobs",
        "commands": {},
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
        },
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

    async def _list_items(
        self,
        item_type_plural: str, # e.g., "arenas"
        client: Any,          # e.g., self.arena_client
        api_path: str,        # e.g., "/api/arena"
        print_function: callable # e.g., print_arena_list
    ):
        try:
            r = await client.get(api_path)
            r.raise_for_status()
            items = r.json()
            self.add_loaded(item_type_plural, items) # Updates self.loaded and completer
            print_function(items)
        except Exception as e:
            print_title(f"Error listing {item_type_plural}: {e}", error=True)
        return True # Keep shell running

    async def _prompt_for_fields(self, field_definitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        data = {}
        for field_def in field_definitions:
            prompt_text = field_def["prompt"]
            default_val = field_def.get("default")
            field_type = field_def.get("type", "str")
            words = field_def.get("words", [])

            if field_type == "int":
                min_val = field_def.get("min_value", 0)
                max_val = field_def.get("max_value", 1000)
                # Ensure default_val is int if provided for prompt_int
                current_default_int = default_val if isinstance(default_val, int) else field_def.get("default_int", 5)

                data[field_def["name"]] = await prompt_int(
                    prompt_text,
                    min_value=min_val,
                    max_value=max_val,
                    default=current_default_int, # prompt_int expects int
                    words=words,
                )
            else: # Default to string prompt
                data[field_def["name"]] = await prompt_str(
                    prompt_text, default=str(default_val) if default_val is not None else None, words=words
                )

            if data[field_def["name"]] is None and field_def.get("required", False):
                print_title(f"{field_def['name']} is required.", error=True)
                # Or raise an exception to halt creation
                return {} # Indicate failure
        return data

    async def _post_and_load_item(self, client: Any, api_path: str, data: Dict[str, Any], item_type_singular: str, item_name_field: str = "name") -> Optional[str]:
        try:
            r = await client.post(api_path, data)
            r.raise_for_status()
            created_item_data = r.json()
            self.loaded[item_type_singular] = created_item_data
            item_display_name = created_item_data.get(item_name_field, created_item_data.get("id", "Unknown"))
            print_title(f"{item_type_singular.capitalize()} {item_display_name} created", success=True)
            return created_item_data["id"]
        except Exception as e:
            print_title(f"Error creating {item_type_singular}: {e}", error=True)
            return None

    async def _load_item_by_id(
        self,
        item_type_singular: str,
        item_type_plural: str,
        item_id: str,
        client: Any,  # ArenaClient, ParticipantClient, or SchedulerClient
        endpoint_path_template: str, # e.g., "/api/arena/{id}"
    ) -> Optional[str]:
        if not item_id:
            print_title(f"No {item_type_singular} id provided", error=True)
            return None
        cleaned_id = self.clean_id(item_id, item_type_plural)
        if not cleaned_id:
            # clean_id will print its own error if "latest" fails
            if item_id != "latest": # Avoid double error message for "latest"
                 print_title(f"Invalid {item_type_singular} id: {item_id}", error=True)
            return None

        try:
            r = await client.get(endpoint_path_template.format(id=cleaned_id))
            r.raise_for_status()
            item_data = r.json()
            self.loaded[item_type_singular] = item_data
            print_title(f"Loaded {item_type_singular} {item_data.get('name', cleaned_id)}", success=True)
            return cleaned_id
        except Exception as e:
            print_title(f"Error loading {item_type_singular} {cleaned_id}: {e}", error=True)
            return None

    def add_loaded(self, key: str, value: Any):
        self.loaded[key] = value
        self.command_completer.add_loaded(key, value)

    async def _handle_item_command(
        self,
        args: list[str],
        item_type_singular: str,
        item_type_plural: str,
        client: Any, # ArenaClient, ParticipantClient, or SchedulerClient
        base_api_path: str, # e.g., "/api/arena"
        create_method: Optional[callable], # e.g., self.cmd_arena_create
        load_method: callable, # e.g., self.cmd_arena_load
        # Some commands have extra subcommands like "start"
        extra_subcommands: Optional[Dict[str, callable]] = None,
        handle_display: bool = True, # If False, returns item_id for custom handling
        item_specific_fetch_and_display_method: Optional[callable] = None, # For participant-like custom display
        use_clean_id_on_direct_arg: bool = True, # For participant, this should be False
    ):
        item_id = None
        action_taken = False # To track if a subcommand like load/create modified item_id
        # If handle_display is False, this function should aim to return the resolved item_id
        # or None if an action failed (e.g. create failed, load failed)

        if not args:
            # No args, check if item is already loaded
            loaded_item = self.loaded.get(item_type_singular)
            item_id = loaded_item["id"] if loaded_item else None
            if not item_id:
                print_title(f"No {item_type_singular} id provided and none loaded.", error=True)
                return True # Keep shell running
            # If loaded, default action is to show it (handled after subcommands)
            args = ["show", item_id] # Synthesize args to show the loaded item

        cmd = args.pop(0) if args else "show" # Default to 'show' if only ID was implicitly loaded

        if cmd == "load":
            item_id = await load_method(args[:1]) # Pass only the ID part of args
            action_taken = True
        elif cmd == "create":
            if create_method:
                item_id = await create_method(args)
            else:
                print_title(f"Creation is not supported for {item_type_singular}.", error=True)
            action_taken = True
        elif extra_subcommands and cmd in extra_subcommands:
            # Handle extra subcommands like "start"
            # These might take the rest of args, or an ID if provided, or use loaded.
            target_id_arg = args[0] if args else None
            current_loaded_id = self.loaded.get(item_type_singular, {}).get("id")

            id_for_subcommand = target_id_arg or current_loaded_id

            if not id_for_subcommand and item_id: # if item_id was set from a previous step like implicit load
                 id_for_subcommand = item_id

            if not id_for_subcommand:
                # Try to clean the target_id_arg if it was "latest"
                if target_id_arg:
                     id_for_subcommand = self.clean_id(target_id_arg, item_type_plural)

            if not id_for_subcommand:
                print_title(f"No {item_type_singular} ID specified or loaded for '{cmd}'.", error=True)
                return True

            # The subcommand itself might return an ID or status.
            # We assume it handles its own logic and printing success/failure.
            # We might want to update item_id if the subcommand returns it.
            result = await extra_subcommands[cmd]([id_for_subcommand] + args[1:]) # Pass ID and any further args
            if isinstance(result, str): # Assuming it returns the ID if successful
                item_id = result
            action_taken = True
            # After an action like 'start', we might not want to display the markdown immediately,
            # or the subcommand handles its own display. For now, let's assume it's fine.
            # If 'start' modified the item, item_id should be the ID of the (potentially modified) item.
        elif not action_taken: # If cmd was not load/create or other action
            # Assume cmd is an ID if no other action was taken yet
            # This covers cases like "arena <id>" directly
            item_id = cmd
            # And if there were more args, they are ignored for direct ID view for now.
            # This aligns with original behavior where "arena <id> foo" would just load <id>.

        # If an item_id was determined (either from load, create, or direct arg)
        # and it's not empty, then try to clean it (if not already cleaned by load_method)
        # and display its markdown.
        if item_id and not action_taken: # only clean if not from load/create which clean themselves
            if use_clean_id_on_direct_arg:
                 item_id = self.clean_id(item_id, item_type_plural)
            # If use_clean_id_on_direct_arg is false (e.g. for participant), item_id remains as is.


        if not handle_display:
            # If create/load failed, item_id might be False/None.
            # If an ID was determined (e.g. from args directly), it's returned.
            # If an action was taken (load/create) and it returned an ID, that's item_id.
            # If an action was taken and it failed (e.g. create_method returned None/False), item_id is None/False.
            return item_id

        if item_id and str(item_id).strip(): # Ensure item_id is not None or empty string
            if item_specific_fetch_and_display_method:
                # This method is responsible for fetching, loading, and displaying.
                # It might need the client or other details.
                # For cmd_participant, it will be a wrapper around its custom logic.
                # It should take item_id as an argument.
                await item_specific_fetch_and_display_method(item_id)
            elif handle_display: # Default markdown display
                try:
                    # Fetch and display markdown representation
                    md_path = f"{base_api_path}/{item_id}.md"
                    body = await client.get(md_path)
                    body.raise_for_status() # Ensure we check for HTTP errors
                    print(render_markdown(body.content.decode("utf-8")))
                except Exception as e:
                    if not action_taken:
                        print_title(f"Could not retrieve details for {item_type_singular} {item_id}: {e}", error=True)
            # else: item_id was resolved, but handle_display is False, so we already returned.

        elif not action_taken and cmd != "create" and handle_display:
            print_title(f"Unknown command or invalid {item_type_singular} specified: {cmd}", error=True)

        return True # Keep shell running


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
        # Arena has a "start" subcommand which is not common.
        # The generic handler might need adjustment or this remains specific.
        # For now, let's try to adapt it. cmd_arena_start needs to be callable.
        # Original cmd_arena_start also had logic to use loaded arena if no arg.
        return await self._handle_item_command(
            args=args,
            item_type_singular="arena",
            item_type_plural="arenas",
            client=self.arena_client,
            base_api_path="/api/arena",
            create_method=self.cmd_arena_create,
            load_method=self.cmd_arena_load,
            extra_subcommands={"start": self.cmd_arena_start} # Pass the start method
        )

    async def cmd_arena_create(self, args: list[str]):
        arena_data = {}
        print_title("Create Arena", info=True)

        # Custom handling for name and description due to interdependency
        arena_data["name"] = await prompt_str("Name", default = "")
        if not arena_data["name"]:
            print_title("Arena name is required.", error=True)
            return None # Original returned False, None is consistent for ID

        arena_data["description"] = await prompt_str(
            "Description", default=f"A new arena named {arena_data['name']}"
        )

        # Use _prompt_for_fields for simpler, independent fields
        simple_field_defs = [
            {"name": "height", "prompt": "Height", "type": "int", "default_int": 10, "min_value": 1, "max_value": 1000},
            {"name": "width", "prompt": "Width", "type": "int", "default_int": 10, "min_value": 1, "max_value": 1000},
            {"name": "winning_condition", "prompt": "Winning Condition", "type": "str", "default": "First player to bring the flag to the base wins"},
            {"name": "max_random_features", "prompt": "Max Random Features", "type": "int", "default_int": 5, "min_value": 0, "max_value": 20},
        ]
        prompted_simple_data = await self._prompt_for_fields(simple_field_defs)
        if not prompted_simple_data and any(f.get("required") for f in simple_field_defs): # check if required failed
            return None
        arena_data.update(prompted_simple_data)

        # Custom handling for rules (direct session.prompt_async)
        arena_data["rules"] = await self.session.prompt_async(
            "Rules", default=CAPTURE_THE_FLAG_RULES
        )

        # Custom handling for features list
        arena_data["features"] = []
        num_features = await prompt_int(
            "Number of features", min_value=0, max_value=20, default=0
        )
        for i in range(num_features):
            feature = {}
            print_title(f"Feature {i+1}", info=True)
            feature_field_defs = [
                {"name": "name", "prompt": f"Name", "type": "str", "default": "base", "words": ["base", "flag"]},
                {"name": "description", "prompt": f"Description", "type": "str", "default": "The flag the players are seeking to capture", "words": ["The flag the players are seeking to capture", "The Scoring Base"]},
                {"name": "position", "prompt": f"Position (x,y)", "type": "str", "default": "5,5", "words": ["5,5", "1,5"]},
            ]
            feature_data = await self._prompt_for_fields(feature_field_defs)
            if not feature_data: return None # Required field failed in feature prompt

            feature.update(feature_data)
            feature["origin"] = "required" # Hardcoded as in original
            arena_data["features"].append(feature)

        return await self._post_and_load_item(
            client=self.arena_client,
            api_path="/api/arena",
            data=arena_data,
            item_type_singular="arena" # name_field defaults to "name"
        )

    async def cmd_arena_load(self, args: list[str]):
        item_id_to_load = args[0] if args else None
        return await self._load_item_by_id(
            item_type_singular="arena",
            item_type_plural="arenas",
            item_id=item_id_to_load,
            client=self.arena_client,
            endpoint_path_template="/api/arena/{id}",
        )

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
        return await self._list_items(
            item_type_plural="arenas",
            client=self.arena_client,
            api_path="/api/arena",
            print_function=print_arena_list,
        )

    async def cmd_clear(self, args: list[str]):
        print_title("Cleared all loaded data", info=True)
        self.loaded = {}
        return True

    async def cmd_contest(self, args: list[str]):
        return await self._handle_item_command(
            args=args,
            item_type_singular="contest",
            item_type_plural="contests",
            client=self.arena_client,
            base_api_path="/api/contest",
            create_method=None, # No cmd_contest_create in original, pass None
            load_method=self.cmd_contest_load,
            extra_subcommands={"start": self.cmd_contest_start}
        )

    async def cmd_contest_load(self, args: list[str]):
        item_id_to_load = args[0] if args else None
        return await self._load_item_by_id(
            item_type_singular="contest",
            item_type_plural="contests",
            item_id=item_id_to_load,
            client=self.arena_client,
            endpoint_path_template="/api/contest/{id}",
        )

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
        return await self._list_items(
            item_type_plural="contests",
            client=self.arena_client,
            api_path="/api/contest",
            print_function=print_contest_list,
        )

    async def cmd_exit(self, args: list[str]):
        print_title("Exiting...", info=True)
        return False

    async def cmd_generatejob(self, args: list[str]):
        return await self._handle_item_command(
            args=args,
            item_type_singular="generatejob",
            item_type_plural="generatejobs",
            client=self.participant_client,
            base_api_path="/api/generatejob",
            create_method=None, # No create for generatejob
            load_method=self.cmd_generatejob_load
        )

    async def cmd_generatejob_load(self, args: list[str]):
        item_id_to_load = args[0] if args else None
        return await self._load_item_by_id(
            item_type_singular="generatejob",
            item_type_plural="generatejobs",
            item_id=item_id_to_load,
            client=self.participant_client,
            endpoint_path_template="/api/generatejob/{id}",
        )

    async def cmd_generatejobs(self, args: list[str]):
        return await self._list_items(
            item_type_plural="generatejobs",
            client=self.participant_client,
            api_path="/api/generatejob",
            print_function=print_generate_job_list,
        )

    async def cmd_help(self, args: list[str]):
        print_title("Help", info=True)
        return True

    async def cmd_job(self, args: list[str]):
        return await self._handle_item_command(
            args=args,
            item_type_singular="job",
            item_type_plural="jobs",
            client=self.scheduler_client,
            base_api_path="/api/job",
            create_method=self.cmd_job_create,
            load_method=self.cmd_job_load
        )

    async def cmd_job_load(self, args: list[str]):
        item_id_to_load = args[0] if args else None
        return await self._load_item_by_id(
            item_type_singular="job",
            item_type_plural="jobs",
            item_id=item_id_to_load,
            client=self.scheduler_client,
            endpoint_path_template="/api/job/{id}",
        )

    async def cmd_job_create(self, args: list[str]):
        print_title("Create Job", info=True)

        field_definitions = [
            {"name": "channel", "prompt": "Channel", "type": "str", "default": "default", "required": True},
            {"name": "method", "prompt": "Method", "type": "str", "default": "POST", "words": ["POST", "GET", "PUT", "DELETE"], "required": True},
            {"name": "url", "prompt": "URL", "type": "str", "default": "http://localhost:8000/api/debug/health", "required": True},
            {"name": "priority", "prompt": "Priority", "type": "int", "default_int": 50, "required": True}, # default_int for prompt_int
            {"name": "data", "prompt": "Data (json)", "type": "str", "default": "{}"},
        ]

        data = await self._prompt_for_fields(field_definitions)

        if not data: # Prompting failed or a required field was missed
            return None

        # The item_name_field for a job is 'id' in the success message "Job {data['id']} created"
        return await self._post_and_load_item(
            client=self.scheduler_client,
            api_path="/api/job",
            data=data,
            item_type_singular="job",
            item_name_field="id"
        )

    async def cmd_jobs(self, args: list[str]):
        return await self._list_items(
            item_type_plural="jobs",
            client=self.scheduler_client,
            api_path="/api/job",
            print_function=print_job_list,
        )

    async def _fetch_and_display_participant(self, participant_id: str):
        if not participant_id:
            # This case should ideally be handled before calling,
            # or _handle_item_command should not call this if item_id is None.
            # For safety, if it's called with a falsy ID.
            # print_title("No participant ID to fetch.", error=True) # Already handled by caller
            return

        try:
            # Note: participant_id is not cleaned with clean_id here, matching original.
            r = await self.participant_client.get(f"/api/agent/{participant_id}")
            r.raise_for_status()
            data = r.json()
            self.loaded["participant"] = data
            print_title(f"Loaded participant {data['name']}", success=True)
            print_participant_list([data])
        except Exception as e:
            print_title(f"Error fetching participant {participant_id}: {e}", error=True)

    async def cmd_participant(self, args: list[str]):
        # cmd_participant_load is special: it doesn't load into self.loaded, just returns ID.
        # It also doesn't use clean_id for "latest".
        # The main cmd_participant then fetches, loads into self.loaded, and prints.

        # We set handle_display=True because _handle_item_command will call
        # _fetch_and_display_participant if an item_id is resolved.
        return await self._handle_item_command(
            args=args,
            item_type_singular="participant",
            item_type_plural="participants", # Used by clean_id if direct ID is "latest"
            client=self.participant_client,
            base_api_path="/api/agent", # For markdown if we ever used it, not used by custom display
            create_method=self.cmd_participant_create,
            load_method=self.cmd_participant_load, # This just returns ID from args
            handle_display=True, # We want the dispatcher to call our custom method
            item_specific_fetch_and_display_method=self._fetch_and_display_participant,
            use_clean_id_on_direct_arg=False # Participant IDs are not cleaned with "latest"
        )

    async def cmd_participant_create(self, args: list[str]):
        participant_data = {}
        print_title("Create participant", info=True)

        simple_field_defs = [
            {"name": "name", "prompt": "Name", "type": "str", "required": True},
            {"name": "participant_id", "prompt": "Participant ID", "type": "str", "required": False}, # Assuming can be optional
            {"name": "model", "prompt": "Model", "type": "str", "default": "gpt-3.5-turbo"},
        ]

        participant_data = await self._prompt_for_fields(simple_field_defs)
        if not participant_data.get("name"): # Name is critical
            # _prompt_for_fields would have printed error if name was required and empty
            # but if it wasn't marked required and came back empty, we stop.
            # Or, if _prompt_for_fields returned empty dict due to a required field failing.
             if not participant_data: # Check if prompt_for_fields itself failed
                return None
             print_title("Participant name is required.", error=True) # Explicit check if name is still empty
             return None


        # Custom logic for strategy selection
        try:
            strat_resp = await self.participant_client.get("/api/strategy")
            strat_resp.raise_for_status()
            strategies = strat_resp.json()
        except Exception as e:
            print_title(f"Could not fetch strategies: {e}", error=True)
            return None

        print_title("Available Strategies", info=True)
        strat_display_list = []
        for s in strategies:
            strat_display_list.append(HTML(f"  {s['id']} - {s['name']} ({s['role']})"))
        # Using _print_list_generic to show strategies if we wanted, but original was simple print
        # For now, stick to original print loop for exactness, or use a simpler formatter.
        if not strategies:
            print(HTML("  <em>No strategies available. Cannot create participant.</em>"))
            return None

        for s_display in strat_display_list:
            print(s_display)

        strat_ids = [s["id"] for s in strategies]
        participant_data["strategy_id"] = await prompt_str("Strategy ID", words=strat_ids)

        if participant_data["strategy_id"] not in strat_ids:
            print_title("Invalid strategy id", error=True)
            return None

        return await self._post_and_load_item(
            client=self.participant_client,
            api_path="/api/agent", # Note: API path
            data=participant_data,
            item_type_singular="participant"
        )

    async def cmd_participant_load(self, args: list[str]):
        if not args:
            print_title("No participant id provided", error=True)
            return None
        # This function, in its original form, just returns the ID.
        # The actual fetching and loading is done in the parent cmd_participant.
        # It does not use clean_id here, nor does it directly update self.loaded.
        return args[0]

    async def cmd_participants(self, args: list[str]):
        return await self._list_items(
            item_type_plural="participants",
            client=self.participant_client,
            api_path="/api/agent", # Note: API path is /api/agent for participants
            print_function=print_participant_list,
        )

    async def _fetch_and_display_strategy(self, strategy_id: str):
        if not strategy_id:
            return
        try:
            # Original cmd_strategy doesn't clean_id for direct ID access.
            # cmd_strategy_load *does* use clean_id via _load_item_by_id.
            # This method assumes strategy_id is the final ID to be used.
            r = await self.participant_client.get(f"/api/strategy/{strategy_id}")
            r.raise_for_status()
            data = r.json()
            # Ensure it's loaded for consistency, though cmd_strategy_load might've already done it.
            self.loaded["strategy"] = data
            print_title(f"Loaded strategy {data['name']}", success=True)
            print_strategy_list([data])
        except Exception as e:
            print_title(f"Error fetching strategy {strategy_id}: {e}", error=True)


    async def cmd_strategy(self, args: list[str]):
        return await self._handle_item_command(
            args=args,
            item_type_singular="strategy",
            item_type_plural="strategies", # Used by clean_id if direct ID is "latest"
            client=self.participant_client,
            base_api_path="/api/strategy", # Not used by custom display
            create_method=self.cmd_strategy_create,
            load_method=self.cmd_strategy_load, # Uses _load_item_by_id
            handle_display=True,
            item_specific_fetch_and_display_method=self._fetch_and_display_strategy,
            use_clean_id_on_direct_arg=False # Original did not clean direct strategy ID
        )

    async def cmd_strategy_create(self, args: list[str]):
        strategy_data = {}
        print_title("Create Strategy", info=True)

        simple_field_defs = [
            {"name": "name", "prompt": "Name", "type": "str", "required": True},
            {"name": "personality", "prompt": "Personality", "type": "str"},
            {"name": "description", "prompt": "Description", "type": "str"},
        ]
        strategy_data = await self._prompt_for_fields(simple_field_defs)
        if not strategy_data.get("name"): # Name is critical
            if not strategy_data: return None # _prompt_for_fields failed
            print_title("Strategy name is required.", error=True)
            return None

        # Custom Role selection
        role_types = ["PLAYER", "ARENA", "JUDGE", "ANNOUNCER"]
        strategy_data["role"] = await prompt_str("Role", default="PLAYER", words=role_types)
        if strategy_data["role"] not in role_types:
            print_title("Invalid role type", error=True)
            return None # Original returned False

        # Custom Prompts loop
        strategy_data["prompts"] = []
        add_more_prompts = True
        print_title("Prompts", info=True)
        while add_more_prompts:
            prompt_key = await prompt_str("Prompt Key (e.g. ARENA_GENERATE_FEATURES)")
            if not prompt_key: # Allow skipping if no key is entered
                more = await prompt_str("No prompt key entered. Add another prompt? (y/n)", default="n", words=["y", "n"])
                add_more_prompts = more and more.lower().startswith("y")
                continue

            prompt_text = await prompt_str("Prompt Text (jinja template or text)")
            if not prompt_text: # Allow skipping if no text is entered for a key
                 more = await prompt_str(f"No prompt text for '{prompt_key}'. Add another prompt? (y/n)", default="n", words=["y", "n"])
                 add_more_prompts = more and more.lower().startswith("y")
                 continue

            strategy_data["prompts"].append({"key": prompt_key, "prompt": prompt_text})
            more = await prompt_str("Add another prompt? (y/n)", default="n", words=["y", "n"])
            add_more_prompts = more and more.lower().startswith("y")

        return await self._post_and_load_item(
            client=self.participant_client,
            api_path="/api/strategy",
            data=strategy_data,
            item_type_singular="strategy"
        )

    async def cmd_strategy_load(self, args: list[str]):
        item_id_to_load = args[0] if args else None
        # Original cmd_strategy_load doesn't use clean_id or "latest",
        # and loads directly. It also doesn't use a plural form for "latest" lookup.
        # However, to make it consistent with the generic loader, we'd pass "strategies"
        # for plural, but the generic loader's clean_id might behave differently
        # than the original if "latest" was ever intended for strategies (it's not currently).
        # For now, adapting to _load_item_by_id means it *could* support "latest" if
        # self.loaded["strategies"] was populated by cmd_strategies.
        # The original also didn't print a success message on load, _load_item_by_id does.
        return await self._load_item_by_id(
            item_type_singular="strategy",
            item_type_plural="strategies", # For "latest" resolution via clean_id
            item_id=item_id_to_load,
            client=self.participant_client,
            endpoint_path_template="/api/strategy/{id}",
        )

    async def cmd_strategies(self, args: list[str]):
        return await self._list_items(
            item_type_plural="strategies",
            client=self.participant_client,
            api_path="/api/strategy",
            print_function=print_strategy_list,
        )

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
