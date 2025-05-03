"""
FeatureDTO controller for the Agent Arena application.
Handles HTTP requests for feature operations.
"""

from typing import Dict, List

import structlog
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from ulid import ULID

from agentarena.config.containers import Container
from agentarena.models.feature import FeatureDTO
from agentarena.services.model_service import ModelService

# Create a router for feature endpoints
router = APIRouter(tags=["FeatureDTO"])
log = structlog.get_logger("feature_controller").bind(module="feature_controller")


@router.post("/feature", response_model=Dict[str, str])
@inject
async def create_feature(
    feature: FeatureDTO,
    feature_service: ModelService[FeatureDTO] = Depends(
        Provide[Container.feature_service]
    ),
) -> Dict[str, str]:
    """
    Create a new feature.

    Args:
        feature: The feature configuration
        feature_service: The feature service

    Returns:
        A dictionary with the ID of the created feature
    """
    [id, response] = await feature_service.create(feature)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"id": id}


@router.get("/feature/{feature_id}", response_model=FeatureDTO)
@inject
async def get_feature(
    feature_id: str,
    feature_service: ModelService[FeatureDTO] = Depends(
        Provide[Container.feature_service]
    ),
) -> FeatureDTO:
    """
    Get a feature by ID.

    Args:
        feature_id: The ID of the feature to get
        feature_service: The feature service

    Returns:
        The feature configuration

    Raises:
        HTTPException: If the feature is not found
    """
    [feature_obj, response] = await feature_service.get(feature_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return feature_obj


@router.get("/feature", response_model=List[FeatureDTO])
@inject
async def get_feature_list(
    feature_service: ModelService[FeatureDTO] = Depends(
        Provide[Container.feature_service]
    ),
) -> List[FeatureDTO]:
    """
    Get a list of all features.

    Args:
        feature_service: The feature service

    Returns:
        A list of feature configurations
    """
    return await feature_service.list()


@router.put("/feature/{feature_id}", response_model=Dict[str, bool])
@inject
async def update_feature(
    feature_id: str,
    feature: FeatureDTO,
    feature_service: ModelService[FeatureDTO] = Depends(
        Provide[Container.feature_service]
    ),
) -> Dict[str, bool]:
    """
    Update a feature.

    Args:
        feature_id: The ID of the feature to update
        feature: The new feature configuration
        feature_service: The feature service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the feature is not found
    """
    response = await feature_service.update(feature_id, feature)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}


@router.delete("/feature/{feature_id}", response_model=Dict[str, bool])
@inject
async def delete_feature(
    feature_id: str,
    feature_service: ModelService[FeatureDTO] = Depends(
        Provide[Container.feature_service]
    ),
) -> Dict[str, bool]:
    """
    Delete a feature.

    Args:
        feature_id: The ID of the feature to delete
        feature_service: The feature service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the feature is not found
    """
    response = await feature_service.delete(feature_id)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}
