from typing import Callable, List, Tuple
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService


class SubscribingService:

    def __init__(
        self,
        subscriptions: List[Tuple[str, Callable]],
        message_broker: MessageBroker,
        logging: LoggingService,
    ):
        self._subscribed = []
        self._pending = subscriptions
        self.message_broker = message_broker
        self.log = logging.get_logger("controller")

    async def subscribe_yourself(self):
        if not self._subscribed and self._pending:
            client = self.message_broker.client
            while self._pending:
                pending = self._pending.pop()
                sub = await client.subscribe(pending[0], cb=pending[1])
                self.log.info("Subscribing", channel=pending[0])
                self._subscribed.append(sub)

    async def unsubscribe_yourself(self):
        if self._subscribed:
            for sub in self._subscribed:
                await sub.unsubscribe()
