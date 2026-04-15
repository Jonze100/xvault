"""
Supabase Client — Singleton with graceful fallback and optional connection.
"""

import structlog
from functools import lru_cache
from typing import Optional
from config import get_settings

log = structlog.get_logger()


@lru_cache
def get_supabase():
    """
    Returns a cached Supabase client.
    Prefers service role key; falls back to anon key if service role is invalid.
    Returns None if Supabase is not configured — callers must handle None.
    """
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_url.startswith("http"):
        log.warning("supabase.not_configured", reason="missing or invalid SUPABASE_URL")
        return None

    try:
        from supabase import create_client

        # Try service role key first; fall back to anon key
        key = settings.supabase_service_role_key or settings.supabase_anon_key
        if not key:
            log.warning("supabase.not_configured", reason="no API key provided")
            return None

        client = create_client(settings.supabase_url, key)
        log.info("supabase.connected", url=settings.supabase_url)
        return client

    except Exception as exc:
        log.warning("supabase.connection_failed", error=str(exc))
        return None
