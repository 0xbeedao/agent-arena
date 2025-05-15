import os
from pathlib import Path
from fastapi import FastAPI

from agentarena.core.scheduler_container import SchedulerContainer


parentDir = Path(__file__).parent.parent.parent
yamlFile = os.path.join(parentDir, "agent-arena-config.yaml")


def make_scheduler():
    container = SchedulerContainer()
    if os.path.exists(yamlFile):
        container.config.from_yaml(yamlFile)
    return container.scheduler_service()


def get_router():
    """Get the API router for scheduler-related endpoints"""
    container = SchedulerContainer()
    if os.path.exists(yamlFile):
        container.config.from_yaml(yamlFile)

    # Add job router
    job_router = container.job_controller().get_router()

    app = FastAPI()
    app.include_router(job_router)

    return app


scheduler = make_scheduler()
