"""
Strategy controller for the Agent Arena application.
Handles HTTP requests for strategy operations.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from ulid import ULID

from agentarena.models.strategy import Strategy
from agentarena.services.model_service import ModelService
from agentarena.config.containers import Container

import json
import structlog

# Create a router for strategy endpoints
router = APIRouter(tags=["Strategy"])
log = structlog.get_logger("strategy_controller").bind(module="strategy_controller")

@router.post("/strategy", response_model=Dict[str, str])
@inject
async def create_strategy(
    strategy: Strategy,
    strategy_service: ModelService[Strategy] = Depends(Provide[Container.strategy_service])
) -> Dict[str, str]:
    """
    Create a new strategy.
    
    Args:
        strategy: The strategy configuration
        strategy_service: The strategy service
        
    Returns:
        A dictionary with the ID of the created strategy
    """
    log.info("Received create strategy request: %s", strategy.model_dump_json())
    strategy_id = await strategy_service.create(strategy)
    return {"id": strategy_id}

@router.get("/strategy/{strategy_id}", response_model=Strategy)
@inject
async def get_strategy(
    strategy_id: str,
    strategy_service: ModelService[Strategy] = Depends(Provide[Container.strategy_service])
) -> Strategy:
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
    strategy = await strategy_service.get(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail=f"Strategy with ID {strategy_id} not found")
    return strategy

@router.get("/strategy", response_model=List[Strategy])
@inject
async def get_strategy_list(
    strategy_service: ModelService[Strategy] = Depends(Provide[Container.strategy_service])
) -> List[Strategy]:
    """
    Get a list of all strategies.
    
    Args:
        strategy_service: The strategy service
        
    Returns:
        A list of strategy configurations
    """
    strategies = await strategy_service.list()
    log.debug("listing %i strategies", len(strategies))
    return strategies

@router.put("/strategy/{strategy_id}", response_model=Dict[str, bool])
@inject
async def update_strategy(
    strategy_id: str,
    strategy: Strategy,
    strategy_service: ModelService[Strategy] = Depends(Provide[Container.strategy_service])
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
    success = await strategy_service.update(strategy_id, strategy)
    if not success:
        raise HTTPException(status_code=404, detail=f"Strategy with ID {strategy_id} not found")
    return {"success": True}
