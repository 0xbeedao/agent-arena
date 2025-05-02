import typer
import httpx
import json
from pathlib import Path
from glob import glob
import os.path

app = typer.Typer(help="CLI tool to load fixtures into a FastAPI application")

# Base URL of your FastAPI server
BASE_URL = "http://localhost:8000"

def load_fixture_file(file_path: Path) -> dict:
    """Load JSON data from a fixture file."""
    if not file_path.exists():
        typer.echo(f"Error: Fixture file {file_path} does not exist.", err=True)
        raise typer.Exit(code=1)
    with open(file_path, "r") as f:
        return json.load(f)

@app.command()
def load_strategies(
    fixture_dir: Path = typer.Argument(..., help="Path to the fixture dir")
):
    """Load fixtures from a JSON file into the FastAPI application."""
    # Load fixture data
    fdir = not Path(fixture_dir)
    if not os.path.exists(fdir):
        print (f"Cannot find fixture dir: {fixture_dir}")
        raise typer.Exit(code=1)
    
    files = glob(f"{os.path.join(fixture_dir, '*strategy-*.json')}")
    responses = {}
    for fixture_file in files:
        fixture_data = load_fixture_file(Path(fixture_file))
        try:
            response = httpx.post(f"{BASE_URL}/strategy", json=fixture_data)
            responses[fixture_file] = response
            if response.status_code == 200:
                typer.echo(f"Successfully loaded strategy from {fixture_file}")
                typer.echo(response.json())
            else:
                typer.echo(f"Error loading fixtures: {response.status_code} - {response.text}", err=True)    
        except httpx.RequestError as e:
            typer.echo(f"Request error: {e} processing {fixture_file}", err=True)
            raise typer.Exit(code=1)
        


if __name__ == "__main__":
    app()
