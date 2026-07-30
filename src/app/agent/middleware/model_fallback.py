from typing import override

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest
from langchain_core.language_models import BaseChatModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelFallbackMiddleware(AgentMiddleware):
    """
    If a model call fails (rate limit, quota, or any other error), retries the
    same request against each model in fallback_models in order, until one
    succeeds. If every fallback also fails, re-raises the last error.
    """

    def __init__(self, fallback_models: list[BaseChatModel]) -> None:
        self.fallback_models = fallback_models

    @override
    async def awrap_model_call(self, request: ModelRequest, handler):
        try:
            return await handler(request)
        except Exception as exc:
            last_exc = exc
            for model in self.fallback_models:
                logger.warning(
                    "Model call failed (%s: %s); retrying with %s",
                    type(last_exc).__name__, last_exc, model.model,
                )
                try:
                    return await handler(request.override(model=model))
                except Exception as fallback_exc:
                    last_exc = fallback_exc
            raise last_exc
