from typing import Awaitable
from typing import Callable
from typing import List

from pydantic import Field

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.arena import Arena
from agentarena.models.arena import ArenaDTO
from agentarena.models.contest import Contest
from agentarena.models.contest import ContestDTO
from agentarena.models.contest import ContestState
from agentarena.models.participant import Participant
from agentarena.models.participant import ParticipantDTO
from agentarena.services.model_service import ModelService


class ContestFactory:

    def __init__(
        self,
        arena_service: ModelService[ArenaDTO] = None,
        participant_service: ModelService[ParticipantDTO] = None,
        participant_factory=Callable[[ParticipantDTO], Awaitable[Participant]],
        arena_factory=Callable[[ArenaDTO], Awaitable[Arena]],
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.arena_service = arena_service
        self.participant_service = participant_service
        self.participant_factory = participant_factory
        self.arena_factory = arena_factory
        self.log = logging.get_logger(module="contest_factory")
        self.log.debug("init")

    async def build(self, contestDTO: ContestDTO) -> Contest:
        """
        Create a contest object from the contest configuration.

        Args:
            contest_id: The contest ID
            contest_service: The contest service

        Returns:
            The contest object
        """
        log = self.log.bind(
            contest="none" if contestDTO is None else contestDTO.arena_config_id
        )
        log.info("making contest")
        if contestDTO is None:
            return None
        [arenaDTO, response] = await self.arena_service.get(contestDTO.arena_config_id)
        if not response.success:
            raise ValueError(f"Arena with ID {contestDTO.arena_config_id} not found")

        log = log.bind(arena_id=arenaDTO.id)
        log.info(f"got arenaDTO: {arenaDTO}")
        arena = await self.arena_factory.build(arenaDTO)
        log.info(f"got arena")

        winner = None
        if contestDTO.winner is not None:
            log.info(f"Found a winner, loading it: {contestDTO.winnner}")
            aa, _ = await self.participant_service.get(contestDTO.winner)
            winner, _ = await self.participant_factory.build(aa, logger=log)

        positions: List[str] = contestDTO.player_positions.split(";")
        log.info(f"positions: {positions}")

        return Contest(
            id=contestDTO.id,
            arena=arena,
            current_round=contestDTO.current_round,
            player_positions=positions,
            state=ContestState(contestDTO.state),
            start_time=contestDTO.start_time,
            end_time=contestDTO.end_time,
            winner=winner,
        )
