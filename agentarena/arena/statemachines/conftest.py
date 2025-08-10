import json
from typing import List

from sqlmodel import Session

from agentarena.actors.models import AgentCreate
from agentarena.actors.models import StrategyCreate
from agentarena.actors.models import StrategyPrompt
from agentarena.arena.models import ArenaCreate, Contest
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import FeatureOriginType
from agentarena.arena.models import ParticipantCreate
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import ContestState, PromptType
from agentarena.models.constants import RoleType

ONE_FEATURE = json.dumps(
    [
        {
            "name": "test feature",
            "description": "test description",
            "position": "4,4",
        },
    ]
)


async def make_contest(
    session: Session,
    contest_service: ModelService[Contest, ContestCreate],
    test_arena,
    player_positions: str = "[]",
    player_inventories: str = "[]",
    state: ContestState = ContestState.STARTING,
) -> Contest:
    cc = ContestCreate(
        arena_id=test_arena.id,
        participant_ids=[],
        player_positions=player_positions,
        player_inventories=player_inventories,
    )
    contest, result = await contest_service.create(cc, session=session)
    assert result.success and contest is not None
    contest.state = state
    session.commit()
    return contest


async def make_arena(
    session: Session,
    arena_service,
    max_random_features=10,
    features: List[Feature] = [],
):
    """Fixture to create an Arena object for testing."""
    ac = ArenaCreate(
        name="Test Arena",
        description="Test Arena",
        width=10,
        height=10,
        rules="Test Rules",
        winning_condition="Test Winning Condition",
        max_random_features=max_random_features,
        features=features,
    )
    arena, result = await arena_service.create(ac, session=session)
    assert result.success
    return arena


async def make_feature(
    session: Session,
    feature_service,
    name: str,
    description="test feature",
    position="0,0",
):
    fc = FeatureCreate(
        name=name,
        description=description,
        position=position,
        origin=FeatureOriginType.REQUIRED,
    )
    feature, result = await feature_service.create(fc, session=session)
    assert result.success
    return feature


async def make_strategy(
    session: Session,
    strategy_service,
    uuid_service: UUIDService,
    name: str,
    description="",
    role: RoleType = RoleType.ARENA,
):

    sc = StrategyCreate(
        name=name,
        personality=f"A clear and simple {role.value}, intending to make things easy to see, experiment and test",
        prompts=[],
        description=description,
        role=role,
    )
    strategy, result = await strategy_service.create(sc, session=session)
    assert result.success
    if role == RoleType.ARENA:
        strategy.prompts.append(
            StrategyPrompt(
                id=uuid_service.make_id(),
                strategy_id=strategy.id,
                key=PromptType.ARENA_GENERATE_FEATURES,
                prompt="#jinja:arena.base.generate_features",
            )
        )
    elif role == RoleType.ANNOUNCER:
        strategy.prompts.append(
            StrategyPrompt(
                id=uuid_service.make_id(),
                strategy_id=strategy.id,
                key=PromptType.ANNOUNCER_DESCRIBE_ARENA,
                prompt="#jinja:announcer.base.describe_arena",
            )
        )
        strategy.prompts.append(
            StrategyPrompt(
                id=uuid_service.make_id(),
                strategy_id=strategy.id,
                key=PromptType.ANNOUNCER_DESCRIBE_RESULTS,
                prompt="#jinja:announcer.base.describe_results",
            )
        )
    session.commit()
    return strategy


async def make_participant(
    session: Session, participant_service, role: RoleType, description=""
):
    pc = ParticipantCreate(
        name=f"test_participant_{role.value}",
        role=role,
        description=description or f"game participant for {role.value}",
        endpoint="channel://TEST_actor.agent.$AGENT_ID$",
        api_key="",
    )
    participant, result = await participant_service.create(pc, session=session)
    assert result.success
    return participant


async def make_agent(
    session: Session,
    agent_service,
    strategy_id: str,
    participant_id: str,
    name: str,
    model: str = "mistral-small",
):
    ac = AgentCreate(
        model=model,
        strategy_id=strategy_id,
        participant_id=participant_id,
        name=name,
    )
    agent, result = await agent_service.create(ac, session=session)
    assert result.success
    return agent


async def make_agent_set(
    session: Session,
    agent_service,
    participant_service,
    strategy_service,
    uuid_service,
    name: str,
    model: str = "mistral-small",
    role: RoleType = RoleType.ANNOUNCER,
):
    """
    Create the participant, strategy and agent, returning the participant.
    """
    participant = await make_participant(session, participant_service, role)
    strategy = await make_strategy(
        session, strategy_service, uuid_service, name, name, role
    )
    _ = await make_agent(
        session, agent_service, strategy.id, participant.id, name, model
    )
    return participant


async def add_contest_agents_to_contest(
    session: Session,
    contest,
    agent_service,
    participant_service,
    strategy_service,
    uuid_service,
):
    """
    Create the arena, announcer, judge and player agents.
    """
    arena_participant = await make_agent_set(
        session,
        agent_service,
        participant_service,
        strategy_service,
        uuid_service,
        "arena",
        role=RoleType.ARENA,
    )
    announcer_participant = await make_agent_set(
        session,
        agent_service,
        participant_service,
        strategy_service,
        uuid_service,
        "announcer",
        role=RoleType.ANNOUNCER,
    )
    judge_participant = await make_agent_set(
        session,
        agent_service,
        participant_service,
        strategy_service,
        uuid_service,
        "judge",
        role=RoleType.JUDGE,
    )
    player1_participant = await make_agent_set(
        session,
        agent_service,
        participant_service,
        strategy_service,
        uuid_service,
        "player1",
        role=RoleType.PLAYER,
    )
    player2_participant = await make_agent_set(
        session,
        agent_service,
        participant_service,
        strategy_service,
        uuid_service,
        "player2",
        role=RoleType.PLAYER,
    )
    contest.participants.extend(
        [
            arena_participant,
            announcer_participant,
            judge_participant,
            player1_participant,
            player2_participant,
        ]
    )
    session.commit()
    return {
        "arena": arena_participant,
        "announcer": announcer_participant,
        "judge": judge_participant,
        "player1": player1_participant,
        "player2": player2_participant,
    }
