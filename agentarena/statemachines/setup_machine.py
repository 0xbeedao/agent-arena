import asyncio
import json
from datetime import datetime

from llm.utils import extract_fenced_code_block
from nats.aio.msg import Msg
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import select
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import ContestRoundState
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import FeatureOriginType
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService
from agentarena.models.constants import JobResponseState, JobState, PromptType
from agentarena.models.constants import RoleType
from agentarena.models.job import CommandJob
from agentarena.models.requests import ParticipantRequest


def extract_fenced_json(raw: str):
    """
    returns the json object if possible, extracting from fence if needed
    """
    try:
        obj = json.loads(raw)
        return obj
    except json.JSONDecodeError:
        pass
    work = extract_fenced_code_block(raw)
    return work or raw


def parse_features_list(features_raw, log=None):
    """
    Parse the features list from a possibly nested or string-encoded structure.
    Handles cases where the features are nested under 'data', are JSON strings, or are fenced code blocks.
    """
    features = features_raw
    while True:
        # Unwrap 'data' if present
        if isinstance(features, dict) and "data" in features:
            features = features["data"]
            continue
        # If it's a string, try to parse it
        if isinstance(features, str):
            s = features.strip()
            if not s:
                return []
            if not s.startswith("["):
                # We'll look for the first occurrence of '[' and the last occurrence of ']' and try to parse that substring
                start = s.find("[")
                end = s.rfind("]")
                if start != -1 and end != -1 and end > start:
                    json_str = s[start : end + 1]
                    try:
                        features = json.loads(json_str)
                        continue
                    except Exception as e:
                        if log:
                            log.error(
                                "Failed to parse feature list from substring", error=e
                            )
                        return []
                # If not found, try fenced code block
                if s.find("```") != -1:
                    features = extract_fenced_json(s)
                    continue
                # Otherwise, try to parse as JSON
                try:
                    features = json.loads(s)
                    continue
                except Exception as e:
                    if log:
                        log.error("Failed to parse feature list as JSON", error=e)
                    return []
            else:
                try:
                    features = json.loads(s)
                    continue
                except Exception as e:
                    if log:
                        log.error("Failed to parse feature list as JSON", error=e)
                    return []
        break
    return features


