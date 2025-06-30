import asyncio
import json
from codecs import decode
from datetime import datetime

from nats.aio.msg import Msg
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import select
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundState
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import FeatureOriginType
from agentarena.arena.services.round_service import RoundService
from agentarena.arena.services.view_service import ViewService
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import Subscriber
from agentarena.models.constants import JobResponseState
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.job import CommandJob
from agentarena.models.requests import ParticipantContestRequest
from agentarena.util.response_parsers import extract_text_response
from agentarena.util.response_parsers import parse_list


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
        message_broker: MessageBroker = Field(description="Message Broker"),
        feature_service: ModelService[Feature, FeatureCreate] = Field(),
        round_service: RoundService = Field(description="Round Service"),
        view_service: ViewService = Field(description="View Service"),
        session: Session = Field(description="Session"),
        log: ILogger = Field(description="Log"),
    ):
        """Initialize the setup machine."""
        self.contest = contest
        self.contest_public = contest.get_public()
        self.contest_round: ContestRound | None = None
        self.feature_service = feature_service
        self.message_broker = message_broker
        self.round_service = round_service
        self.view_service = view_service
        self.session = session
        self.completion_channel = f"arena.contest.{contest.id}.setup.complete"
        self.log = log.bind(contest_id=contest.id)
        stmt = (
            select(ContestRound)
            .where(ContestRound.round_no == 0)
            .where(ContestRound.contest_id == contest.id)
        )
        round = session.exec(stmt).one_or_none()
        self.contest_round = round
        self.subscriber = Subscriber()
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
        req = ParticipantContestRequest(
            command=PromptType.ANNOUNCER_DESCRIBE_ARENA,
            data=contest,
            message="",
        )

        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=announcer.url(f"{PromptType.ANNOUNCER_DESCRIBE_ARENA.value}/{job_id}"),
        )
        await self.subscriber.subscribe(
            self.message_broker.client,
            channel,
            self.log,
            cb=self.handle_arena_description_message,
        )
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
        req = ParticipantContestRequest(
            command=PromptType.ARENA_GENERATE_FEATURES,
            data=contest,
            message="",
        )

        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=arena_agent.url(f"{PromptType.ARENA_GENERATE_FEATURES.value}/{job_id}"),
        )
        await self.subscriber.subscribe(
            self.message_broker.client,
            channel,
            self.log,
            cb=self.handle_feature_generation_message,
        )
        await self.message_broker.send_job(job)

    async def handle_arena_description_message(self, msg: Msg):
        """Handle the message from the announcer agent with generated features."""
        log = self.log.bind(msg=msg.subject)
        log.info("Received arena description message", msg=msg.subject)
        try:
            description = extract_text_response(
                decode(msg.data, "utf-8", "unicode_escape")
            )

            round = self.contest_round
            if not round:
                log.error("No round found")
                return
            round.state = ContestRoundState.DESCRIBING_SETUP
            round.updated_at = int(datetime.now().timestamp())
            log.info("Setting round narrative", description=description)
            round.narrative = description
            self.session.commit()

        except Exception as e:
            log.error("Failed to parse description", error=e)
            self.send("step_failed", "bad description")

        await self.subscriber.unsubscribe(msg.subject, self.log)
        asyncio.create_task(self.send("cycle"))  # type: ignore

    async def handle_feature_generation_message(self, msg: Msg):
        """Handle the message from the arena agent with generated features."""
        log = self.log.bind(msg=msg.subject)
        log.info("Received feature generation message", msg=msg)
        try:
            job_data = decode(msg.data, "utf-8", "unicode_escape")
            obj = json.loads(job_data)
            state = obj.get("state", None)

            while isinstance(obj, dict) and "data" in obj:
                obj = obj["data"]
                if isinstance(obj, str) and obj.find('"data"') != -1:
                    obj = json.loads(obj)
                if state is None:
                    state = obj.get("state", None)  # type: ignore

            if state != JobResponseState.COMPLETE.value:
                log.error("Feature generation job failed", obj=obj)
                asyncio.create_task(self.send("step_failed", "job failed"))  # type: ignore
                return
            features = parse_list(obj, log=log)
            log.info("Parsed feature generation message", features=features)
        except Exception as e:
            log.error("Failed to parse feature generation message", error=e)
            asyncio.create_task(self.send("step_failed", "bad feature generation message"))  # type: ignore
            return

        await self.subscriber.unsubscribe(msg.subject, self.log)
        round = self.contest_round
        assert round, "should have a contest round"
        log.info("Copying new random features to round 0")
        if features:
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
                feature, result = await self.feature_service.create(
                    feature, self.session
                )
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
        # TODO: we need to add the initial player_states here - and this should probably by done in the round service
        if not self.contest_round:
            round = await self.round_service.create_round(
                self.contest.id, 0, self.session
            )
            self.contest_round = round
            self.log = self.log.bind(round_id=round.id)
            log.info("Round 0 created successfully")

        await self.send("cycle", "from creating round")  # type: ignore

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
            await self.subscriber.unsubscribe_all(self.log)
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
