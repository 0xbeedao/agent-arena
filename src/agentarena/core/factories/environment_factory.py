from pathlib import Path

from agentarena.util.files import find_directory_of_file


def get_project_root():
    hit = find_directory_of_file("agent-arena-config.yaml")
    assert hit is not None, "Where's my config file"
    return Path(hit)
