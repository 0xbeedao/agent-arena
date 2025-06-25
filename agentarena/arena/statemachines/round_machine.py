import asyncio
from codecs import decode
from datetime import datetime

from nats.aio.msg import Msg
from sqlmodel import Field
from sqlmodel import Session
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import ContestRound
from agentarena.arena.models import JudgeResultCreate
from agentarena.arena.models import Participant
from agentarena.arena.models import PlayerAction
from agentarena.arena.models import PlayerActionCreate
from agentarena.arena.services.view_service import ViewService
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import Subscriber
from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.job import CommandJob
from agentarena.models.requests import ParticipantRequest
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
    awaiting_actions = State(ContestRoundState.AWAITING_ACTIONS.value)
    judging_actions = State(ContestRoundState.JUDGING_ACTIONS.value)
    awaiting_judging_actions = State(ContestRoundState.AWAITING_JUDGING_ACTIONS.value)
    applying_effects = State(ContestRoundState.APPLYING_EFFECTS.value)
    describing_results = State(ContestRoundState.DESCRIBING_RESULTS.value)
    presenting_results = State(ContestRoundState.PRESENTING_RESULTS.value)
    round_complete = State(ContestRoundState.ROUND_COMPLETE.value, final=True)
    round_fail = State(ContestRoundState.ROUND_FAIL.value, final=True)

    cycle = (
        in_progress.to(round_prompting)
        | round_prompting.to(awaiting_actions)
        | awaiting_actions.to(judging_actions)
        | judging_actions.to(awaiting_judging_actions)
        | awaiting_judging_actions.to(applying_effects)
        | applying_effects.to(describing_results)
        | describing_results.to(presenting_results)
        | presenting_results.to(round_complete)
    )

    step_failed = (
        round_prompting.to(round_fail)
        | awaiting_actions.to(round_fail)
        | judging_actions.to(round_fail)
        | awaiting_judging_actions.to(round_fail)
        | applying_effects.to(round_fail)
        | describing_results.to(round_fail)
        | presenting_results.to(round_fail)
    )

    def __init__(
        self,
        contest_round: ContestRound,
        judge_result_service: ModelService,
        playeraction_service: ModelService[PlayerAction, PlayerActionCreate] = Field(
            description="Player Action Service"
        ),
        message_broker: MessageBroker = Field(description="Message Broker"),
        view_service: ViewService = Field(description="View Service"),
        session: Session = Field(description="Session"),
        log: ILogger = Field(description="Logger"),
    ):
        """Initialize the round machine."""
        self.action_service = playeraction_service
        self.completion_channel = f"arena.contest.{contest_round.contest.id}.round.{contest_round.round_no}.complete"
        self.contest_round = contest_round
        self.message_broker = message_broker
        self.view_service = view_service
        self.session = session
        self.subscriber = Subscriber()
        self.log = log.bind(contest_round=contest_round.id)
        self.judge_result_service = judge_result_service
        super().__init__(start_value=contest_round.state.value)
        assert self.message_broker is not None, "Message broker is not set"
        self.pending_actions = set()
        self.pending_judging_actions = set()

    async def on_enter_in_progress(self):
        """Called when entering the InProgress state."""
        await self.cycle("in_progress")

    async def on_enter_round_prompting(self):
        """Called when entering the RoundPrompting state."""
        players = self.contest_round.contest.get_role(RoleType.PLAYER)

        if not players:
            self.log.error("No players found for round prompting")
            await self.cycle("round_fail")
            return

        for player in players:
            await self.send_player_prompt(player)
        self.log.info("sent player prompts")
        await self.cycle("From round_prompting to awaiting_actions")

    async def on_enter_awaiting_actions(self):
        """Called when entering the AwaitingActions state."""
        self.log.info("entering awaiting actions")

    async def on_enter_judging_actions(self):
        """Called when entering the JudgingActions state."""
        for action in self.contest_round.player_actions:
            await self.send_judging_action_prompt(action)
        self.log.info("sent judging actions prompts")
        await self.cycle("judging_actions")

    async def on_enter_applying_effects(self):
        """Called when entering the ApplyingEffects state."""
        await self.send_apply_effects_prompt()
        self.log.info("sent applying effects prompt")
        await self.cycle("applying_effects")

    async def on_enter_describing_results(self):
        """Called when entering the DescribingResults state."""
        await self.cycle("describing_results")

    async def on_enter_presenting_results(self):
        """Called when entering the PresentingResults state."""
        await self.cycle("presenting_results")  # to describing_results

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
                await self.cycle("step_failed")
                return
            result = extract_obj_from_json(raw)
            if not result:
                log.error("No result in message")
                await self.cycle("step_failed")
                return
            log.info("received apply effects message", result=result)
            asyncio.create_task(self.cycle("describing_results"))
        except Exception as e:
            log.error("Exception in handle_apply_effects_message", error=e)
            await self.cycle("step_failed")

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
                await self.cycle("step_failed")
                return
            result = extract_obj_from_json(raw)
            if not result:
                log.error("No result in message")
                await self.cycle("step_failed")
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
                await self.cycle("step_failed")
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
            await self.cycle("step_failed")

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
                await self.cycle("step_failed")
                return
            action = extract_obj_from_json(raw)
            if not action:
                log.error("No action in message")
                await self.step_failed(player_id)
                return
            log.info("received action", action=action)
            valid = "action" in action and action.get("action", "") != ""
            if not valid:
                log.error("Invalid action", action=action)
                await self.step_failed(player_id)
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
                await self.step_failed(player_id)
                return
            log.info("created action", action=created.id)
            self.pending_actions.remove(player_id)
            # transition to judging actions if all actions are received and we are in the awaiting actions state
            if (
                self.current_state.id == ContestRoundState.AWAITING_ACTIONS.value
                and len(self.pending_actions) == 0
            ):
                log.info("all actions received, transitioning to judging actions")
                asyncio.create_task(self.cycle("judging_actions"))
        except Exception as e:
            log.error("Failed to extract text response", error=e)
            await self.step_failed(player_id)
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
        log.info("sending apply effects prompt")
        channel = f"arena.contest.{self.contest_round.contest.id}.round.{self.contest_round.round_no}.apply_effects.prompt"
        await self.subscriber.subscribe(
            self.message_broker.client,
            channel,
            log,
            cb=self.handle_apply_effects_message,
        )
        log.info(f"subscribed", channel=channel)
        contest = self.contest_round.contest
        contest_json = contest.get_public().model_dump_json()
        req = ParticipantRequest(
            job_id=job_id,
            command=PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT,
            data=f'{{"contest":{contest_json}}}',
            message="judging action",
        )
        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=judge.url("request"),
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
        contest_json = contest.get_public().model_dump_json()
        action_json = action.get_public().model_dump_json()
        player_json = action.player.get_public().model_dump_json()
        req = ParticipantRequest(
            job_id=job_id,
            command=PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT,
            data=f'{{"contest":{contest_json},"action":{action_json},"player":{player_json}}}',
            message="judging action",
        )
        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=judge.url("request"),
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
        contest_json = view.model_dump_json()
        req = ParticipantRequest(
            job_id=job_id,
            command=PromptType.PLAYER_PLAYER_ACTION,
            data='{"contest":' + contest_json + "}",
            message="player action",
        )
        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=player.url("request"),
        )
        self.pending_actions.add(player.id)
        await self.message_broker.send_job(job)

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
