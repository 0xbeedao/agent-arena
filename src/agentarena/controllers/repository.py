"""
Generic model controller for the Agent Arena application.
Provides a reusable controller for CRUD operations on any model that inherits from DbBase.
"""

import sqlite3
from fastapi import HTTPException
from typing import Dict, List, TypeVar

from agentarena.models.dbmodel import DbBase
from agentarena.services.model_service import ModelService

import structlog

T = TypeVar('T', bound=DbBase)

log = structlog.getLogger("model_controller")

async def create_model(
    model: T,
    model_service: ModelService[T]
) -> Dict[str, str]:
    """
    Create a new model instance.
    
    Args:
        model_config: The model configuration
        model_service: The model service
        
    Returns:
        A dictionary with the ID of the created model instance
    """
    model_name = model_service.table_name
    log.bind(model=model_name)
    log.info(f"Received create {model_name} request: %s", model.model_dump_json())
    model_id = await model_service.create(model)
    return {"id": model_id}
    
async def get_model(
    model_id: str,
    model_service: ModelService[T]
) -> T:
    """
    Get a model instance by ID.
    
    Args:
        model_id: The ID of the model instance to get
        model_service: The model service
        
    Returns:
        The model configuration
        
    Raises:
        HTTPException: If the model instance is not found
    """
    model_name = model_service.table_name
    log.bind(model=model_name)
    
    model = await model_service.get(model_id)
    if model is None:
        log.info("404 on %s", model_id)
        raise HTTPException(status_code=404, detail=f"{model_name} with ID {model_id} not found")
    
    return model
    
async def get_model_list(
    model_service: ModelService[T]
) -> List[T]:
    """
    Get a list of all model instances.
    
    Args:
        model_service: The model service
        
    Returns:
        A list of model configurations
    """
    log.bind(model=model_service.table_name)
    
    models = await model_service.list()
    log.debug(f"listing %i {model_service.table_name}s", len(models))
    return models
    
async def update_model(
    model_id: str,
    model_config: T,
    model_service: ModelService[T]
) -> Dict[str, bool]:
    """
    Update a model instance.
    
    Args:
        model_id: The ID of the model instance to update
        model_config: The new model configuration
        model_service: The model service
        
    Returns:
        A dictionary indicating success
        
    Raises:
        HTTPException: If the model instance is not found
    """
    model_name = model_service.table_name
    log.bind(model=model_name)
    
    success = await model_service.update(model_id, model_config)
    if not success:
        raise HTTPException(status_code=404, detail=f"{model_name} with ID {model_id} not found")
    return {"success": True}
    
async def delete_model(
    model_id: str,
    model_service: ModelService[T]
) -> Dict[str, bool]:
    """
    Delete a model instance.
    
    Args:
        model_id: The ID of the model instance to delete
        model_service: The model service
        
    Returns:
        A dictionary indicating success
        
    Raises:
        HTTPException: If the model instance is not found
    """
    model_name = model_service.table_name
    success = await model_service.delete(model_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"{model_name} with ID {model_id} not found")
    return {"success": True}

   
