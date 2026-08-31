import httpx
import pandas as pd
from datetime import datetime, timedelta
from app.core.config import settings
from app.database.supabase import supabase
import logging

logger = logging.getLogger(__name__)

FIRMS_CSV_FALLBACK_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_South_Asia_24h.csv"
FIRMS_VIIRS_FALLBACK_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_South_Asia_24h.csv"

async def fetch_firms_data():
    """
    Fetches latest hotspot data from NASA FIRMS.
    Uses API key if available, otherwise falls back to public CSV.
    """
    data_frames = []
    
    async with httpx.AsyncClient() as client:
        if settings.NASA_FIRMS_MAP_KEY:
            # Use real API if key is provided (example pattern)
            # firms_url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{settings.NASA_FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/world/1"
            # For simplicity, we just log this and use public for now if API isn't strictly defined
            logger.info("FIRMS API key found, but implementing CSV fallback for MVP as per requirements.")
            
        try:
            # Fetch MODIS
            modis_resp = await client.get(FIRMS_CSV_FALLBACK_URL)
            modis_resp.raise_for_status()
            
            # Fetch VIIRS
            viirs_resp = await client.get(FIRMS_VIIRS_FALLBACK_URL)
            viirs_resp.raise_for_status()
            
            # Since pandas might not be installed, we use a basic fallback mechanism if import fails
            try:
                import pandas as pd
                from io import StringIO
                
                df_modis = pd.read_csv(StringIO(modis_resp.text))
                df_modis['source'] = 'MODIS'
                
                df_viirs = pd.read_csv(StringIO(viirs_resp.text))
                df_viirs['source'] = 'VIIRS'
                
                # Combine
                df_combined = pd.concat([df_modis, df_viirs], ignore_index=True)
                
                # Filter for India roughly (Lat: 8.4 to 37.6, Lon: 68.7 to 97.2)
                df_india = df_combined[
                    (df_combined['latitude'] >= 8.4) & (df_combined['latitude'] <= 37.6) &
                    (df_combined['longitude'] >= 68.7) & (df_combined['longitude'] <= 97.2)
                ]
                
                return _process_and_store(df_india)
                
            except ImportError:
                logger.warning("Pandas not installed. Falling back to manual CSV parsing.")
                return _manual_csv_process(modis_resp.text, viirs_resp.text)
                
        except Exception as e:
            logger.error(f"Failed to fetch FIRMS data: {e}")
            return {"status": "error", "message": str(e)}

def _manual_csv_process(modis_csv: str, viirs_csv: str):
    # Fallback if pandas fails on Windows local dev
    import csv
    from io import StringIO
    
    records = []
    for source, csv_text in [("MODIS", modis_csv), ("VIIRS", viirs_csv)]:
        reader = csv.DictReader(StringIO(csv_text))
        for row in reader:
            try:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                if 8.4 <= lat <= 37.6 and 68.7 <= lon <= 97.2:
                    records.append({
                        "latitude": lat,
                        "longitude": lon,
                        "brightness": float(row.get('brightness', row.get('bright_ti4', 0))),
                        "frp": float(row.get('frp', 0)),
                        "confidence": str(row.get('confidence', 'n/a')),
                        "acq_date": row['acq_date'],
                        "acq_time": str(row['acq_time']).zfill(4),
                        "satellite": row.get('satellite', source),
                        "source": source
                    })
            except Exception:
                continue
    return _store_records(records)

def _process_and_store(df):
    records = df.to_dict('records')
    # Map column names if needed
    clean_records = []
    for r in records:
        clean_records.append({
            "latitude": r['latitude'],
            "longitude": r['longitude'],
            "brightness": r.get('brightness', r.get('bright_ti4', 0)),
            "frp": r.get('frp', 0),
            "confidence": str(r.get('confidence', 'n/a')),
            "acq_date": r['acq_date'],
            "acq_time": str(r['acq_time']).zfill(4),
            "satellite": r.get('satellite', r['source']),
            "source": r['source']
        })
    return _store_records(clean_records)

def _store_records(records):
    if not supabase:
        logger.warning("Supabase client not configured. Skipping database write.")
        return {"status": "mock", "count": len(records), "sample": records[:5]}
        
    inserted = 0
    for record in records:
        try:
            # Upsert using unique constraint on (latitude, longitude, acq_date, acq_time, satellite, source)
            # Supabase Python client upsert:
            response = supabase.table('hotspots').upsert(
                record, 
                on_conflict='latitude,longitude,acq_date,acq_time,satellite,source'
            ).execute()
            inserted += 1
        except Exception as e:
            logger.debug(f"Duplicate or error: {e}")
            
    return {"status": "success", "processed": len(records), "inserted": inserted}
