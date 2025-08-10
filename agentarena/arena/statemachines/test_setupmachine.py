"""
Tests for the SetupMachine class.
"""

import pytest
from nats.aio.msg import Msg

from agentarena.arena.models import Contest
from agentarena.arena.statemachines.setup_machine import SetupMachine
from agentarena.clients.message_broker import MessageBroker
from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import JobResponseState
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.public import JobResponse

from .conftest import ONE_FEATURE
from .conftest import make_agent_set
from .conftest import make_arena
from .conftest import make_contest
from .conftest import make_feature


@pytest.mark.asyncio
async def test_initialization(
    contest_service,
    arena_service,
    feature_service,
    round_service,
    message_broker,
    logger,
):
    """Test that the SetupMachine initializes correctly."""
    with round_service.get_session() as session:
        test_arena = await make_arena(session, arena_service)
        test_contest = await make_contest(session, contest_service, test_arena)
        # Create a setup machine
        setup_machine = SetupMachine(
            test_contest,
            feature_service=feature_service,
            round_service=round_service,
            message_broker=message_broker,
            log=logger,
            auto_advance=False,
        )
        await setup_machine.activate_initial_state()  # type: ignore

        # Check initial state
        assert setup_machine.current_state.id == ContestRoundState.IDLE.value
        assert setup_machine.current_state.initial
        assert not setup_machine.current_state.final

        # Check that the contest was set correctly
        assert setup_machine.contest == test_contest


@pytest.mark.asyncio
async def test_transition_to_creating_round(
    contest_service,
    arena_service,
    feature_service,
    round_service,
    view_service,
    message_broker,
    logger,
):
    """Test transition from idle to creating_round.
    Sometimes fails when run in parallel with other tests with "event_loop" closed.
    """
    with round_service.get_session() as session:
        test_arena = await make_arena(session, arena_service)
        test_contest = await make_contest(session, contest_service, test_arena)
        assert type(test_contest) == Contest
        # Create a setup machine
        setup_machine = SetupMachine(
            test_contest,
            message_broker=message_broker,
            feature_service=feature_service,
            round_service=round_service,
            view_service=view_service,
            session=session,
            log=logger,
            auto_advance=False,
        )
        await setup_machine.activate_initial_state()  # type: ignore
        session.refresh(test_contest)
        assert len(test_contest.rounds) == 0

        # Transition to generating_positions
        await setup_machine.cycle("test_event")

        # Check current state
        session.refresh(test_contest)
        assert setup_machine.current_state.id == ContestRoundState.CREATING_ROUND.value

        # Check that the round was created
        assert len(test_contest.rounds) == 1
        assert test_contest.rounds[0].round_no == 0
        assert test_contest.rounds[0].state == ContestRoundState.CREATING_ROUND.value
        assert not setup_machine.current_state.initial
        assert not setup_machine.current_state.final


@pytest.mark.asyncio
async def test_adding_fixed_features(
    contest_service,
    arena_service,
    feature_service,
    round_service,
    view_service,
    message_broker,
    logger,
):
    """Test adding fixed features to the contest."""
    with round_service.get_session() as session:
        base_feature = await make_feature(session, feature_service, "base")
        tree_feature = await make_feature(
            session, feature_service, "tree", position="1,1"
        )
        test_arena = await make_arena(
            session, arena_service, features=[base_feature, tree_feature]
        )
        assert len(test_arena.features) == 2
        test_contest = await make_contest(session, contest_service, test_arena)

        round = await round_service.create_round(
            test_contest.id, 0, session, state=ContestRoundState.ADDING_FIXED_FEATURES
        )
        assert len(round.features) == 0
        assert len(test_contest.rounds) == 1
        session.commit()
        setup_machine = SetupMachine(
            test_contest,
            message_broker=message_broker,
            feature_service=feature_service,
            round_service=round_service,
            view_service=view_service,
            session=session,
            log=logger,
            auto_advance=False,
        )
        await setup_machine.activate_initial_state()  # type: ignore
        assert (
            setup_machine.current_state.id
            == ContestRoundState.ADDING_FIXED_FEATURES.value
        )
        assert not setup_machine.current_state.initial
        assert not setup_machine.current_state.final
        session.refresh(round)

        # did we add the features?
        assert len(round.features) == 2


