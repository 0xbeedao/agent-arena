"""
Strategy service for the Agent Arena application.
Handles business logic for strategy operations.
"""

from typing import Optional, Dict, List
from ulid import ULID
from agentarena.models.strategy import Strategy
from .db_service import DbService
from datetime import datetime

import json
import structlog

class StrategyService:
    """Service for strategy operations."""
    
    def __init__(self, dbService: DbService):
        """Initialize the strategy service."""
        self.table = dbService.db['strategies']
        self.dbService = dbService
        self.log = structlog.get_logger('strategyservice').bind(module="strategyservice")
    
    async def create_strategy(self, strategy: Strategy) -> str:
        """
        Create a new strategy.
        
        Args:
            strategy: The strategy to create
            
        Returns:
            The ID of the created strategy
        """
        db_strategy = strategy.model_copy()
        # always make a new ID
        db_strategy.id = ULID().hex
        # And set the created_at
        db_strategy.created_at = datetime.now().isoformat()

        strategy_id = str(db_strategy.id)
 
        self.table.insert(db_strategy.model_dump(), pk="id")
        self.log.info("Added strategy: %s", strategy_id)
        self.dbService.add_audit_log("Added strategy: %s" % strategy_id)
        return strategy_id
    
    async def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """
        Get a strategy by ID.
        
        Args:
            strategy_id: The ID of the strategy to get
            
        Returns:
            The strategy, or None if not found
        """
        row = self.table.get(str(strategy_id))
        self.log.info("Getting strategy: %s", strategy_id)
        return Strategy.model_validate(row) if row is not None else None
            
    async def update_strategy(self, strategy_id: str, strategy: Strategy) -> bool:
        """
        Update a strategy.
        
        Args:
            strategy_id: The ID of the strategy to update
            strategy: The updated strategy data
            
        Returns:
            True if the strategy was updated, False if not found
        """
        existing = await self.get_strategy(strategy_id)
        if existing is None:
            self.log.warn("No such strategy to update: %s", strategy_id)
            return False
        updated = strategy.model_dump(exclude=["id", "created_at"])
        self.table.update(strategy_id, updated)
        self.dbService.add_audit_log("Updated strategy %s: %s" % (strategy_id, json.dumps(updated)))
        return True
    
    async def delete_strategy(self, strategy_id: str) -> bool:
        """
        Delete a strategy.
        
        Args:
            strategy_id: The ID of the strategy to delete
            
        Returns:
            True if the strategy was deleted, False if not found
        """
        strategy = await self.get_strategy(strategy_id)
        if strategy is None:
            self.log.warn("No such strategy to delete: %s", strategy_id)
            return False
            
        self.table.delete(strategy_id)
        self.log.info("Deleted strategy: %s", strategy_id)
        self.dbService.add_audit_log("Deleted strategy: %s" % strategy_id)
        return True
    
    async def list_strategies(self) -> List[Strategy]:
        """
        List all strategies.
        
        Returns:
            A list of all strategies
        """
        return [Strategy.model_validate(row) for row in self.table.rows]