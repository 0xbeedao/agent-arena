import json

import pytest
from nats.aio.msg import Msg

from agentarena.arena.models import ContestState
from agentarena.arena.statemachines.conftest import add_contest_agents_to_contest
from agentarena.arena.statemachines.conftest import make_arena
from agentarena.arena.statemachines.conftest import make_contest
from agentarena.arena.statemachines.contest_machine import ContestMachine
from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import JobResponseState
from agentarena.models.constants import PromptType
from agentarena.models.public import JobResponse


@pytest.mark.asyncio
async def test_initial_state(
    contest_service,
    arena_service,
    feature_service,
    round_service,
    judge_result_service,
    player_action_service,
    player_state_service,
    view_service,
    message_broker,
    uuid_service,
    logger,
):
    with contest_service.get_session() as session:
        test_arena = await make_arena(session, arena_service)
        test_contest = await make_contest(session, contest_service, test_arena)
        machine = ContestMachine(
            test_contest,
            message_broker,
            feature_service,
            judge_result_service,
            player_action_service,
            player_state_service,
            round_service,
            session,
            uuid_service,
            view_service,
            logger,
            auto_advance=False,
        )
        await machine.activate_initial_state()  # type: ignore
        assert machine.current_state.id == ContestState.STARTING.value
        assert len(test_contest.rounds) == 0
        assert test_contest.state == ContestState.STARTING.value
        assert test_contest.current_round == 0
        assert test_contest.winner_id is None
        assert test_contest.updated_at is not None
        assert test_contest.created_at is not None
        assert test_contest.updated_at >= test_contest.created_at


@pytest.mark.asyncio
async def test_role_call(
    contest_service,
    arena_service,
    agent_service,
    participant_service,
    strategy_service,
    feature_service,
    round_service,
    judge_result_service,
    player_action_service,
    player_state_service,
    view_service,
    message_broker,
    uuid_service,
    logger,
):
    with contest_service.get_session() as session:
        test_arena = await make_arena(session, arena_service)
        test_contest = await make_contest(
            session, contest_service, test_arena, state=ContestState.ROLE_CALL
        )
        agents = await add_contest_agents_to_contest(
            session,
            test_contest,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
        )
        session.commit()
        ok = JobResponse(
            job_id=uuid_service.make_id(),
            state=JobResponseState.COMPLETE,
            data=json.dumps({"ok": True}),
        )

        async def ok_cb(msg: Msg):
            called.append(msg.subject)
            await message_broker.send_response(msg.reply, ok)

        channels = [p.channel("request.health.*") for p in test_contest.participants]
        subs = []
        called = []
        for channel in channels:
            sub = await message_broker.client.subscribe(channel, cb=ok_cb)
            subs.append(sub)

        machine = ContestMachine(
            test_contest,
            message_broker,
            feature_service,
            judge_result_service,
            player_action_service,
            player_state_service,
            round_service,
            session,
            uuid_service,
            view_service,
            logger,
            auto_advance=False,
        )
        await machine.activate_initial_state()  # type: ignore
        for sub in subs:
            await sub.unsubscribe()
            sub = None

        assert machine.current_state.id == ContestState.ROLE_CALL.value
        assert len(test_contest.rounds) == 0
        assert len(called) == len(channels), "Expected all channels to be called"
        assert len(channels) >= 4, "Expected at least 4 participants"
        # check that all channels in called are unique
        assert len(set(called)) == len(called), "Expected all channels to be called"
        # contest is set for next state
        assert test_contest.state == ContestState.SETUP_ARENA.value


@pytest.mark.asyncio
async def test_setup_arena(
    contest_service,
    arena_service,
    agent_service,
    participant_service,
    strategy_service,
    feature_service,
    round_service,
    judge_result_service,
    player_action_service,
    player_state_service,
    view_service,
    message_broker,
    uuid_service,
    logger,
):
    with contest_service.get_session() as session:
        test_arena = await make_arena(session, arena_service)
        test_contest = await make_contest(
            session, contest_service, test_arena, state=ContestState.SETUP_ARENA
        )
        test_contest.player_positions = json.dumps(["1,1", "9,9"])
        agents = await add_contest_agents_to_contest(
            session,
            test_contest,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
        )
        session.commit()

        machine = ContestMachine(
            test_contest,
            message_broker,
            feature_service,
            judge_result_service,
            player_action_service,
            player_state_service,
            round_service,
            session,
            uuid_service,
            view_service,
            logger,
            auto_advance=False,
        )
        await machine.activate_initial_state()  # type: ignore
        assert machine.current_state.id == ContestState.SETUP_ARENA.value
        assert len(test_contest.rounds) == 1
        assert test_contest.state == ContestState.SETUP_ARENA.value
        assert test_contest.current_round == 0
        assert machine.has_setup_machine()
        assert machine._setup_machine is not None
        assert machine._setup_machine.current_state.id == ContestRoundState.CREATING_ROUND.value

        # test that if we cycle the setup machine, it advances to the next state in the setup machine
        # which is "creating_round"
        await machine.advance_state("test event")
        assert machine.current_state.id == ContestState.SETUP_ARENA.value
        assert len(test_contest.rounds) == 1
        assert test_contest.state == ContestState.SETUP_ARENA.value
        assert machine.has_setup_machine()
        assert machine._setup_machine is not None
        assert (
            machine._setup_machine.current_state.id
            == ContestRoundState.ADDING_FIXED_FEATURES.value
        )
        assert machine._setup_machine.contest_round is not None
        assert machine._setup_machine.contest_round.id == test_contest.rounds[0].id


