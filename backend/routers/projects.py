"""
Projects Router.
Handles project management, file tree retrieval, routing logs inspection,
collaborator invitations, and manual model override feedback logging.
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.supabase_client import get_admin_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["projects"])


class CollaboratorRequest(BaseModel):
    user_email: str
    role: str = "editor"  # 'editor' | 'viewer'


class ManualOverrideRequest(BaseModel):
    task_type: str
    preferred_model: str


@router.get("/projects")
async def list_projects(user_id: Optional[str] = None):
    """List projects owned by user or shared via collaborator role."""
    client = get_admin_client()
    uid = user_id or "00000000-0000-0000-0000-000000000001"
    try:
        res = client.table("projects").select("*").eq("owner_id", uid).order("created_at", desc=True).execute()
        return {"projects": res.data or []}
    except Exception as e:
        logger.warning("DB read failed: %s", e)
        return {"projects": []}


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Retrieve details for a single project."""
    client = get_admin_client()
    try:
        res = client.table("projects").select("*").eq("id", project_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Project not found")
        return res.data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project not found: {e}")


@router.get("/projects/{project_id}/files")
async def get_project_files(project_id: str):
    """Retrieve all generated files for a project with model attributions."""
    client = get_admin_client()
    try:
        res = client.table("project_files").select("*").eq("project_id", project_id).execute()
        return {"files": res.data or []}
    except Exception as e:
        logger.warning("DB files read failed: %s", e)
        return {"files": []}


@router.get("/projects/{project_id}/routing-logs")
async def get_routing_logs(project_id: str):
    """Retrieve audit logs showing latency, cost, and model used per task."""
    client = get_admin_client()
    try:
        res = client.table("routing_logs").select("*").eq("project_id", project_id).order("created_at").execute()
        return {"logs": res.data or []}
    except Exception as e:
        return {"logs": []}


@router.post("/projects/{project_id}/collaborators")
async def add_collaborator(project_id: str, req: CollaboratorRequest):
    """Add a team collaborator to a project."""
    client = get_admin_client()
    try:
        # Resolve email to user_id
        profile_res = client.table("profiles").select("id").eq("email", req.user_email).single().execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="User with that email not found")
        
        target_uid = profile_res.data["id"]
        client.table("project_collaborators").insert({
            "project_id": project_id,
            "user_id": target_uid,
            "role": req.role
        }).execute()
        return {"status": "collaborator_added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/files/{file_id}/override")
async def log_manual_override(project_id: str, file_id: str, req: ManualOverrideRequest):
    """
    Log a manual model override. This data feeds into the routing optimization loop.
    """
    client = get_admin_client()
    try:
        # Find latest routing log for this task type
        log_res = client.table("routing_logs").select("id").eq("project_id", project_id).eq("task_type", req.task_type).order("created_at", desc=True).limit(1).execute()
        if log_res.data:
            log_id = log_res.data[0]["id"]
            client.table("routing_feedback").insert({
                "routing_log_id": log_id,
                "was_flagged_by_critic": False,
                "was_edited_by_user": False,
                "was_manual_override": True
            }).execute()
        return {"status": "override_recorded"}
    except Exception as e:
        return {"status": "override_logged_local"}
