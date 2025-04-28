"""
Test for the ModelService class.

This file demonstrates how to use the ModelService with different model classes.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional
from pydantic import Field
from ulid import ULID
from sqlite_utils.db import Database

from agentarena.models.dbmodel import DbBase
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService

# Define a simple test model that inherits from DbBase
class TestModel(DbBase):
    """A simple test model for demonstrating ModelService."""
    name: str = Field(description="Name of the test model")
    description: Optional[str] = Field(default="", description="Description of the test model")

def get_database(filename: str, memory: bool = False) -> Database:
    """Get a database instance."""
    if memory:
        return Database(memory=True)
    
    print(f"Opening db at: {filename}")
    return Database(filename)

async def main():
    """Main test function."""
    # Create a temporary database file
    db_file = "test_model_service.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    
    # Initialize the DbService
    db_service = DbService(".", db_file, get_database)
    
    # Create a ModelService for TestModel
    test_service = ModelService(TestModel, db_service, "test_models")
    
    # Create a test model
    test_model = TestModel(name="Test Model 1", description="This is a test model")
    test_id = await test_service.create(test_model)
    print(f"Created test model with ID: {test_id}")
    
    # Get the test model
    retrieved_model = await test_service.get(test_id)
    print(f"Retrieved test model: {retrieved_model}")
    
    # Update the test model
    retrieved_model.name = "Updated Test Model"
    success = await test_service.update(test_id, retrieved_model)
    print(f"Updated test model: {success}")
    
    # Get the updated test model
    updated_model = await test_service.get(test_id)
    print(f"Retrieved updated test model: {updated_model}")
    
    # List all test models
    all_models = await test_service.list()
    print(f"All test models: {all_models}")
    
    # Delete the test model
    success = await test_service.delete(test_id)
    print(f"Deleted test model: {success}")
    
    # List all test models after deletion
    all_models = await test_service.list()
    print(f"All test models after deletion: {all_models}")
    
    # Clean up
    if os.path.exists(db_file):
        os.remove(db_file)

if __name__ == "__main__":
    asyncio.run(main())