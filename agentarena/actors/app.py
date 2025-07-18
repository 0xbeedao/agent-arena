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
from agentarena.models.validation import ModelResponse
from agentarena.util.files import find_file_upwards

from .actor_container import ActorContainer

better_exceptions.MAX_LENGTH = None
config_file = os.getenv("AGENTARENA_CONFIG_FILE", "agent-arena-config.yaml")
print(f"Using config file: {config_file}")
yamlFile = find_file_upwards(config_file)
if yamlFile is None:
    raise ValueError(f"Config file {config_file} not found")

# Initialize the container
container = ActorContainer()
container.config.from_yaml(yamlFile)
# Create the FastAPI application
app = FastAPI(
    title="Agent Arena (Actors) API",
    description="API for the Actors portion of the app",
    version="0.1.0",
)


async def startup_event():
    """Initialize resources on application startup."""
    container.init_resources()
    container.wire(
        modules=[
            sys.modules[__name__],  # wire current module
        ]
    )

    logger = container.logging()
    log = logger.get_logger("actors")
    db = container.db_service()
    db.create_db()
    broker = await container.message_broker()  # type: ignore
    agent_controller = await container.agent_controller()  # type: ignore
    await agent_controller.subscribe_yourself(broker)

    # Setup routers after all dependencies are initialized
    await setup_routers()

    log.info("Application startup complete, resources initialized and container wired.")


async def shutdown_event():
    """Shutdown resources on application stop."""
    controller = await container.agent_controller()  # type: ignore
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

# Module-level variable to store routers after initialization
routers = None


async def setup_routers():
    """Setup and include all routers."""
    global routers
    routers = [
        await container.agent_controller(),  # type: ignore
        await container.strategy_controller(),  # type: ignore
        await container.generatejob_controller(),  # type: ignore
        await container.llmmodel_controller(),  # type: ignore
        # (await container.debug_controller())
    ]
    for router in routers:
        app.include_router(router.get_router())


# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    detail = exc.detail
    if isinstance(detail, dict):
        # Already a structured error response
        return JSONResponse(
            status_code=exc.status_code,
            content=detail,
        )
    elif hasattr(detail, "model_dump"):
        detail = detail.model_dump()

    return JSONResponse(
        status_code=exc.status_code,
        content={"message": detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    # Log the full exception for debugging
    import traceback
    import sys

    logger = container.logging()
    log = logger.get_logger("actors")
    log.error(
        "Unhandled exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        traceback=traceback.format_exc(),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": "Please check the server logs for more information",
        },
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
    log = container.logging().get_logger("actors")
    log.info(f"path: {container.projectroot()}")
    log.info("Starting app with uvicorn")

    uvicorn.run("agentarena.actors.app:app", host="0.0.0.0", port=8001, reload=True)
