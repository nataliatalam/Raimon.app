from supabase import create_client, Client
from core.config import get_settings

settings = get_settings()

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
supabase_admin: Client = create_client(
    settings.supabase_url, settings.supabase_service_role_key
)


def get_supabase() -> Client:
    return supabase


def get_supabase_admin() -> Client:
    return supabase_admin
