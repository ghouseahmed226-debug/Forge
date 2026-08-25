"""
Provider registry — maps tiers to providers with fallback logic.
Provider fallback: if preferred provider errors/rate-limits, tries next in tier list.
"""
import logging

import sentry_sdk

from services.providers.base import FAST_TIER, REASONING_TIER, LLMProvider, ProviderError
from services.providers.anthropic import AnthropicProvider
from services.providers.openai import OpenAIProvider
from services.providers.gemini import GeminiProvider

logger = logging.getLogger(__name__)

# Ordered preference list per tier.
# To add a 4th provider: create its file, add instance here. Nothing else changes.
_REGISTRY: dict[str, list[LLMProvider]] = {
    FAST_TIER: [
        AnthropicProvider(tier=FAST_TIER),
        OpenAIProvider(tier=FAST_TIER),
        GeminiProvider(tier=FAST_TIER),
    ],
    REASONING_TIER: [
        AnthropicProvider(tier=REASONING_TIER),
        OpenAIProvider(tier=REASONING_TIER),
        GeminiProvider(tier=REASONING_TIER),
    ],
}

# Provider name → index in registry for preferred-provider lookup
_PROVIDER_ORDER = ["anthropic", "openai", "gemini"]


def get_provider(
    tier: str,
    preferred: str = "anthropic",
) -> tuple[LLMProvider, bool]:
    """Return the best available provider for a tier.

    Args:
        tier: FAST_TIER or REASONING_TIER.
        preferred: Preferred provider name. Falls back to next if not available.

    Returns:
        Tuple of (provider_instance, was_fallback).
        was_fallback is True if preferred was not used.
    """
    providers = _REGISTRY.get(tier, _REGISTRY[FAST_TIER])

    # Re-order so preferred comes first
    preferred_idx = next(
        (i for i, p in enumerate(providers) if p.name == preferred), 0
    )
    ordered = providers[preferred_idx:] + providers[:preferred_idx]

    return ordered[0], (ordered[0].name != preferred)


async def get_provider_with_fallback(
    tier: str,
    preferred: str = "anthropic",
    messages: list[dict] | None = None,
    max_tokens: int = 4096,
    system: str | None = None,
):
    """Try providers in order until one succeeds. Log fallback events to Sentry.

    Returns:
        Tuple of (ProviderResponse, provider_name_used, was_fallback).
    """
    providers = _REGISTRY.get(tier, _REGISTRY[FAST_TIER])
    preferred_idx = next(
        (i for i, p in enumerate(providers) if p.name == preferred), 0
    )
    ordered = providers[preferred_idx:] + providers[:preferred_idx]

    messages = messages or []
    last_error: Exception | None = None

    for i, provider in enumerate(ordered):
        try:
            response = await provider.complete(
                messages=messages,
                max_tokens=max_tokens,
                system=system,
            )
            was_fallback = i > 0
            if was_fallback:
                logger.warning(
                    "Provider fallback: preferred=%s, used=%s, tier=%s",
                    preferred, provider.name, tier,
                )
                sentry_sdk.capture_message(
                    f"Provider fallback triggered: {preferred} → {provider.name} ({tier})",
                    level="warning",
                )
            return response, provider.name, was_fallback

        except ProviderError as e:
            last_error = e
            logger.warning("Provider %s failed: %s. Trying next.", provider.name, e)
            sentry_sdk.capture_exception(e)

    raise ProviderError(
        "all_providers",
        f"All providers failed for tier={tier}. Last error: {last_error}",
    )
