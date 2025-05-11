from pydantic import Field
from agentarena.factories.logger_factory import LoggingService
from dependency_injector import resources
import typing

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from agentarena.services.queue_service import QueueService


class SchedulerService(resources.AsyncResource):
    """
    Provides our polling loop using APScheduler.
    This service is managed as a resource by dependency_injector.
    """

    def __init__(
        self,
        delay: int = Field(default=1, description="Delay in seconds between polls"),
        queue_service: QueueService = Field(),
        logging: LoggingService = Field(description="Logging Service"),
    ):
        self.q = queue_service
        self.delay = delay
        self.log = logging.get_logger(module="scheduler")

    async def init(self) -> typing.AsyncIterator[AsyncIOScheduler]:
        """
        Initializes and starts the APScheduler.
        This method is called by the dependency_injector container.
        """
        self.log.info(
            f"Initializing scheduler with polling interval: {self.delay} seconds"
        )
        scheduler = AsyncIOScheduler()

        scheduler.add_job(
            self.q.poll_and_process,
            IntervalTrigger(seconds=self.delay),
            id="poll_and_process_job",
            replace_existing=True,
        )

        scheduler.start()
        self.log.info("Scheduler started successfully.")
        yield scheduler

    async def shutdown(self, scheduler: AsyncIOScheduler):
        """
        Shuts down the APScheduler.
        This method is called by the dependency_injector container.
        The 'scheduler' argument is the instance yielded by the init() method.
        """
        self.log.info("Shutting down scheduler...")
        if scheduler and scheduler.running:
            scheduler.shutdown()
            self.log.info("Scheduler shut down successfully.")
        else:
            self.log.info(
                "Scheduler was not running or not provided/initialized correctly."
            )
