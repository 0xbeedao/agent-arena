import json
import os
import os.path
import secrets
import sys
from glob import glob
from pathlib import Path
from typing import Any, Dict, List

import httpx
import typer

from agentarena.util.files import find_directory_of_file

# Determine the project root directory
project_root = find_directory_of_file("agent-arena-config.yaml")
os.chdir(str(project_root))
sys.path.append(".")
app = typer.Typer(help="CLI tool to load fixtures into a FastAPI application")

# Base URL of your FastAPI server
ARENA_URL = "http://localhost:8000/api"
ACTOR_URL = "http://localhost:8001/api"


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
        response = httpx.post(f"{ARENA_URL}/arena/", json=fixture_data)
        if response.status_code == 200:
            obj = json.loads(response.content)
            obj_id = obj["id"]
            typer.echo(
                f"Successfully created arena from {fixture_file}:  {obj['name']} {obj_id}"
            )
            return obj
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
        response = httpx.post(f"{ARENA_URL}/participant/", json=fixture_data)
        if response.status_code == 200:
            obj = json.loads(response.content)
            typer.echo(
                f"Successfully created participant from {fixture_file}: {obj['name']} {obj['id']}"
            )
            return obj
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
        response = httpx.post(f"{ACTOR_URL}/strategy/", json=fixture_data)
        if response.status_code == 200:
            obj = json.loads(response.content)
            typer.echo(
                f"Successfully created strategy from {fixture_file}: {obj['name']}"
            )
            return obj
        else:
            typer.echo(
                f"Error loading fixtures: {response.status_code} - {response}",
                err=True,
            )
            return None
    except httpx.RequestError as e:
        typer.echo(f"Request error: {e} processing {fixture_file}", err=True)
        return None


def make_agent(participant, strategy):
    agent_data = {
        "strategy_id": strategy["id"],
        "name": participant["name"],
    }

    json_data = json.dumps(agent_data)

    try:
        response = httpx.post(f"{ACTOR_URL}/agent/", json=agent_data)
        if response.status_code == 200:
            obj = json.loads(response.content)
            typer.echo(f"Successfully created agent: {obj['id']}")
            return obj
        else:
            print("error with json:\n", json_data)
            typer.echo(
                f"Error loading fixtures: {response.status_code} - {response.text}",
                err=True,
            )
    except httpx.RequestError as e:
        typer.echo(f"Request error making agent: {e}", err=True)
        return None


def load_contest_fixture(
    fname: str, arena_id: str, players=2, parts: Dict[str, List[Any]] = {}
):
    fixture_data = load_fixture_file(Path(fname))
    contest_players = []
    playerCt = len(parts["player"])
    if playerCt == 0:
        typer.echo("Need at least one player")
        sys.exit(1)
    else:
        while len(contest_players) < players:
            possible = secrets.choice(parts["player"])
            if possible not in contest_players:
                contest_players.append(possible)

    arena = secrets.choice(parts["arena"])
    judge = secrets.choice(parts["judge"])
    announcer = secrets.choice(parts["announcer"])

    fixture = os.path.basename(fname)
    typer.echo(f"Loading fixture: {fixture}")
    typer.echo(f"  Arena: {arena['name']}")
    typer.echo(f"  Judge: {judge['name']}")
    typer.echo(f"  Announcer: {announcer['name']}")
    for i in range(len(contest_players)):
        typer.echo(f"  player {i}: {contest_players[i]['name']}")

    participants = [
        judge["id"],
        arena["id"],
        announcer["id"],
        *[player["id"] for player in contest_players],
    ]

    contest_req = {
        "player_positions": fixture_data["player_positions"],
        "arena_id": arena_id,
        "participant_ids": participants,
    }

    fixture_json = json.dumps(contest_req)

    try:
        response = httpx.post(f"{ARENA_URL}/contest/", json=contest_req)
        if response.status_code == 200:
            obj = json.loads(response.content)
            typer.echo(f"Successfully created contest from {fname}: '{obj['id']}'")
            return obj
        else:
            print("error with json:\n", fixture_json)
            typer.echo(
                f"Error loading fixtures: {response.status_code}\n{response.text}\n{response.content}",
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
    participants: Dict[str, List[Any]] = {
        "judge": [],
        "arena": [],
        "player": [],
        "announcer": [],
    }
    for fixture_file in files:
        participant = load_participant_fixture(Path(fixture_file))
        if participant is None:
            typer.echo("Error")
            raise typer.Exit(code=1)
        participants[str(participant["role"])].append(participant)
    typer.echo(f"Loaded {len(participants)} participants")

    files = glob(os.path.join(fixture_dir, "arena-*.json"))
    arenas = []
    for fixture_file in files:
        arena = load_arena_fixture(fixture_file)
        if arena is None:
            typer.echo("Error")
            raise typer.Exit(code=1)
        arenas.append(arena)
    typer.echo(f"Loaded {len(arenas)} arenas")

    files = glob(os.path.join(fixture_dir, "*strategy-*.json"))
    strategies = {
        "judge": [],
        "arena": [],
        "player": [],
        "announcer": [],
    }
    for fixture_file in files:
        strategy = load_strategy_fixture(Path(fixture_file))
        if strategy is None:
            typer.echo(f"Error, could not load strategy from {fixture_file}", err=True)
            raise typer.Exit(code=1)
        strategies[str(strategy["role"])].append(strategy)

    # make agents for each strategy
    agents: Dict[str, List] = {"judge": [], "arena": [], "player": [], "announcer": []}
    for role in participants.keys():
        if role not in strategies or len(strategies[role]) == 0:
            typer.echo(f"No strategies for role {role}, skipping agent creation")
            continue

        strats = strategies[role]

        for participant in participants[role]:
            agent = make_agent(participant, secrets.choice(strats))
            if not agent:
                typer.echo(f"Error creating agent for {participant}")
                raise typer.Exit(code=1)
            agents[role].append(agent)

        typer.echo(f"{len(agents[role])} {role} Agents created")

    contest_files = glob(os.path.join(fixture_dir, "contest-*.json"))
    contests = []
    for contest_fixture in contest_files:
        for arena in arenas:
            contest = load_contest_fixture(
                contest_fixture, arena["id"], parts=participants
            )
            if contest is None:
                typer.echo(f"Error loading contest from {contest_fixture}", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"Created contest: {contest['id']} in arena {arena['name']}")
            contests.append(contest)

    typer.echo(f"Loaded {len(contests)} contests")


if __name__ == "__main__":
    app()
