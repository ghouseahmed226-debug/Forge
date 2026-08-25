"""
Spend Guard Service.
Enforces per-user monthly spend caps server-side before each generation step.
Protects unit economics and notifies Sentry if any check fails to fire.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
import sentry_sdk

from db.supabase_client import get_admin_client

logger = logging.getLogger(__name__)


@dataclass
class SpendCheckResult:
    allowed: bool
    current_spend_usd: float
    monthly_spend_cap_usd: float
    estimated_cost_usd: float
    remaining_usd: float
    error_message: str = ""


class SpendGuard:
    """Server-side monthly budget protection."""

    async def check_and_reserve(
        self,
        user_id: str,
        estimated_cost_usd: float = 0.05
    ) -> SpendCheckResult:
        """
        Check if the user has enough budget remaining in their monthly spend cap.
        Sum total costs in routing_logs for the current calendar month.
        """
        try:
            client = get_admin_client()

            # 1. Fetch user's profile and spend cap
            profile_res = client.table("profiles").select("monthly_spend_cap_usd").eq("id", user_id).single().execute()
            spend_cap = 20.00
            if profile_res.data and "monthly_spend_cap_usd" in profile_res.data:
                spend_cap = float(profile_res.data["monthly_spend_cap_usd"])

            # 2. Compute current month's start timestamp in UTC
            now = datetime.now(timezone.utc)
            month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc).isoformat()

            # 3. Sum routing logs for user's projects created this month
            projects_res = client.table("projects").select("id").eq("owner_id", user_id).execute()
            project_ids = [p["id"] for p in (projects_res.data or [])]

            current_spend = 0.0
            if project_ids:
                logs_res = client.table("routing_logs").select("cost_usd, created_at").in_("project_id", project_ids).gte("created_at", month_start).execute()
                for log in (logs_res.data or []):
                    current_spend += float(log.get("cost_usd") or 0.0)

            remaining = max(0.0, spend_cap - current_spend)
            allowed = (current_spend + estimated_cost_usd) <= spend_cap

            if not allowed:
                msg = (
                    f"Generation blocked: Estimated cost (${estimated_cost_usd:.4f}) would exceed "
                    f"your monthly spend cap of ${spend_cap:.2f} (Current spend: ${current_spend:.4f})."
                )
                logger.warning("Spend cap exceeded for user %s: %s", user_id, msg)
                return SpendCheckResult(
                    allowed=False,
                    current_spend_usd=current_spend,
                    monthly_spend_cap_usd=spend_cap,
                    estimated_cost_usd=estimated_cost_usd,
                    remaining_usd=remaining,
                    error_message=msg
                )

            return SpendCheckResult(
                allowed=True,
                current_spend_usd=current_spend,
                monthly_spend_cap_usd=spend_cap,
                estimated_cost_usd=estimated_cost_usd,
                remaining_usd=remaining
            )

        except Exception as e:
            logger.error("Spend guard check failed: %s", e)
            sentry_sdk.capture_exception(e)
            return SpendCheckResult(
                allowed=True,
                current_spend_usd=0.0,
                monthly_spend_cap_usd=20.00,
                estimated_cost_usd=estimated_cost_usd,
                remaining_usd=20.00,
                error_message=""
            )
