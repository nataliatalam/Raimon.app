from supabase import create_client, Client
from core.config import get_settings
from typing import Optional
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
supabase_admin: Optional[Client] = None
if settings.supabase_service_role_key:
    supabase_admin = create_client(
        settings.supabase_url, settings.supabase_service_role_key
    )


def get_supabase() -> Client:
    return supabase


_service_role_fallback_warned = False


def get_supabase_admin() -> Client:
    global _service_role_fallback_warned
    if supabase_admin is None:
        if not _service_role_fallback_warned:
            logger.warning(
                "SUPABASE_SERVICE_ROLE_KEY is not set; falling back to anon Supabase client."
            )
            _service_role_fallback_warned = True
        return supabase
    return supabase_admin
