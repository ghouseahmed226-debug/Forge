"""
LLM Provider base interface.
Adding a 4th provider = one new file implementing this interface.
Zero routing logic changes required.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Tier constants
FAST_TIER = "fast"
REASONING_TIER = "reasoning"


@dataclass
class ProviderResponse:
    """Standardized response from any LLM provider."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    provider_name: str


class LLMProvider(ABC):
    """Abstract base class for all LLM providers.

    To add a new provider:
    1. Create a new file in services/providers/
    2. Implement this interface
    3. Register in registry.py
    No changes to routing_engine.py or any router.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g. 'anthropic', 'openai', 'gemini')."""
        ...

    @property
    @abstractmethod
    def tier(self) -> str:
        """Which tier this provider instance serves: FAST_TIER or REASONING_TIER."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ProviderResponse:
        """Generate a completion.

        Args:
            messages: List of {role: str, content: str} dicts.
            max_tokens: Maximum tokens to generate.
            system: Optional system prompt.

        Returns:
            ProviderResponse with content, usage, and cost.

        Raises:
            ProviderError: If the provider fails after all retries.
        """
        ...


class ProviderError(Exception):
    """Raised when a provider fails after all retries."""
    def __init__(self, provider_name: str, message: str, is_rate_limit: bool = False):
        self.provider_name = provider_name
        self.is_rate_limit = is_rate_limit
        super().__init__(f"[{provider_name}] {message}")
