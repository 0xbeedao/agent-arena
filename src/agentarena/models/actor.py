from pydantic import Field

from agentarena.models.dbbase import DbBase


class ActorDTO(DbBase):
    """
    A simple model reference object to tie an agent to a strategy - for use in the Actor subsystem
    """

    agent_id: str = Field(description="Agent")
    strategy_id: str = Field(description="Strategy")

    def get_foreign_keys(self):
        return [("agent_id", "agents", "id"), ("strategy_id", "strategies", "id")]
