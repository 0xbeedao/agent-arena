import os
import subprocess
import time

import pytest
import requests
from nats.aio.client import Client as NATS
from testcontainers.core.container import DockerContainer

from agentarena.actors.models import Agent
from agentarena.actors.models import AgentCreate
from agentarena.actors.models import Strategy
from agentarena.actors.models import StrategyCreate
from agentarena.arena.arena_container import get_wordlist
from agentarena.arena.models import Arena
from agentarena.arena.models import ArenaCreate
from agentarena.arena.models import Contest
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import JudgeResult
from agentarena.arena.models import JudgeResultCreate
from agentarena.arena.models import Participant
from agentarena.arena.models import ParticipantCreate
from agentarena.arena.models import PlayerAction
from agentarena.arena.models import PlayerActionCreate
from agentarena.arena.models import PlayerState
from agentarena.arena.models import PlayerStateCreate
from agentarena.arena.services.round_service import RoundService
from agentarena.arena.services.view_service import ViewService
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.integration.test_helpers import ACTOR_URL
from agentarena.integration.test_helpers import ARENA_URL
from agentarena.integration.test_helpers import load_fixture
from agentarena.integration.test_helpers import make_agent

ARENA_CONFIG = {
    "name": "Flag Castle",
    "description": "A capture the flag game set in a castle courtyard, with viewers cheering on from the walls lining the courtyard",
    "height": 10,
    "width": 10,
    "rules": "Capture the flag. No fighting. Players move up to 2 spaces, if running, but may trip or be vulnerable when doing so. Players may only grab the flag or place it on the base from one space away.",
    "max_random_features": 5,
    "winning_condition": "First player to bring the flag to the base wins",
    "features": [
        {
            "name": "flag",
            "description": "the flag the players are seeking to capture",
            "position": "5,5",
            "origin": "required",
        },
        {
            "name": "base",
            "description": "the scoring base",
            "position": "1,5",
            "origin": "required",
        },
    ],
}

ANNOUNCER_STRATEGY = {
    "name": "Announcer",
    "personality": "You aren an engaged and enthusiastic announcer, you are excited to be the announcer for the contest.",
    "model": "{{ model }}",
    "prompts": [
        {
            "key": "announcer_describe_arena",
            "prompt": "#jinja:announcer.summary.describe_arena",
        },
        {
            "key": "announcer_describe_results",
            "prompt": "#jinja:announcer.summary.describe_results",
        },
    ],
    "description": "Simple announcer, just describing the arena and results.",
    "role": "announcer",
}

ANNOUNCER_PARTICIPANT = {
    "name": "Mr. A",
    "role": "announcer",
    "description": "Mr. A is the announcer for the game, providing updates and commentary.",
    "endpoint": "channel://actor.agent.$AGENT_ID$",
    "api_key": "",
}

JUDGE_STRATEGY = {
    "name": "Judge",
    "model": "{{ model }}",
    "personality": "Analytical, detail-oriented, and fair.",
    "prompts": [
        {
            "key": "judge_player_action_judgement",
            "prompt": "#jinja:judge.fair.player_action_judgement",
        },
        {"key": "judge_apply_effects", "prompt": "#jinja:judge.fair.apply_effects"},
    ],
    "description": "Your standard fair judge",
    "role": "judge",
}

JUDGE_PARTICIPANT = {
    "name": "Mr. Je",
    "role": "judge",
    "description": "Mr. J is the judge for the game, providing updates and commentary.",
    "endpoint": "channel://actor.agent.$AGENT_ID$",
    "api_key": "",
}

PLAYER1_STRATEGY = {
    "name": "Strategic Player",
    "model": "{{ model }}",
    "personality": "Clear, methodical, and patient. Not very emotive, simply clear and precise",
    "prompts": [
        {"key": "player_player_action", "prompt": "#jinja:player.base.player_action"}
    ],
    "description": "Strategic player, you respond stragically and concisely",
    "role": "player",
}

PLAYER2_STRATEGY = {
    "name": "Careful Player",
    "model": "{{ model }}",
    "personality": "Careful player, you respond carefully and with strategy",
    "prompts": [
        {"key": "player_player_action", "prompt": "#jinja:player.base.player_action"}
    ],
    "description": "Careful player, you respond carefully and with strategy",
    "role": "player",
}

