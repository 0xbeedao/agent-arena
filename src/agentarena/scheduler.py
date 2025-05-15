import os
from pathlib import Path

from agentarena.core.scheduler_container import SchedulerContainer

parentDir = Path(__file__).parent.parent.parent
yamlFile = os.path.join(parentDir, "agent-arena-config.yaml")


def make_scheduler():
    container = SchedulerContainer()
    if os.path.exists(yamlFile):
        container.config.from_yaml(yamlFile)
    return container.scheduler_service()


scheduler = make_scheduler()
