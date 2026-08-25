"""
Prompt Moderation Service.
Screens user prompts before generation to detect and block malicious intents:
phishing, credential scrapers, spam infrastructure, and exploit generators.
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger(__name__)

# Patterns indicative of malicious intent
PHISHING_PATTERNS = [
    r"(?i)\b(clone|replicate|fake)\s+(of\s+)?(login|signin|sign-in|portal|bank|paypal|google|facebook|apple|microsoft|netflix|chase|wellsfargo)\b",
    r"(?i)\bcredential\s+(harvest|stealer|scraper|phish|grabber)\b",
    r"(?i)\bphishing\s+(page|kit|template|site|campaign)\b",
    r"(?i)\bsteal\s+(passwords?|credentials?|credit\s*cards?|tokens?|session)\b",
]

SPAM_PATTERNS = [
    r"(?i)\bmass\s+mailer\s+(bot|script|spammer)\b",
    r"(?i)\bemail\s+spammer\s+tool\b",
    r"(?i)\bsms\s+bomb(er|ing)\b",
    r"(?i)\bseo\s+cloaking\s+redirector\b",
]

MALWARE_PATTERNS = [
    r"(?i)\bkeylogger\b",
    r"(?i)\bransomware\b",
    r"(?i)\breverse\s+shell\s+generator\b",
    r"(?i)\bpayload\s+dropper\b",
    r"(?i)\bbotnet\s+c2\b",
]


@dataclass
class ModerationResult:
    safe: bool
    reason: Optional[str] = None
    category: Optional[str] = None


class PromptModerator:
    """Detects malicious generation requests prior to dispatching to LLM providers."""

    async def moderate(self, prompt: str) -> ModerationResult:
        cleaned_prompt = prompt.strip()

        # Check Phishing
        for pattern in PHISHING_PATTERNS:
            if re.search(pattern, cleaned_prompt):
                return ModerationResult(
                    safe=False,
                    reason="Prompt flagged: Detected potential phishing, fake login, or credential harvesting pattern.",
                    category="phishing"
                )

        # Check Spam
        for pattern in SPAM_PATTERNS:
            if re.search(pattern, cleaned_prompt):
                return ModerationResult(
                    safe=False,
                    reason="Prompt flagged: Detected spam infrastructure or automated mass-delivery abuse pattern.",
                    category="spam"
                )

        # Check Malware / Exploits
        for pattern in MALWARE_PATTERNS:
            if re.search(pattern, cleaned_prompt):
                return ModerationResult(
                    safe=False,
                    reason="Prompt flagged: Detected malicious software or exploit utility pattern.",
                    category="malware"
                )

        return ModerationResult(safe=True)
