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
from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.requests import ActionRequestPayload
from agentarena.models.requests import ContestRequestPayload
from agentarena.models.requests import ContestRoundPayload
from agentarena.models.requests import ParticipantActionRequest
from agentarena.models.requests import ParticipantContestRequest
from agentarena.models.requests import ParticipantContestRoundRequest
from agentarena.util.response_parsers import extract_obj_from_json
from agentarena.util.response_parsers import extract_text_response


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
        auto_advance: bool = True,
    ):
        """Initialize the round machine."""
        assert isinstance(contest_round, ContestRound)
        assert message_broker is not None, "Message broker is not set"
        self.action_service = player_action_service
        self.contest_round = contest_round
        self.feature_service = feature_service
        self.uuid_service = feature_service.uuid_service
        self.message_broker = message_broker
        self.player_state_service = player_state_service
        self.view_service = view_service
        self.session = session
        self.log = log.bind(contest_round=contest_round.id)
        self.judge_result_service = judge_result_service
        self.auto_advance = auto_advance
        super().__init__(start_value=contest_round.state.value)

    async def cycle_or_pause(self, event: str):
        if self.auto_advance:
            await self.cycle(event)
        else:
            self.log.info(
                "Pausing state machine",
                state=self.current_state_value,
            )

    async def on_enter_in_progress(self):
        """Called when entering the InProgress state."""
        await self.cycle_or_pause("in_progress")

    async def on_enter_round_prompting(self):
        """Called when entering the RoundPrompting state."""
        players = self.contest_round.contest.get_role(RoleType.PLAYER)

        if not players:
            self.log.error("No players found for round prompting")
            await self.cycle_or_pause("round_fail")
            return

        success = True
        error = ""
        for player in players:
            log = self.log.bind(player=player.name, player_id=player.id)
            msg: Msg = await self.get_player_action(player)
            log.info("received player prompt message", msg=msg)
            success, error = await self.handle_player_action(player, msg)
            if not success:
                log.error("failed to handle player action", error=error)
                break

        if success:
            self.log.info(
                "all player actions received, transitioning to judging actions"
            )
            await self.cycle_or_pause("round_prompting_done")
        else:
            await self.step_failed(error)

    async def on_enter_judging_actions(self):
        """Called when entering the JudgingActions state.

        This state is a holding state, waiting for the judge results to be received.
        The message handler will transition to the next state.
        """
        judges = self.contest_round.contest.get_role(RoleType.JUDGE)
        if not judges:
            self.log.error("No judges found for judging action prompt")
            await self.cycle_or_pause("round_fail")
            return
        judge = judges[0]

        success = True
        error = ""
        for action in self.contest_round.player_actions:
            log = self.log.bind(player=action.player.name, player_id=action.player.id)
            msg: Msg = await self.get_judging_action(judge, action)
            success, error = await self.handle_judging_action(action, msg)
            if not success:
                log.error("failed to handle judging action", error=error)
                break

        if success:
            self.log.info(
                "all judging actions received, transitioning to applying effects"
            )
            await self.cycle_or_pause("judging_actions_done")
        else:
            await self.step_failed(error)

    async def on_enter_applying_effects(self):
        """Called when entering the ApplyingEffects state.

        This state is a holding state, waiting for the apply effects message to be received.
        The message handler will transition to the next state.
        """
        judges = self.contest_round.contest.get_role(RoleType.JUDGE)
        if not judges:
            self.log.error("No judges found for applying effects")
            await self.step_failed("round_fail")
            return
        judge = judges[0]
        msg = await self.get_apply_effects(judge)
        success, error = await self.handle_apply_effects(msg)
        if not success:
            self.log.error("Failed to apply effects", error=error)
            await self.step_failed(error)
            return
        await self.cycle_or_pause("applying_effects_done")

    async def on_enter_describing_results(self):
        """Called when entering the DescribingResults state."""
        announcers = self.contest_round.contest.get_role(RoleType.ANNOUNCER)
        if not announcers:
            self.log.error("No announcers found for describing results")
            await self.step_failed("round_fail")
            return
        announcer = announcers[0]
        msg = await self.get_describing_results(announcer)
        success, error = await self.handle_describing_results(msg)
        if not success:
            self.log.error("Failed to describe results", error=error)
            await self.step_failed(error)
            return
        await self.cycle_or_pause("describing_results_done")

    async def on_enter_round_fail(self, message: str):
        """Called when entering the RoundFail state."""
        # TODO: Would be nice to save the message to the round
        self.log.error(f"Round failed: {message}")

    # ---- Message handlers ----

    async def get_player_action(self, player: Participant) -> Msg:
        """Send a prompt to a player."""
        log = self.log.bind(player=player.name, player_id=player.id)
        log.info("sending player prompt")

        job_id = self.uuid_service.make_id()
        channel = player.channel_prompt(
            PromptType.PLAYER_PLAYER_ACTION, "request", job_id
        )
        view = self.view_service.get_contest_view(self.contest_round.contest, player)
        req = ParticipantContestRequest(
            command=PromptType.PLAYER_PLAYER_ACTION,
            data=ContestRequestPayload(contest=view),
            message="player action",
        )
        return await self.message_broker.request_job(channel, req.model_dump_json())

    async def handle_player_action(
        self, player: Participant, msg: Msg
    ) -> tuple[bool, str]:
        """Handle a player prompt message. This is a response to a request for a player action."""
        player_id = player.id
        log = self.log.bind(player_id=player_id)
        log.info(
            "received player prompt message",
            prompt=PromptType.PLAYER_PLAYER_ACTION.value,
            msg=msg,
        )
        try:
            raw = decode(msg.data, "utf-8", "unicode_escape")
            if not raw:
                log.error("No data in message")
                asyncio.create_task(self.step_failed("no data in message"))
                return False, "no data in message"
            action = extract_obj_from_json(raw)
            if not action:
                log.error("No action in message")
                return False, "no action in message"
            log.info("received action", action=action)
            valid = "action" in action and action.get("action", "") != ""
            if not valid:
                log.error("Invalid action", action=action)
                return False, f"invalid action for player {player_id}"

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
                return False, f"failed to create action for player {player_id}"

            log.info("created action", action=created.id)
            return True, ""
        except Exception as e:
            log.error("Failed to handle player action", error=e)
            return False, f"failed to handle player action for player {player_id}"

    async def get_judging_action(self, judge: Participant, action: PlayerAction) -> Msg:
        """Send a prompt to a judge."""
        log = self.log.bind(
            action=PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT.value,
            judge=judge.name,
            judge_id=judge.id,
        )
        log.info("sending judging action prompt", action=action)
        job_id = self.uuid_service.make_id()
        channel = judge.channel_prompt(
            PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT, "request", job_id
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
        return await self.message_broker.request_job(channel, req.model_dump_json())

    async def handle_judging_action(
        self, action: PlayerAction, msg: Msg
    ) -> tuple[bool, str]:
        """Handle a judging action message."""
        log = self.log.bind(
            prompt=PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT.value,
            action=action.id,
            player=action.player.name,
            player_id=action.player.id,
        )
        log.info("received judging action message", msg=msg)
        try:
            raw = decode(msg.data, "utf-8", "unicode_escape")
            if not raw:
                log.error("No data in message")
                return False, "no data in message"
            result = extract_obj_from_json(raw)
            if not result:
                log.error("No result in message")
                return False, "no result in message"
            log.info("received judging action", result=result)
            jc = JudgeResultCreate(
                contestround_id=self.contest_round.id,
                participant_id=action.player.id,
                narration=result.get("narration", ""),
                memories=result.get("memories", ""),
                result=result.get("result", ""),
                reason=result.get("reason", ""),
            )
            created, result = await self.judge_result_service.create(jc, self.session)
            if not created or not result.success:
                log.error("Failed to create judge result", error=result)
                return False, "failed to create judge result"
            log.info("created judge result", judge_result=created.id)
        except Exception as e:
            log.error("Exception in handle_judging_action_message", error=e)
            return False, "error in judging action message"

        return True, ""

    async def get_apply_effects(self, judge: Participant) -> Msg:
        """Send a prompt to apply effects."""
        log = self.log.bind(
            prompt=PromptType.JUDGE_APPLY_EFFECTS.value,
            judge=judge.name,
            judge_id=judge.id,
        )
        log.info("sending apply effects prompt")
        contest = self.contest_round.contest
        req = ParticipantContestRequest(
            command=PromptType.JUDGE_APPLY_EFFECTS,
            data=ContestRequestPayload(contest=contest.get_public()),
            message="judge apply effects of actions",
        )
        job_id = self.uuid_service.make_id()
        channel = judge.channel_prompt(
            PromptType.JUDGE_APPLY_EFFECTS, "request", job_id
        )
        return await self.message_broker.request_job(channel, req.model_dump_json())

    async def handle_apply_effects(self, msg: Msg) -> tuple[bool, str]:
        """Handle a apply effects message."""
        log = self.log.bind(prompt=PromptType.JUDGE_APPLY_EFFECTS.value)
        log.info("received apply effects message", msg=msg)
        try:
            raw = decode(msg.data, "utf-8", "unicode_escape")
            if not raw:
                log.error("No data in message")
                return False, "no data in apply effects message"
            result = extract_obj_from_json(raw)
            if not result:
                log.error("No result in message")
                return False, "no result in apply effects message"
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

            return True, ""
        except Exception as e:
            log.error("Exception in handle_apply_effects", error=e)
            return False, "error in apply effects message"

    async def get_describing_results(self, announcer: Participant) -> Msg:
        """Send a prompt to the announcer to describe round results."""
        log = self.log.bind(
            prompt=PromptType.ANNOUNCER_DESCRIBE_RESULTS.value,
            announcer=announcer.name,
            announcer_id=announcer.id,
        )
        log.info("sending describing results prompt")
        job_id = self.uuid_service.make_id()
        channel = announcer.channel_prompt(
            PromptType.ANNOUNCER_DESCRIBE_RESULTS, "request", job_id
        )
        payload = ContestRoundPayload(
            contest=self.contest_round.contest.get_public(),
            round=self.contest_round.get_public(),
        )
        req = ParticipantContestRoundRequest(
            command=PromptType.ANNOUNCER_DESCRIBE_RESULTS,
            data=payload,
            message="describe round results",
        )
        return await self.message_broker.request_job(channel, req.model_dump_json())

    async def handle_describing_results(self, msg: Msg) -> tuple[bool, str]:
        """Handle the message from the announcer agent with the round ending narrative."""
        log = self.log.bind(prompt=PromptType.ANNOUNCER_DESCRIBE_RESULTS.value)
        log.info("received describing results message", msg=msg)
        try:
            raw = decode(msg.data, "utf-8", "unicode_escape")
            narrative = extract_text_response(raw)
            if not narrative:
                log.error("No narrative in describing results message")
                return False, "no narrative in describing results message"
            self.contest_round.ending_narrative = narrative
            self.contest_round.updated_at = int(datetime.now().timestamp())
            self.session.commit()
            log.info("Set ending_narrative for round", ending_narrative=narrative)
            return True, ""
        except Exception as e:
            log.error("Failed to handle describing results message", error=e)
            return False, "error in describing results message"

    async def on_enter_state(self, target, event):
        # update the round state
        self.contest_round.state = target.id
        self.contest_round.updated_at = int(datetime.now().timestamp())
        self.session.commit()

        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
