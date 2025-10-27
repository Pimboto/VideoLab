"""
Supabase Client Singleton

This module provides a singleton instance of the Supabase client
for database and storage operations.
"""
from functools import lru_cache
from supabase import create_client, Client
from core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """
    Get a singleton Supabase client instance.

    Uses the service role key for backend operations, which bypasses RLS.
    For user-specific operations, we'll manually enforce user isolation.

    Returns:
        Client: Supabase client instance
    """
    settings = get_settings()

    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_role_key
    )
