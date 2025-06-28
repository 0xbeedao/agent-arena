"""
ContestDTO controller for the Agent Arena application.
Handles HTTP requests for contest operations.
"""

from codecs import decode
from datetime import datetime
from typing import Dict
from typing import List
from typing import Tuple

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from nats.aio.msg import Msg
from sqlmodel import Field
from sqlmodel import Session

from agentarena.arena.models import Contest, ContestRound
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import ContestPublic
from agentarena.arena.models import ContestState
from agentarena.arena.models import ContestUpdate
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
from agentarena.arena.statemachines.contest_machine import ContestMachine
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import SubscribingService
from agentarena.models.constants import JobResponseState
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.constants import ContestRoundState
from agentarena.models.public import JobResponse
from agentarena.models.requests import ControllerRequest
from agentarena.models.requests import ParticipantRequest


class ContestController(
    ModelController[Contest, ContestCreate, ContestUpdate, ContestPublic],
    SubscribingService,
):

    def __init__(
        self,
        base_path: str = "/api",
        feature_service: ModelService[Feature, FeatureCreate] = Field(),
        message_broker: MessageBroker = Field(
            description="Message broker service",
        ),
        model_service: ModelService[Contest, ContestCreate] = Field(
            description="The contest service"
        ),
        judge_result_service: ModelService[JudgeResult, JudgeResultCreate] = Field(
            description="The judge result service"
        ),
        participant_service: ModelService[Participant, ParticipantCreate] = Field(
            description="The feature service"
        ),
        playeraction_service: ModelService[PlayerAction, PlayerActionCreate] = Field(
            description="The player action service"
        ),
        player_state_service: ModelService[PlayerState, PlayerStateCreate] = Field(
            description="The player state service"
        ),
        round_service: RoundService = Field(description="The round service"),
        template_service: JinjaRenderer = Field(description="The template service"),
        view_service: ViewService = Field(description="The view service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.feature_service = feature_service
        self.participant_service = participant_service
        self.playeraction_service = playeraction_service
        self.player_state_service = player_state_service
        self.round_service = round_service
        assert message_broker is not None, "Message broker is not set"
        self.message_broker = message_broker
        self.view_service = view_service
        self.judge_result_service = judge_result_service
        to_subscribe = [
            ("arena.contest.request", self.handle_request),
            ("arena.contest.*.contestflow.*", self.handle_flow),
        ]
        super().__init__(
            base_path=base_path,
            model_service=model_service,
            model_public=ContestPublic,
            model_name="contest",
            template_service=template_service,
            logging=logging,
        )
        SubscribingService.__init__(self, to_subscribe, self.log)
        self.log.info(f"Templates: {template_service.env.list_templates()}")

    async def clone_contest(self, contest_id: str, session: Session) -> ContestPublic:
        """
        Clone a contest, including all non-failed rounds and their children.
        """
        contest, response = await self.model_service.get(contest_id, session)
        if not contest or not response.success:
            raise HTTPException(status_code=404, detail=response.model_dump())

        clone = Contest(
            id=self.model_service.uuid_service.make_id(),
            arena_id=contest.arena_id,
            current_round=0,
            player_inventories=contest.player_inventories,
            player_positions=contest.player_positions,
            state=ContestState.CREATED,
        )
        session.add(clone)
        session.commit()

        for p in contest.participants:
            clone.participants.append(p)
        session.commit()

        # Deep clone rounds and children if not in a fail state
        fail_states = {
            ContestRoundState.FAIL,
            ContestRoundState.ROUND_FAIL,
            ContestRoundState.SETUP_FAIL,
        }
        for round in contest.rounds:
            if round.state in fail_states:
                continue
            new_round_id = self.model_service.uuid_service.make_id()
            new_round = ContestRound(
                id=new_round_id,
                contest_id=clone.id,
                round_no=round.round_no,
                narrative=round.narrative,
                state=round.state,
            )
            session.add(new_round)
            session.flush()

            # Features
            for f in round.features:
                new_feature = Feature(
                    id=self.model_service.uuid_service.make_id(),
                    arena_id=f.arena_id,
                    contestround_id=new_round_id,
                    name=f.name,
                    description=f.description,
                    position=f.position,
                    origin=f.origin,
                )
                session.add(new_feature)
                new_round.features.append(new_feature)

            # Judge Results
            for jr in round.judge_results:
                new_jr = JudgeResult(
                    id=self.model_service.uuid_service.make_id(),
                    contestround_id=new_round_id,
                    participant_id=jr.participant_id,
                    narration=jr.narration,
                    memories=jr.memories,
                    result=jr.result,
                    reason=jr.reason,
                )
                session.add(new_jr)
                new_round.judge_results.append(new_jr)

            # Player States
            for ps in round.player_states:
                new_ps = PlayerState(
                    id=self.model_service.uuid_service.make_id(),
                    participant_id=ps.participant_id,
                    contestround_id=new_round_id,
                    position=ps.position,
                    inventory=list(ps.inventory) if ps.inventory else [],
                    health=ps.health,
                    score=ps.score,
                )
                session.add(new_ps)
                new_round.player_states.append(new_ps)

            # Player Actions
            for pa in round.player_actions:
                new_pa = PlayerAction(
                    id=self.model_service.uuid_service.make_id(),
                    participant_id=pa.participant_id,
                    contestround_id=new_round_id,
                    action=pa.action,
                    narration=pa.narration,
                    memories=pa.memories,
                    target=pa.target,
                )
                session.add(new_pa)
                new_round.player_actions.append(new_pa)

            # Round Stats (optional, 1:1)
            if round.round_stats:
                rs = round.round_stats
                new_rs = type(rs)(
                    id=self.model_service.uuid_service.make_id(),
                    contestround_id=new_round_id,
                    actions_count=rs.actions_count,
                    duration_ms=rs.duration_ms,
                    metrics_json=dict(rs.metrics_json) if rs.metrics_json else {},
                )
                session.add(new_rs)
                new_round.round_stats = new_rs

            clone.rounds.append(new_round)
        session.commit()
        return clone.get_public()

    # @router.post("/contest", response_model=Dict[str, str])
    async def create_contest(self, req: ContestCreate, session: Session) -> Contest:
        """
        Create a new contest.

        Args:
            contest: The contest configuration
            model_service: The contest service

        Returns:
            A dictionary with the ID of the created contest
        """
        if not req.participant_ids:
            raise HTTPException(status_code=422, detail="Need at least 1 participant")

        participants = await self.participant_service.get_by_ids(
            req.participant_ids, session
        )

        if len(participants) != len(req.participant_ids):
            session.rollback()
            raise HTTPException(
                status_code=422, detail="Could not get all participants"
            )

        contest, result = await self.model_service.create(req, session)
        if not result.success:
            raise HTTPException(status_code=422, detail=result.model_dump())
        if not contest:
            raise HTTPException(status_code=422, detail="internal error")

        for p in participants:
            contest.participants.append(p)

        session.commit()
        return contest

    async def handle_flow(self, msg: Msg):
        """
        Handle incoming messages for contest flow updates.

        Args:
            msg: The message containing the flow data
        """
        self.log.info("Handling contest flow message", msg=msg)
        if not msg.data:
            self.log.error("No data in message, ignoring")
            return

        try:
            parts = msg.subject.split(".")
            contest_id = parts[2]
            state = parts[4]

            log = self.log.bind(contest=contest_id, state=state, method="handle_flow")
            if state == ContestState.STARTING.value:

                log.info("Contest starting flow message received")
                with self.model_service.get_session() as session:
                    contest, response = await self.model_service.get(
                        contest_id, session
                    )
                    if not response.success:
                        log.error("Failed to get contest", error=response.validation)
                        return

                    if not contest:
                        log.error("Contest not found")
                        return

                # Create and run the contest machine in the current event loop
                await self.run_contest_machine(contest_id, log)

        except Exception as e:
            self.log.error("Failed to handle contest flow message", error=str(e))

    async def handle_request(self, msg: Msg):
        """
        Handle incoming messages for contest requests.

        Args:
            msg: The message containing the request data
        """
        self.log.info("Handling contest request", msg=msg)
        sane = True
        message = ""
        request = None
        contest_id = ""
        if not msg.data:
            self.log.error("No data in message, ignoring")
            sane = False
        else:
            try:
                request: ControllerRequest | None = (
                    ControllerRequest.model_validate_json(
                        decode(msg.data, "utf-8", "unicode_escape")
                    )
                )
            except Exception as e:
                self.log.error(
                    "Failed to parse request data", error=str(e), data=msg.data
                )
                sane = False

        if sane and request:
            contest_id = request.target_id
            if not contest_id:
                message = "No contest_id in request"
                sane = False
            else:
                log = self.log.bind(contest=contest_id, action=request.action)
                action = request.action
                if action == "start":
                    sane, message = await self.handle_start_message(
                        msg, contest_id, log
                    )
                else:
                    message = "Ignoring request"
                    sane = False

        if sane and contest_id:
            response = JobResponse(
                job_id=contest_id,
                message=message,
                state=JobResponseState.COMPLETE,
                url=f"/api/contest/{contest_id}",
            )
        else:
            response = JobResponse(
                job_id=contest_id or "unknown",
                message=message or "Unknown error",
                state=JobResponseState.FAIL,
                url=f"/api/contest/{contest_id or 'unknown'}",
            )

        await self.message_broker.publish_response(msg, response)

    async def handle_start_message(
        self, msg: Msg, contest_id: str, log: ILogger
    ) -> Tuple[bool, str]:
        log.info("Contest start request received", msg=msg)
        with self.model_service.get_session() as session:
            try:
                result = await self.start_contest(contest_id, session)
                message = "Contest started successfully"
                log.info(message, result=result)
                # await msg.ack()
                return True, (
                    result.model_dump_json()
                    if isinstance(result, ContestPublic)
                    else result
                )
            except HTTPException as e:
                log.error("Failed to start contest", error=str(e))
                return False, e.detail

    async def prompt(
        self, contest_id: str, target_id: str, prompt_type: PromptType, session: Session
    ) -> ParticipantRequest:
        """
        Get the prompt the contest will use with a given prompt type.
        """
        contest, response = await self.model_service.get(contest_id, session)
        if not contest or not response.success:
            raise HTTPException(status_code=404, detail=response.model_dump())
        if prompt_type == PromptType.PLAYER_PLAYER_ACTION:
            players = contest.participants_by_role()[RoleType.PLAYER]
            player = next((p for p in players if p.id == target_id), None)
            if not player:
                raise HTTPException(
                    status_code=404, detail=f"Player {target_id} not found"
                )
            view = self.view_service.get_contest_view(contest, player)
            view_json = view.model_dump_json()
            req = ParticipantRequest(
                job_id=self.model_service.uuid_service.make_id(),
                command=prompt_type,
                data='{"contest":' + view_json + "}",
                message=f"prompt for {player.name}",
            )
            return req
        elif prompt_type == PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT:
            judges = contest.get_role(RoleType.JUDGE)
            if not judges:
                raise HTTPException(status_code=404, detail="No judges found")
            judge = judges[0]

            action, response = await self.playeraction_service.get(target_id, session)
            if not action or not response.success:
                raise HTTPException(
                    status_code=404, detail=f"No action found for {target_id}"
                )
            contest_json = contest.get_public().model_dump_json()
            action_json = action.get_public().model_dump_json()
            req = ParticipantRequest(
                job_id=self.model_service.uuid_service.make_id(),
                command=prompt_type,
                data=f'{{"contest":{contest_json},"action":{action_json}}}',
                message=f"prompt for {judge.name}",
            )
            return req
        elif prompt_type == PromptType.JUDGE_APPLY_EFFECTS:
            judges = contest.get_role(RoleType.JUDGE)
            if not judges:
                raise HTTPException(status_code=404, detail="No judges found")
            judge = judges[0]
            contest_json = contest.get_public().model_dump_json()
            req = ParticipantRequest(
                job_id=self.model_service.uuid_service.make_id(),
                command=prompt_type,
                data=f'{{"contest":{contest_json}}}',
                message=f"prompt for {judge.name}",
            )
            return req

        raise HTTPException(
            status_code=404, detail=f"Prompt type {prompt_type} not found"
        )

    async def run_contest_machine(self, contest_id: str, log: ILogger):
        """Run the contest machine in the current event loop context"""
        machine = ContestMachine(
            contest_id=contest_id,
            message_broker=self.message_broker,
            feature_service=self.feature_service,
            playeraction_service=self.playeraction_service,
            player_state_service=self.player_state_service,
            round_service=self.round_service,
            uuid_service=self.model_service.uuid_service,
            view_service=self.view_service,
            log=log,
            judge_result_service=self.judge_result_service,
        )
        await machine.activate_initial_state()  # type: ignore
        log = log.bind(state=machine.current_state.id)
        if machine.current_state.initial:
            log.info("Machine is in initial state, starting contest")
            await machine.start_contest("start_contest")
        else:
            log.info("Machine already started, not restarting")

        log.info(
            "started contest machine",
            contest_id=contest_id,
            state=machine.current_state.id,
        )

    # @router.post("/contest/{contest_id}/start", response_model=Dict[str, str])
    async def start_contest(self, contest_id: str, session: Session) -> ContestPublic:
        """
        Start a contest, and returns the ID of the started contest, with everything set up for first round.

        Args:
            contest_id: The ID of the contest to start
            model_service: The contest service

        Returns:
            A dictionary with the ID of the started contest
        """
        boundlog = self.log.bind(contest_id=contest_id)
        boundlog.info("starting contest")
        contest, response = await self.model_service.get(contest_id, session)
        if not response.success:
            boundlog.error("failed to get contest")
            raise HTTPException(status_code=404, detail=response.model_dump())
        if not contest:
            boundlog.error("failed to get contest data")
            raise HTTPException(status_code=404, detail="internal error")

        participants = [p for p in contest.participants]
        if len(participants) < 4:
            boundlog.error("No agents in arena, raising error")
            raise HTTPException(
                status_code=422,
                detail="Arena needs at least 4 agents: player, announcer, judge, and participant",
            )

        roles = contest.participants_by_role()

        for role in RoleType:
            key = role.value
            if roles[key] is None or len(roles[key]) == 0:
                boundlog.error(f"No agents in arena for role {key}, raising error")
                raise HTTPException(
                    status_code=422, detail=f"Arena needs at least one {key} agent"
                )

        # sanity check done, let's start

        # Set contest state to STARTING
        # and update start time
        if contest.state == ContestState.STARTING:
            contest.start_time = int(datetime.now().timestamp())
        await self.model_service.update(contest_id, contest, session)
        await self.message_broker.send_message(
            # should be STARTING, so that the machine starts
            f"arena.contest.{contest_id}.contestflow.{ContestState.STARTING.value}",
            contest_id,
        )

        return contest.get_public()

    def get_router(self):
        prefix = self.base_path
        self.log.info("setting up routes", path=prefix)
        router = APIRouter(prefix=prefix, tags=["arena"])

        @router.post("/", response_model=Contest)
        async def create(req: ContestCreate = Body(...)):
            with self.model_service.get_session() as session:
                rv = await self.create_contest(req, session)
                self.log.info("created contest", contest_id=rv.id, state=rv.state)
                return rv

        @router.post(
            "/{contest_id}/prompt/{prompt_type}/{target_id}",
            response_model=ParticipantRequest,
        )
        async def prompt(contest_id: str, prompt_type: PromptType, target_id: str):
            with self.model_service.get_session() as session:
                return await self.prompt(contest_id, target_id, prompt_type, session)

        @router.post("/{contest_id}/clone", response_model=ContestPublic)
        async def clone(contest_id: str):
            with self.model_service.get_session() as session:
                return await self.clone_contest(contest_id, session)

        @router.post("/{contest_id}/start", response_model=ContestPublic)
        async def start(contest_id: str):
            with self.model_service.get_session() as session:
                return await self.start_contest(contest_id, session)

        @router.get("/{obj_id}.{format}", response_model=str)
        async def get_md(obj_id: str, format: str = "md"):
            with self.model_service.get_session() as session:
                return await self.get_model_with_format(obj_id, session, format=format)

        @router.get("/{obj_id}", response_model=ContestPublic)
        async def get(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.get_model(obj_id, session)

        @router.get("", response_model=List[ContestPublic])
        async def list_all():
            with self.model_service.get_session() as session:
                return await self.get_model_list(session)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.delete_model(obj_id, session)

        return router
