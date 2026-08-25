"""Anthropic (Claude) provider implementation."""
import asyncio
import logging
import time

import anthropic

from config import settings
from services.providers.base import (
    FAST_TIER,
    REASONING_TIER,
    LLMProvider,
    ProviderError,
    ProviderResponse,
)

logger = logging.getLogger(__name__)

# Model mapping per tier
FAST_MODEL = "claude-haiku-3-5-20241022"
REASONING_MODEL = "claude-opus-4-5"

# Cost per 1k tokens (USD)
COST_TABLE = {
    FAST_MODEL: {"input": 0.00025, "output": 0.00125},
    REASONING_MODEL: {"input": 0.015, "output": 0.075},
}

MAX_RETRIES = 3
BASE_DELAY = 1.0


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = COST_TABLE.get(model, {"input": 0.001, "output": 0.005})
    return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


class AnthropicProvider(LLMProvider):
    """Claude provider. Fast tier: Haiku. Reasoning tier: Opus."""

    def __init__(self, tier: str = FAST_TIER):
        self._tier = tier
        self._model = FAST_MODEL if tier == FAST_TIER else REASONING_MODEL
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def tier(self) -> str:
        return self._tier

    async def complete(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ProviderResponse:
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                t0 = time.monotonic()
                response = await self._client.messages.create(**kwargs)
                elapsed = time.monotonic() - t0

                content = response.content[0].text if response.content else ""
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = _calculate_cost(self._model, input_tokens, output_tokens)

                logger.debug(
                    "Anthropic %s completed in %.2fs, cost=$%.4f",
                    self._model, elapsed, cost,
                )
                return ProviderResponse(
                    content=content,
                    model=self._model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    provider_name=self.name,
                )

            except anthropic.RateLimitError as e:
                last_error = e
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning("Anthropic rate limit hit, retrying in %.1fs (attempt %d)", delay, attempt + 1)
                await asyncio.sleep(delay)

            except anthropic.APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning("Anthropic API error: %s, retrying in %.1fs", e, delay)
                    await asyncio.sleep(delay)

        is_rate_limit = isinstance(last_error, anthropic.RateLimitError)
        raise ProviderError(self.name, str(last_error), is_rate_limit=is_rate_limit)
