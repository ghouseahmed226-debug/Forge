"""
Generation Router with Server-Sent Events (SSE).
Orchestrates the multi-model generation pipeline:
1. Prompt moderation
2. Spend cap verification
3. Project classification (Website vs Application)
4. Subtask decomposition & routing to model tiers
5. Real-time SSE streaming of routing trace events
6. Mandatory critic pass for security-sensitive tasks
7. Quality gates evaluation
8. Project persistence & readiness status
"""
import asyncio
import json
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from db.supabase_client import get_admin_client
from services.activation_tracker import ActivationTracker
from services.critic import CriticService
from services.moderation import PromptModerator
from services.providers.registry import get_provider_with_fallback
from services.quality_gates import QualityGateRunner
from services.router_engine import (
    ProjectType,
    TaskType,
    classify_project_type,
    decompose_prompt,
)
from services.spend_guard import SpendGuard

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])

# In-memory event queues for live SSE streaming per project
_STREAM_QUEUES: dict[str, asyncio.Queue] = {}


class GenerateRequest(BaseModel):
    prompt: str
    project_type: str | None = None  # 'website' | 'application' | None
    preferred_provider: str | None = "anthropic"
    owner_id: str | None = None  # Supabase user uuid or default


class GenerateResponse(BaseModel):
    project_id: str
    project_type: str
    requires_confirmation: bool = False
    ambiguity_details: str | None = None
    status: str = "generating"


@router.post("/generate", response_model=GenerateResponse)
async def create_generation(req: GenerateRequest):
    """
    Initiates a new project generation workflow or flags ambiguity.
    """
    user_id = req.owner_id or "00000000-0000-0000-0000-000000000001"
    prompt = req.prompt.strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    # 1. Prompt Moderation Gate
    moderator = PromptModerator()
    mod_result = await moderator.moderate(prompt)
    if not mod_result.safe:
        raise HTTPException(
            status_code=400,
            detail=f"Prompt blocked by moderation policy: {mod_result.reason}"
        )

    # 2. Spend Guard Check
    spend_guard = SpendGuard()
    spend_res = await spend_guard.check_and_reserve(user_id=user_id, estimated_cost_usd=0.08)
    if not spend_res.allowed:
        raise HTTPException(status_code=402, detail=spend_res.error_message)

    # 3. Project-Type Classification
    if req.project_type in [ProjectType.WEBSITE.value, ProjectType.APPLICATION.value]:
        p_type = ProjectType(req.project_type)
    else:
        p_type = classify_project_type(prompt)

    # If ambiguous, prompt user to confirm rather than guessing wrong shape
    if p_type == ProjectType.UNCLASSIFIED:
        temp_id = str(uuid.uuid4())
        return GenerateResponse(
            project_id=temp_id,
            project_type=ProjectType.UNCLASSIFIED.value,
            requires_confirmation=True,
            ambiguity_details="The prompt could be either a static website (portfolio, marketing) or a data-backed application with auth & database. Please confirm your desired project type.",
            status="awaiting_confirmation"
        )

    # 4. Create Project Record in Database
    project_id = str(uuid.uuid4())
    client = get_admin_client()

    title_words = prompt.split()[:5]
    title = " ".join(title_words).title() if title_words else "New Project"

    try:
        client.table("projects").insert({
            "id": project_id,
            "owner_id": user_id,
            "title": title,
            "prompt": prompt,
            "project_type": p_type.value,
            "status": "generating"
        }).execute()
    except Exception as e:
        logger.warning("Could not persist initial project to DB (running offline mode): %s", e)

    # Create event queue for SSE
    queue: asyncio.Queue[Any] = asyncio.Queue()
    _STREAM_QUEUES[project_id] = queue

    # Start generation pipeline in background
    asyncio.create_task(
        _run_generation_pipeline(
            project_id=project_id,
            user_id=user_id,
            prompt=prompt,
            project_type=p_type,
            preferred_provider=req.preferred_provider or "anthropic",
            queue=queue
        )
    )

    # Track first prompt activation
    await ActivationTracker.track(user_id, "first_prompt", {"project_id": project_id, "project_type": p_type.value})

    return GenerateResponse(
        project_id=project_id,
        project_type=p_type.value,
        requires_confirmation=False,
        status="generating"
    )


