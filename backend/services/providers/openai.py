"""OpenAI (GPT) provider implementation."""
import asyncio
import logging
import time

from openai import AsyncOpenAI, RateLimitError, APIError

from config import settings
from services.providers.base import (
    FAST_TIER,
    REASONING_TIER,
    LLMProvider,
    ProviderError,
    ProviderResponse,
)

logger = logging.getLogger(__name__)

FAST_MODEL = "gpt-4o-mini"
REASONING_MODEL = "gpt-4o"

COST_TABLE = {
    FAST_MODEL: {"input": 0.00015, "output": 0.0006},
    REASONING_MODEL: {"input": 0.005, "output": 0.015},
}

MAX_RETRIES = 3
BASE_DELAY = 1.0


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = COST_TABLE.get(model, {"input": 0.001, "output": 0.005})
    return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


class OpenAIProvider(LLMProvider):
    """OpenAI provider. Fast tier: GPT-4o-mini. Reasoning tier: GPT-4o."""

    def __init__(self, tier: str = FAST_TIER):
        self._tier = tier
        self._model = FAST_MODEL if tier == FAST_TIER else REASONING_MODEL
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def name(self) -> str:
        return "openai"

    @property
    def tier(self) -> str:
        return self._tier

    async def complete(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ProviderResponse:
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                t0 = time.monotonic()
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=all_messages,
                    max_tokens=max_tokens,
                )
                elapsed = time.monotonic() - t0

                content = response.choices[0].message.content or ""
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0
                cost = _calculate_cost(self._model, input_tokens, output_tokens)

                logger.debug(
                    "OpenAI %s completed in %.2fs, cost=$%.4f",
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

            except RateLimitError as e:
                last_error = e
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning("OpenAI rate limit hit, retrying in %.1fs", delay)
                await asyncio.sleep(delay)

            except APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning("OpenAI API error: %s, retrying in %.1fs", e, delay)
                    await asyncio.sleep(delay)

        is_rate_limit = isinstance(last_error, RateLimitError)
        raise ProviderError(self.name, str(last_error), is_rate_limit=is_rate_limit)
