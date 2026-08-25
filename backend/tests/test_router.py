"""
Unit tests for Router Engine:
1. Website classification
2. Application classification
3. Ambiguity handling (UNCLASSIFIED)
4. Subtask decomposition per project type
5. Explicit routing table mapping
"""
from services.providers.base import FAST_TIER, REASONING_TIER
from services.router_engine import (
    ROUTING_TABLE,
    ProjectType,
    TaskType,
    classify_project_type,
    decompose_prompt,
    get_routing_explanation,
)


def test_classify_website_prompts():
    """Websites: portfolios, landing pages, marketing sites, static blogs."""
    assert classify_project_type("Create a portfolio site for a product designer") == ProjectType.WEBSITE
    assert classify_project_type("Marketing page for a new AI startup with waitlist page") == ProjectType.WEBSITE
    assert classify_project_type("Simple static blog showcase") == ProjectType.WEBSITE
    assert classify_project_type("About me brochure page") == ProjectType.WEBSITE


def test_classify_application_prompts():
    """Applications: auth, database, dashboards, payments, SaaS."""
    assert classify_project_type("Build a customer support ticket system with database and login") == ProjectType.APPLICATION
    assert classify_project_type("SaaS analytics dashboard with user accounts and auth") == ProjectType.APPLICATION
    assert classify_project_type("E-commerce store with payments and shopping cart") == ProjectType.APPLICATION
    assert classify_project_type("Multi-user team project tracker with roles and permissions") == ProjectType.APPLICATION


def test_classify_ambiguous_prompts():
    """Prompts containing both website and app signals or neither should return UNCLASSIFIED."""
    # Both signals
    assert classify_project_type("Marketing landing page with user login and database") == ProjectType.UNCLASSIFIED
    # Neither signal
    assert classify_project_type("Make something cool for my dog") == ProjectType.UNCLASSIFIED


def test_decompose_website_project():
    """Websites must only have UI scaffold and copy generation. No backend or critic tasks."""
    tasks = decompose_prompt("Minimalist portfolio site", ProjectType.WEBSITE)
    task_types = [t.task_type for t in tasks]

    assert task_types == [TaskType.UI_SCAFFOLD, TaskType.COPY_GENERATION]
    assert len(tasks) == 2
    for t in tasks:
        assert t.tier == FAST_TIER
        assert t.requires_critic is False


def test_decompose_application_project():
    """Applications must decompose into all 5 subtasks including security review."""
    tasks = decompose_prompt("Task management app with authentication", ProjectType.APPLICATION)
    task_types = [t.task_type for t in tasks]

    assert task_types == [
        TaskType.UI_SCAFFOLD,
        TaskType.COPY_GENERATION,
        TaskType.DATA_MODELS,
        TaskType.BUSINESS_LOGIC,
        TaskType.SECURITY_REVIEW,
    ]
    assert len(tasks) == 5

    # Check tier mapping
    assert tasks[0].tier == FAST_TIER       # UI scaffold
    assert tasks[1].tier == FAST_TIER       # Copy generation
    assert tasks[2].tier == REASONING_TIER  # Data models
    assert tasks[3].tier == REASONING_TIER  # Business logic
    assert tasks[4].tier == REASONING_TIER  # Security review
    assert tasks[4].requires_critic is True # Security critic pass mandatory


def test_routing_table_integrity():
    """Ensure all task types are mapped in ROUTING_TABLE with explicit reasons."""
    for task_type in TaskType:
        entry = ROUTING_TABLE[task_type]
        assert "tier" in entry
        assert "requires_critic" in entry
        assert "reason" in entry
        assert len(entry["reason"]) > 10

        explanation = get_routing_explanation(task_type)
        assert explanation["tier"] == entry["tier"]
