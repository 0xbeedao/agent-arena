"""
StrategyDTO controller for the Agent Arena application.
Handles HTTP requests for strategy operations.
"""

from typing import Dict
from typing import List

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from agentarena.containers import Container
from agentarena.models.strategy import StrategyDTO
from agentarena.services.model_service import ModelService

# Create a router for strategy endpoints
router = APIRouter(tags=["StrategyDTO"])


@router.post("/strategy", response_model=Dict[str, str])
@inject
async def create_strategy(
    strategy: StrategyDTO,
    strategy_service: ModelService[StrategyDTO] = Depends(
        Provide[Container.strategy_service]
    ),
) -> Dict[str, str]:
    """
    Create a new strategy.

    Args:
        strategy: The strategy configuration
        strategy_service: The strategy service

    Returns:
        A dictionary with the ID of the created strategy
    """
    [id, response] = await strategy_service.create(strategy)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"id": id}


@router.get("/strategy/{strategy_id}", response_model=StrategyDTO)
@inject
async def get_strategy(
    strategy_id: str,
    strategy_service: ModelService[StrategyDTO] = Depends(
        Provide[Container.strategy_service]
    ),
) -> StrategyDTO:
    """
    Get a strategy by ID.

    Args:
        strategy_id: The ID of the strategy to get
        strategy_service: The strategy service

    Returns:
        The strategy configuration

    Raises:
        HTTPException: If the strategy is not found
    """
    [strategy_obj, response] = await strategy_service.get(strategy_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return strategy_obj


@router.get("/strategy", response_model=List[StrategyDTO])
@inject
async def get_strategy_list(
    strategy_service: ModelService[StrategyDTO] = Depends(
        Provide[Container.strategy_service]
    ),
) -> List[StrategyDTO]:
    """
    Get a list of all strategies.

    Args:
        strategy_service: The strategy service

    Returns:
        A list of strategy configurations
    """
    return await strategy_service.list()


@router.put("/strategy/{strategy_id}", response_model=Dict[str, bool])
@inject
async def update_strategy(
    strategy_id: str,
    strategy: StrategyDTO,
    strategy_service: ModelService[StrategyDTO] = Depends(
        Provide[Container.strategy_service]
    ),
) -> Dict[str, bool]:
    """
    Update a strategy.

    Args:
        strategy_id: The ID of the strategy to update
        strategy: The new strategy configuration
        strategy_service: The strategy service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the strategy is not found
    """
    response = await strategy_service.update(strategy_id, strategy)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}


@router.delete("/strategy/{strategy_id}", response_model=Dict[str, bool])
@inject
async def delete_strategy(
    strategy_id: str,
    strategy_service: ModelService[StrategyDTO] = Depends(
        Provide[Container.strategy_service]
    ),
) -> Dict[str, bool]:
    """
    Delete a strategy.

    Args:
        strategy_id: The ID of the strategy to delete
        strategy_service: The strategy service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the strategy is not found
    """
    response = await strategy_service.delete(strategy_id)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}
