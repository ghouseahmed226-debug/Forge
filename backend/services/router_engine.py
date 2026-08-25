"""
Rules-based task classifier and router engine.
NO machine learning. Pure keyword/category matching.
This is v1 — the data to justify an ML classifier comes from routing_feedback logs.
"""
from dataclasses import dataclass
from enum import Enum

from services.providers.base import FAST_TIER, REASONING_TIER


class ProjectType(str, Enum):
    WEBSITE = "website"
    APPLICATION = "application"
    UNCLASSIFIED = "unclassified"


class TaskType(str, Enum):
    UI_SCAFFOLD = "ui_scaffold"
    COPY_GENERATION = "copy_generation"
    BUSINESS_LOGIC = "business_logic"
    DATA_MODELS = "data_models"
    SECURITY_REVIEW = "security_review"


# ── Routing Table ─────────────────────────────────────────────────────────────
# Explicit, auditable. Every routing decision is traceable to this table.
ROUTING_TABLE: dict[TaskType, dict] = {
    TaskType.UI_SCAFFOLD: {
        "tier": FAST_TIER,
        "requires_critic": False,
        "reason": "High volume, low risk — style consistency matters more than deep reasoning",
    },
    TaskType.COPY_GENERATION: {
        "tier": FAST_TIER,
        "requires_critic": False,
        "reason": "Low risk copy; flagged for user review before publish — never auto-publishes marketing claims",
    },
    TaskType.BUSINESS_LOGIC: {
        "tier": REASONING_TIER,
        "requires_critic": False,
        "reason": "Correctness matters; mistakes in logic compound downstream and are hard to catch in review",
    },
    TaskType.DATA_MODELS: {
        "tier": REASONING_TIER,
        "requires_critic": False,
        "reason": "Schema correctness and normalization are critical — wrong models require migrations to fix",
    },
    TaskType.SECURITY_REVIEW: {
        "tier": REASONING_TIER,
        "requires_critic": True,
        "reason": "Security-sensitive code (auth, RLS, payments) never ships without a mandatory critic pass",
    },
}

# ── Classification Keywords ───────────────────────────────────────────────────
WEBSITE_KEYWORDS = {
    "portfolio", "marketing", "landing page", "landing-page", "blog", "showcase",
    "static", "brochure", "about us", "about me", "personal site", "homepage",
    "informational", "gallery", "one-page", "one page", "resume site",
    "nonprofit", "charity", "event page", "coming soon", "waitlist page",
}

APPLICATION_KEYWORDS = {
    "auth", "login", "sign up", "signup", "register", "authentication",
    "database", "users", "user accounts", "dashboard", "admin panel",
    "api", "backend", "rest api", "graphql", "payments", "stripe",
    "store", "e-commerce", "ecommerce", "shopping", "cart",
    "saas", "subscription", "crm", "erp", "inventory", "orders",
    "real-time", "realtime", "websocket", "notifications",
    "multi-user", "multiuser", "team", "roles", "permissions",
    "upload", "file storage", "analytics dashboard", "reporting",
    "booking", "reservation", "scheduler",
}


@dataclass
class SubTask:
    """A discrete piece of work to route to a model tier."""
    task_type: TaskType
    description: str
    tier: str
    routing_reason: str
    requires_critic: bool
    estimated_cost_usd: float = 0.05  # Conservative default estimate


def classify_project_type(prompt: str) -> ProjectType:
    """Classify prompt as website, application, or unclassified.

    Uses keyword matching. Returns UNCLASSIFIED if both or neither keyword
    categories match — caller should ask user to clarify.

    Args:
        prompt: Raw user prompt string.

    Returns:
        ProjectType enum value.
    """
    lower = prompt.lower()

    website_score = sum(1 for kw in WEBSITE_KEYWORDS if kw in lower)
    app_score = sum(1 for kw in APPLICATION_KEYWORDS if kw in lower)

    if website_score > 0 and app_score == 0:
        return ProjectType.WEBSITE
    if app_score > 0 and website_score == 0:
        return ProjectType.APPLICATION
    if app_score > 0 and website_score > 0:
        # Both signal types present — ambiguous, don't guess
        return ProjectType.UNCLASSIFIED
    if website_score == 0 and app_score == 0:
        # No signals — ambiguous
        return ProjectType.UNCLASSIFIED

    return ProjectType.UNCLASSIFIED


def decompose_prompt(prompt: str, project_type: ProjectType) -> list[SubTask]:
    """Decompose a prompt into typed subtasks based on project type.

    Website: UI_SCAFFOLD + COPY_GENERATION only. No backend tasks.
    Application: All 5 task types.

    Args:
        prompt: Raw user prompt.
        project_type: Classified project type (must not be UNCLASSIFIED).

    Returns:
        Ordered list of SubTask objects.

    Raises:
        ValueError: If project_type is UNCLASSIFIED.
    """
    if project_type == ProjectType.UNCLASSIFIED:
        raise ValueError("Cannot decompose an UNCLASSIFIED project. Confirm type first.")

    def make_subtask(task_type: TaskType, description: str) -> SubTask:
        routing = ROUTING_TABLE[task_type]
        return SubTask(
            task_type=task_type,
            description=description,
            tier=routing["tier"],
            routing_reason=routing["reason"],
            requires_critic=routing["requires_critic"],
        )

    if project_type == ProjectType.WEBSITE:
        # Static website: only UI and copy. No backend, no security review.
        return [
            make_subtask(
                TaskType.UI_SCAFFOLD,
                f"Generate the page layout, components, and visual structure for: {prompt[:200]}",
            ),
            make_subtask(
                TaskType.COPY_GENERATION,
                f"Write all copy (headlines, body text, CTAs) for: {prompt[:200]}",
            ),
        ]

    # Application: full task set
    return [
        make_subtask(
            TaskType.UI_SCAFFOLD,
            f"Generate UI components, layouts, and frontend structure for: {prompt[:200]}",
        ),
        make_subtask(
            TaskType.COPY_GENERATION,
            f"Write all interface copy (labels, messages, empty states) for: {prompt[:200]}",
        ),
        make_subtask(
            TaskType.DATA_MODELS,
            f"Design the database schema, data models, and relationships for: {prompt[:200]}",
        ),
        make_subtask(
            TaskType.BUSINESS_LOGIC,
            f"Implement the core business logic, API endpoints, and data processing for: {prompt[:200]}",
        ),
        make_subtask(
            TaskType.SECURITY_REVIEW,
            f"Generate authentication, authorization, RLS policies, and security hardening for: {prompt[:200]}",
        ),
    ]


def get_routing_explanation(task_type: TaskType) -> dict:
    """Get the routing table entry for a task type. Used by 'Why this model' feature."""
    return ROUTING_TABLE[task_type].copy()
