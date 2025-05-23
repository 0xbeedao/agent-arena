from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import Depends
from sqlmodel import Field

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.scheduler.services.request_service import RequestService


class SchedulerService:
    """
    Provides our polling loop using APScheduler.
    This service is managed as a resource by dependency_injector.
    """

    def __init__(
        self,
        db_service: DbService = Field(),
        delay: int = Field(default=1, description="Delay in seconds between polls"),
        max_concurrent: int = Field(
            default=1, description="Maximum concurrent polling runs"
        ),
        request_service: RequestService = Field(description="Request Service"),
        logging: LoggingService = Field(description="Logging Service"),
    ):
        self.delay = delay
        self.max_concurrent = max_concurrent
        self.db_service = db_service
        self.request_service = request_service
        self.logging = logging
        self.scheduler: AsyncIOScheduler = Depends()
        self.log = logging.get_logger("service")

    async def start(
        self,
    ):
        """
        Initializes and starts the APScheduler.
        This method is called by the dependency_injector container.
        """
        self.log.info(
            f"Initializing scheduler with polling interval: {self.delay} seconds"
        )
        self.scheduler = AsyncIOScheduler()

        self.scheduler.add_job(
            self.poll,
            IntervalTrigger(seconds=self.delay),
            id="poll_and_process_job",
            replace_existing=True,
            max_instances=self.max_concurrent,
        )

        try:
            self.scheduler.start()
            self.log.info("Scheduler started successfully.")
        except Exception as e:
            self.log.error(e)
        return self.scheduler

    async def shutdown(self):
        """
        Shuts down the APScheduler.
        This method is called by the dependency_injector container.
        The 'scheduler' argument is the instance yielded by the init() method.
        """
        self.log.info("Shutting down scheduler...")
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            self.log.info("Scheduler shut down successfully.")
        else:
            self.log.info(
                "Scheduler was not running or not provided/initialized correctly."
            )

    async def poll(self):
        with self.db_service.get_session() as session:
            await self.request_service.poll_and_process(session)
