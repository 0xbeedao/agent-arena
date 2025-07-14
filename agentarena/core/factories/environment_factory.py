import os
from pathlib import Path

from agentarena.util.files import find_directory_of_file


def get_project_root():
    config_file = os.getenv("AGENTARENA_CONFIG_FILE", "agent-arena-config.yaml")

    hit = find_directory_of_file(config_file)
    assert hit is not None, "Where's my config file"
    return Path(hit)
