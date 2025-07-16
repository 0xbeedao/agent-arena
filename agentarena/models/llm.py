from typing import Optional
from sqlmodel import Field, SQLModel

from agentarena.models.dbbase import DbBase
from agentarena.models.public import LlmModelPricePublic, LlmModelPublic


class LlmModelBase(SQLModel):
    name: str = Field(description="Model display name")
    model_id: str = Field(description="Model key or identifier", index=True)
    canonical_id: Optional[str] = Field(
        default="",
        description="Model canonical identifier",
        index=True,
    )
    active: bool = Field(default=True, description="Whether the model is active")
    notes: Optional[str] = Field(default="", description="Notes about the model")
    supports_json: bool = Field(
        default=False, description="Whether the model can output JSON"
    )
    supports_schema: bool = Field(
        default=False, description="Whether the model can handle schemas"
    )
    score: int = Field(default=0, description="Suitability score for the model")

    def get_public(self):
        return LlmModelPublic(
            name=self.name,
            model_id=self.model_id,
            canonical_id=self.canonical_id,
            supports_json=self.supports_json,
            supports_schema=self.supports_schema,
            score=self.score,
        )


class LlmModel(LlmModelBase, DbBase, table=True):
    pass


class LlmModelCreate(LlmModelBase, table=False):
    pass


class LlmModelUpdate(SQLModel, table=False):
    pass


class LlmModelPriceBase(SQLModel):
    llm_model_id: str = Field(
        foreign_key="llmmodel.id", description="Foreign key to LlmModel"
    )
    prompt_price: float = Field(description="Price per token")
    completion_price: float = Field(description="Price per token")
    request_price: float = Field(description="Price per token")
    image_price: float = Field(description="Price per token")
    web_search_price: float = Field(description="Price per token")
    internal_reasoning_price: float = Field(description="Price per token")
    context_length: int = Field(description="Context length")

    def get_public(self):
        return LlmModelPricePublic(
            prompt_price=self.prompt_price,
            completion_price=self.completion_price,
            request_price=self.request_price,
            image_price=self.image_price,
            web_search_price=self.web_search_price,
            internal_reasoning_price=self.internal_reasoning_price,
            context_length=self.context_length,
        )


class LlmModelPrice(LlmModelPriceBase, DbBase, table=True):
    pass


class LlmModelPriceCreate(LlmModelPriceBase, table=False):
    pass


class LlmModelPriceUpdate(SQLModel, table=False):
    pass


class LlmModelStatsBase(SQLModel):
    llm_model_id: int = Field(
        foreign_key="llmmodel.id", description="Foreign key to LlmModel"
    )
    eval_type: str = Field(index=True, description="Type of evaluation/scenario")
    run_id: Optional[str] = Field(
        default=None, description="Unique identifier for the eval run"
    )
    duration_ms: Optional[int] = Field(
        default=None, description="Duration of the eval in milliseconds"
    )
    success: Optional[bool] = Field(
        default=None, description="Whether the eval was successful"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if eval failed"
    )
    timestamp: Optional[int] = Field(
        default=None, description="When the eval was performed (epoch ms)"
    )
    extra: Optional[str] = Field(
        default=None, description="Any extra info or JSON-encoded stats"
    )


class LlmModelStats(LlmModelStatsBase, DbBase, table=True):
    pass


class LlmModelStatsCreate(LlmModelStatsBase, table=False):
    pass


class LlmModelStatsUpdate(SQLModel, table=False):
    pass