PLAYER1_PARTICIPANT = {
    "name": "Captain Agent",
    "role": "player",
    "description": "Captain Agent is a strategic player, you respond stragically and concisely",
    "endpoint": "channel://actor.agent.$AGENT_ID$",
    "api_key": "",
}

PLAYER2_PARTICIPANT = {
    "name": "Captain Sneakor",
    "role": "player",
    "description": "Captain Sneakor is a careful player, you respond carefully and with strategy",
    "endpoint": "channel://actor.agent.$AGENT_ID$",
    "api_key": "",
}

ARENA_STRATEGY = {
    "name": "Straightforward Arena",
    "model": "{{ model }}",
    "personality": "A clear and simple arena, intending to make things easy to see, experiment and test",
    "prompts": [
        {
            "key": "arena_generate_features",
            "prompt": "#jinja:arena.base.generate_features",
        }
    ],
    "description": "The simplest arena, keeping things as clean and straighforward as possible.",
    "role": "arena",
}

ARENA_PARTICIPANT = {
    "name": "Proving Grounds",
    "role": "arena",
    "description": "You are the personification of the proving grounds, you are the arena for the game, providing updates and commentary.",
    "endpoint": "channel://actor.agent.$AGENT_ID$",
    "api_key": "",
}

CONTEST_CONFIG = {"player_positions": '["1,1", "9,9"]', "player_inventories": "[]"}


@pytest.fixture(scope="session")
def logging():
    service = LoggingService(capture=True)
    return service


@pytest.fixture(scope="session")
def logger(logging):
    return logging.get_logger("integration")


@pytest.fixture(scope="session")
def uuid_service():
    wordlist = get_wordlist(str(get_project_root()), "etc/words.csv")
    return UUIDService(word_list=wordlist, prod=False)


@pytest.fixture(scope="session")
def arena_db_service(uuid_service, logging):
    """Fixture to create an in-memory DB service"""
    service = DbService(
        str(get_project_root()),
        dbfile="arena-test.db",
        get_engine=get_engine,
        memory=False,
        prod=False,
        uuid_service=uuid_service,
        logging=logging,
    )
    return service.create_db()


@pytest.fixture(scope="session")
def actor_db_service(uuid_service, logging):
    service = DbService(
        str(get_project_root()),
        dbfile="actor-test.db",
        get_engine=get_engine,
        memory=False,
        prod=False,
        uuid_service=uuid_service,
        logging=logging,
    )
    return service.create_db()


