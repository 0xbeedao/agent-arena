import asyncio
from codecs import decode
from datetime import datetime

from nats.aio.msg import Msg
from sqlmodel import Session
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import ContestRound
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import JudgeResultCreate
from agentarena.arena.models import Participant
from agentarena.arena.models import PlayerAction
from agentarena.arena.models import PlayerActionCreate
from agentarena.arena.models import PlayerState
from agentarena.arena.models import PlayerStateCreate
from agentarena.arena.services.view_service import ViewService
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import Subscriber
from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.job import CommandJob
from agentarena.models.requests import ActionRequestPayload, ContestRequestPayload
from agentarena.models.requests import ContestRoundPayload
from agentarena.models.requests import ParticipantActionRequest
from agentarena.models.requests import ParticipantContestRequest
from agentarena.models.requests import ParticipantContestRoundRequest
from agentarena.util.response_parsers import extract_obj_from_json


class RoundMachine(StateMachine):
    """
    Round machine for handling the flow of a single round.

    States:
    - RoundPrompting: Initial state for prompting
    - AwaitingActions: State for awaiting actions
    - JudgingActions: State for judging actions
    - ApplyingEffects: State for applying effects
    - DescribingResults: State for describing results
    - PresentingResults: State for presenting results
    """

    in_progress = State(ContestRoundState.IN_PROGRESS.value, initial=True)
    round_prompting = State(ContestRoundState.ROUND_PROMPTING.value)
    judging_actions = State(ContestRoundState.JUDGING_ACTIONS.value)
    applying_effects = State(ContestRoundState.APPLYING_EFFECTS.value)
    describing_results = State(ContestRoundState.DESCRIBING_RESULTS.value)
    round_complete = State(ContestRoundState.ROUND_COMPLETE.value, final=True)
    round_fail = State(ContestRoundState.ROUND_FAIL.value, final=True)

    cycle = (
        in_progress.to(round_prompting)
        | round_prompting.to(judging_actions)
        | judging_actions.to(applying_effects)
        | applying_effects.to(describing_results)
        | describing_results.to(round_complete)
    )

    step_failed = (
        round_prompting.to(round_fail)
        | judging_actions.to(round_fail)
        | applying_effects.to(round_fail)
        | describing_results.to(round_fail)
    )

    def __init__(
        self,
        contest_round: ContestRound,
        feature_service: ModelService[Feature, FeatureCreate],
        judge_result_service: ModelService,
        message_broker: MessageBroker,
        session: Session,
        player_action_service: ModelService[PlayerAction, PlayerActionCreate],
        player_state_service: ModelService[PlayerState, PlayerStateCreate],
        view_service: ViewService,
        log: ILogger,
    ):
        """Initialize the round machine."""
        assert isinstance(contest_round, ContestRound)
        assert message_broker is not None, "Message broker is not set"
        self.action_service = player_action_service
        self.completion_channel = f"arena.contest.{contest_round.contest.id}.round.{contest_round.round_no}.complete"
        self.contest_round = contest_round
        self.feature_service = feature_service
        self.message_broker = message_broker
        self.player_state_service = player_state_service
        self.view_service = view_service
        self.session = session
        self.subscriber = Subscriber()
        self.log = log.bind(contest_round=contest_round.id)
        self.judge_result_service = judge_result_service
        super().__init__(start_value=contest_round.state.value)
        self.pending_actions = set()
        self.pending_judging_actions = set()

    async def on_enter_in_progress(self):
        """Called when entering the InProgress state."""
        await self.cycle("in_progress")

    async def on_enter_round_prompting(self):
        """Called when entering the RoundPrompting state.

        This state is a holding state, waiting for the player actions to be received.
        The message handler will transition to the next state.
        """
        players = self.contest_round.contest.get_role(RoleType.PLAYER)

        if not players:
            self.log.error("No players found for round prompting")
            await self.cycle("round_fail")
            return

        for player in players:
            await self.send_player_prompt(player)
        self.log.info("sent player prompts")

    async def on_enter_judging_actions(self):
        """Called when entering the JudgingActions state.

        This state is a holding state, waiting for the judge results to be received.
        The message handler will transition to the next state.
        """
        for action in self.contest_round.player_actions:
            await self.send_judging_action_prompt(action)
        self.log.info("sent judging actions prompts")

    async def on_enter_applying_effects(self):
        """Called when entering the ApplyingEffects state.

        This state is a holding state, waiting for the apply effects message to be received.
        The message handler will transition to the next state.
        """
        await self.send_apply_effects_prompt()
        self.log.info("sent applying effects prompt")

    async def on_enter_describing_results(self):
        """Called when entering the DescribingResults state."""
        await self.send_describing_results_prompt()
        self.log.info("sent describing results prompt")

    async def on_enter_presenting_results(self):
        """Called when entering the PresentingResults state."""

    async def on_enter_round_fail(self, message: str):
        """Called when entering the RoundFail state."""
        # TODO: Would be nice to save the message to the round
        self.log.error(f"Round failed: {message}")

    async def handle_apply_effects_message(self, msg: Msg):
        """Handle a apply effects message."""
        msg_parts = msg.subject.split(".")
        contest_id = msg_parts[2]
        round_no = msg_parts[4]
        log = self.log.bind(contest_id=contest_id, round_no=round_no)
        log.info("received apply effects message", msg=msg)
        await self.subscriber.unsubscribe(msg.subject, self.log)
        try:
            raw = decode(msg.data, "utf-8", "unicode_escape")
            if not raw:
                log.error("No data in message")
                await self.step_failed("no data in apply effects message")
                return
            result = extract_obj_from_json(raw)
            if not result:
                log.error("No result in message")
                await self.step_failed("no result in apply effects message")
                return
            log.info("parsed apply effects message", result=result)
            player_state_map = {}
            for player_state in self.contest_round.player_states:
                player_state_map[player_state.participant_id] = player_state

            for updated_player in result.get("players", []):
                player_id = updated_player.get("id")
                current_player = player_state_map.get(player_id)
                if not current_player:
                    log.error(
                        "Player in updates from judge not found", player_id=player_id
                    )
                    continue
                if "position" in updated_player:
                    current_player.position = updated_player.get("position")
                if "health" in updated_player:
                    current_player.health = updated_player.get("health")
                if "score" in updated_player:
                    current_player.score = updated_player.get("score")
                if "inventory" in updated_player:
                    current_player.inventory = updated_player.get("inventory")
                self.session.add(current_player)

            feature_map = {}
            for feature in self.contest_round.features:
                feature_map[feature.id] = feature
            for updated_feature in result.get("features", []):
                feature_id = updated_feature.get("id")
                current_feature = feature_map.get(feature_id)
                if not current_feature:
                    log.error(
                        "Feature in updates from judge not found", feature_id=feature_id
                    )
                    continue
                if "description" in updated_feature:
                    current_feature.description = updated_feature.get("description")
                if "position" in updated_feature:
                    current_feature.position = updated_feature.get("position")
                self.session.add(current_feature)

            self.session.commit()
            log.info("updated player states and features")

            asyncio.create_task(self.cycle("apply effects done"))
        except Exception as e:
            log.error("Exception in handle_apply_effects_message", error=e)
            await self.step_failed("error in apply effects message")

    async def handle_judging_action_message(self, msg: Msg):
        """Handle a judging action message."""
        msg_parts = msg.subject.split(".")
        player_id = msg_parts[-2]
        log = self.log.bind(player_id=player_id)
        log.info("received judging action message", msg=msg)
        await self.subscriber.unsubscribe(msg.subject, self.log)
        try:
            raw = decode(msg.data, "utf-8", "unicode_escape")
            if not raw:
                log.error("No data in message")
                await self.step_failed("no data in judging action message")
                return
            result = extract_obj_from_json(raw)
            if not result:
                log.error("No result in message")
                await self.step_failed("no result in judging action message")
                return
            log.info("received judging action", result=result)
            jc = JudgeResultCreate(
                contestround_id=self.contest_round.id,
                participant_id=player_id,
                narration=result.get("narration", ""),
                memories=result.get("memories", ""),
                result=result.get("result", ""),
                reason=result.get("reason", ""),
            )
            created, result = await self.judge_result_service.create(jc, self.session)
            if not created or not result.success:
                log.error("Failed to create judge result", error=result)
                await self.step_failed("failed to create judge result")
                return
            self.pending_judging_actions.remove(player_id)
            if not self.pending_judging_actions:
                log.info(
                    "all judging actions received, transitioning to applying effects"
                )
                asyncio.create_task(self.cycle("applying_effects"))
            else:
                log.info(
                    "not all judging actions received, staying in awaiting judging actions",
                    state=self.current_state.id,
                    pending_judging_actions=self.pending_judging_actions,
                )
        except Exception as e:
            log.error("Exception in handle_judging_action_message", error=e)
            await self.step_failed("error in judging action message")

    async def handle_player_prompt_message(self, msg: Msg):
        """Handle a player prompt message."""
        msg_parts = msg.subject.split(".")
        player_id = msg_parts[-2]
        log = self.log.bind(player_id=player_id)
        log.info("received player prompt message", msg=msg)
        await self.subscriber.unsubscribe(msg.subject, log)
        try:
            raw = decode(msg.data, "utf-8", "unicode_escape")
            if not raw:
                log.error("No data in message")
                asyncio.create_task(self.step_failed("no data in message"))
                return
            action = extract_obj_from_json(raw)
            if not action:
                log.error("No action in message")
                asyncio.create_task(
                    self.step_failed(f"no action in message for player {player_id}")
                )
                return
            log.info("received action", action=action)
            valid = "action" in action and action.get("action", "") != ""
            if not valid:
                log.error("Invalid action", action=action)
                asyncio.create_task(
                    self.step_failed(f"invalid action for player {player_id}")
                )
                return
            pa = PlayerActionCreate(
                participant_id=player_id,
                contestround_id=self.contest_round.id,
                action=action.get(
                    "action", "invalid action, player failed to respond."
                ),
                narration=action.get("narration", ""),
                memories=action.get("memories", ""),
                target=action.get("target", ""),
            )
            created, result = await self.action_service.create(pa, self.session)
            if not created or not result.success:
                log.error("Failed to create action", error=result)
                asyncio.create_task(
                    self.step_failed(f"failed to create action for player {player_id}")
                )
                return
            log.info("created action", action=created.id)
            self.pending_actions.remove(player_id)
            # transition to judging actions if all actions are received and we are in the awaiting actions state
            if len(self.pending_actions) == 0:
                log.info("all actions received, transitioning to judging actions")
                asyncio.create_task(self.cycle("judging_actions"))
        except Exception as e:
            log.error("Failed to extract text response", error=e)
            asyncio.create_task(
                self.step_failed(
                    f"failed to extract text response for player {player_id}"
                )
            )
            return

    async def send_apply_effects_prompt(self):
        """Send a prompt to apply effects."""
        job_id = self.message_broker.uuid_service.make_id()
        log = self.log.bind(job_id=job_id)
        judges = self.contest_round.contest.get_role(RoleType.JUDGE)
        if not judges:
            log.error("No judges found for apply effects prompt")
            return
        judge = judges[0]
        channel, _ = await self.subscribe_to_apply_effects_message(log)
        log.info("sending apply effects prompt")
        contest = self.contest_round.contest
        req = ParticipantContestRequest(
            command=PromptType.JUDGE_APPLY_EFFECTS,
            data=ContestRequestPayload(contest=contest.get_public()),
            message="judge apply effects of actions",
        )
        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=judge.url(f"{job_id}/{PromptType.JUDGE_APPLY_EFFECTS.value}"),
        )
        await self.message_broker.send_job(job)

    async def send_judging_action_prompt(self, action: PlayerAction):
        log = self.log
        log.info("sending judging action prompt", action=action)
        job_id = self.message_broker.uuid_service.make_id()
        channel = f"arena.contest.{self.contest_round.contest.id}.round.{self.contest_round.round_no}.judge_action.{action.participant_id}.prompt"
        judges = self.contest_round.contest.get_role(RoleType.JUDGE)
        if not judges:
            log.error("No judges found for judging action prompt")
            return
        judge = judges[0]
        log.info(f"subscribed", job_id=job_id, channel=channel)
        await self.subscriber.subscribe(
            self.message_broker.client,
            channel,
            log,
            cb=self.handle_judging_action_message,
        )
        contest = self.contest_round.contest
        payload = ActionRequestPayload(
            contest=contest.get_public(),
            action=action.get_public(),
            player=action.player.get_public(),
        )
        req = ParticipantActionRequest(
            command=PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT,
            data=payload,
            message="judge player action",
        )
        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=judge.url(f"{job_id}/{PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT.value}"),
        )
        self.pending_judging_actions.add(action.participant_id)
        await self.message_broker.send_job(job)

    async def send_player_prompt(self, player: Participant):
        """Send a prompt to a player."""
        log = self.log.bind(player=player.name)
        log.info("sending player prompt")
        job_id = self.message_broker.uuid_service.make_id()
        channel = f"arena.contest.{self.contest_round.contest.id}.round.{self.contest_round.round_no}.player.{player.id}.prompt"
        log.info(f"subscribed", job_id=job_id, channel=channel)
        await self.subscriber.subscribe(
            self.message_broker.client,
            channel,
            log,
            cb=self.handle_player_prompt_message,
        )
        view = self.view_service.get_contest_view(self.contest_round.contest, player)
        req = ParticipantContestRequest(
            command=PromptType.PLAYER_PLAYER_ACTION,
            data=ContestRequestPayload(contest=view),
            message="player action",
        )
        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=player.url(f"{job_id}/{PromptType.PLAYER_PLAYER_ACTION.value}"),
        )
        self.pending_actions.add(player.id)
        await self.message_broker.send_job(job)

    async def subscribe_to_apply_effects_message(self, log: ILogger):
        channel = f"arena.contest.{self.contest_round.contest.id}.round.{self.contest_round.round_no}.apply_effects.prompt"
        sub = await self.subscriber.subscribe(
            self.message_broker.client,
            channel,
            log,
            cb=self.handle_apply_effects_message,
        )
        log.info(f"subscribed", channel=channel)
        return channel, sub

    async def send_describing_results_prompt(self):
        """Send a prompt to the announcer to describe round results."""
        job_id = self.message_broker.uuid_service.make_id()
        log = self.log.bind(job_id=job_id)
        announcers = self.contest_round.contest.get_role(RoleType.ANNOUNCER)
        if not announcers:
            log.error("No announcer found for describing results")
            return
        announcer = announcers[0]
        channel, _ = await self.subscribe_to_describing_results_message(log)
        log.info("sending describing results prompt")
        payload = ContestRoundPayload(
            contest=self.contest_round.contest.get_public(),
            round=self.contest_round.get_public(),
        )
        req = ParticipantContestRoundRequest(
            command=PromptType.ANNOUNCER_DESCRIBE_RESULTS,
            data=payload,
            message="describe round results",
        )
        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=announcer.url(
                f"{job_id}/{PromptType.ANNOUNCER_DESCRIBE_RESULTS.value}"
            ),
        )
        await self.message_broker.send_job(job)

    async def subscribe_to_describing_results_message(self, log: ILogger):
        channel = f"arena.contest.{self.contest_round.contest.id}.round.{self.contest_round.round_no}.describing_results.prompt"
        sub = await self.subscriber.subscribe(
            self.message_broker.client,
            channel,
            log,
            cb=self.handle_describing_results_message,
        )
        log.info(f"subscribed", channel=channel)
        return channel, sub

    async def handle_describing_results_message(self, msg: Msg):
        """Handle the message from the announcer agent with the round ending narrative."""
        log = self.log.bind(msg=msg.subject)
        log.info("Received describing results message", msg=msg.subject)
        await self.subscriber.unsubscribe(msg.subject, self.log)
        try:
            raw = decode(msg.data, "utf-8", "unicode_escape")
            result = extract_obj_from_json(raw)
            if not result:
                log.error("No result in describing results message")
                await self.step_failed("no result in describing results message")
                return
            narrative = (
                result.get("narrative")
                or result.get("description")
                or result.get("text")
            )
            if not narrative:
                log.error("No narrative in describing results message", result=result)
                await self.step_failed("no narrative in describing results message")
                return
            self.contest_round.ending_narrative = narrative
            self.contest_round.updated_at = int(datetime.now().timestamp())
            self.session.commit()
            log.info("Set ending_narrative for round", ending_narrative=narrative)
            asyncio.create_task(self.cycle("describing_results_done"))
        except Exception as e:
            log.error("Failed to handle describing results message", error=e)
            await self.step_failed("error in describing results message")

    async def on_enter_state(self, target, event):
        # update the round state
        self.contest_round.state = target.id
        self.contest_round.updated_at = int(datetime.now().timestamp())
        self.session.commit()

        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
            await self.message_broker.send_message(self.completion_channel, target.id)
            await self.subscriber.unsubscribe_all(self.log)
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
