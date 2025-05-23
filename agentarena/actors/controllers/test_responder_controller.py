from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

# from agentarena.actors.controllers.responder_controller import ResponderController
# from agentarena.arena.models.arena import Participant
from agentarena.core.factories.logger_factory import LoggingService

# from agentarena.models.requests import HealthResponse
# from agentarena.models.requests import HealthStatus


@pytest.fixture
def mock_participant_service():
    service = AsyncMock()
    return service


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def mock_participant_factory():
    service = AsyncMock()
    return service


class ParticipantStub(BaseModel):
    name: str


# @pytest.mark.asyncio
# async def test_healthcheck_success(
#     mock_participant_service, mock_participant_factory, logging
# ):
#     responder_controller = ResponderController(
#         participant_service=mock_participant_service,
#         logging=logging,
#         participant_factory=mock_participant_factory,
#     )
#     # Arrange
#     participant_id = "aa1"
#     job_id = "job42"
#     p = Participant(arena_id="arena1", role="player", name="test")
#     mock_participant_service.get.return_value = (p, Mock(success=True))

#     mock_participant_factory.build.return_value = ParticipantStub(
#         name="test participant"
#     )

#     # Act
#     result = await responder_controller.healthcheck(
#         participant_id=participant_id,
#         job_id=job_id,
#     )

#     # Assert
#     assert isinstance(result, HealthResponse)
#     assert result.state == "completed"
#     assert result.job_id == job_id
#     assert isinstance(result.data, HealthStatus)
#     assert result.data.name == "test participant"
#     assert result.data.state == "OK"
