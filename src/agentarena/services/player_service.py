"""
Player service for the Agent Arena application.
Handles business logic for player operations.
"""

from typing import Optional, Dict, List
from ulid import ULID
from datetime import datetime
from agentarena.models.player import PlayerState, PlayerAction
from .db_service import DbService
import json
import structlog

class PlayerService:
    """Service for player operations."""
    
    def __init__(self, dbService: DbService):
        """Initialize the player service."""
        self.table = dbService.db['players']
        self.dbService = dbService
        self.log = structlog.get_logger('playerservice').bind(module="playerservice")
    
    async def create_player(self, player: PlayerState) -> str:
        """
        Create a new player.
        
        Args:
            player: The player to create
            
        Returns:
            The ID of the created player
        """
        db_player = player.model_copy()
        # Generate new ID
        db_player.id = ULID().hex
        # Set timestamps
        isonow = datetime.now().isoformat()
        db_player.created_at = isonow
        db_player.updated_at = isonow

        player_id = str(db_player.id)
 
        self.table.insert(db_player.model_dump(), pk="id")
        self.log.info("Added player: %s", player_id)
        self.dbService.add_audit_log("Added player: %s" % player_id)
        return player_id
    
    async def get_player(self, player_id: str) -> Optional[PlayerState]:
        """
        Get a player by ID.
        
        Args:
            player_id: The ID of the player to get
            
        Returns:
            The player, or None if not found
        """
        row = self.table.get(str(player_id))
        self.log.info("Getting player: %s", player_id)
        return PlayerState.model_validate(row) if row is not None else None
            
    async def update_player(self, player_id: str, player: PlayerState) -> bool:
        """
        Update a player.
        
        Args:
            player_id: The ID of the player to update
            player: The updated player data
            
        Returns:
            True if the player was updated, False if not found
        """
        existing = await self.get_player(player_id)
        if existing is None:
            self.log.warn("No such player to update: %s", player_id)
            return False
        updated = player.model_dump(exclude=["id", "created_at"])
        updated['updated_at'] = datetime.now().isoformat()
        self.table.update(player_id, updated)
        self.dbService.add_audit_log("Updated player %s: %s" % (player_id, json.dumps(updated)))
        return True
    
    async def delete_player(self, player_id: str) -> bool:
        """
        Delete a player.
        
        Args:
            player_id: The ID of the player to delete
            
        Returns:
            True if the player was deleted, False if not found
        """
        player = await self.get_player(player_id)
        if player is None:
            self.log.warn("No such player to delete: %s", player_id)
            return False
            
        self.table.delete(player_id)
        self.log.info("Deleted player: %s", player_id)
        self.dbService.add_audit_log("Deleted player: %s" % player_id)
        return True
    
    async def list_players(self) -> List[PlayerState]:
        """
        List all players.
        
        Returns:
            A list of all players
        """
        return [PlayerState.model_validate(row) for row in self.table.rows]