from typing import Callable
from typing import Protocol
from typing import Type

from agentarena.models.event import JobEvent
from agentarena.services.model_service import ModelService


class IEventBus(Protocol):
    async def publish(self, event: object) -> None: ...
    def subscribe(self, event_type: str, handler: Callable[[object], None]) -> None: ...


class InMemoryEventBus(IEventBus):
    def __init__(self, logging=None):
        self.log = logging.get_logger(module="memory_eventbus")
        self._handlers: dict[str, list[Callable]] = {}

    async def publish(self, event: object) -> None:

        for handler in self._handlers.get(type(event), []):
            await handler(event)

    def subscribe(self, event_type: str, handler: Callable[[JobEvent], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)


class DbEventBus(IEventBus):
    def __init__(
        self,
        model_service: ModelService[JobEvent] = None,
        inner: IEventBus = None,
        logging=None,
    ):
        self._inner = inner if inner is not None else InMemoryEventBus(logging=logger)
        self.model_service = model_service
        self.log = logging.get_logger(module="db_eventbus")

    async def publish(self, event: JobEvent) -> None:
        ready, response = self.model_service.create(event)
        if not response.success:
            self.log.warn("Error in event system, event not published")
        else:
            self.log.debug(f"Published event {ready.id}")
            self._inner.publish(ready)  # in-process dispatch

    def subscribe(self, event_type: Type, handler: Callable[[JobEvent], None]) -> None:
        self._inner.subscribe(event_type, handler)
