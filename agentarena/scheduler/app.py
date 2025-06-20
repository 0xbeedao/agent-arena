"""
FastAPI server for the Agent Arena application.
"""

import os
import sys

import better_exceptions
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentarena.core.middleware import add_logging_middleware
from agentarena.scheduler.scheduler_container import SchedulerContainer
from agentarena.util.files import find_directory_of_file

better_exceptions.MAX_LENGTH = None

# Initialize the container
container = SchedulerContainer()
project_root = find_directory_of_file("agent-arena-config.yaml")
assert project_root is not None, "Can't find config"

yamlFile = os.path.join(project_root, "agent-arena-config.yaml")
container.config.from_yaml(yamlFile)
# Create the FastAPI application
app = FastAPI(
    title="Agent Arena (Scheduler) API",
    description="API for the Scheduler portion of the app",
    version="0.1.0",
)


async def startup_event():
    """Initialize resources on application startup."""
    container.init_resources()
    container.wire(
        modules=[
            sys.modules[__name__],  # wire current module
            "agentarena.scheduler.controllers.debug_controller",
            "agentarena.core.controllers.model_controller",
        ]
    )

    logger = container.logging()
    log = logger.get_logger("scheduler")
    db = container.db_service()
    db.create_db()
    with db.get_session() as session:
        db.add_audit_log("startup", session)
    broker = await container.message_broker()  # type: ignore
    for svc in [
        await container.debug_controller(),  # type: ignore
        await container.queue_service(),  # type: ignore
    ]:
        await svc.subscribe_yourself(broker)
    await setup_routers()
    log.info("Application startup complete, resources initialized and container wired.")


async def shutdown_event():
    """Shutdown resources on application stop."""
    controller = await container.debug_controller()  # type: ignore
    await controller.unsubscribe_yourself()
    await container.shutdown_resources()  # type: ignore


app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_logging_middleware(app)


async def setup_routers():
    routers = [
        await container.job_controller(),  # type: ignore
        await container.debug_controller(),  # type: ignore
    ]
    [app.include_router(router.get_router()) for router in routers]


# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal server error: {str(exc)}"},
    )


# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Run the server if this file is executed directly
if __name__ == "__main__":
    # Check if config file exists
    if not os.path.exists(yamlFile):
        print(f"Cannot find the config file: {yamlFile}")
        sys.exit(1)
    log = container.logging().get_logger("scheduler")
    log.info(f"path: {container.projectroot()}")
    log.info("Starting app with uvicorn")

    uvicorn.run("agentarena.scheduler.app:app", host="0.0.0.0", port=8002, reload=True)
