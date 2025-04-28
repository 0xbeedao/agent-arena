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

from . import repository
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
    return await repository.create_model(arena_config, arena_service)

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
    return await repository.get_model(arena_id, arena_service)

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
    return await repository.get_model_list(arena_service)

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
    return await repository.update_model(arena_id, arena_config, arena_service)

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
    return await repository.delete_model(arena_id, arena_service)