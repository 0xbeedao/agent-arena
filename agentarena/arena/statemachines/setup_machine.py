import json
from codecs import decode
from datetime import datetime

from nats.aio.msg import Msg
from sqlmodel import Field
from sqlmodel import Session
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundState
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import FeatureOriginType
from agentarena.arena.models import Participant
from agentarena.arena.services.round_service import RoundService
from agentarena.arena.services.view_service import ViewService
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService
from agentarena.models.constants import JobResponseState
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.requests import ContestRequestPayload
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

    step_failed = (
        creating_round.to(setup_fail)
        | adding_fixed_features.to(setup_fail)
        | generating_features.to(setup_fail)
        | describing_setup.to(setup_fail)
    )

    cycle = (
        idle.to(creating_round, unless="has_opening_round")
        | idle.to(adding_fixed_features, cond="has_opening_round")
        | creating_round.to(adding_fixed_features)
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
        auto_advance: bool = Field(
            description="Auto advance to next state", default=True
        ),
    ):
        """Initialize the setup machine."""
        self.contest = contest
        self.contest_public = contest.get_public()
        self.contest_round: ContestRound | None = (
            contest.rounds[0] if contest.rounds else None
        )
        self.feature_service = feature_service
        self.uuid_service = feature_service.uuid_service
        self.message_broker = message_broker
        self.round_service = round_service
        self.view_service = view_service
        self.session = session
        self.log = log.bind(contest_id=contest.id)
        self.auto_advance = auto_advance
        super().__init__(
            start_value=(
                self.contest_round.state
                if self.contest_round
                else ContestRoundState.IDLE.value
            )
        )

    def has_opening_round(self) -> bool:
        """Check if the contest has an opening round."""
        return self.contest_round is not None

    async def cycle_or_pause(self, event: str):
        if self.auto_advance:
            await self.cycle(event)
        else:
            self.log.info(
                "Pausing state machine",
                state=self.current_state_value,
            )
            state = self.current_state_value or "ERROR - NO STATE"
            await self.message_broker.send_message(
                f"arena.contest.{self.contest.id}.setupmachine.{self.current_state_value.lower()}.pause", event)

    async def on_enter_creating_round(self):
        """Called when entering the CreatingRound state."""
        log = self.log.bind(state="creating_round")
        log.info("Creating round 0 for contest")

        if not self.contest_round:
            round = await self.round_service.create_round(
                self.contest.id, 0, self.session
            )
            self.contest_round = round
            self.log = self.log.bind(round_id=round.id)
            log.info("Round 0 created successfully")

        await self.cycle_or_pause("from creating round")  # type: ignore

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
        # TODO: Add replay protection here
        for feature in self.contest.arena.features:
            log.debug(f"Adding feature", feature=feature.name)
            round.features.append(feature)
            ct += 1

        self.session.commit()

        log.info(f"{ct} Fixed features added successfully")
        await self.cycle_or_pause("added fixed features")  # type: ignore

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
            await self.cycle_or_pause("from generating features")  # type: ignore
            return
        if (
            len([f for f in round.features if f.origin == FeatureOriginType.RANDOM])
            >= 1
        ):
            self.log.info("Already have features, skipping")
            await self.cycle_or_pause("from generating features")  # type: ignore
            return

        agents = self.contest.get_role(RoleType.ARENA)
        if not agents:
            self.log.error("No arena agents found for generating features")
            await self.step_failed("from generating features")  # type: ignore
            return
        arena_agent = agents[0]
        log = self.log.bind(agent=arena_agent.name)

        # Generate random features and add them to the round
        self.log.info("Starting Generate features")
        msg: Msg = await self.get_generate_features(arena_agent)
        success, error = await self.handle_generate_features(msg)
        if not success:
            self.log.error("Failed to handle feature generation message", error=error)
            await self.step_failed("from generating features")  # type: ignore
            return
        await self.cycle_or_pause("from generating features")  # type: ignore

    async def on_enter_describing_setup(self):
        """Called when entering the DescribingSetup state."""
        agents = self.contest.get_role(RoleType.ANNOUNCER)
        if not agents:
            self.log.error("No announcer agents found for describing setup")
            await self.step_failed("from describing setup")  # type: ignore
            return
        announcer = agents[0]
        log = self.log.bind(agent=announcer.name)
        log.info("Describing setup")
        msg: Msg = await self.get_describe_arena(announcer)
        success, error = await self.handle_describe_arena(msg)
        if not success:
            self.log.error("Failed to handle describe setup message", error=error)
            await self.step_failed("from describing setup")  # type: ignore
            return
        await self.cycle_or_pause("from describing setup")  # type: ignore

    def on_enter_state(self, target, event):
        log = self.log.bind(state=target.id)
        log.debug("entering state", event=event)
        if self.contest_round:
            # update the round state
            self.contest_round.state = target.id
            self.contest_round.updated_at = int(datetime.now().timestamp())
            self.session.commit()

        if target.final:
            log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            log.debug(f"{self.name} enter: {target.id} from {event}")

    # message handlers

    async def get_describe_arena(self, announcer: Participant) -> Msg:
        """Generate the arena description, now that we have all the features.
        This will come back on our handler channel "arena.contest.{self.contest.id}.setup.description".
        """
        log = self.log.bind(
            agent=announcer.name, prompt=PromptType.ANNOUNCER_DESCRIBE_ARENA.value
        )
        log.debug("generating")
        log.info(
            "requesting description from announcer agent",
        )
        job_id = self.uuid_service.make_id()
        channel = announcer.channel_prompt(
            PromptType.ANNOUNCER_DESCRIBE_ARENA, "request", job_id
        )
        contest = self.contest.get_public()
        req = ParticipantContestRequest(
            command=PromptType.ANNOUNCER_DESCRIBE_ARENA,
            data=ContestRequestPayload(contest=contest),
            message="",
        )
        return await self.message_broker.request_job(channel, req.model_dump_json())

    async def handle_describe_arena(self, msg: Msg) -> tuple[bool, str]:
        """Handle the message from the announcer agent with the arena description."""
        log = self.log.bind(msg=msg.subject)
        log.info("Received arena description message", msg=msg.subject)
        try:
            description = extract_text_response(
                decode(msg.data, "utf-8", "unicode_escape")
            )

            round = self.contest_round
            if not round:
                log.error("No round found")
                return False, "no round found"
            round.state = ContestRoundState.DESCRIBING_SETUP
            round.updated_at = int(datetime.now().timestamp())
            log.info("Setting round narrative", description=description)
            round.narrative = description
            self.session.commit()

        except Exception as e:
            log.error("Failed to parse description", error=e)
            return False, "bad description"

        return True, ""

    async def get_generate_features(self, arena_agent: Participant) -> Msg:
        """Generate a list of random features up to count, by sending a job to the message broker"""
        log = self.log.bind(
            agent=arena_agent.name, prompt=PromptType.ARENA_GENERATE_FEATURES.value
        )
        job_id = self.uuid_service.make_id()
        channel = arena_agent.channel_prompt(
            PromptType.ARENA_GENERATE_FEATURES, "request", job_id
        )
        log.info("requesting random features from arena agent", channel=channel)
        contest = self.contest.get_public()
        req = ParticipantContestRequest(
            command=PromptType.ARENA_GENERATE_FEATURES,
            data=ContestRequestPayload(contest=contest),
            message="",
        )
        return await self.message_broker.request_job(channel, req.model_dump_json())

    def parse_generate_features_response(self, msg: Msg) -> tuple[list[dict], bool]:
        """Parse the response from the arena agent with generated features."""
        log = self.log.bind(msg=msg.subject)
        log.info("Received feature generation message", msg=msg)
        features = []
        try:
            job_data = decode(msg.data, "utf-8", "unicode_escape")
            obj = json.loads(job_data)
            state = obj["state"] if isinstance(obj, dict) and "state" in obj else None

            while isinstance(obj, dict) and "data" in obj:
                obj = obj["data"]
                if isinstance(obj, str) and obj.find('"data"') != -1:
                    obj = json.loads(obj)
                if state is None and isinstance(obj, dict):
                    state = obj.get("state", None)  # type: ignore

            if state != JobResponseState.COMPLETE.value:
                log.error("Feature generation job failed", obj=obj)
                return [], False
            features = parse_list(obj, log=log)
            log.info("Parsed feature generation message", features=features)
        except Exception as e:
            log.error("Failed to parse feature generation message", error=e)
            return [], False

        return features, True  # type: ignore

    async def handle_generate_features(self, msg: Msg) -> tuple[bool, str]:
        """Handle the message from the arena agent with generated features."""
        log = self.log.bind(msg=msg.subject)
        features, success = self.parse_generate_features_response(msg)
        if not success:
            return False, "bad feature generation message"

        round = self.contest_round
        assert round, "should have a contest round"

        try:
            job_data = decode(msg.data, "utf-8", "unicode_escape")
            obj = json.loads(job_data)
            state = obj["state"] if isinstance(obj, dict) and "state" in obj else None

            while isinstance(obj, dict) and "data" in obj:
                obj = obj["data"]
                if isinstance(obj, str) and obj.find('"data"') != -1:
                    obj = json.loads(obj)
                if state is None and isinstance(obj, dict):
                    state = obj.get("state", None)  # type: ignore

            if state != JobResponseState.COMPLETE.value:
                log.error("Feature generation job failed", obj=obj)
                return False, "job failed"
            features = parse_list(obj, log=log)
            log.info("Parsed feature generation message", features=features)
        except Exception as e:
            log.error("Failed to parse feature generation message", error=e)
            return False, "bad feature generation message"

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
                log.debug(f"Adding feature", feature=feature.name)
                feature, result = await self.feature_service.create(
                    feature, self.session
                )
                if feature and result.success:
                    round.features.append(feature)

                    if "end_position" in f:
                        # if a feature has a position of 1,1 and an end_position of 3,3, then we need to fill in the cells 1,2 and 2,1 and 2,2
                        # and then add a feature for each of those cells
                        start_pos = f["position"]
                        end_pos = f["end_position"]
                        start_x, start_y = start_pos.split(",")
                        end_x, end_y = end_pos.split(",")
                        for x in range(int(start_x), int(end_x) + 1):
                            for y in range(int(start_y), int(end_y) + 1):
                                log.debug(
                                    "filling in feature cells for ranges", x=x, y=y
                                )
                                feature = Feature(
                                    id="",
                                    name=f["name"],
                                    description=(
                                        f["description"] if "description" in f else ""
                                    ),
                                    position=f"{x},{y}",
                                    origin=FeatureOriginType.RANDOM,
                                )
                                feature, result = await self.feature_service.create(
                                    feature, self.session
                                )
                                if feature and result.success:
                                    round.features.append(feature)

                else:
                    log.info("could not create feature", result=result)

        self.session.commit()
        return True, ""
