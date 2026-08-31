import logging
from app.database.supabase import supabase
from app.services.firms import fetch_firms_data
from app.services.osm import get_cached_geo_context
from app.services.classifier import classifier
from app.services.risk import calculate_risk

logger = logging.getLogger(__name__)

async def search_hotspots(limit: int = 10):
    if not supabase: return {"error": "DB not configured", "data": []}
    resp = supabase.table('hotspots').select('*').order('created_at', desc=True).limit(limit).execute()
    return {"data": resp.data}

async def get_hotspot(hotspot_id: str):
    if not supabase: return {"error": "DB not configured"}
    resp = supabase.table('hotspots').select('*').eq('id', hotspot_id).execute()
    return resp.data[0] if resp.data else None

async def get_geographic_context(hotspot_id: str, lat: float, lon: float):
    return await get_cached_geo_context(hotspot_id, lat, lon)

async def analyze_hotspot_tool(hotspot_id: str):
    hotspot = await get_hotspot(hotspot_id)
    if not hotspot: return {"error": "Not found"}
    geo_context = await get_geographic_context(hotspot_id, hotspot['latitude'], hotspot['longitude'])
    class_res = classifier.classify(hotspot, geo_context or {})
    risk = calculate_risk(hotspot, geo_context or {}, class_res['classification'])
    return {
        "hotspot": hotspot,
        "geo_context": geo_context,
        "classification": class_res,
        "risk": risk
    }

async def generate_report(hotspot_id: str):
    analysis = await analyze_hotspot_tool(hotspot_id)
    return {
        "title": f"Intelligence Report: Hotspot {hotspot_id}",
        "summary": f"This hotspot is classified as {analysis.get('classification',{}).get('classification')} with a {analysis.get('risk')} risk level.",
        "details": analysis
    }

async def execute_tool(tool_name: str, args: dict):
    """
    Custom tool-calling orchestration
    """
    logger.info(f"Agent executing tool: {tool_name} with args: {args}")
    try:
        if tool_name == "search_hotspots":
            return await search_hotspots(args.get("limit", 10))
        elif tool_name == "get_hotspot":
            return await get_hotspot(args["hotspot_id"])
        elif tool_name == "get_geographic_context":
            return await get_geographic_context(args["hotspot_id"], args["lat"], args["lon"])
        elif tool_name == "analyze_hotspot":
            return await analyze_hotspot_tool(args["hotspot_id"])
        elif tool_name == "calculate_risk":
            # Just wrap analysis for now
            analysis = await analyze_hotspot_tool(args["hotspot_id"])
            return {"risk": analysis.get("risk")}
        elif tool_name == "generate_report":
            return await generate_report(args["hotspot_id"])
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return {"error": str(e)}
