import typer
import httpx
import json
from pathlib import Path
from glob import glob
import os.path
import secrets

app = typer.Typer(help="CLI tool to load fixtures into a FastAPI application")

# Base URL of your FastAPI server
BASE_URL = "http://localhost:8000"

def load_fixture_file(file_path: Path) -> dict:
    """Load JSON data from a fixture file."""
    if not file_path.exists():
        typer.echo(f"Error: Fixture file {file_path} does not exist.", err=True)
        return None
    with open(file_path, "r") as f:
        return json.load(f)

# TODO: have it create tha agents at the same time - with each strategy

def load_strategy_fixture(fixture_file: Path):
    fixture_data = load_fixture_file(Path(fixture_file))
    try:
        response = httpx.post(f"{BASE_URL}/strategy", json=fixture_data)
        if response.status_code == 200:
            obj_id = json.loads(response.content)['id']
            typer.echo(f"Successfully created strategy from {fixture_file}: #{obj_id}")
            return obj_id, fixture_data['role']
        else:
            typer.echo(f"Error loading fixtures: {response.status_code} - {response.text}", err=True)   
            return None, None
    except httpx.RequestError as e:
        typer.echo(f"Request error: {e} processing {fixture_file}", err=True)
        return None, None

def make_agent(strategy_id: str, fname: str):
    fixture = os.path.basename(fname)
    name, _ = os.path.splitext(fixture)
    name = name.replace('strategy', 'agent')
    metadata = {
        "fixture": fixture
    }
    agent_data = {
        "name": name,
        "description": f"A test agent using {name}",
        "endpoint": "/agent/<id>",
        "api_key": "",
        "metadata": json.dumps(metadata),
        "strategy_id": strategy_id
    }

    json_data = json.dumps(agent_data)

    try:
        response = httpx.post(f"{BASE_URL}/agent", json=agent_data)
        if response.status_code == 200:
            obj_id = json.loads(response.content)['id']
            typer.echo(f"Successfully created agent from strategy {fname}: #{obj_id}")
            return obj_id, name
        else:
            print ("error with json:\n", json_data)
            typer.echo(f"Error loading fixtures: {response.status_code} - {response.text}", err=True)   
    except httpx.RequestError as e:
        typer.echo(f"Request error: {e} processing {fname}", err=True)
        return None, None

@app.command()
def load_fixtures(
    fixture_dir: Path = typer.Argument(..., help="Path to the fixture dir")
):
    """Load fixtures from a JSON file into the FastAPI application."""
    # Load fixture data
    fdir = not Path(fixture_dir)
    if not os.path.exists(fdir):
        typer.echo(f"Cannot find fixture dir: {fixture_dir}")
        raise typer.Exit(code=1)
    
    files = glob(f"{os.path.join(fixture_dir, '*strategy-*.json')}")
    ix = 0
    strategies = {
        "judge": [],
        "arena": [],
        "player": [],
        "announcer": [],
    }
    agents = {
        "judge": [],
        "arena": [],
        "player": [],
        "announcer": []
    }
    for fixture_file in files:
        ix += 1
        strategy_id, role = load_strategy_fixture(Path(fixture_file))
        if strategy_id is None:
            typer.echo("Error")
            raise typer.Exit(code=1)
        strategies[role].append(strategy_id)
        
        agent_id, name = make_agent(strategy_id, fixture_file)
        if agent_id is None:
            typer.echo("Error")
            raise typer.Exit(code=1)
        agents[role].append((agent_id, name))
        
    # now that we've got some agents, let's use them
    # first lets just print what we've got
    typer.echo("Agents created:")
    
    for role, agent_list in agents.items():
        typer.echo(f"Role: {role}")
        for agent_id, name in agent_list:
            typer.echo(f"  Agent ID: {agent_id}, Name: {name}")
        
    players = []
    playerCt = len(agents['player'])
    if playerCt == 0:
        typer.echo("Need at least one player")
    elif playerCt == 1:
        players.append(agents['player'][0])
    else:
        while len(players) < 2:
            possible = secrets.choice(agents['player'])
            if possible not in players:
                players.append(possible)
        
    arena = secrets.choice(agents['arena'])
    judge = secrets.choice(agents['judge'])
    announcer = secrets.choice(agents['announcer'])

    typer.echo(f"Arena: {arena[1]}")
    typer.echo(f"Judge: {judge[1]}")
    typer.echo(f"Announcer: {announcer[1]}")
    typer.echo(f"player1: {players[0][1]}")
    typer.echo(f"player2: {players[1][1]}")


if __name__ == "__main__":
    app()
