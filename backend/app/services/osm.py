import httpx
import logging
from app.core.config import settings
from app.database.supabase import supabase

logger = logging.getLogger(__name__)

# Radius to search for infrastructure in meters
SEARCH_RADIUS = 5000

async def fetch_geo_context(lat: float, lon: float):
    """
    Fetches the distance to nearest industry, forest, settlement, and road
    using the Overpass API.
    Returns distances in meters.
    """
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["landuse"="industrial"](around:{SEARCH_RADIUS},{lat},{lon});
      way["landuse"="industrial"](around:{SEARCH_RADIUS},{lat},{lon});
      node["landuse"="forest"](around:{SEARCH_RADIUS},{lat},{lon});
      way["landuse"="forest"](around:{SEARCH_RADIUS},{lat},{lon});
      node["place"~"city|town|village"](around:{SEARCH_RADIUS},{lat},{lon});
      way["highway"](around:{SEARCH_RADIUS},{lat},{lon});
    );
    out center;
    """
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                settings.OVERPASS_API_URL, 
                data={"data": overpass_query},
                headers={"User-Agent": "AgniWatch/1.0"},
                timeout=30.0
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Since we don't always have geopandas, we use a crude distance formula for the MVP
            # or shapely if available.
            return _parse_overpass_result(data, lat, lon)
        except Exception as e:
            logger.error(f"Overpass API error: {e}")
            return None

def _haversine_dist(lat1, lon1, lat2, lon2):
    import math
    R = 6371000  # radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _parse_overpass_result(data, origin_lat, origin_lon):
    result = {
        "nearest_industry_m": None,
        "nearest_forest_m": None,
        "nearest_settlement_m": None,
        "nearest_road_m": None,
    }
    
    for element in data.get('elements', []):
        lat = element.get('lat') or (element.get('center', {}).get('lat'))
        lon = element.get('lon') or (element.get('center', {}).get('lon'))
        
        if not lat or not lon:
            continue
            
        dist = _haversine_dist(origin_lat, origin_lon, lat, lon)
        tags = element.get('tags', {})
        
        if tags.get('landuse') == 'industrial':
            if result['nearest_industry_m'] is None or dist < result['nearest_industry_m']:
                result['nearest_industry_m'] = round(dist, 2)
        elif tags.get('landuse') == 'forest':
            if result['nearest_forest_m'] is None or dist < result['nearest_forest_m']:
                result['nearest_forest_m'] = round(dist, 2)
        elif 'place' in tags:
            if result['nearest_settlement_m'] is None or dist < result['nearest_settlement_m']:
                result['nearest_settlement_m'] = round(dist, 2)
        elif 'highway' in tags:
            if result['nearest_road_m'] is None or dist < result['nearest_road_m']:
                result['nearest_road_m'] = round(dist, 2)
                
    return result

async def get_cached_geo_context(hotspot_id: str, lat: float, lon: float):
    """
    Checks Supabase cache for geo context. If not found, fetches from Overpass,
    caches it, and returns.
    """
    if not supabase:
        return {"mock": True, "nearest_industry_m": 1200, "nearest_forest_m": 500}
        
    try:
        # Check cache
        response = supabase.table('hotspot_geo_context').select('*').eq('hotspot_id', hotspot_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
            
        # Fetch fresh
        context = await fetch_geo_context(lat, lon)
        if not context:
            return None
            
        # Save to cache
        cache_row = {
            "hotspot_id": hotspot_id,
            **context
        }
        insert_resp = supabase.table('hotspot_geo_context').insert(cache_row).execute()
        if insert_resp.data:
            return insert_resp.data[0]
        return context
    except Exception as e:
        logger.error(f"Geo context cache error: {e}")
        return None
