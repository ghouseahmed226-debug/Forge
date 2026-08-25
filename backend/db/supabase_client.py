"""
Supabase client helper.
Provides standard anonymous client and privileged admin client (service role).
"""
import logging
from typing import Optional
from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)

_client: Optional[Client] = None
_admin_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Returns standard client initialized with anon key."""
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            logger.warning("Supabase credentials not configured, client running in unconfigured state")
        _client = create_client(
            settings.supabase_url or "https://placeholder.supabase.co",
            settings.supabase_anon_key or "placeholder_anon_key"
        )
    return _client


def get_admin_client() -> Client:
    """Returns privileged client initialized with service role key for admin operations."""
    global _admin_client
    if _admin_client is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            logger.warning("Supabase service role key not configured")
        _admin_client = create_client(
            settings.supabase_url or "https://placeholder.supabase.co",
            settings.supabase_service_role_key or settings.supabase_anon_key or "placeholder_service_key"
        )
    return _admin_client
