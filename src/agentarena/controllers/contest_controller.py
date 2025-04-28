"""
Contest controller for the Agent Arena application.
Handles HTTP requests for contest operations.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, Dict, List
from ulid import ULID

from agentarena.models.contest import Contest
from agentarena.services.model_service import ModelService
from agentarena.config.containers import Container

from . import repository
import structlog

# Create a router for contest endpoints
router = APIRouter(tags=["Contest"])
log = structlog.get_logger("contest_controller").bind(module="contest_controller")

@router.post("/contest", response_model=Dict[str, str])
@inject
async def create_contest(
    contest: Contest,
    contest_service: ModelService[Contest] = Depends(Provide[Container.contest_service])
) -> Dict[str, str]:
    """
    Create a new contest.

    Args:
        contest: The contest configuration
        contest_service: The contest service

    Returns:
        A dictionary with the ID of the created contest
    """
    return await repository.create_model(contest, contest_service)

@router.get("/contest/{contest_id}", response_model=Contest)
@inject
async def get_contest(
    contest_id: str,
    contest_service: ModelService[Contest] = Depends(Provide[Container.contest_service])
) -> Contest:
    """
    Get a contest by ID.

    Args:
        contest_id: The ID of the contest to get
        contest_service: The contest service

    Returns:
        The contest configuration

    Raises:
        HTTPException: If the contest is not found
    """
    return await repository.get_model(contest_id, contest_service)

@router.get("/contest", response_model=List[Contest])
@inject
async def get_contest_list(
    contest_service: ModelService[Contest] = Depends(Provide[Container.contest_service])
) -> List[Contest]:
    """
    Get a list of all contests.

    Args:
        contest_service: The contest service

    Returns:
        A list of contest configurations
    """
    return await repository.get_model_list(contest_service)

@router.put("/contest/{contest_id}", response_model=Dict[str, bool])
@inject
async def update_contest(
    contest_id: str,
    contest: Contest,
    contest_service: ModelService[Contest] = Depends(Provide[Container.contest_service])
) -> Dict[str, bool]:
    """
    Update a contest.

    Args:
        contest_id: The ID of the contest to update
        contest: The new contest configuration
        contest_service: The contest service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the contest is not found
    """
    return await repository.update_model(contest_id, contest, contest_service)

@router.delete("/contest/{contest_id}", response_model=Dict[str, bool])
@inject
async def delete_contest(
    contest_id: str,
    contest_service: ModelService[Contest] = Depends(Provide[Container.contest_service])
) -> Dict[str, bool]:
    """
    Delete a contest.

    Args:
        contest_id: The ID of the contest to delete
        contest_service: The contest service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the contest is not found
    """
    return await repository.delete_model(contest_id, contest_service)