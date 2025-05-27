import json
import os
import os.path
import secrets
import sys
from glob import glob
from pathlib import Path

import httpx
import typer

from agentarena.util.files import find_directory_of_file

# Determine the project root directory
project_root = find_directory_of_file("agent-arena-config.yaml")
os.chdir(str(project_root))
sys.path.append(".")
app = typer.Typer(help="CLI tool to load fixtures into a FastAPI application")

# Base URL of your FastAPI server
BASE_URL = "http://localhost:8000/api"


def load_fixture_file(file_path: Path) -> dict:
    """Load JSON data from a fixture file."""
    if not file_path.exists():
        typer.echo(f"Error: Fixture file {file_path} does not exist.", err=True)
        return {}
    with open(file_path, "r") as f:
        return json.load(f)


def load_arena_fixture(fixture_file: str):
    fixture_data = load_fixture_file(Path(fixture_file))
    try:
        response = httpx.post(f"{BASE_URL}/arena/", json=fixture_data)
        if response.status_code == 200:
            obj_id = json.loads(response.content)["id"]
            typer.echo(f"Successfully created arena from {fixture_file}: {obj_id}")
            return obj_id
        else:
            typer.echo(
                f"Error loading fixtures: {response.status_code} - {response}",
                err=True,
            )
            return None
    except httpx.RequestError as e:
        typer.echo(f"Request error: {e} processing {fixture_file}", err=True)
        return None


def load_participant_fixture(fixture_file: Path):
    fixture_data = load_fixture_file(Path(fixture_file))
    try:
        response = httpx.post(f"{BASE_URL}/participant/", json=fixture_data)
        if response.status_code == 200:
            obj_id = json.loads(response.content)["id"]
            typer.echo(
                f"Successfully created participant from {fixture_file}: {obj_id}"
            )
            return obj_id
        else:
            typer.echo(
                f"Error loading fixtures: {response.status_code} - {response}",
                err=True,
            )
            return None
    except httpx.RequestError as e:
        typer.echo(f"Request error: {e} processing {fixture_file}", err=True)
        return None


def load_strategy_fixture(fixture_file: Path):
    fixture_data = load_fixture_file(Path(fixture_file))
    try:
        response = httpx.post(f"{BASE_URL}/strategy/", json=fixture_data)
        if response.status_code == 200:
            obj_id = json.loads(response.content)["id"]
            typer.echo(f"Successfully created strategy from {fixture_file}: {obj_id}")
            return obj_id, fixture_data["role"]
        else:
            typer.echo(
                f"Error loading fixtures: {response.status_code} - {response}",
                err=True,
            )
            return None, None
    except httpx.RequestError as e:
        typer.echo(f"Request error: {e} processing {fixture_file}", err=True)
        return None, None


def make_agent(strategy_id: str, fname: str):
    fixture = os.path.basename(fname)
    name, _ = os.path.splitext(fixture)
    name = name.replace("strategy", "agent")
    metadata = {"fixture": fixture}

    # TODO - make actor with strategy instead

    agent_data = {
        "name": name,
        "description": f"A test agent using {name}",
        "endpoint": "/api/responders/$AGENT$",
        "api_key": "",
        "extra": metadata,
        "strategy_id": strategy_id,
    }

    json_data = json.dumps(agent_data)

    try:
        response = httpx.post(f"{BASE_URL}/agent/", json=agent_data)
        if response.status_code == 200:
            obj_id = json.loads(response.content)["id"]
            typer.echo(f"Successfully created agent from strategy {fname}: {obj_id}")
            return obj_id, name
        else:
            print("error with json:\n", json_data)
            typer.echo(
                f"Error loading fixtures: {response.status_code} - {response.text}",
                err=True,
            )
    except httpx.RequestError as e:
        typer.echo(f"Request error: {e} processing {fname}", err=True)
        return None, None


