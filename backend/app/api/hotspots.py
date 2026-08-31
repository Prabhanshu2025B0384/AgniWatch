from fastapi import APIRouter, HTTPException, Depends
from app.database.supabase import supabase
from app.services.firms import fetch_firms_data
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
def get_hotspots(limit: int = 1000):
    """
    Public free layer endpoint.
    Returns basic hotspot information for the map.
    """
    if not supabase:
        return {"status": "mock", "data": []}
        
    try:
        response = supabase.table('hotspots').select('*').order('created_at', desc=True).limit(limit).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        logger.error(f"Error fetching hotspots: {e}")
        raise HTTPException(status_code=500, detail="Database error")

@router.post("/ingest")
async def trigger_ingestion():
    """
    Triggers FIRMS data ingestion. In production this could be called by a cron job or admin.
    """
    result = await fetch_firms_data()
    return result
