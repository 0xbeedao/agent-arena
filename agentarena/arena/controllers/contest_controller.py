"""
ContestDTO controller for the Agent Arena application.
Handles HTTP requests for contest operations.
"""

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

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import ContestPublic
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import ContestState
from agentarena.arena.models import ContestUpdate
from agentarena.arena.models import Participant
from agentarena.arena.models import ParticipantCreate
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import SubscribingService
from agentarena.models.constants import RoleType
from agentarena.models.job import ControllerRequest
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.statemachines.contestmachine import ContestMachine


class ContestController(
    ModelController[Contest, ContestCreate, ContestUpdate, ContestPublic],
    SubscribingService,
):

    def __init__(
        self,
        base_path: str = "/api",
        message_broker: MessageBroker = Field(
            description="Message broker service",
        ),
        model_service: ModelService[Contest, ContestCreate] = Field(
            description="The contest service"
        ),
        participant_service: ModelService[Participant, ParticipantCreate] = Field(
            description="The feature service"
        ),
        round_service: ModelService[ContestRound, ContestRoundCreate] = Field(
            description="The round service"
        ),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.participant_service = participant_service
        self.round_service = round_service
        self.message_broker = message_broker
        to_subscribe = [
            ("arena.contest.request", self.handle_request),
            ("arena.contest.*.flow.*", self.handle_flow),
        ]
        super().__init__(
            base_path=base_path,
            model_service=model_service,
            model_public=ContestPublic,
            model_name="contest",
            logging=logging,
        )
        SubscribingService.__init__(self, to_subscribe, self.log)

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
            raise HTTPException(status_code=422, detail=result.model_dump_json())
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

                    # Create the contest machine
                    machine = ContestMachine(
                        contest=contest,
                        message_broker=self.message_broker,
                        round_service=self.round_service,
                        uuid_service=self.model_service.uuid_service,
                        log=log,
                    )
                    await machine.activate_initial_state()  # type: ignore
                    await machine.start_contest("start_contest")
                    log.info(
                        "started contest machine",
                        contest_id=contest_id,
                        state=machine.current_state.id,
                    )

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
                    ControllerRequest.model_validate_json(msg.data.decode("utf-8"))
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
                channel="",
                state=JobResponseState.COMPLETE,
                url=f"/api/contest/{contest_id}",
            )
        else:
            response = JobResponse(
                job_id=contest_id or "unknown",
                message=message or "Unknown error",
                channel="",
                state=JobResponseState.FAIL,
                url=f"/api/contest/{contest_id or 'unknown'}",
            )

        await self.message_broker.publish_response(msg, response)

    async def handle_start_message(
        self, msg: Msg, contest_id: str, log: ILogger
    ) -> Tuple[bool, str]:
        log.info("Contest start request received")
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
            raise HTTPException(status_code=404, detail=response.validation)
        if not contest:
            boundlog.error("failed to get contest data")
            raise HTTPException(status_code=404, detail="internal error")

        if contest.state != ContestState.CREATED:
            boundlog.error(f"contest is not in CREATED state, was: {contest.state}")
            raise HTTPException(
                status_code=422, detail="Contest is not in CREATED state"
            )

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
        contest.state = ContestState.STARTING
        contest.start_time = int(datetime.now().timestamp())
        await self.model_service.update(contest_id, contest, session)
        await self.message_broker.send_message(
            f"arena.contest.{contest_id}.flow.{ContestState.STARTING.value}", contest_id
        )

        return ContestPublic.model_validate(contest)

    def get_router(self):
        prefix = self.base_path
        if not prefix.endswith(self.model_name):
            prefix = f"{prefix}/contest"
        self.log.info("setting up routes", path=prefix)
        router = APIRouter(prefix=prefix, tags=["arena"])

        @router.post("/", response_model=Contest)
        async def create(req: ContestCreate = Body(...)):
            with self.model_service.get_session() as session:
                rv = await self.create_contest(req, session)
                self.log.info("created contest", contest_id=rv.id, state=rv.state)
                return rv

        @router.post("/{contest_id}/start", response_model=ContestPublic)
        async def start(contest_id: str):
            with self.model_service.get_session() as session:
                return await self.start_contest(contest_id, session)

        @router.get("/{obj_id}", response_model=Contest)
        async def get(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.get_model(obj_id, session)

        @router.get("", response_model=List[Contest])
        async def list_all():
            with self.model_service.get_session() as session:
                return await self.get_model_list(session)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.delete_model(obj_id, session)

        return router
