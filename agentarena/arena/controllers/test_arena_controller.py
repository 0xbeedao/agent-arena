import pytest

from agentarena.arena.controllers.arena_controller import ArenaController
from agentarena.arena.models import Arena
from agentarena.arena.models import ArenaCreate
from agentarena.arena.models import Feature
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService


@pytest.fixture
def logging():
    return LoggingService(capture=True)


@pytest.fixture
def uuid_service(logging):
    return UUIDService(word_list=[], prod=False)


@pytest.fixture
def db_service(uuid_service, logging):
    """Fixture to create an in-memory DB service"""
    service = DbService(
        str(get_project_root()),
        dbfile="test.db",
        get_engine=get_engine,
        memory=True,
        prod=False,
        uuid_service=uuid_service,
        logging=logging,
    )
    return service.create_db()


@pytest.fixture
def arena_service(db_service, uuid_service, logging):
    """Fixture to create a ModelService for arenas"""
    return ModelService[Arena](
        model_class=Arena,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def feature_service(db_service, uuid_service, logging):
    """Fixture to create a ModelService for features"""
    return ModelService[Feature](
        model_class=Feature,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def ctrl(arena_service, feature_service, logging):
    return ArenaController(
        arena_service=arena_service,
        feature_service=feature_service,
        logging=logging,
    )


@pytest.mark.asyncio
async def test_create_arena_success(ctrl, db_service):
    req = ArenaCreate(
        name="test",
        description="testing",
        height=10,
        width=10,
        rules="",
        winning_condition="",
        max_random_features=1,
        features=[],
    )

    # Act
    with db_service.get_session() as session:
        result = await ctrl.create_arena(req, session)
        # Assert
        assert result
        assert result.id
        assert result.name == "test"
        assert result.height == 10


# Additional tests for error cases, get_arena, get_arena_list, update_arena, delete_arena, etc. should be added similarly.