def load_contest_fixture(fname: str, arena_id: str, players=2, parts={}):
    fixture_data = load_fixture_file(Path(fname))
    players = []
    playerCt = len(parts["player"])
    if playerCt == 0:
        typer.echo("Need at least one player")
        sys.exit(1)
    elif playerCt == 1:
        players.append(parts["player"][0])
    else:
        while len(players) < 2:
            possible = secrets.choice(parts["player"])
            if possible not in players:
                players.append(possible)

    arena = secrets.choice(parts["arena"])
    judge = secrets.choice(parts["judge"])
    announcer = secrets.choice(parts["announcer"])

    fixture = os.path.basename(fname)
    typer.echo(f"Loading fixture: {fixture}")
    typer.echo(f"  Arena: {arena[1]}")
    typer.echo(f"  Judge: {judge[1]}")
    typer.echo(f"  Announcer: {announcer[1]}")
    for i in range(len(players)):
        typer.echo(f"  player{i}: {players[i][1]}")

    fixture_data["participants"] = [
        {"role": "judge", "agent_id": judge[0]},
        {"role": "announcer", "agent_id": announcer[0]},
        {"role": "arena", "agent_id": arena[0]},
    ]
    fixture_data["parts"].extend(
        [{"role": "player", "agent_id": player[0]} for player in players]
    )

    # copied above
    fixture_data = load_fixture_file(Path(fname))
    contest_req = {
        "player_positions": fixture_data["player_positions"],
        "arena_config_id": arena_id,
        "current_round": 1,
    }

    fixture_json = json.dumps(contest_req)

    try:
        response = httpx.post(f"{BASE_URL}/contest/", json=contest_req)
        if response.status_code == 200:
            obj_id = json.loads(response.content)["id"]
            typer.echo(f"Successfully created contest from {fname}: {obj_id}")
            return obj_id
        else:
            print("error with json:\n", fixture_json)
            typer.echo(
                f"Error loading fixtures: {response.status_code} - {response.text}",
                err=True,
            )
    except httpx.RequestError as e:
        typer.echo(f"Request error: {e} processing {fname}", err=True)
        return None


@app.command()
def load_fixtures(
    fixture_dir: Path = typer.Argument(..., help="Path to the fixture dir")
):
    """Load fixtures from a JSON file into the FastAPI application."""
    # Load fixture data
    norm_dir = os.path.abspath(fixture_dir)
    fdir = Path(norm_dir)
    typer.echo(f"Checking {norm_dir}")
    if not os.path.exists(fdir):
        typer.echo(f"Cannot find fixture dir: {norm_dir}")
        raise typer.Exit(code=1)

    files = glob(os.path.join(fixture_dir, "participant-*.json"))
    participants = []
    for fixture_file in files:
        participant = load_participant_fixture(Path(fixture_file))
        if participant is None:
            typer.echo("Error")
            raise typer.Exit(code=1)
        participants.append(participant)
    typer.echo(f"Loaded {len(participants)} participants")

    files = glob(os.path.join(fixture_dir, "arena-*.json"))
    arenas = []
    for fixture_file in files:
        arena = load_arena_fixture(fixture_file)
        if arena is None:
            typer.echo("Error")
            raise typer.Exit(code=1)
        participants.append(arena)
    typer.echo(f"Loaded {len(arenas)} arenas")

    # files = glob(os.path.join(fixture_dir, "*strategy-*.json"))
    # strategies = {
    #     "judge": [],
    #     "arena": [],
    #     "player": [],
    #     "announcer": [],
    # }
    # agents = {"judge": [], "arena": [], "player": [], "announcer": []}
    # for fixture_file in files:
    #     strategy_id, role = load_strategy_fixture(Path(fixture_file))
    #     if strategy_id is None:
    #         typer.echo("Error")
    #         raise typer.Exit(code=1)
    #     strategies[role].append(strategy_id)

    #     agent_id, name = make_agent(strategy_id, fixture_file)
    #     if agent_id is None:
    #         typer.echo("Error")
    #         raise typer.Exit(code=1)
    #     agents[role].append((agent_id, name))

    # # now that we've got some agents, let's use them
    # # first lets just print what we've got
    # typer.echo("Agents created")

    # arena_files = glob(os.path.join(fixture_dir, "arena-*.json"))
    # arenas = []
    # for arena_fixture in arena_files:
    #     arena_id = load_arena_fixture(Path(arena_fixture), players=2, agents=agents)
    #     typer.echo(f"created arena: {arena_id}")
    #     arenas.append(arena_id)

    # contest_files = glob(os.path.join(fixture_dir, "contest-*.json"))
    # contests = []
    # for contest_fixture in contest_files:
    #     for arena_id in arenas:
    #         contest_id = load_contest_fixture(Path(contest_fixture), arena_id)
    #         typer.echo(f"Created contest: {contest_id}")

    #         contest = httpx.get((f"{BASE_URL}/contest/{contest_id}"))
    #         c = json.loads(contest.content)
    #         print(json.dumps(c, indent=4, sort_keys=True))


if __name__ == "__main__":
    app()
