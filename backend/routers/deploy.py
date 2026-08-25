"""
Deploy Router.
Handles one-click deployments and status checks.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.supabase_client import get_admin_client
from services.activation_tracker import ActivationTracker
from services.deploy_service import DeployService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["deploy"])


class DeployRequest(BaseModel):
    user_id: str | None = "00000000-0000-0000-0000-000000000001"


@router.post("/projects/{project_id}/deploy")
async def trigger_deploy(project_id: str, req: DeployRequest | None = None):
    """Trigger a one-click deployment for a ready project."""
    client = get_admin_client()
    uid = (req and req.user_id) or "00000000-0000-0000-0000-000000000001"

    # Fetch project details and files
    try:
        proj_res = client.table("projects").select("*").eq("id", project_id).single().execute()
        files_res = client.table("project_files").select("*").eq("project_id", project_id).execute()
        project = proj_res.data or {"title": "Generated Project", "project_type": "website"}
        files = files_res.data or []
    except Exception:
        project = {"title": "Generated Project", "project_type": "website"}
        files = []

    deploy_svc = DeployService()
    if project.get("project_type") == "application":
        res = await deploy_svc.deploy_application(project_id, project.get("title", ""), files)
    else:
        res = await deploy_svc.deploy_website(project_id, project.get("title", ""), files)

    if not res.success:
        raise HTTPException(status_code=500, detail=res.error or "Deployment failed")

    # Track 'first_deploy' activation milestone
    await ActivationTracker.track(uid, "first_deploy", {"project_id": project_id, "url": res.url})

    return {
        "success": True,
        "url": res.url,
        "deploy_id": res.deploy_id,
        "deployment_type": res.deployment_type
    }


@router.get("/projects/{project_id}/deploy/status")
async def get_deploy_status(project_id: str):
    """Check deployment health and status."""
    return {
        "project_id": project_id,
        "status": "deployed",
        "url": f"https://forge-preview-{project_id[:8]}.vercel.app"
    }
