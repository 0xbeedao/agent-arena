"""
Generic model service for the Agent Arena application.
Provides a reusable service for CRUD operations on any model that inherits from DbBase.
"""

from typing import Optional, List, Type, TypeVar, Generic, Any, Dict
from ulid import ULID
from datetime import datetime
import json
import structlog
import re
from pydantic import BaseModel

from agentarena.models.dbmodel import DbBase
from .db_service import DbService

T = TypeVar('T', bound=DbBase)

class ModelService(Generic[T]):
    """
    Generic service for model operations.
    
    This service provides CRUD operations for any model that inherits from DbBase.
    It can be used directly or as a base class for more specialized services.
    """
    
    def __init__(self, model_class: Type[T], dbService: DbService, table_name: Optional[str] = None):
        """
        Initialize the model service.
        
        Args:
            model_class: The Pydantic model class (must be a subclass of DbBase)
            dbService: The database service
            table_name: Optional table name (if not provided, will be inferred from model_class name)
        """
        if not issubclass(model_class, DbBase):
            raise TypeError(f"model_class must be a subclass of DbBase, got {model_class}")
        
        self.model_class = model_class
        self.dbService = dbService
        
        # Infer table name if not provided
        if table_name is None:
            # Convert CamelCase to snake_case and pluralize
            model_name = model_class.__name__
            # Handle special case for "Strategy" -> "strategies"
            if model_name.lower() == "strategy":
                table_name = "strategies"
            else:
                # Simple pluralization - just add 's'
                table_name = f"{model_name.lower()}s"
        
        self.table = dbService.db[table_name]
        model_name = model_class.__name__
        self.log = structlog.get_logger(f"{model_name.lower()}service").bind(module=f"{model_name.lower()}service")
    
    async def create(self, obj: T) -> str:
        """
        Create a new model instance.
        
        Args:
            obj: The model instance to create
            
        Returns:
            The ID of the created instance
        """
        db_obj = obj.model_copy()
        # Always make a new ID
        db_obj.id = ULID().hex
        # And set the timestamps
        isonow = datetime.now().isoformat()
        db_obj.created_at = isonow
        db_obj.updated_at = isonow

        obj_id = str(db_obj.id)
        
        self.table.insert(db_obj.model_dump(), pk="id")
        model_name = self.model_class.__name__
        self.log.info(f"Added {model_name.lower()}: %s", obj_id)
        self.dbService.add_audit_log(f"Added {model_name.lower()}: {obj_id}")
        return obj_id
    
    async def get(self, obj_id: str) -> Optional[T]:
        """
        Get a model instance by ID.
        
        Args:
            obj_id: The ID of the instance to get
            
        Returns:
            The model instance, or None if not found
        """
        row = self.table.get(str(obj_id))
        model_name = self.model_class.__name__
        self.log.info(f"Getting {model_name.lower()}: %s", obj_id)
        return self.model_class.model_validate(row) if row is not None else None
            
    async def update(self, obj_id: str, obj: T) -> bool:
        """
        Update a model instance.
        
        Args:
            obj_id: The ID of the instance to update
            obj: The updated instance data
            
        Returns:
            True if the instance was updated, False if not found
        """
        existing = await self.get(obj_id)
        model_name = self.model_class.__name__
        if existing is None:
            self.log.warn(f"No such {model_name.lower()} to update: %s", obj_id)
            return False
        
        updated = obj.model_dump(exclude=["id", "created_at"])
        updated["updated_at"] = datetime.now().isoformat()
        self.table.update(obj_id, updated)
        self.dbService.add_audit_log(f"Updated {model_name.lower()} {obj_id}: {json.dumps(updated)}")
        return True
    
    async def delete(self, obj_id: str) -> bool:
        """
        Delete a model instance.
        
        Args:
            obj_id: The ID of the instance to delete
            
        Returns:
            True if the instance was deleted, False if not found
        """
        existing = await self.get(obj_id)
        model_name = self.model_class.__name__
        if existing is None:
            self.log.warn(f"No such {model_name.lower()} to delete: %s", obj_id)
            return False
            
        self.table.delete(obj_id)
        self.log.info(f"Deleted {model_name.lower()}: %s", obj_id)
        self.dbService.add_audit_log(f"Deleted {model_name.lower()}: {obj_id}")
        return True
    
    async def list(self) -> List[T]:
        """
        List all model instances.
        
        Returns:
            A list of all model instances
        """
        return [self.model_class.model_validate(row) for row in self.table.rows]