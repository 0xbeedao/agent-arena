from datetime import datetime
from typing import Dict
from unittest.mock import AsyncMock

import pytest

from agentarena.arena.controllers.contest_controller import ContestController
from agentarena.arena.models import (
    Arena,
    ArenaCreate,
    ArenaUpdate,
    Contest,
    ContestCreate,
    Feature,
    FeatureCreate,
    Participant,
    ParticipantCreate,
    PlayerState,
    PlayerStateCreate,
)
from agentarena.arena.services.round_service import RoundService
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import RoleType
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobCreate
from agentarena.models.job import CommandJobUpdate
from agentarena.models.public import ArenaPublic, ContestPublic


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
def playerstate_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for CommandJob"""
    return ModelService[PlayerState, PlayerStateCreate](
        model_class=PlayerState,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def round_service(
    playerstate_service, db_service, uuid_service, message_broker, logging
):
    """Fixture to create a RoundService"""
    return RoundService(
        playerstate_service, db_service, uuid_service, message_broker, logging
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
        model_public=ArenaPublic, model_service=arena_service, logging=logging
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


@pytest.fixture
def contest_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for Contest"""
    return ModelService[Contest, ContestCreate](
        model_class=Contest,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def feature_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for Feature"""
    return ModelService[Feature, FeatureCreate](
        model_class=Feature,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def contest_ctrl(
    contest_service,
    feature_service,
    participant_service,
    round_service,
    message_broker,
    logging,
):
    return ContestController(
        feature_service=feature_service,
        participant_service=participant_service,
        round_service=round_service,
        message_broker=message_broker,
        model_service=contest_service,
        logging=logging,
    )


@pytest.fixture
def participant_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for Participant"""
    return ModelService[Participant, ParticipantCreate](
        model_class=Participant,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.mark.asyncio
async def test_create_round(
    round_service: RoundService,
    db_service: DbService,
    contest_ctrl,
    participant_service,
    arena_ctrl,
):
    """Test creating a round"""
    with db_service.get_session() as session:
        player, _ = await participant_service.create(
            ParticipantCreate(
                name="Test Participant",
                description="Test Description",
                role=RoleType.PLAYER,
                endpoint="http://localhost:8000/test/$ID$",
            ),
            session,
        )
        session.commit()
        assert player
        arena = await get_arena(arena_ctrl, session)
        contest = await contest_ctrl.create_contest(
            ContestCreate(
                arena_id=arena.id,
                player_positions='["1,1","9,9"]',
                player_inventories="[]",
                participant_ids=[player.id],
            ),
            session,
        )
        session.commit()
        assert contest
        round = await round_service.create_round(
            contest_id=contest.id, round_no=0, session=session
        )
        assert round is not None
        assert round.id is not None
        assert round.contest_id == contest.id
        assert round.round_no == 0
        assert round.player_states is not None
        assert len(round.player_states) == 1
        assert round.player_states[0].id is not None
        assert round.player_states[0].contestround_id == round.id
        assert round.player_states[0].participant_id == player.id
        assert round.player_states[0].position == "1,1"
        assert round.player_states[0].inventory == []
        assert round.player_states[0].health == "Fresh"
        assert round.player_states[0].score == 0
