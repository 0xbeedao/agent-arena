import json
from typing import List

from sqlmodel import Session

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import Participant
from agentarena.arena.models import PlayerState
from agentarena.arena.models import PlayerStateCreate
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import RoleType


class RoundService(ModelService[ContestRound, ContestRoundCreate]):
    """
    Service for managing contest rounds.
    """

    def __init__(
        self,
        playerstate_service: ModelService[PlayerState, PlayerStateCreate],
        db_service: DbService,
        uuid_service: UUIDService,
        message_broker: MessageBroker,
        message_prefix: str,
        logging: LoggingService,
    ):
        self.playerstate_service = playerstate_service
        self.db_service = db_service
        self.uuid_service = uuid_service
        self.message_broker = message_broker
        self.log = logging.get_logger("service")
        super().__init__(
            model_class=ContestRound,
            db_service=db_service,
            uuid_service=uuid_service,
            message_broker=message_broker,
            logging=logging,
            message_prefix=message_prefix,
        )

    async def create_round(
        self,
        contest_id: str,
        round_no: int,
        session: Session,
        state=ContestRoundState.CREATING_ROUND,
    ) -> ContestRound:
        """
        Create a new round for a contest.
        """
        log = self.log.bind(contest_id=contest_id, round_no=round_no)
        log.info("Creating round")
        round = ContestRound(
            id=self.uuid_service.make_id(),
            contest_id=contest_id,
            round_no=round_no,
            narrative="",
            state=state,
        )
        contest = session.get(Contest, contest_id)
        assert contest is not None, "Contest not found"
        players = contest.participants_by_role()[RoleType.PLAYER]
        contest.rounds.append(round)
        log = log.bind(round_id=round.id)
        log.info("Added round to contest")
        session.flush()
        player_states: List[PlayerState] = []
        ct = 0
        for player in players:
            player_states.append(
                await self.create_player_state(
                    contest, round.id, round_no, ct, player, session
                )
            )
            ct += 1
        round.player_states = player_states
        log.info("Added player states to round")
        session.commit()
        return round

    async def create_player_state(
        self,
        contest: Contest,
        round_id: str,
        round_no: int,
        ix: int,
        player: Participant,
        session: Session,
    ) -> PlayerState:
        """
        Create a new player state for a contest round.
        """
        log = self.log.bind(
            contest_id=contest.id,
            round_id=round_id,
            round_no=round_no,
            ix=ix,
            player_id=player.id,
        )
        if round_no == 0:

            log.info("Creating initial player state")
            positions = json.loads(contest.player_positions)
            assert len(positions) > ix, "Player position not found"
            position = positions[ix]
            score = 0
            health = "Fresh"
            inventory = []
            if contest.player_inventories:
                inventories = json.loads(contest.player_inventories)
                if len(inventories) > ix:
                    inventory = inventories[ix]
        else:
            log.info("Creating subsequent player state")
            last_round = contest.rounds[-1]
            last_player_state = last_round.player_states[ix]
            position = last_player_state.position
            score = last_player_state.score
            health = last_player_state.health
            inventory = last_player_state.inventory

        pc = PlayerStateCreate(
            participant_id=player.id,
            contestround_id=round_id,
            position=position,
            inventory=inventory,
            health=health,
            score=score,
        )
        playerstate, result = await self.playerstate_service.create(pc, session)
        if not result.success:
            log.error("Failed to create player state", result=result)
            raise Exception("Failed to create player state")
        if not playerstate:
            log.error("Failed to create player state", result=result)
            raise Exception("Failed to create player state")
        log.info("Created player state", playerstate_id=playerstate.id)
        return playerstate
