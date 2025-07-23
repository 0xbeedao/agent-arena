"""
FastAPI server for the Agent Arena application.
"""

import os
import sys
from datetime import datetime

import better_exceptions
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import select

from agentarena.arena.arena_container import ArenaContainer
from agentarena.core.middleware import add_logging_middleware
from agentarena.models.job import JobLock
from agentarena.util.files import find_file_upwards

better_exceptions.MAX_LENGTH = None

config_file = os.getenv("AGENTARENA_CONFIG_FILE", "agent-arena-config.yaml")
print(f"Using config file: {config_file}")
yamlFile = find_file_upwards(config_file)
if yamlFile is None:
    raise ValueError(f"Config file {config_file} not found")

# Initialize the container
container = ArenaContainer()
container.config.from_yaml(yamlFile)

# Create the FastAPI application
app = FastAPI(
    title="Agent Arena (Arena) API",
    description="API for the Arena portion of the app",
    version="0.1.0",
)


async def startup_event():
    """Initialize resources on application startup."""
    # container.wire(
    #     modules=[
    #         # sys.modules[__name__],  # wire current module
    #     ]
    # )
    container.init_resources()
    logger = container.logging()
    log = logger.get_logger("arena")
    db = container.db_service()
    db.create_db()
    await delete_expired_joblocks()
    broker = await container.message_broker()  # type: ignore
    for svc in [
        await container.contest_controller(),  # type: ignore
    ]:
        await svc.subscribe_yourself(broker)

    await setup_routers()
    log.info("Application startup complete, resources initialized and container wired.")


async def shutdown_event():
    """Shutdown resources on application stop."""
    for svc in [
        await container.contest_controller(),  # type: ignore
    ]:
        await svc.unsubscribe_yourself()  # type: ignore
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
        await container.contest_controller(),  # type: ignore
        await container.arena_controller(),  # type: ignore
        await container.participant_controller(),  # type: ignore
        container.debug_controller(),
    ]
    [app.include_router(router.get_router()) for router in routers]


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

    logger = container.logging()
    log = logger.get_logger("arena")
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


def get_current_unix_time() -> int:
    """Get the current time as a unix timestamp (seconds)."""
    return int(datetime.now().timestamp())


async def delete_expired_joblocks():
    """Delete all JobLock objects whose TTL has expired."""
    db_service = container.db_service()
    now = get_current_unix_time()
    with db_service.get_session() as session:
        # Fetch all JobLocks
        all_locks = session.exec(select(JobLock)).all()
        # Filter for valid created_at and expired
        expired_locks = [
            lock
            for lock in all_locks
            if (
                lock.created_at is not None
                and isinstance(lock.created_at, int)
                and lock.created_at > 0
                and lock.ttl is not None
                and isinstance(lock.ttl, int)
                and (lock.created_at + lock.ttl) < now
            )
        ]
        for lock in expired_locks:
            session.delete(lock)
        if expired_locks:
            session.commit()


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

    uvicorn.run("agentarena.arena.app:app", host="0.0.0.0", port=8000, reload=True)