class SetupMachine(StateMachine):
    """
    Setup machine for generating features, positions, and descriptions.

    States:
    - GeneratingFeatures: Initial state for generating features
    - GeneratingPositions: State for generating positions
    - DescribingSetup: State for describing the setup
    """

    idle = State(ContestRoundState.IDLE.value, initial=True)
    creating_round = State(ContestRoundState.CREATING_ROUND.value)
    adding_fixed_features = State(ContestRoundState.ADDING_FIXED_FEATURES.value)
    generating_features = State(ContestRoundState.GENERATING_FEATURES.value)
    describing_setup = State(ContestRoundState.DESCRIBING_SETUP.value)
    setup_complete = State(ContestRoundState.SETUP_COMPLETE.value, final=True)
    setup_fail = State(ContestRoundState.SETUP_FAIL.value, final=True)

    # Transitions
    start_generating_features = idle.to(
        creating_round,
        unless="has_opening_round",
    ) | idle.to(
        adding_fixed_features,
        cond="has_opening_round",
    )

    step_failed = (
        creating_round.to(setup_fail)
        | adding_fixed_features.to(setup_fail)
        | generating_features.to(setup_fail)
        | describing_setup.to(setup_fail)
    )

    cycle = (
        creating_round.to(adding_fixed_features)
        | adding_fixed_features.to(generating_features)
        | generating_features.to(describing_setup)
        | describing_setup.to(setup_complete)
    )

    def __init__(
        self,
        contest: Contest,
        completion_channel: str = Field(description="Completion channel"),
        message_broker: MessageBroker = Field(description="Message Broker"),
        feature_service: ModelService[Feature, FeatureCreate] = Field(),
        round_service: ModelService[ContestRound, ContestRoundCreate] = Field(
            description="Round Service"
        ),
        session: Session = Field(description="Session"),
        log: ILogger = Field(description="Log"),
    ):
        """Initialize the setup machine."""
        self.completion_channel = completion_channel
        self.contest = contest
        self.contest_public = contest.get_public()
        self.contest_round: ContestRound | None = None
        self.feature_service = feature_service
        self.message_broker = message_broker
        self.round_service = round_service
        self.session = session
        self.log = log.bind(contest_id=contest.id)
        self.subscriptions = {}
        stmt = (
            select(ContestRound)
            .where(ContestRound.round_no == 0)
            .where(ContestRound.contest_id == contest.id)
        )
        round = session.exec(stmt).one_or_none()
        self.contest_round = round
        super().__init__()

    async def generate_arena_description(self):
        """Generate the arena description, now that we have all the features.
        This will come back on our handler channel "arena.contest.{self.contest.id}.setup.description".
        """
        log = self.log
        log.debug("generating")
        agents = self.contest.get_role(RoleType.ANNOUNCER)
        if not agents:
            log.error("No announcer agent found for describing arena")
            return
        announcer = agents[0]
        log = log.bind(agent=announcer.name)
        job_id = self.round_service.uuid_service.make_id()
        channel = f"arena.contest.{self.contest.id}.setup.description"
        log.info(
            "requesting description from announcer agent",
            job_id=job_id,
            channel=channel,
        )
        contest = self.contest.get_public()
        req = ParticipantRequest(
            job_id=job_id,
            command=PromptType.ANNOUNCER_DESCRIBE_ARENA,
            data=contest.model_dump_json(),
            message="",
        )

        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=announcer.url("request"),
        )
        sub = await self.message_broker.client.subscribe(
            channel, cb=self.handle_arena_description_message
        )
        log.info(f"subscribed to {channel}")
        self.subscriptions[channel] = sub
        await self.message_broker.send_job(job)

    async def generate_random_features(self):
        """Generate a list of random features up to count, by sending jobs to the message broker,
        which will come back on our handler channel "arena.contest.{self.contest.id}.setup.features".
        """
        log = self.log
        log.debug("generating")
        agents = self.contest.get_role(RoleType.ARENA)
        if not agents:
            log.error("No arena agents found for generating features")
            return
        arena_agent = agents[0]
        log = log.bind(agent=arena_agent.name)
        channel = f"arena.contest.{self.contest.id}.setup.features"
        job_id = self.round_service.uuid_service.make_id()
        log.info(
            "requesting random features from arena agent",
            job_id=job_id,
            channel=channel,
        )
        contest = self.contest.get_public()
        req = ParticipantRequest(
            job_id=job_id,
            command=PromptType.ARENA_GENERATE_FEATURES,
            data=contest.model_dump_json(),
            message="",
        )

        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=arena_agent.url("request"),
        )
        sub = await self.message_broker.client.subscribe(
            channel, cb=self.handle_feature_generation_message
        )
        log.info(f"subscribed to {channel}")
        self.subscriptions[channel] = sub
        await self.message_broker.send_job(job)

    async def handle_arena_description_message(self, msg: Msg):
        """Handle the message from the announcer agent with generated features."""
        log = self.log.bind(msg=msg.subject)
        log.info("Received arena description message", msg=msg.subject)
        try:
            job_data = msg.data.decode("utf-8")
            log.info("job data", job_data=job_data)
            description = json.loads(job_data)
            if "data" in description:
                description = json.loads(description["data"])
            if "data" in description:
                description = description["data"]

            round = self.contest_round
            if not round:
                log.error("No round found")
                return
            round.state = ContestRoundState.DESCRIBING_SETUP
            round.updated_at = int(datetime.now().timestamp())
            round.narrative = description
            self.session.commit()

        except Exception as e:
            log.error("Failed to parse description", error=e)
            self.send("step_failed", "bad description")

        await self.subscriptions[msg.subject].unsubscribe()
        del self.subscriptions[msg.subject]
        asyncio.create_task(self.send("cycle"))  # type: ignore

    async def handle_feature_generation_message(self, msg: Msg):
        """Handle the message from the arena agent with generated features."""
        log = self.log.bind(msg=msg.subject)
        log.info("Received feature generation message", msg=msg)
        try:
            job_data = msg.data.decode("utf-8")
            obj = json.loads(job_data)
            state = obj.get("state", None)

            while isinstance(obj, dict) and "data" in obj:
                obj = obj["data"]
                if isinstance(obj, str) and obj.find('"data"') != -1:
                    obj = json.loads(obj)
                if state is None:
                    state = obj.get("state", None)

            if state != JobResponseState.COMPLETE.value:
                log.error("Feature generation job failed", obj=obj)
                asyncio.create_task(self.send("step_failed", "job failed"))  # type: ignore
                return
            features = parse_features_list(obj, log=log)
            log.info("Parsed feature generation message", features=features)
        except Exception as e:
            log.error("Failed to parse feature generation message", error=e)
            asyncio.create_task(self.send("step_failed", "bad feature generation message"))  # type: ignore
            return

        await self.subscriptions[msg.subject].unsubscribe()
        del self.subscriptions[msg.subject]
        round = self.contest_round
        assert round, "should have a contest round"
        log.info("Copying new random features to round 0")
        for f in features:
            feature = Feature(
                id="",
                name=f["name"],
                description=f["description"] if "description" in f else "",
                position=f["position"],
                origin=FeatureOriginType.RANDOM,
            )
            # TODO handle end_pos
            log.debug(f"Adding feature", feature=feature.name)
            feature, result = await self.feature_service.create(feature, self.session)
            if feature and result.success:
                round.features.append(feature)
            else:
                log.info("could not create feature", result=result)

        self.session.commit()
        asyncio.create_task(self.send("cycle"))  # type: ignore

    def has_opening_round(self) -> bool:
        """Check if the contest has an opening round."""
        return self.contest_round is not None and self.contest_round.round_no == 0

    async def on_enter_creating_round(self):
        """Called when entering the CreatingRound state."""
        log = self.log.bind(state="creating_round")
        log.info("Creating round 0 for contest")

        # Create a new round 0 if it doesn't exist
        if not self.contest_round:
            round = ContestRound(
                id=self.round_service.uuid_service.make_id(),
                round_no=0,
                contest_id=self.contest.id,
                narrative="",
                state=ContestRoundState.IDLE,
            )
            self.contest.rounds.append(round)
            self.session.commit()
            self.contest_round = round
            self.log = self.log.bind(round_id=round.id)
            log.info("Round 0 created successfully", round_id=round.id)

        self.send("cycle", "from creating round")

    async def on_enter_adding_fixed_features(self):
        """Called when entering the AddingFixedFeatures state."""
        log = self.log.bind(state="adding_fixed_features")
        log.info("Adding fixed features to round 0")
        round = self.contest_round

        # Ensure we have a contest round
        if not round:
            log.error("INVALID STATE! No contest round available, cannot add features")
            return

        ct = 0
        log.info("Copying arena features to round 0")
        for feature in self.contest.arena.features:
            log.debug(f"Adding feature", feature=feature.name)
            round.features.append(feature)
            ct += 1

        self.session.commit()

        log.info(f"{ct} Fixed features added successfully")
        asyncio.create_task(self.cycle(""))

    async def on_enter_generating_features(self):
        """Called when entering the GeneratingFeatures state, which adds the random features."""
        round = self.contest_round
        # Ensure we have a contest round
        if not round:
            self.log.error(
                "INVALID STATE! No contest round available, cannot add features"
            )
            return

        needed = self.contest_public.arena.max_random_features
        if needed <= 0:
            self.log.info("No random features to generate, skipping")
            self.send("cycle", "from generating features")
            return
        # Generate random features and add them to the round
        self.log.info("Starting Generate")
        await self.generate_random_features()

    async def on_enter_describing_setup(self):
        """Called when entering the DescribingSetup state."""
        await self.generate_arena_description()

    async def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")
        state = self.current_state.id
        self.log = self.log.bind(state=state)
        await self.message_broker.send_message(
            f"arena.contest.{self.contest_public.id}.contestflow.setup.{source.id}.{target.id}",
            state,
        )

    async def on_enter_state(self, target, event):
        if self.contest_round:
            # update the round state
            self.contest_round.state = target.id
            self.contest_round.updated_at = int(datetime.now().timestamp())
            self.session.commit()

        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
            await self.message_broker.send_message(self.completion_channel, target.id)
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