@pytest.fixture(scope="session")
def contest_fixtures(logger):
    logger.info("Checking Arena and Actor servers before creating fixtures")
    for _ in range(20):
        try:
            requests.get("http://localhost:8000/health", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    for _ in range(20):
        try:
            requests.get("http://localhost:8001/health", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    logger.info("Arena and Actor servers are up - creating fixtures")
    announcer_id = load_fixture(ANNOUNCER_PARTICIPANT, f"{ARENA_URL}/participant/")
    arena_id = load_fixture(ARENA_PARTICIPANT, f"{ARENA_URL}/participant/")
    judge_id = load_fixture(JUDGE_PARTICIPANT, f"{ARENA_URL}/participant/")
    player1_id = load_fixture(PLAYER1_PARTICIPANT, f"{ARENA_URL}/participant/")
    player2_id = load_fixture(PLAYER2_PARTICIPANT, f"{ARENA_URL}/participant/")
    announcer_strategy_id = load_fixture(ANNOUNCER_STRATEGY, f"{ACTOR_URL}/strategy/")
    arena_strategy_id = load_fixture(ARENA_STRATEGY, f"{ACTOR_URL}/strategy/")
    judge_strategy_id = load_fixture(JUDGE_STRATEGY, f"{ACTOR_URL}/strategy/")
    player1_strategy_id = load_fixture(PLAYER1_STRATEGY, f"{ACTOR_URL}/strategy/")
    player2_strategy_id = load_fixture(PLAYER2_STRATEGY, f"{ACTOR_URL}/strategy/")

    make_agent(ANNOUNCER_PARTICIPANT["name"], announcer_strategy_id, announcer_id)
    make_agent(ARENA_PARTICIPANT["name"], arena_strategy_id, arena_id)
    make_agent(JUDGE_PARTICIPANT["name"], judge_strategy_id, judge_id)
    make_agent(PLAYER1_PARTICIPANT["name"], player1_strategy_id, player1_id)
    make_agent(PLAYER2_PARTICIPANT["name"], player2_strategy_id, player2_id)

    arena_config_id = load_fixture(ARENA_CONFIG, f"{ARENA_URL}/arena/")
    return {
        "arena_config": arena_config_id,
        "announcer": announcer_id,
        "arena": arena_id,
        "judge": judge_id,
        "player1": player1_id,
        "player2": player2_id,
    }


@pytest.fixture(scope="session")
def nats_container():
    nats = DockerContainer("nats:latest").with_exposed_ports(4222)
    nats.start()
    yield nats
    nats.stop()


@pytest.fixture(scope="session")
def nats_client(nats_container):
    async def _get_client():
        nc = NATS()
        port = nats_container.get_exposed_port(4222)
        await nc.connect(servers=[f"nats://localhost:{port}"])
        return nc

    return _get_client()


@pytest.fixture(scope="session")
def nats_url(nats_container):
    port = nats_container.get_exposed_port(4222)
    return f"nats://localhost:{port}"


@pytest.fixture(scope="session")
def message_broker(nats_client, uuid_service, logging):
    return MessageBroker(client=nats_client, uuid_service=uuid_service, logging=logging)


@pytest.fixture(scope="session")
def arena_service(arena_db_service, uuid_service, message_broker, logging):
    """Fixture to create an ArenaService for Arena"""
    return ModelService[Arena, ArenaCreate](
        model_class=Arena,
        message_broker=message_broker,
        db_service=arena_db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def agent_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[Agent, AgentCreate](
        model_class=Agent,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def contest_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[Contest, ContestCreate](
        model_class=Contest,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def feature_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[Feature, FeatureCreate](
        model_class=Feature,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def judge_result_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[JudgeResult, JudgeResultCreate](
        model_class=JudgeResult,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def player_action_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[PlayerAction, PlayerActionCreate](
        model_class=PlayerAction,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def player_state_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[PlayerState, PlayerStateCreate](
        model_class=PlayerState,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def participant_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[Participant, ParticipantCreate](
        model_class=Participant,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def strategy_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[Strategy, StrategyCreate](
        model_class=Strategy,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def playerstate_service(arena_db_service, message_broker, uuid_service, logging):
    return ModelService[PlayerState, PlayerStateCreate](
        model_class=PlayerState,
        db_service=arena_db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def round_service(
    arena_db_service, message_broker, uuid_service, logging, playerstate_service
):
    return RoundService(
        db_service=arena_db_service,
        playerstate_service=playerstate_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture(scope="session")
def view_service(logging):
    return ViewService(logging=logging)


@pytest.fixture(scope="session")
def config_file(nats_url: str):
    with open("agent-arena-test-config.yaml", "r") as f:
        content = f.read()
        content = content.replace("nats://localhost:4222", nats_url)
    fname = f"integration-config.yaml"
    with open(fname, "w") as f:
        f.write(content)
    return fname


@pytest.fixture(scope="session")
def start_arena_server(logger, config_file):
    logger.info(f"Starting arena server with config file {config_file}")
    proc = subprocess.Popen(
        ["python3", "scripts/agentarena.arena"],
        env={**os.environ, "AGENTARENA_CONFIG_FILE": config_file},
    )
    # Optionally: Wait for the server to be up
    for _ in range(20):
        try:
            requests.get("http://localhost:8000/health", timeout=1)
            logger.info("Arena server is up")
            break
        except Exception:
            time.sleep(0.5)
    yield
    proc.terminate()
    proc.wait()


@pytest.fixture(scope="session")
def start_actor_server(logger, config_file):
    logger.info(f"Starting actor server with config file {config_file}")
    proc = subprocess.Popen(
        ["python3", "scripts/agentarena.actor"],
        env={**os.environ, "AGENTARENA_CONFIG_FILE": config_file},
    )
    # Optionally: Wait for the server to be up
    for _ in range(20):
        try:
            requests.get("http://localhost:8001/health", timeout=1)
            logger.info("Actor server is up")
            break
        except Exception:
            time.sleep(0.5)
    yield
    proc.terminate()
    proc.wait()
