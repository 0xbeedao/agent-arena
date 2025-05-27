import pytest

from agentarena.arena.models import Arena
from agentarena.arena.models import ArenaCreate
from agentarena.arena.models import ArenaPublic
from agentarena.arena.models import ArenaUpdate
from agentarena.arena.models import Contest
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import ContestPublic
from agentarena.arena.models import ContestState
from agentarena.arena.models import ContestUpdate
from agentarena.core.controllers.model_controller import ModelController
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
def model_service(db_service, uuid_service, logging):
    """Fixture to create a ModelService for features"""
    return ModelService[Contest](
        model_class=Contest,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def ctrl(model_service, logging):
    return ModelController[Contest, ContestCreate, ContestUpdate, ContestPublic](
        model_public=ContestPublic, model_service=model_service, logging=logging
    )


@pytest.fixture
def arena_service(db_service, uuid_service, logging):
    """Fixture to create a ModelService for Arena"""
    return ModelService[Arena](
        model_class=Arena,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def arena_ctrl(arena_service, logging):
    return ModelController[Arena, ArenaCreate, ArenaUpdate, ArenaPublic](
        model_public=ArenaPublic, model_service=arena_service, logging=logging
    )


@pytest.mark.asyncio
async def test_create_contest_success(ctrl, db_service, arena_ctrl):
    with db_service.get_session() as session:
        # Arrange
        create_arena = ArenaCreate(
            name="test arena",
            description="test",
            height=10,
            width=10,
            rules="",
            winning_condition="",
            max_random_features=1,
            features=[],
        )
        arena = await arena_ctrl.create_model(create_arena, session)

        create_contest = ContestCreate(
            arena_id=arena.id,
            player_positions="A;B;C;D",
            participant_ids=["a", "b", "c"],
        )

        result = await ctrl.create_model(create_contest, session)
        # Assert
        assert result.id
        assert result.arena_id == arena.id
        assert result.state == ContestState.CREATED.value
