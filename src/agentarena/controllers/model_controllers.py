"""
Generic model controller for the Agent Arena application.
Provides a reusable controller for CRUD operations on any model that inherits from DbBase.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, Dict, List, TypeVar, Generic, Type
from pydantic import BaseModel

from agentarena.models.dbmodel import DbBase
from agentarena.services.model_service import ModelService

import structlog

T = TypeVar('T', bound=DbBase)

def make_model_controller(model_type: Type[T], container_provider_path: str):
    """
    Creates a FastAPI router with CRUD routes for a model service.
    
    Args:
        model_type: The model type (must be a subclass of DbBase)
        container_provider_path: The path to the model service in the container
                                (e.g., "Container.agent_service")
    
    Returns:
        A FastAPI router with CRUD routes for the model
    """
    # Extract model name for route and tag naming
    model_name = model_type.__name__
    model_name_lower = model_name.lower()
    
    # Create a router for the model endpoints
    router = APIRouter(tags=[model_name])
    log = structlog.get_logger(f"{model_name_lower}_controller").bind(module=f"{model_name_lower}_controller")
    
    @router.post(f"/{model_name_lower}", response_model=Dict[str, str])
    @inject
    async def create_model(
        model_config: model_type,
        model_service: ModelService[model_type] = Depends(Provide[container_provider_path])
    ) -> Dict[str, str]:
        """
        Create a new model instance.
        
        Args:
            model_config: The model configuration
            model_service: The model service
            
        Returns:
            A dictionary with the ID of the created model instance
        """
        log.info(f"Received create {model_name_lower} request: %s", model_config.model_dump_json())
        model_id = await model_service.create(model_config)
        return {"id": model_id}
    
    @router.get(f"/{model_name_lower}/{{model_id}}", response_model=model_type)
    @inject
    async def get_model(
        model_id: str,
        model_service: ModelService[model_type] = Depends(Provide[container_provider_path])
    ) -> model_type:
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
        model = await model_service.get(model_id)
        if model is None:
            raise HTTPException(status_code=404, detail=f"{model_name} with ID {model_id} not found")
        return model
    
    @router.get(f"/{model_name_lower}", response_model=List[model_type])
    @inject
    async def get_model_list(
        model_service: ModelService[model_type] = Depends(Provide[container_provider_path])
    ) -> List[model_type]:
        """
        Get a list of all model instances.
        
        Args:
            model_service: The model service
            
        Returns:
            A list of model configurations
        """
        models = await model_service.list()
        log.debug(f"listing %i {model_name_lower}s", len(models))
        return models
    
    @router.put(f"/{model_name_lower}/{{model_id}}", response_model=Dict[str, bool])
    @inject
    async def update_model(
        model_id: str,
        model_config: model_type,
        model_service: ModelService[model_type] = Depends(Provide[container_provider_path])
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
        success = await model_service.update(model_id, model_config)
        if not success:
            raise HTTPException(status_code=404, detail=f"{model_name} with ID {model_id} not found")
        return {"success": True}
    
    @router.delete(f"/{model_name_lower}/{{model_id}}", response_model=Dict[str, bool])
    @inject
    async def delete_model(
        model_id: str,
        model_service: ModelService[model_type] = Depends(Provide[container_provider_path])
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
        success = await model_service.delete(model_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"{model_name} with ID {model_id} not found")
        return {"success": True}
    
    return router
