from unittest.mock import AsyncMock

import pytest

from agentarena.arena.models import Arena
from agentarena.arena.models import ArenaCreate
from agentarena.arena.models import ArenaUpdate
from agentarena.arena.models import Contest
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import ContestState
from agentarena.arena.models import ContestUpdate
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.public import ArenaPublic
from agentarena.models.public import ContestPublic


@pytest.fixture
def logging():
    return LoggingService(capture=True)


@pytest.fixture
def uuid_service(logging):
    return UUIDService(word_list=[], prod=False)


@pytest.fixture
def message_broker():
    """Fixture to create a mock message broker"""
    broker = AsyncMock()
    broker.publish_model_change = AsyncMock()
    broker.publish_response = AsyncMock()
    return broker


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
def model_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for features"""
    return ModelService[Contest, ContestCreate](
        model_class=Contest,
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def template_service(logging):
    return JinjaRenderer()


@pytest.fixture
def contest_ctrl(model_service, template_service, logging):
    return ModelController[Contest, ContestCreate, ContestUpdate, ContestPublic](
        base_path="/api/contest",
        model_name="contest",
        model_create=ContestCreate,
        model_update=ContestUpdate,
        model_public=ContestPublic,
        model_service=model_service,
        template_service=template_service,
        logging=logging,
    )


@pytest.fixture
def arena_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for Arena"""
    return ModelService[Arena, ArenaCreate](
        model_class=Arena,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def arena_ctrl(arena_service, logging):
    return ModelController[Arena, ArenaCreate, ArenaUpdate, ArenaPublic](
        base_path="/api/arena",
        model_name="arena",
        model_create=ArenaCreate,
        model_update=ArenaUpdate,
        model_public=ArenaPublic,
        model_service=arena_service,
        logging=logging,
    )


async def get_arena(arena_ctrl, session):
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
    return await arena_ctrl.create_model(create_arena, session)


@pytest.mark.asyncio
async def test_create_contest_success(contest_ctrl, db_service, arena_ctrl):
    with db_service.get_session() as session:
        arena = await get_arena(arena_ctrl, session)
        create_contest = ContestCreate(
            arena_id=arena.id,
            player_positions="A;B;C;D",
            player_inventories="[]",
            participant_ids=["a", "b", "c"],
        )

        result = await contest_ctrl.create_model(create_contest, session)
        # Assert
        assert result.id
        assert result.arena_id == arena.id
        assert result.state == ContestState.CREATED.value


@pytest.mark.asyncio
async def test_get_contest(contest_ctrl, db_service, arena_ctrl):
    with db_service.get_session() as session:
        arena = await get_arena(arena_ctrl, session)

        create_contest = ContestCreate(
            arena_id=arena.id,
            player_positions="A;B;C;D",
            player_inventories="[]",
            participant_ids=["a", "b", "c"],
        )

        result = await contest_ctrl.create_model(create_contest, session)
        assert result.id

        session.commit()

        fresh = await contest_ctrl.get_model(result.id, session)
        assert isinstance(fresh, ContestPublic)
        assert fresh.id
        assert fresh.arena.id == arena.id
        assert fresh.state == ContestState.CREATED.value
        assert fresh.rounds == []


@pytest.mark.asyncio
async def test_get_contest_list(contest_ctrl, db_service, arena_ctrl):
    with db_service.get_session() as session:
        arena = await get_arena(arena_ctrl, session)

        for _ in range(10):
            create_contest = ContestCreate(  # noqa: F841
                arena_id=arena.id,
                player_positions="A;B;C;D",
                player_inventories="[]",
                participant_ids=["a", "b", "c"],
            )
            await contest_ctrl.create_model(create_contest, session)

        contests = await contest_ctrl.get_model_list(session)
        assert len(contests) == 10
        assert all(isinstance(c, ContestPublic) for c in contests)
        assert all(c.arena.id == arena.id for c in contests)
