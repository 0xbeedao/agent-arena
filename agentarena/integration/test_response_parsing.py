import httpx
import pytest
from nats.aio.msg import Msg

from agentarena.arena.models import Participant
from agentarena.arena.statemachines.setup_machine import SetupMachine
from agentarena.integration.test_helpers import ARENA_URL
from agentarena.integration.test_helpers import make_contest
from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import RoleType

from ..conftest import CONTEST_CONFIG


@pytest.mark.usefixtures("nats_container")
@pytest.mark.asyncio
async def test_nats_integration_with_request(nats_client):
    # Use a future to capture the received message

    client = await nats_client

    async def message_responder(msg):
        await client.publish(msg.reply, b"OK")

    sub = await client.subscribe("test.subject", cb=message_responder)

    response = await client.request("test.subject", b"hello")
    assert response.data == b"OK"

    await sub.unsubscribe()
    await client.close()


@pytest.mark.usefixtures(
    "nats_container",
    "start_actor_server",
    "logger",
    "config_file",
    "nats_url",
)
@pytest.mark.asyncio
async def test_actor_server_health():
    response = httpx.get(f"http://localhost:8001/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.usefixtures(
    "nats_container",
    "start_arena_server",
    "logger",
    "config_file",
    "nats_url",
)
@pytest.mark.asyncio
async def test_arena_server_health():
    response = httpx.get(f"http://localhost:8000/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.usefixtures(
    "start_arena_server",
    "start_actor_server",
)
@pytest.mark.asyncio
async def test_contest_fixtures(contest_fixtures, contest_service):
    assert contest_fixtures["announcer"] is not None
    assert contest_fixtures["arena"] is not None
    assert contest_fixtures["judge"] is not None
    assert contest_fixtures["player1"] is not None
    assert contest_fixtures["player2"] is not None
    with contest_service.db_service.get_session() as session:
        contest = await make_contest(
            contest_fixtures["arena_config"],
            [
                contest_fixtures["player1"],
                contest_fixtures["player2"],
                contest_fixtures["announcer"],
                contest_fixtures["judge"],
            ],
            config=CONTEST_CONFIG,
            session=session,
        )
        assert contest is not None
        assert contest.id is not None


@pytest.mark.usefixtures(
    "start_arena_server",
    "start_actor_server",
)
@pytest.mark.asyncio
async def test_generate_features(
    contest_fixtures,
    round_service,
    arena_db_service,
    feature_service,
    view_service,
    message_broker,
    logger,
):
    announcer_id = contest_fixtures["announcer"]
    announcer_response = httpx.get(f"{ARENA_URL}/participant/{announcer_id}")
    assert announcer_response.status_code == 200
    announcer = Participant.model_validate(announcer_response.json())
    assert announcer is not None
    assert announcer.role == RoleType.ANNOUNCER

    with arena_db_service.get_session() as session:
        contest = await make_contest(
            contest_fixtures["arena_config"],
            [
                contest_fixtures["player1"],
                contest_fixtures["player2"],
                contest_fixtures["announcer"],
                contest_fixtures["judge"],
                contest_fixtures["arena"],
            ],
            config=CONTEST_CONFIG,
            session=session,
        )

        assert contest is not None

        round = await round_service.create_round(contest.id, 0, session)
        assert round is not None

        round.state = ContestRoundState.GENERATING_FEATURES
        session.add(round)
        session.commit()

        log = logger.bind(test="test_generate_features")
        machine = SetupMachine(
            contest,
            message_broker,
            feature_service,
            round_service,
            view_service,
            session,
            log,
        )

        arena_agent = contest.get_role(RoleType.ARENA)[0]
        assert arena_agent is not None
        msg: Msg = await machine.get_generate_features(arena_agent)
        features, success = machine.parse_generate_features_response(msg)
        assert success
        assert len(features) > 0
        feature = features[0]
        assert feature["name"] is not None
        assert feature["description"] is not None
        assert feature["position"] is not None
