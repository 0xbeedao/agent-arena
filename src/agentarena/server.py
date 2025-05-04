"""
FastAPI server for the Agent Arena application.
"""

import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentarena.containers import Container
from agentarena.controllers import routers

# Initialize the container
container = Container()
parentDir = Path(__file__).parent.parent.parent
yamlFile = os.path.join(parentDir, "agent-arena-config.yaml")
if os.path.exists(yamlFile):
    container.config.from_yaml(yamlFile)
# Always initialize resources and wire the container
container.init_resources()

to_wire = [
    "agentarena.controllers.%s_controller" % module
    for module in [
        "agent",
        "arena",
        "contest",
        "feature",
        "responder",
        "roundstats",
        "strategy",
    ]
]

container.wire(modules=to_wire)

# Create the FastAPI application
app = FastAPI(
    title="Agent Arena API",
    description="API for the Agent Arena application",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
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
    log = container.logging.make_logger("server", module="server")
    log.info("path: %s", container.projectroot())
    log.info("Starting app")
    dbService = container.db_service().add_audit_log("startup")

    uvicorn.run("agentarena.server:app", host="0.0.0.0", port=8000, reload=True)
