"""
RoundStatsDTO controller for the Agent Arena application.
Handles HTTP requests for roundstats operations.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, Dict, List
from ulid import ULID

from agentarena.models.stats import RoundStatsDTO
from agentarena.services.model_service import ModelService
from agentarena.config.containers import Container

import structlog

# Create a router for roundstats endpoints
router = APIRouter(tags=["RoundStatsDTO"])
log = structlog.get_logger("roundstats_controller").bind(module="roundstats_controller")

@router.post("/roundstats", response_model=Dict[str, str])
@inject
async def create_roundstats(
    roundstats: RoundStatsDTO,
    roundstats_service: ModelService[RoundStatsDTO] = Depends(Provide[Container.roundstats_service])
) -> Dict[str, str]:
    """
    Create a new roundstats.

    Args:
        roundstats: The roundstats configuration
        roundstats_service: The roundstats service

    Returns:
        A dictionary with the ID of the created roundstats
    """
    [id, response] = await roundstats_service.create(roundstats)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"id": id}

@router.get("/roundstats/{roundstats_id}", response_model=RoundStatsDTO)
@inject
async def get_roundstats(
    roundstats_id: str,
    roundstats_service: ModelService[RoundStatsDTO] = Depends(Provide[Container.roundstats_service])
) -> RoundStatsDTO:
    """
    Get a roundstats by ID.

    Args:
        roundstats_id: The ID of the roundstats to get
        roundstats_service: The roundstats service

    Returns:
        The roundstats configuration

    Raises:
        HTTPException: If the roundstats is not found
    """
    [roundstats_obj, response] = await roundstats_service.get(roundstats_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return roundstats_obj

@router.get("/roundstats", response_model=List[RoundStatsDTO])
@inject
async def get_roundstats_list(
    roundstats_service: ModelService[RoundStatsDTO] = Depends(Provide[Container.roundstats_service])
) -> List[RoundStatsDTO]:
    """
    Get a list of all roundstats.

    Args:
        roundstats_service: The roundstats service

    Returns:
        A list of roundstats configurations
    """
    return await roundstats_service.list()

@router.put("/roundstats/{roundstats_id}", response_model=Dict[str, bool])
@inject
async def update_roundstats(
    roundstats_id: str,
    roundstats: RoundStatsDTO,
    roundstats_service: ModelService[RoundStatsDTO] = Depends(Provide[Container.roundstats_service])
) -> Dict[str, bool]:
    """
    Update a roundstats.

    Args:
        roundstats_id: The ID of the roundstats to update
        roundstats: The new roundstats configuration
        roundstats_service: The roundstats service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the roundstats is not found
    """
    response = await roundstats_service.update(roundstats_id, roundstats)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}

@router.delete("/roundstats/{roundstats_id}", response_model=Dict[str, bool])
@inject
async def delete_roundstats(
    roundstats_id: str,
    roundstats_service: ModelService[RoundStatsDTO] = Depends(Provide[Container.roundstats_service])
) -> Dict[str, bool]:
    """
    Delete a roundstats.

    Args:
        roundstats_id: The ID of the roundstats to delete
        roundstats_service: The roundstats service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the roundstats is not found
    """
    response = await roundstats_service.delete(roundstats_id)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}