async def _run_generation_pipeline(
    project_id: str,
    user_id: str,
    prompt: str,
    project_type: ProjectType,
    preferred_provider: str,
    queue: asyncio.Queue
):
    """Executes the sequential multi-model generation pipeline and emits SSE events."""
    client = get_admin_client()
    critic_service = CriticService()
    gate_runner = QualityGateRunner()

    generated_files: list[dict[str, str]] = []
    critic_flagged = False

    try:
        # Step 1: Decomposition
        subtasks = decompose_prompt(prompt, project_type)
        total_tasks = len(subtasks)

        await queue.put({
            "event_type": "classification_done",
            "project_type": project_type.value,
            "total_subtasks": total_tasks,
            "timestamp": time.time()
        })

        # Step 2: Execute Subtasks sequentially with model transparency
        for idx, task in enumerate(subtasks):
            task_name = task.task_type.value
            tier = task.tier
            routing_reason = task.routing_reason

            await queue.put({
                "event_type": "subtask_started",
                "task_type": task_name,
                "tier": tier,
                "routing_reason": routing_reason,
                "progress_pct": int((idx / (total_tasks + 2)) * 100),
                "timestamp": time.time()
            })

            t_start = time.time()

            # Construct targeted system & user prompts for each specific subtask
            system_prompt = (
                f"You are the specialist agent for '{task_name}' in the Forge build engine.\n"
                f"Routing Tier: {tier.upper()}.\n"
                f"Reason: {routing_reason}.\n"
                "Generate complete, robust, ready-to-run code without any omitted sections or placeholders."
            )

            user_prompt = (
                f"Project Type: {project_type.value.upper()}\n"
                f"User Request: {prompt}\n\n"
                f"Generate the exact file contents for task: {task.description}."
            )

            # LLM Provider Call with Fallback
            provider_resp, model_used, _was_fallback = await get_provider_with_fallback(
                tier=tier,
                preferred=preferred_provider,
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                max_tokens=4096
            )

            latency_ms = int((time.time() - t_start) * 1000)
            cost_usd = provider_resp.cost_usd

            # Determine file path based on task
            if task.task_type == TaskType.UI_SCAFFOLD:
                file_path = "app/page.tsx" if project_type == ProjectType.WEBSITE else "components/Dashboard.tsx"
            elif task.task_type == TaskType.COPY_GENERATION:
                file_path = "content/copy.json"
            elif task.task_type == TaskType.DATA_MODELS:
                file_path = "db/schema.sql"
            elif task.task_type == TaskType.BUSINESS_LOGIC:
                file_path = "lib/logic.ts"
            elif task.task_type == TaskType.SECURITY_REVIEW:
                file_path = "lib/auth.ts"
            else:
                file_path = f"generated/{task_name}.ts"

            file_entry = {
                "project_id": project_id,
                "path": file_path,
                "content": provider_resp.content,
                "generated_by_model": model_used
            }
            generated_files.append(file_entry)

            # Log to routing_logs
            log_id = str(uuid.uuid4())
            try:
                client.table("routing_logs").insert({
                    "id": log_id,
                    "project_id": project_id,
                    "task_type": task_name,
                    "model_used": model_used,
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd
                }).execute()
            except Exception as e:
                logger.debug("DB log insert skipped: %s", e)

            # Run Critic Pass if required (Apps only on security-sensitive tasks)
            if task.requires_critic and project_type == ProjectType.APPLICATION:
                await queue.put({
                    "event_type": "critic_started",
                    "task_type": task_name,
                    "model": "claude-opus-4-5 / gpt-4o",
                    "timestamp": time.time()
                })

                critic_res = await critic_service.review(
                    code=provider_resp.content,
                    task_type=task_name,
                    context=prompt,
                    preferred_provider=preferred_provider
                )

                if not critic_res.passed:
                    critic_flagged = True
                    if critic_res.revised_code:
                        file_entry["content"] = critic_res.revised_code

                # Record critic feedback log
                try:
                    client.table("routing_feedback").insert({
                        "routing_log_id": log_id,
                        "was_flagged_by_critic": not critic_res.passed,
                        "was_edited_by_user": False,
                        "was_manual_override": False
                    }).execute()
                except Exception as e:
                    logger.debug("Routing feedback insert skipped: %s", e)

                await queue.put({
                    "event_type": "critic_done",
                    "task_type": task_name,
                    "passed": critic_res.passed,
                    "issues": critic_res.issues,
                    "timestamp": time.time()
                })

            await queue.put({
                "event_type": "subtask_done",
                "task_type": task_name,
                "model_used": model_used,
                "tier": tier,
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
                "file_path": file_path,
                "routing_reason": routing_reason,
                "progress_pct": int(((idx + 1) / (total_tasks + 2)) * 100),
                "timestamp": time.time()
            })

        # Step 3: Run 11 Quality Gates
        gate_results = await gate_runner.run_all(
            project_id=project_id,
            project_type=project_type.value,
            files=generated_files,
            critic_passed=not critic_flagged
        )

        for gate in gate_results:
            await queue.put({
                "event_type": "quality_gate_done",
                "gate_name": gate.gate_name,
                "passed": gate.passed,
                "details": gate.details,
                "score": gate.score,
                "timestamp": time.time()
            })

        # Step 4: Persist files to DB
        try:
            for f in generated_files:
                client.table("project_files").insert(f).execute()
            client.table("projects").update({"status": "ready"}).eq("id", project_id).execute()
        except Exception as e:
            logger.debug("DB file persistence skipped: %s", e)

        # Final Event
        await queue.put({
            "event_type": "generation_complete",
            "project_id": project_id,
            "status": "ready",
            "files_count": len(generated_files),
            "progress_pct": 100,
            "timestamp": time.time()
        })

    except Exception as e:
        logger.error("Generation pipeline failed for project %s: %s", project_id, e)
        await queue.put({
            "event_type": "error",
            "project_id": project_id,
            "error_message": str(e),
            "timestamp": time.time()
        })
    finally:
        await queue.put(None)  # Sentinel to close stream


@router.get("/generate/{project_id}/stream")
async def stream_generation_events(project_id: str):
    """
    Server-Sent Events endpoint providing real-time relay trace data.
    """
    queue = _STREAM_QUEUES.get(project_id)
    if not queue:
        # Generate simulated events if project already processed
        async def fallback_stream():
            yield f"data: {json.dumps({'event_type': 'connected', 'project_id': project_id})}\n\n"
        return StreamingResponse(fallback_stream(), media_type="text/event-stream")

    async def event_generator():
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            _STREAM_QUEUES.pop(project_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
