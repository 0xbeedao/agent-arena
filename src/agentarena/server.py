"""
FastAPI server for the Agent Arena application.
"""

import os
import sys
from pathlib import Path

import better_exceptions
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentarena.core.arena_container import ArenaContainer
from agentarena.core.middleware import add_logging_middleware

better_exceptions.MAX_LENGTH = None

# Initialize the container
container = ArenaContainer()
parentDir = Path(__file__).parent.parent.parent
yamlFile = os.path.join(parentDir, "agent-arena-config.yaml")
if os.path.exists(yamlFile):
    container.config.from_yaml(yamlFile)
# Create the FastAPI application
app = FastAPI(
    title="Agent Arena API",
    description="API for the Agent Arena application",
    version="0.1.0",
)


async def startup_event():
    """Initialize resources on application startup."""
    container.init_resources()
    # Wire the container after resources are initialized
    # Note: wiring might be better suited after specific resource initialization if dependencies exist
    # For now, global wiring after all init should be fine.
    container.wire(
        modules=[
            sys.modules[__name__],  # wire current module
            "agentarena.controllers.arena_controller",
            "agentarena.controllers.contest_controller",
            "agentarena.controllers.debug_controller",
            "agentarena.controllers.model_controller",
            "agentarena.controllers.responder_controller",
        ]
    )
    # Add initial audit log after resources (like db_service) are ready
    # db_service = container.db_service()
    # await db_service.add_audit_log("startup_complete")
    logger = container.logging()
    log = logger.get_logger("server", module="server")
    log.info("Application startup complete, resources initialized and container wired.")


async def shutdown_event():
    """Shutdown resources on application stop."""
    container.shutdown_resources()


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

# Include routers
routers = [
    container.contest_controller().get_router(),
    container.agent_controller().get_router(),
    container.arena_controller().get_router(),
    container.strategy_controller().get_router(),
    container.responder_controller().get_router(),
    container.debug_controller().get_router(),
]
[app.include_router(router) for router in routers]


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
    log = container.logging().get_logger("server", module="server")
    log.info(f"path: {container.projectroot()}")
    log.info("Starting app with uvicorn")
    # db_service call moved to startup_event to ensure resources are initialized

    uvicorn.run("agentarena.server:app", host="0.0.0.0", port=8000, reload=True)