@pytest.mark.asyncio
async def test_in_round_0(
    contest_service,
    arena_service,
    agent_service,
    participant_service,
    strategy_service,
    feature_service,
    round_service,
    judge_result_service,
    player_action_service,
    player_state_service,
    view_service,
    message_broker,
    uuid_service,
    logger,
):
    with contest_service.get_session() as session:
        test_arena = await make_arena(session, arena_service)
        test_contest = await make_contest(
            session, contest_service, test_arena, state=ContestState.IN_ROUND
        )
        test_contest.player_positions = json.dumps(["1,1", "9,9"])
        test_round = await round_service.create_round(
            test_contest.id, 0, session, state=ContestRoundState.IN_PROGRESS
        )
        test_contest.rounds.append(test_round)
        agents = await add_contest_agents_to_contest(
            session,
            test_contest,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
        )
        session.commit()

        machine = ContestMachine(
            test_contest,
            message_broker,
            feature_service,
            judge_result_service,
            player_action_service,
            player_state_service,
            round_service,
            session,
            uuid_service,
            view_service,
            logger,
            auto_advance=False,
        )
        await machine.activate_initial_state()  # type: ignore
        assert machine.current_state.id == ContestState.IN_ROUND.value
        assert len(test_contest.rounds) == 1
        assert test_contest.state == ContestState.IN_ROUND.value
        assert test_contest.current_round == 0
        assert not machine.has_setup_machine()
        assert machine.has_round_machine()
        assert machine._round_machine is not None
        assert (
            machine._round_machine.current_state.id
            == ContestRoundState.IN_PROGRESS.value
        )

        # test that if we cycle the round machine, it advances to the next state in the round machine
        # which is "round_prompting"
        # we need to set up the mocks to handle this

        player1_called = False
        player2_called = False

        player1_channel = agents["player1"].channel_prompt(
            PromptType.PLAYER_PLAYER_ACTION, "request", "*"
        )
        player2_channel = agents["player2"].channel_prompt(
            PromptType.PLAYER_PLAYER_ACTION, "request", "*"
        )

        async def player1_responder(msg: Msg):
            job_id = msg.subject.split(".")[-1]
            response = JobResponse(
                job_id=job_id,
                state=JobResponseState.COMPLETE,
                data=json.dumps(
                    {
                        "action": "move",
                        "target": "1,2",
                        "narration": "I'm moving to 1,2",
                        "memories": "I'm moving to 1,2",
                    }
                ),
            )
            await message_broker.send_response(msg.reply, response)
            nonlocal player1_called
            player1_called = True

        async def player2_responder(msg: Msg):
            job_id = msg.subject.split(".")[-1]
            response = JobResponse(
                job_id=job_id,
                state=JobResponseState.COMPLETE,
                data=json.dumps({"action": "move", "target": "5,6"}),
            )
            await message_broker.send_response(msg.reply, response)
            nonlocal player2_called
            player2_called = True

        sub1 = await message_broker.client.subscribe(
            player1_channel, cb=player1_responder
        )
        sub2 = await message_broker.client.subscribe(
            player2_channel, cb=player2_responder
        )

        await machine.advance_state("test event")
        await sub1.unsubscribe()
        await sub2.unsubscribe()
        assert machine.current_state.id == ContestState.IN_ROUND.value
        assert len(test_contest.rounds) == 1
        assert test_contest.state == ContestState.IN_ROUND.value
        assert test_contest.current_round == 0
        assert not machine.has_setup_machine()
        assert machine.has_round_machine()
        assert machine._round_machine is not None
        assert (
            machine._round_machine.current_state.id
            == ContestRoundState.ROUND_PROMPTING.value
        )
        assert player1_called
        assert player2_called
        assert len(test_round.player_actions) == 2
        # remaining tests for round prompting in `test_roundmachine.py`
