"""
Activation Analytics Tracker.
Records user journey milestones: 'signed_up', 'first_prompt', 'first_deploy', 'session_start'
in the activation_events table with RLS enforcement.
"""
import logging
from typing import Any

from db.supabase_client import get_admin_client

logger = logging.getLogger(__name__)


class ActivationTracker:
    """Records key conversion and activation metrics."""

    @staticmethod
    async def track(
        user_id: str,
        event_type: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Record an activation event into public.activation_events table.
        """
        try:
            client = get_admin_client()
            payload = {
                "user_id": user_id,
                "event_type": event_type,
                "metadata": metadata or {}
            }
            client.table("activation_events").insert(payload).execute()
            logger.info("Tracked activation event '%s' for user %s", event_type, user_id)
            return True
        except Exception as e:
            logger.warning("Failed to record activation event '%s': %s", event_type, e)
            return False
