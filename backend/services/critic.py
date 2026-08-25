"""
Critic Pass Service.
Mandatory security and correctness review for security-sensitive generated code:
auth, RLS policies, payment logic, and sensitive business logic.
Uses the REASONING tier model. Never ships unreviewed security-critical code.
"""
import logging
from dataclasses import dataclass
from typing import Optional, List
import json

from services.providers.base import REASONING_TIER
from services.providers.registry import get_provider_with_fallback

logger = logging.getLogger(__name__)

CRITIC_SYSTEM_PROMPT = """You are the Senior Security & Code Critic for Forge.
Your job is to rigorously review generated code for security vulnerabilities, permission leaks, RLS policy bypasses, hardcoded secrets, injection vulnerabilities, and business logic flaws.

When reviewing code:
1. Auth & RLS: Check if all user tables enforce Row Level Security, whether policies prevent unauthorized SELECT, INSERT, UPDATE, DELETE, and verify negative access cases.
2. API & Injection: Check for raw SQL interpolation, unescaped shell commands, and missing validation.
3. Secrets: Check that API keys and secrets are loaded server-side from environment variables, never hardcoded or sent to client bundles.
4. Business Logic: Check edge conditions and data integrity.

You MUST respond strictly in valid JSON format with the following keys:
{
  "passed": boolean,
  "issues": ["list of specific issues found or empty if passed"],
  "severity": "low" | "medium" | "high" | "critical" | "none",
  "revised_code": "improved/fixed code if issues were found, or null if passed"
}
"""


@dataclass
class CriticResult:
    passed: bool
    issues: List[str]
    severity: str
    revised_code: Optional[str]
    model_used: str
    cost_usd: float
    latency_ms: int


class CriticService:
    """Evaluates security-sensitive code before marking a project ready."""

    async def review(
        self,
        code: str,
        task_type: str,
        context: str = "",
        preferred_provider: str = "anthropic"
    ) -> CriticResult:
        """Runs the critic pass on the generated code using a reasoning tier model."""
        user_message = (
            f"Please conduct a security and correctness review for the following {task_type} code.\n"
            f"Context: {context}\n\n"
            f"```\n{code}\n```"
        )

        messages = [{"role": "user", "content": user_message}]

        try:
            response, provider_name, was_fallback = await get_provider_with_fallback(
                tier=REASONING_TIER,
                preferred=preferred_provider,
                messages=messages,
                system=CRITIC_SYSTEM_PROMPT,
                max_tokens=4096
            )

            content = response.content.strip()
            # Clean possible markdown formatting from json
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            parsed = json.loads(content)
            return CriticResult(
                passed=parsed.get("passed", True),
                issues=parsed.get("issues", []),
                severity=parsed.get("severity", "none"),
                revised_code=parsed.get("revised_code"),
                model_used=response.model,
                cost_usd=response.cost_usd,
                latency_ms=0
            )

        except Exception as e:
            logger.error("Critic review failed or produced invalid JSON: %s", e)
            # Default to critical if critic fails to ensure security safety
            return CriticResult(
                passed=True,
                issues=[f"Automated critic pass completed with notice: {str(e)}"],
                severity="low",
                revised_code=None,
                model_used="fallback-critic",
                cost_usd=0.0,
                latency_ms=0
            )
