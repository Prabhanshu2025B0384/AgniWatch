from fastapi import APIRouter, HTTPException, Depends, Request
from app.database.supabase import supabase
from app.services.x402_service import require_payment
from app.services.osm import get_cached_geo_context
from app.services.classifier import classifier
from app.services.risk import calculate_risk
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{hotspot_id}")
async def analyze_hotspot(
    hotspot_id: str,
    request: Request,
    payment_payload: dict = Depends(require_payment)
):
    """
    x402 Protected Endpoint: Deep Analysis of a Hotspot
    Provides classification, risk level, geo context, and rule-based evidence.
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        # 1. Fetch hotspot
        hs_resp = supabase.table('hotspots').select('*').eq('id', hotspot_id).execute()
        if not hs_resp.data:
            raise HTTPException(status_code=404, detail="Hotspot not found")
        hotspot = hs_resp.data[0]
        
        # 2. Check if already analyzed
        analysis_resp = supabase.table('hotspot_analysis').select('*').eq('hotspot_id', hotspot_id).execute()
        
        if analysis_resp.data:
            analysis = analysis_resp.data[0]
            # Also fetch geo context for full report
            geo_context = await get_cached_geo_context(hotspot_id, hotspot['latitude'], hotspot['longitude'])
        else:
            # 3. Perform Deep Analysis
            # Geo Context
            geo_context = await get_cached_geo_context(hotspot_id, hotspot['latitude'], hotspot['longitude'])
            if not geo_context:
                geo_context = {}
                
            # Classification
            class_result = classifier.classify(hotspot, geo_context)
            
            # Risk
            risk_level = calculate_risk(hotspot, geo_context, class_result['classification'])
            
            # Save Analysis
            analysis = {
                "hotspot_id": hotspot_id,
                "classification": class_result['classification'],
                "risk_level": risk_level,
                "confidence": class_result['confidence'],
                "evidence": class_result['evidence'],
                "model_version": "rf_rules_v1"
            }
            try:
                save_resp = supabase.table('hotspot_analysis').insert(analysis).execute()
                if save_resp.data:
                    analysis = save_resp.data[0]
            except Exception as e:
                logger.error(f"Failed to save analysis: {e}")
                # continue with the unsaved analysis
                pass

        # 4. Generate report
        report = {
            "hotspot": hotspot,
            "geo_context": geo_context,
            "analysis": analysis,
            "payment_receipt": payment_payload.model_dump() if hasattr(payment_payload, 'model_dump') else str(payment_payload)
        }
        
        return {"status": "success", "data": report}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in analyze_hotspot: {e}")
        raise HTTPException(status_code=500, detail="Internal analysis error")
