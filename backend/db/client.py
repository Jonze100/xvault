"""
Supabase Client — Singleton with service role key for backend operations.
"""

from functools import lru_cache
from supabase import create_client, Client
from config import get_settings


@lru_cache
def get_supabase() -> Client:
    """
    Returns a cached Supabase client using service role key.
    Service role bypasses RLS — only use server-side, never expose to client.
    """
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
