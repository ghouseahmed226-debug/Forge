"""Google Gemini provider implementation."""
import asyncio
import logging
import time

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

from config import settings
from services.providers.base import (
    FAST_TIER,
    REASONING_TIER,
    LLMProvider,
    ProviderError,
    ProviderResponse,
)

logger = logging.getLogger(__name__)

FAST_MODEL = "gemini-1.5-flash"
REASONING_MODEL = "gemini-1.5-pro"

COST_TABLE = {
    FAST_MODEL: {"input": 0.000075, "output": 0.0003},
    REASONING_MODEL: {"input": 0.00125, "output": 0.005},
}

MAX_RETRIES = 3
BASE_DELAY = 1.0


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = COST_TABLE.get(model, {"input": 0.001, "output": 0.005})
    return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


class GeminiProvider(LLMProvider):
    """Google Gemini provider. Fast: gemini-1.5-flash. Reasoning: gemini-1.5-pro."""

    def __init__(self, tier: str = FAST_TIER):
        self._tier = tier
        self._model_name = FAST_MODEL if tier == FAST_TIER else REASONING_MODEL
        genai.configure(api_key=settings.google_api_key)
        self._model = genai.GenerativeModel(self._model_name)

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def tier(self) -> str:
        return self._tier

    async def complete(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ProviderResponse:
        # Convert messages to Gemini format
        parts = []
        if system:
            parts.append({"role": "user", "parts": [system]})
            parts.append({"role": "model", "parts": ["Understood."]})
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            parts.append({"role": role, "parts": [msg["content"]]})

        generation_config = genai.GenerationConfig(max_output_tokens=max_tokens)

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                t0 = time.monotonic()
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._model.generate_content(
                        parts, generation_config=generation_config
                    ),
                )
                elapsed = time.monotonic() - t0

                content = response.text if response.parts else ""
                input_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
                output_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
                cost = _calculate_cost(self._model_name, input_tokens, output_tokens)

                logger.debug(
                    "Gemini %s completed in %.2fs, cost=$%.4f",
                    self._model_name, elapsed, cost,
                )
                return ProviderResponse(
                    content=content,
                    model=self._model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    provider_name=self.name,
                )

            except ResourceExhausted as e:
                last_error = e
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning("Gemini rate limit hit, retrying in %.1fs", delay)
                await asyncio.sleep(delay)

            except GoogleAPIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning("Gemini API error: %s, retrying in %.1fs", e, delay)
                    await asyncio.sleep(delay)

        is_rate_limit = isinstance(last_error, ResourceExhausted)
        raise ProviderError(self.name, str(last_error), is_rate_limit=is_rate_limit)
