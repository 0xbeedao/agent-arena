"""
Arena controller for the Agent Arena application.
Handles HTTP requests for arena operations.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, Dict, List
from ulid import ULID

from agentarena.models.arena import ArenaConfig
from agentarena.services.model_service import ModelService
from agentarena.config.containers import Container

import structlog

# Create a router for arena endpoints
router = APIRouter(tags=["Arena"])
log = structlog.get_logger("arena_controller").bind(module="arena_controller")

@router.post("/arena", response_model=Dict[str, str])
@inject
async def create_arena(
    arena_config: ArenaConfig,
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service])
) -> Dict[str, str]:
    """
    Create a new arena.

    Args:
        arena_config: The arena configuration
        arena_service: The arena service

    Returns:
        A dictionary with the ID of the created arena
    """
    [id, response] = await arena_service.create(arena_config)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"id": id}

@router.get("/arena/{arena_id}", response_model=ArenaConfig)
@inject
async def get_arena(
    arena_id: str,
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service])
) -> ArenaConfig:
    """
    Get an arena by ID.

    Args:
        arena_id: The ID of the arena to get
        arena_service: The arena service

    Returns:
        The arena configuration

    Raises:
        HTTPException: If the arena is not found
    """
    [arena, response] = await arena_service.get(arena_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return arena

@router.get("/arena", response_model=List[ArenaConfig])
@inject
async def get_arena_list(
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service])
) -> List[ArenaConfig]:
    """
    Get a list of all arenas.

    Args:
        arena_service: The arena service

    Returns:
        A list of arena configurations
    """
    return await arena_service.list()

@router.put("/arena/{arena_id}", response_model=Dict[str, bool])
@inject
async def update_arena(
    arena_id: str,
    arena_config: ArenaConfig,
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service])
) -> Dict[str, bool]:
    """
    Update an arena.

    Args:
        arena_id: The ID of the arena to update
        arena_config: The new arena configuration
        arena_service: The arena service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the arena is not found
    """
    response = await arena_service.update(arena_id, arena_config)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}

@router.delete("/arena/{arena_id}", response_model=Dict[str, bool])
@inject
async def delete_arena(
    arena_id: str,
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service])
) -> Dict[str, bool]:
    """
    Delete an arena.

    Args:
        arena_id: The ID of the arena to delete
        arena_service: The arena service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the arena is not found
    """
    response = await arena_service.delete(arena_id)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}