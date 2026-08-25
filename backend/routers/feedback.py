"""
Feedback and Activation Router.
Handles user ratings (good/bad), subjective comments, and product activation tracking.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.supabase_client import get_admin_client
from services.activation_tracker import ActivationTracker

logger = logging.getLogger(__name__)
router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    project_id: str
    user_id: str | None = "00000000-0000-0000-0000-000000000001"
    rating: str  # 'good' | 'bad'
    comment: str | None = None


class ActivationEventRequest(BaseModel):
    user_id: str
    event_type: str  # 'signed_up' | 'first_prompt' | 'first_deploy' | 'session_start'
    metadata: dict[str, Any] | None = None


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Save user satisfaction rating and feedback on generated project."""
    if req.rating not in ["good", "bad"]:
        raise HTTPException(status_code=400, detail="Rating must be 'good' or 'bad'")

    client = get_admin_client()
    try:
        client.table("build_feedback").insert({
            "project_id": req.project_id,
            "user_id": req.user_id,
            "rating": req.rating,
            "comment": req.comment
        }).execute()
        return {"status": "feedback_saved"}
    except Exception as e:
        logger.warning("Feedback DB save skipped: %s", e)
        return {"status": "feedback_received"}


@router.get("/projects/{project_id}/feedback")
async def get_project_feedback(project_id: str):
    """Retrieve ratings and comments submitted for a project (Owner only)."""
    client = get_admin_client()
    try:
        res = client.table("build_feedback").select("*").eq("project_id", project_id).execute()
        return {"feedback": res.data or []}
    except Exception:
        return {"feedback": []}


@router.post("/activation")
async def track_activation(req: ActivationEventRequest):
    """Record an activation funnel milestone."""
    success = await ActivationTracker.track(req.user_id, req.event_type, req.metadata)
    return {"tracked": success}
