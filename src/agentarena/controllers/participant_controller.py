from typing import List

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from pydantic import Field

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.agent import AgentDTO
from agentarena.models.event import JobEvent
from agentarena.models.job import CommandJob
from agentarena.models.job import JobCommandType
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.models.job import JsonRequestSummary
from agentarena.models.participant import ParticipantDTO
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService

READINESS_CHECK_BATCH = "READINESS_CHECK_BATCH"


class ParticipantController:

    def __init__(
        self,
        base_path: str = "/api",
        agent_service: ModelService[AgentDTO] = Field(
            description="The Agent DTO Service"
        ),
        participant_service: ModelService[ParticipantDTO] = Field(
            description="The participant DTO service"
        ),
        queue_service: QueueService = Field(description="Job Queue service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.agent_service = agent_service
        self.base_path = f"{base_path}/participant"
        self.participant_service = participant_service
        self.q = queue_service
        self.log = logging.get_logger("controller", path=self.base_path)

    def _validate_participant_ids(self, participant_ids: List[str]) -> None:
        """Checks if the participant_ids list is empty and raises HTTPException if it is."""
        if not participant_ids:
            self.log.warning(
                "participant_check_workflow called with no participant_ids."
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "title": "No participant IDs provided.",
                    "status": 400,
                    "message": "The list of participant IDs to check cannot be empty.",
                },
            )

    async def _fetch_valid_participants(
        self, participant_ids: List[str], log
    ) -> List[ParticipantDTO]:
        """Fetches participants by IDs, handles errors, and returns a list of valid ParticipantDTOs."""
        parts, problems = await self.participant_service.get_by_ids(participant_ids)
        if problems:
            problem_reports = []
            for problem_instance in problems:
                p_id = getattr(problem_instance, "id", "Unknown/NA")
                msg = getattr(problem_instance, "message", None)
                if msg:
                    report_detail = f"Participant ID '{p_id}': {msg}"
                else:
                    report_detail = (
                        f"Participant ID '{p_id}': {problem_instance.model_dump_json()}"
                    )
                log.info(report_detail)
                problem_reports.append({"participant_issue": report_detail})

            error_payload = {
                "title": "One or more participants could not be processed or found.",
                "status": 400,
                "errors": problem_reports,
            }
            raise HTTPException(status_code=400, detail=error_payload)

        if not parts:
            log.warning(
                "No participants found for the provided IDs after checking for problems."
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "title": "No participants found.",
                    "status": 404,
                    "message": "None of the provided participant IDs could be found or matched.",
                },
            )
        return parts

    async def _get_valid_agents(
        self, participants: List[ParticipantDTO], log
    ) -> List[AgentDTO]:
        """
        Retrieves valid AgentDTOs for a list of ParticipantDTOs.
        """
        agents = []
        agent_problems = []
        for p in participants:
            if not p.agent_id:
                problem = f"Participant {p.id} has a missing or empty agent_id."
                agent_problems.append({"participant_id": p.id, "error": problem})
                log.warn(problem)
                continue

            agent, response = await self.agent_service.get(p.agent_id)
            if response.success and agent:
                agents.append(agent)
            else:
                error_message = (
                    response.message
                    if response and response.message
                    else "Unknown error during agent retrieval"
                )
                problem = f"Agent is invalid or not found for participant {p.id} (agent_id: {p.agent_id}). Details: {error_message}"
                agent_problems.append(
                    {"participant_id": p.id, "agent_id": p.agent_id, "error": problem}
                )
                log.warn(problem)

        if agent_problems:
            error_payload = {
                "title": "One or more agents could not be retrieved or are invalid.",
                "status": 400,
                "errors": agent_problems,
            }
            raise HTTPException(
                status_code=error_payload["status"], detail=error_payload
            )

        if not agents:
            log.warn("No valid agents were found for any of the provided participants.")
            raise HTTPException(
                status_code=404,
                detail={
                    "title": "No valid agents found.",
                    "status": 404,
                    "message": "No valid agents could be retrieved for the processed participants.",
                },
            )
        return agents

    async def _send_readiness_check_batch(
        self, valid_agents: List[AgentDTO], log
    ) -> bool:
        """Creates and dispatches a batch job for readiness checks on valid agents."""
        # valid_agents is guaranteed non-empty by _get_valid_agents raising HTTPException otherwise
        batch = CommandJob(
            command=JobCommandType.BATCH.value,
            data="",
            event=READINESS_CHECK_BATCH,
            method="POST",
            url=f"$ARENA${self.base_path}/event",
        )

        requests_summaries = [
            JsonRequestSummary(
                url=agent.url("health"),
                event="",
                method="GET",
                data="",
                delay=0,
            )
            for agent in valid_agents
        ]

        sent: CommandJob = await self.q.send_batch(batch, requests_summaries)
        if sent:
            batch_id_str = getattr(
                batch, "id", "N/A"
            )  # Attempt to get batch ID if queue service sets it
            log.info(
                f"Successfully sent readiness check batch for {len(valid_agents)} agents. Batch ID (if available): {batch_id_str}"
            )
        else:
            log.error(
                f"Failed to send readiness check batch for {len(valid_agents)} agents."
            )
        return sent

    async def start_readiness_check_flow(
        self, participant_ids: List[str]
    ) -> JobResponse:
        """
        Starts the workflow to check status of listed participants by validating IDs,
        fetching participant data, retrieving their associated agents,
        and dispatching a batch readiness check job.
        """
        self._validate_participant_ids(participant_ids)

        log = self.log.bind(
            flow="readiness_check",
            method="start_readiness_check_flow",
            participant_ids_count=len(participant_ids),
        )
        log.info("Readiness check flow initiated.")

        valid_participants = await self._fetch_valid_participants(participant_ids, log)
        log.info(f"Successfully fetched {len(valid_participants)} valid participants.")

        valid_agents = await self._get_valid_agents(valid_participants, log)
        log.info(
            f"Successfully retrieved {len(valid_agents)} valid agents for the participants."
        )

        sent: CommandJob = await self._send_readiness_check_batch(valid_agents, log)

        if not sent:
            log.error("Readiness check batch could not be dispatched to the queue.")
            return JobResponse(
                job_id="",
                delay=0,
                message="internal queue error",
                state=JobResponseState.FAIL.value,
                data='{"status_code": 500}',
            )
        log.info("Returning success response", batch=sent.id)
        return JobResponse(
            job_id=sent.id,
            delay=0,
            message="started readiness check",
            state=JobResponseState.PENDING.value,
            data="",
        )

    async def receive_event(self, event: JobEvent):
        self.log.info("Received event payload", event=event)
        return True

    def get_router(self):
        router = APIRouter(prefix=self.base_path, tags=["participant"])

        @router.post("/flow/readiness", response_model=JobResponse)
        async def start_readiness_check_flow(req: List[str] = Body(...)):
            return await self.start_readiness_check_flow(req)

        @router.post("/flow/event", response_model=bool)
        async def receive_event(event: JobEvent = Body(...)):
            return await self.receive_event(event)
