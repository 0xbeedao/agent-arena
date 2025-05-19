import os

from dependency_injector import containers
from dependency_injector import providers
from fastapi import Depends

from agentarena.clients.message_broker import MessageBroker
from agentarena.clients.message_broker import get_message_broker_connection
from agentarena.core.factories.db_factory import get_database
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services import uuid_service
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobHistory
from agentarena.scheduler.controllers.debug_controller import DebugController
from agentarena.scheduler.controllers.job_controller import JobController
from agentarena.scheduler.services.queue_service import QueueService
from agentarena.scheduler.services.request_service import RequestService
from agentarena.scheduler.services.scheduler_service import SchedulerService


async def get_scheduler(
    delay: int = 1,
    max_concurrent: int = 5,
    request_service: RequestService = Depends(),
    logging: LoggingService = Depends(),
):
    scheduler = SchedulerService(
        delay=delay,
        max_concurrent=max_concurrent,
        request_service=request_service,
        logging=logging,
    )
    await scheduler.start()
    yield scheduler
    await scheduler.shutdown()


def get_wordlist(
    projectroot: str,
    word_file: str,
):
    filename = word_file.replace("<projectroot>", str(projectroot))
    return uuid_service.get_wordlist(filename)


class SchedulerContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    projectroot = providers.Resource(get_project_root)
    wordlist = providers.Resource(get_wordlist, projectroot, config.uuid.wordlist)

    logging = providers.Singleton(
        LoggingService,
        capture=config.scheduler.logging.capture,
        level=config.scheduler.logging.level,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
        name="scheduler",
        logger_levels=config.scheduler.logging.loggers,
    )

    message_broker_connection = providers.Resource(
        get_message_broker_connection, config.messagebroker.url, logging
    )

    uuid_service = providers.Singleton(
        UUIDService,
        word_list=wordlist,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
    )

    message_broker = providers.Singleton(
        MessageBroker,
        client=message_broker_connection,
        uuid_service=uuid_service,
        logging=logging,
    )

    db_service = providers.Singleton(
        DbService,
        projectroot,
        config.scheduler.db.filename,
        get_database=get_database,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
        uuid_service=uuid_service,
        logging=logging,
    )

    # model services

    commandjob_service = providers.Singleton(
        ModelService[CommandJob],
        model_class=CommandJob,
        db_service=db_service,
        table_name="jobs",
        logging=logging,
    )

    jobhistory_service = providers.Singleton(
        ModelService[CommandJobHistory],
        model_class=CommandJobHistory,
        db_service=db_service,
        table_name="jobhistories",
        logging=logging,
    )

    queue_service = providers.Singleton(
        QueueService,
        history_service=jobhistory_service,
        job_service=commandjob_service,
        message_broker=message_broker,
        logging=logging,
    )

    request_service = providers.Singleton(
        RequestService,
        arena_url=config.arena.url,
        queue_service=queue_service,
        message_broker=message_broker,
        logging=logging,
    )

    scheduler_service = providers.Resource(
        get_scheduler,
        delay=config.scheduler.delay,
        max_concurrent=config.scheduler.max_concurrent,
        request_service=request_service,
        logging=logging,
    )

    # controllers

    job_controller = providers.Singleton(
        JobController,
        base_path="/api",
        model_service=commandjob_service,
        logging=logging,
    )

    debug_controller = providers.Singleton(
        DebugController,
        job_service=commandjob_service,
        logging=logging,
    )
