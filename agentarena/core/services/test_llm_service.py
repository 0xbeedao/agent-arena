import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import llm  # Import llm at the top
import pytest
from sqlmodel import Session

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.services.db_service import DbService
from agentarena.core.services.llm_service import LLMService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobState
from agentarena.models.job import GenerateJob


@pytest.fixture
def mock_db_service():
    return MagicMock(spec=DbService)


@pytest.fixture
def mock_message_broker():
    return MagicMock(spec=MessageBroker)


@pytest.fixture
def mock_uuid_service():
    return MagicMock(spec=UUIDService)


@pytest.fixture
def mock_logging_service():
    mock = MagicMock()
    mock.get_logger.return_value = MagicMock()
    return mock


@pytest.fixture
def llm_service(
    mock_db_service, mock_message_broker, mock_uuid_service, mock_logging_service
):
    return LLMService(
        db_service=mock_db_service,
        message_broker=mock_message_broker,
        uuid_service=mock_uuid_service,
        logging=mock_logging_service,
    )


@pytest.mark.asyncio
async def test_execute_job_success(llm_service, mock_db_service, mock_message_broker):
    job_id = "test_job_id"
    gen_id = "test_gen_id"
    model_alias = "test_model"
    prompt = "test_prompt"
    generated_text = "test_generated_text"

    mock_job = GenerateJob(
        id=gen_id,
        job_id=job_id,
        model=model_alias,
        prompt=prompt,
        state=JobState.IDLE,
    )

    # Configure mock session and job retrieval
    mock_session = MagicMock(spec=Session)
    mock_session.get.return_value = mock_job
    mock_db_service.get_session.return_value.__enter__.return_value = mock_session

    # Mock LLM generate method
    with patch.object(llm_service, "generate", return_value=generated_text):
        # Wrap the synchronous execute_job call in an awaitable
        result_job = await asyncio.to_thread(llm_service.execute_job, gen_id)

    # Assertions
    assert result_job is not None
    assert result_job.state == JobState.COMPLETE
    assert result_job.generated == generated_text
    assert result_job.finished_at is not None

    # Verify database interactions
    mock_session.commit.assert_called()

    # Verify message broker calls
    mock_message_broker.publish_model_change.assert_any_call(
        channel=f"actor.llm.{gen_id}.{job_id}.{JobState.REQUEST}",
        obj_id=job_id,
        detail="Generation job started",
    )
    mock_message_broker.publish_model_change.assert_any_call(
        channel=f"actor.llm.{gen_id}.{job_id}.{JobState.COMPLETE}",
        obj_id=job_id,
        detail="Generation job completed successfully",
    )


@pytest.mark.asyncio
async def test_execute_job_failure_invalid_model(
    llm_service, mock_db_service, mock_message_broker
):
    job_id = "test_job_id_fail"
    gen_id = "test_gen_id_fail"
    model_alias = "invalid_model"
    prompt = "test_prompt_fail"

    mock_job = GenerateJob(
        id=gen_id,
        job_id=job_id,
        model=model_alias,
        prompt=prompt,
        state=JobState.IDLE,
    )

    # Configure mock session and job retrieval
    mock_session = MagicMock(spec=Session)
    mock_session.get.return_value = mock_job
    mock_db_service.get_session.return_value.__enter__.return_value = mock_session

    # Mock LLM generate method to raise UnknownModelError
    with patch.object(
        llm_service, "generate", side_effect=llm.UnknownModelError("Model not found")
    ):
        result_job = await asyncio.to_thread(llm_service.execute_job, gen_id)

    # Assertions
    assert result_job is not None
    assert result_job.state == JobState.FAIL
    assert result_job.finished_at is not None

    # Verify database interactions
    mock_session.commit.assert_called()

    # Verify message broker calls
    mock_message_broker.publish_model_change.assert_any_call(
        channel=f"actor.llm.{gen_id}.{job_id}.{JobState.REQUEST}",
        obj_id=job_id,
        detail="Generation job started",
    )
    mock_message_broker.publish_model_change.assert_any_call(
        channel=f"actor.llm.{gen_id}.{job_id}.{JobState.FAIL}",
        obj_id=job_id,
        detail="Generation job failed due to invalid model",
    )
