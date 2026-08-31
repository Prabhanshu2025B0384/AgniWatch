def calculate_risk(hotspot_data: dict, geo_context: dict, classification: str) -> str:
    """
    Risk scoring engine (LOW / MODERATE / HIGH / CRITICAL)
    combining intensity, persistence, and proximity factors.
    """
    score = 0
    
    # 1. Intensity factor
    frp = float(hotspot_data.get('frp', 0))
    if frp > 500:
        score += 3
    elif frp > 100:
        score += 2
    elif frp > 20:
        score += 1
        
    # 2. Proximity factor
    dist_set = geo_context.get('nearest_settlement_m')
    dist_for = geo_context.get('nearest_forest_m')
    
    if dist_set is not None:
        if dist_set < 1000:
            score += 3
        elif dist_set < 3000:
            score += 1
            
    if dist_for is not None and classification == "wildfire":
        if dist_for < 500:
            score += 2
            
    # 3. Classification factor
    if classification == "industrial" or classification == "gas_flare":
        # Industrial burns are usually controlled
        score -= 2
        
    # Final Risk mapping
    if score >= 5:
        return "CRITICAL"
    elif score >= 3:
        return "HIGH"
    elif score >= 1:
        return "MODERATE"
    else:
        return "LOW"
