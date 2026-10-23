def generate_explanation(risk_tier: str, verification_result: dict, credibility: float, diffusion):
    explanation = f"Flagged {risk_tier}: "
    
    sources = verification_result.get('analyzed_sources', [])
    refuted_count = sum(1 for s in sources if s['stance'] == "REFUTES")
    supported_count = sum(1 for s in sources if s['stance'] == "SUPPORTS")
    
    if refuted_count > 0:
        explanation += f"Refuted by {refuted_count} reputable source(s). "
    elif supported_count > 0:
        explanation += f"Corroborated by {supported_count} source(s). "
    else:
        explanation += "No definitive external corroboration found. "
        
    explanation += f"Author credibility is {credibility:.2f}. "
    
    # Handle dict or float diffusion
    diffusion_score = diffusion.get("score", 0.5) if isinstance(diffusion, dict) else float(diffusion)
    local_news_risk = diffusion.get("local_news_risk", 0.0) if isinstance(diffusion, dict) else 0.0
    
    if diffusion_score > 0.7:
        explanation += "High viral velocity detected across social channels. "
    elif diffusion_score < 0.3:
        explanation += "Low diffusion risk detected. "

    if local_news_risk >= 0.6:
        explanation += f"CRITICAL: High spillover risk into small & regional local news ({int(local_news_risk*100)}%). "
    elif local_news_risk >= 0.35:
        explanation += f"Elevated local community spread risk ({int(local_news_risk*100)}%). "
        
    action = "No action required."
    if risk_tier == "Critical":
        action = "Automatic Assignment of Warning Label, Moderator Escalation & Local Press Advisory."
    elif risk_tier == "High":
        action = "Algorithmic Downranking applied and Fact-Check Banner appended."
    elif risk_tier == "Medium":
        action = "Fact-Check Links and Contextual Clarification appended."
        
    return {
        "summary": explanation.strip(),
        "recommended_action": action
    }
