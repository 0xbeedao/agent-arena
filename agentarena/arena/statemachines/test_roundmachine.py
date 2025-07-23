import json
import pytest

from agentarena.arena.models import Arena, PlayerActionCreate
from agentarena.arena.models import Contest
from agentarena.arena.models import ContestState
from agentarena.arena.models import Participant
from agentarena.arena.statemachines.conftest import (
    make_contest,
    add_contest_agents_to_contest,
    make_feature,
)
from agentarena.arena.statemachines.round_machine import RoundMachine
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.constants import (
    ContestRoundState,
    JobResponseState,
    PromptType,
    RoleType,
)
from agentarena.arena.statemachines.conftest import make_arena
from nats.aio.msg import Msg

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
    logger,
):
    with round_service.get_session() as session:
        test_arena = await make_arena(session, arena_service)
        test_contest = await make_contest(session, contest_service, test_arena)
        round = await round_service.create_round(
            test_contest.id, 0, session, state=ContestRoundState.IN_PROGRESS
        )
        round.narrative = "This is the first round, the arena has been set up with a base at 1,1 and a flag at 5,5"
        session.commit()
        machine = RoundMachine(
            round,
            feature_service=feature_service,
            judge_result_service=judge_result_service,
            message_broker=message_broker,
            session=session,
            player_action_service=player_action_service,
            player_state_service=player_state_service,
            view_service=view_service,
            log=logger,
            auto_advance=False,
        )
        await machine.activate_initial_state()  # type: ignore
        assert machine.current_state.id == ContestRoundState.IN_PROGRESS.value


@pytest.mark.asyncio
async def test_round_prompting(
    contest_service,
    agent_service,
    participant_service,
    strategy_service,
    uuid_service,
    arena_service,
    feature_service,
    round_service,
    judge_result_service,
    player_action_service,
    player_state_service,
    view_service,
    message_broker,
    logger,
):
    with round_service.get_session() as session:
        base_feature = await make_feature(
            session, feature_service, "base", position="8,8"
        )
        flag_feature = await make_feature(
            session, feature_service, "flag", position="1,9"
        )
        test_arena = await make_arena(
            session, arena_service, features=[base_feature, flag_feature]
        )
        test_contest = await make_contest(
            session,
            contest_service,
            test_arena,
            player_positions='["1,1", "5,5"]',
            player_inventories="[[], []]",
        )
        agents = await add_contest_agents_to_contest(
            session,
            test_contest,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
        )

        round = await round_service.create_round(
            test_contest.id, 0, session, state=ContestRoundState.ROUND_PROMPTING
        )
        round.narrative = "This is the first round, the arena has been set up with a base at 8,8 and a flag at 1,9, player1 is at 1,1 and player2 is at 5,5"
        session.commit()

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

        machine = RoundMachine(
            round,
            feature_service=feature_service,
            judge_result_service=judge_result_service,
            message_broker=message_broker,
            session=session,
            player_action_service=player_action_service,
            player_state_service=player_state_service,
            view_service=view_service,
            log=logger,
            auto_advance=False,
        )
        await machine.activate_initial_state()  # type: ignore
        await sub1.unsubscribe()
        await sub2.unsubscribe()
        assert machine.current_state.id == ContestRoundState.ROUND_PROMPTING.value
        assert player1_called
        assert player2_called

        # were actions created?
        assert len(round.player_actions) == 2
        assert round.player_actions[0].participant_id == agents["player1"].id
        assert round.player_actions[0].action == "move"
        assert round.player_actions[0].target == "1,2"
        assert round.player_actions[0].narration == "I'm moving to 1,2"
        assert round.player_actions[0].memories == "I'm moving to 1,2"
        assert round.player_actions[1].participant_id == agents["player2"].id
        assert round.player_actions[1].action == "move"
        assert round.player_actions[1].target == "5,6"
        assert round.player_actions[1].narration == ""
        assert round.player_actions[1].memories == ""


