from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client | None:
    """
    Returns the Supabase client. 
    If credentials are missing, returns None so services can fallback gracefully.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
        
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )

supabase = get_supabase_client()
