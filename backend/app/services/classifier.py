import logging

logger = logging.getLogger(__name__)

class HotspotClassifier:
    def __init__(self):
        # We use a purely deterministic rule-based risk and classification engine
        # No fabricated training data or scikit-learn models are used.
        pass

    def classify(self, hotspot_data: dict, geo_context: dict) -> dict:
        """
        Classifies the hotspot into: wildfire / agricultural / industrial / unknown
        Returns classification, a static confidence score, and rule-based evidence.
        """
        evidence = []
        classification = "unknown"
        confidence = 0.5
        
        # Extract features
        brightness = float(hotspot_data.get('brightness', 0))
        frp = float(hotspot_data.get('frp', 0))
        dist_ind = geo_context.get('nearest_industry_m')
        dist_for = geo_context.get('nearest_forest_m')
        dist_set = geo_context.get('nearest_settlement_m')
        
        # Rule-based Evidence Layer
        is_near_industry = dist_ind is not None and dist_ind < 2000
        is_near_forest = dist_for is not None and dist_for < 2000
        is_intense = frp > 100 or brightness > 330
        
        if is_near_industry:
            evidence.append(f"Located {dist_ind}m from known industrial zone.")
        if is_near_forest:
            evidence.append(f"Located {dist_for}m from forested area.")
        if is_intense:
            evidence.append(f"High thermal intensity (FRP: {frp}, Brightness: {brightness}K).")
            
        # Rule-based logic
        if is_near_industry and is_intense:
            classification = "industrial"
            confidence = 0.85
            evidence.append("Rule-based classification: High intensity near industry -> industrial.")
        elif is_near_forest:
            classification = "wildfire"
            confidence = 0.75
            evidence.append("Rule-based classification: Located in/near forest -> wildfire.")
        elif frp < 20 and dist_set is not None and dist_set < 5000:
            classification = "agricultural"
            confidence = 0.70
            evidence.append("Rule-based classification: Low intensity near settlement -> agricultural.")

        if not evidence:
            evidence.append("No strong contextual markers found.")
            
        return {
            "classification": classification,
            "confidence": confidence,
            "evidence": evidence
        }

classifier = HotspotClassifier()