@pytest.mark.asyncio
async def test_generating_features(
    contest_service,
    arena_service,
    feature_service,
    participant_service,
    strategy_service,
    agent_service,
    uuid_service,
    round_service,
    view_service,
    message_broker: MessageBroker,
    logger,
):
    """Test adding fixed features to the contest."""
    with round_service.get_session() as session:
        test_arena = await make_arena(session, arena_service, max_random_features=4)
        assert len(test_arena.features) == 0
        test_contest = await make_contest(session, contest_service, test_arena)

        round = await round_service.create_round(
            test_contest.id, 0, session, state=ContestRoundState.GENERATING_FEATURES
        )
        assert len(round.features) == 0
        assert len(test_contest.rounds) == 1
        session.commit()

        arena_participant = await make_agent_set(
            session,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
            "arena",
            role=RoleType.ARENA,
        )
        test_contest.participants.append(arena_participant)
        session.commit()

        request_channel = arena_participant.channel_prompt(
            PromptType.ARENA_GENERATE_FEATURES, "request", "*"
        )
        request_key = request_channel[:-2]

        responder_called = False

        async def responder(msg: Msg):

            parts = msg.subject.split(".")
            key = ".".join(parts[:-1])
            job_id = parts[-1]
            response = JobResponse(
                job_id=job_id,
                state=JobResponseState.COMPLETE,
                data=ONE_FEATURE,
            )
            await message_broker.send_response(msg.reply, response)
            assert key == request_key
            nonlocal responder_called
            responder_called = True

        sub = await message_broker.client.subscribe(
            request_channel,
            cb=responder,
        )

        # Create a setup machine
        setup_machine = SetupMachine(
            test_contest,
            message_broker=message_broker,
            feature_service=feature_service,
            round_service=round_service,
            view_service=view_service,
            session=session,
            log=logger,
            auto_advance=False,
        )
        await setup_machine.activate_initial_state()  # type: ignore
        await sub.unsubscribe()
        assert (
            setup_machine.current_state.id
            == ContestRoundState.GENERATING_FEATURES.value
        )

        assert not setup_machine.current_state.initial
        assert not setup_machine.current_state.final
        assert responder_called
        session.refresh(round)

        # did we add the features?
        assert len(round.features) == 1


@pytest.mark.asyncio
async def test_describing_setup(
    contest_service,
    arena_service,
    feature_service,
    round_service,
    view_service,
    message_broker,
    logger,
    participant_service,
    strategy_service,
    agent_service,
    uuid_service,
):
    with round_service.get_session() as session:
        base_feature = await make_feature(session, feature_service, "base")
        tree_feature = await make_feature(
            session, feature_service, "tree", position="1,1"
        )
        test_arena = await make_arena(
            session, arena_service, features=[base_feature, tree_feature]
        )
        assert len(test_arena.features) == 2
        test_contest = await make_contest(session, contest_service, test_arena)

        round = await round_service.create_round(
            test_contest.id, 0, session, state=ContestRoundState.DESCRIBING_SETUP
        )
        round.features.append(base_feature)
        round.features.append(tree_feature)
        session.commit()
        assert len(round.features) == 2
        assert len(test_contest.rounds) == 1

        announcer_participant = await make_agent_set(
            session,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
            "arena",
            role=RoleType.ANNOUNCER,
        )
        test_contest.participants.append(announcer_participant)
        session.commit()

        request_channel = announcer_participant.channel_prompt(
            PromptType.ANNOUNCER_DESCRIBE_ARENA, "request", "*"
        )
        request_key = request_channel[:-2]

        responder_called = False

        async def responder(msg: Msg):
            parts = msg.subject.split(".")
            key = ".".join(parts[:-1])
            job_id = parts[-1]
            response = JobResponse(
                job_id=job_id,
                state=JobResponseState.COMPLETE,
                data="test description",
            )
            await message_broker.send_response(msg.reply, response)
            assert key == request_key
            nonlocal responder_called
            responder_called = True

        sub = await message_broker.client.subscribe(
            request_channel,
            cb=responder,
        )

        setup_machine = SetupMachine(
            test_contest,
            message_broker=message_broker,
            feature_service=feature_service,
            round_service=round_service,
            view_service=view_service,
            session=session,
            log=logger,
            auto_advance=False,
        )
        await setup_machine.activate_initial_state()  # type: ignore
        await sub.unsubscribe()
        assert (
            setup_machine.current_state.id == ContestRoundState.DESCRIBING_SETUP.value
        )
        assert not setup_machine.current_state.initial
        assert not setup_machine.current_state.final
        session.refresh(round)
        assert responder_called
        assert round.narrative == "test description"


