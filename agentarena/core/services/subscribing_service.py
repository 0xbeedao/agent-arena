from typing import Callable
from typing import List
from typing import Tuple

from nats.aio.client import Client as NatsClient

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger


class SubscribingService:

    def __init__(self, subscriptions: List[Tuple[str, Callable]], log: ILogger):
        self._subscribed = []
        self._pending = subscriptions
        self._log = log

    async def subscribe_yourself(self, message_broker: MessageBroker):
        if not self._subscribed and self._pending:
            client = message_broker.client
            while self._pending:
                pending = self._pending.pop()
                sub = await client.subscribe(pending[0], cb=pending[1])
                self._log.info("Subscribing", channel=pending[0])
                self._subscribed.append(sub)

    async def unsubscribe_yourself(self):
        if self._subscribed:
            for sub in self._subscribed:
                await sub.unsubscribe()


class Subscriber:
    def __init__(self):
        self.subscriptions = {}

    async def subscribe(self, nats: NatsClient, channel: str, log: ILogger, **kwargs):
        if channel in self.subscriptions:
            log.debug(f"Already subscribed to {channel}, skipping subscription")
        else:
            sub = await nats.subscribe(channel, **kwargs)
            self.subscriptions[channel] = sub
            log.debug(f"Subscribed to {channel}")
        return self.subscriptions[channel]

    async def unsubscribe(self, channel: str, log: ILogger):
        if channel in self.subscriptions:
            sub = self.subscriptions[channel]
            await sub.unsubscribe()
            del self.subscriptions[channel]
            log.debug(f"Unsubscribed from {channel}")

    async def unsubscribe_all(self, log: ILogger):
        for channel in self.subscriptions:
            sub = self.subscriptions[channel]
            await sub.unsubscribe()
            log.debug(f"Unsubscribed from {channel}")
        self.subscriptions.clear()
