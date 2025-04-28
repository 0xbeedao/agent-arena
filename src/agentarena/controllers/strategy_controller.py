"""
strategy controller for the strategy Arena application.
Handles HTTP requests for strategy operations.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from ulid import ULID

from agentarena.models.strategy import strategyConfig
from agentarena.services.strategy_service import StrategyService
from agentarena.config.containers import Container

import json
import structlog

# Create a router for strategy endpoints
router = APIRouter(tags=["strategy"])
log = structlog.get_logger("strategy_controller").bind(module="strategy_controller")

@router.post("/strategy", response_model=Dict[str, str])
@inject
async def create_strategy(
    strategy: strategyConfig,
    strategy_service: StrategyService = Depends(Provide[Container.strategy_service])
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
    strategy_id = await strategy_service.create_strategy(strategy)
    return {"id": strategy_id}

@router.get("/strategy/{strategy_id}", response_model=strategyConfig)
@inject
async def get_strategy(
    strategy_id: str,
    strategy_service: StrategyService = Depends(Provide[Container.strategy_service])
) -> strategyConfig:
    """
    Get an strategy by ID.
    
    Args:
        strategy_id: The ID of the strategy to get
        strategy_service: The strategy service
        
    Returns:
        The strategy configuration
        
    Raises:
        HTTPException: If the strategy is not found
    """
    strategy = await strategy_service.get_strategy(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail=f"strategy with ID {strategy_id} not found")
    return strategy

@router.get("/strategy", response_model=List[strategyConfig])
@inject
async def get_strategy_list(
    strategy_service: StrategyService = Depends(Provide[Container.strategy_service])
) -> List[strategyConfig]:
    """
    Get a list of all strategys.
    
    Args:
        strategy_service: The strategy service
        
    Returns:
        A list of strategy configurations
    """
    strategys = await strategy_service.list_strategys()
    log.debug("listing %i strategys", len(strategys))
    return strategys

@router.put("/strategy/{strategy_id}", response_model=Dict[str, bool])
@inject
async def update_strategy(
    strategy_id: str,
    strategy: strategyConfig,
    strategy_service: StrategyService = Depends(Provide[Container.strategy_service])
) -> Dict[str, bool]:
    """
    Update an strategy.
    
    Args:
        strategy_id: The ID of the strategy to update
        strategy: The new strategy configuration
        strategy_service: The strategy service
        
    Returns:
        A dictionary indicating success
        
    Raises:
        HTTPException: If the strategy is not found
    """
    success = await strategy_service.update_strategy(strategy_id, strategy)
    if not success:
        raise HTTPException(status_code=404, detail=f"strategy with ID {strategy_id} not found")
    return {"success": True}