@pytest.mark.asyncio
async def test_judging_actions(
    contest_service,
    agent_service,
    participant_service,
    strategy_service,
    uuid_service,
    arena_service,
    feature_service,
    round_service,
    judge_result_service,
    player_action_service,
    player_state_service,
    view_service,
    message_broker,
    logger,
):
    with round_service.get_session() as session:
        base_feature = await make_feature(
            session, feature_service, "base", position="8,8"
        )
        flag_feature = await make_feature(
            session, feature_service, "flag", position="1,9"
        )
        test_arena = await make_arena(
            session, arena_service, features=[base_feature, flag_feature]
        )
        test_contest = await make_contest(
            session,
            contest_service,
            test_arena,
            player_positions='["1,1", "5,5"]',
            player_inventories="[[], []]",
        )
        agents = await add_contest_agents_to_contest(
            session,
            test_contest,
            agent_service,
            participant_service,
            strategy_service,
            uuid_service,
        )

        round = await round_service.create_round(
            test_contest.id, 0, session, state=ContestRoundState.JUDGING_ACTIONS
        )
        round.narrative = "This is the first round, the arena has been set up with a base at 8,8 and a flag at 1,9, player1 is at 1,1 and player2 is at 5,5"
        ac1 = PlayerActionCreate(
            participant_id=agents["player1"].id,
            contestround_id=round.id,
            action="move",
            narration="I'm moving to 1,2",
            memories="I'm moving to 1,2",
            target="1,2",
        )
        action1, success = await player_action_service.create(ac1, session)
        assert success
        ac2 = PlayerActionCreate(
            participant_id=agents["player2"].id,
            contestround_id=round.id,
            action="move",
            narration="Woohoo!",
            memories="",
            target="5,6",
        )
        action2, success = await player_action_service.create(ac2, session)
        assert success
        round.player_actions.append(action1)
        round.player_actions.append(action2)
        session.commit()

        judge_call_count = 0
        judge_channel = agents["judge"].channel_prompt(
            PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT, "request", "*"
        )

        async def judge_responder(msg: Msg):
            nonlocal judge_call_count
            judge_call_count += 1
            if judge_call_count == 1:
                judgement = {
                    "result": "player successfully moved to 1,2, score: 10",
                    "reason": "simple success",
                    "narration": "a successful move!",
                    "memories": "player started at 1,1",
                }
            else:
                judgement = {
                    "result": "player successfully moved to 5,6, score: 10",
                    "reason": "simple success",
                    "narration": "a successful move!",
                    "memories": "player started at 5,5",
                }
            response = JobResponse(
                job_id=msg.subject.split(".")[-1],
                state=JobResponseState.COMPLETE,
                data=json.dumps(judgement),
            )
            await message_broker.send_response(msg.reply, response)

        sub = await message_broker.client.subscribe(judge_channel, cb=judge_responder)

        machine = RoundMachine(
            round,
            feature_service=feature_service,
            judge_result_service=judge_result_service,
            message_broker=message_broker,
            session=session,
            player_action_service=player_action_service,
            player_state_service=player_state_service,
            view_service=view_service,
            log=logger,
            auto_advance=False,
        )
        await machine.activate_initial_state()  # type: ignore
        await sub.unsubscribe()
        assert machine.current_state.id == ContestRoundState.JUDGING_ACTIONS.value
        assert judge_call_count == 2

        # were judge results created?
        assert len(round.judge_results) == 2
        assert round.judge_results[0].participant_id == agents["player1"].id
        assert (
            round.judge_results[0].result
            == "player successfully moved to 1,2, score: 10"
        )
        assert round.judge_results[0].reason == "simple success"
        assert round.judge_results[0].narration == "a successful move!"
        assert round.judge_results[0].memories == "player started at 1,1"
        assert round.judge_results[1].participant_id == agents["player2"].id
        assert (
            round.judge_results[1].result
            == "player successfully moved to 5,6, score: 10"
        )
        assert round.judge_results[1].reason == "simple success"
        assert round.judge_results[1].narration == "a successful move!"
        assert round.judge_results[1].memories == "player started at 5,5"
