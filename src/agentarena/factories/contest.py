from typing import Awaitable
from typing import Callable
from typing import List

from agentarena.models.arena import Arena
from agentarena.models.arena import ArenaDTO
from agentarena.models.arenaagent import ArenaAgent
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.contest import Contest
from agentarena.models.contest import ContestDTO
from agentarena.models.contest import ContestStatus
from agentarena.services.model_service import ModelService


async def contest_factory(
    contestDTO: ContestDTO,
    arena_service: ModelService[ArenaDTO] = None,
    arenaagent_service: ModelService[ArenaAgentDTO] = None,
    make_arenaagent=Callable[[ArenaAgentDTO], Awaitable[ArenaAgent]],
    make_arena=Callable[[ArenaDTO], Awaitable[Arena]],
    make_logger=None,
) -> Contest:
    """
    Create a contest object from the contest configuration.

    Args:
        contest_id: The contest ID
        contest_service: The contest service

    Returns:
        The contest object
    """
    log = make_logger(contest=contestDTO.arena_config_id)
    log.info("making contest")
    [arenaDTO, response] = await arena_service.get(contestDTO.arena_config_id)
    if not response.success:
        raise ValueError(f"Arena with ID {contestDTO.arena_config_id} not found")

    log.info(f"got arenaDTO: {arenaDTO}")
    arena = await make_arena(arenaDTO)
    log.info(f"got arena: {arena.id}")

    winner = None
    if contestDTO.winner is not None:
        log.info("Found a winner, loading it: {}", contestDTO.winnner)
        aa, _ = await arenaagent_service.get(contestDTO.winner)
        winner, _ = await make_arenaagent(aa, logger=log)

    positions: List[str] = contestDTO.player_positions.split(";")
    log.info(f"positions: {positions}")

    return Contest(
        id=contestDTO.id,
        arena=arena,
        current_round=contestDTO.current_round,
        player_positions=positions,
        status=ContestStatus(contestDTO.status),
        start_time=contestDTO.start_time,
        end_time=contestDTO.end_time,
        winner=winner,
    )