@pytest.mark.asyncio
async def test_full_lifecycle(
    contest_service,
    arena_service,
    feature_service,
    round_service,
    message_broker,
    agent_service,
    participant_service,
    strategy_service,
    uuid_service,
    view_service,
    logger,
):
    """Test that the SetupMachine goes through the full lifecycle."""
    with round_service.get_session() as session:
        test_arena = await make_arena(session, arena_service, max_random_features=4)
        test_contest = await make_contest(session, contest_service, test_arena)
        announcer_participant = await make_agent_set(
            session,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
            "arena",
            role=RoleType.ANNOUNCER,
        )
        test_contest.participants.append(announcer_participant)
        arena_participant = await make_agent_set(
            session,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
            "arena",
            role=RoleType.ARENA,
        )
        test_contest.participants.append(arena_participant)
        session.commit()

        # setup the responders

        describe_channel = announcer_participant.channel_prompt(
            PromptType.ANNOUNCER_DESCRIBE_ARENA, "request", "*"
        )
        describe_key = describe_channel[:-2]

        describe_responder_called = False

        async def describe_responder(msg: Msg):
            parts = msg.subject.split(".")
            key = ".".join(parts[:-1])
            job_id = parts[-1]
            response = JobResponse(
                job_id=job_id,
                state=JobResponseState.COMPLETE,
                data="test description",
            )
            await message_broker.send_response(msg.reply, response)
            assert key == describe_key
            nonlocal describe_responder_called
            describe_responder_called = True

        describe_sub = await message_broker.client.subscribe(
            describe_channel,
            cb=describe_responder,
        )

        generate_channel = arena_participant.channel_prompt(
            PromptType.ARENA_GENERATE_FEATURES, "request", "*"
        )
        generate_key = generate_channel[:-2]

        generate_responder_called = False

        async def generate_responder(msg: Msg):
            parts = msg.subject.split(".")
            key = ".".join(parts[:-1])
            job_id = parts[-1]
            response = JobResponse(
                job_id=job_id,
                state=JobResponseState.COMPLETE,
                data=ONE_FEATURE,
            )
            await message_broker.send_response(msg.reply, response)
            assert key == generate_key
            nonlocal generate_responder_called
            generate_responder_called = True

        gen_sub = await message_broker.client.subscribe(
            generate_channel,
            cb=generate_responder,
        )

        # Create a setup machine
        setup_machine = SetupMachine(
            test_contest,
            feature_service=feature_service,
            round_service=round_service,
            message_broker=message_broker,
            view_service=view_service,
            session=session,
            log=logger,
            auto_advance=True,
        )

        await setup_machine.activate_initial_state()  # type: ignore
        assert setup_machine.current_state.id == ContestRoundState.IDLE.value
        assert setup_machine.current_state.initial
        assert not setup_machine.current_state.final

        await setup_machine.cycle("test_event")

        await gen_sub.unsubscribe()
        await describe_sub.unsubscribe()

        assert generate_responder_called
        assert describe_responder_called

        # Check state
        assert setup_machine.current_state.id == ContestRoundState.SETUP_COMPLETE.value
        assert setup_machine.current_state.final
        assert len(test_contest.rounds) == 1
        assert test_contest.rounds[0].state == ContestRoundState.SETUP_COMPLETE.value
        assert test_contest.rounds[0].narrative == "test description"
        assert len(test_contest.rounds[0].features) == 1
        assert test_contest.rounds[0].features[0].name == "test feature"
        assert test_contest.rounds[0].features[0].description == "test description"
        assert test_contest.rounds[0].features[0].position == "4,4"
