def generate_explanation(risk_tier: str, verification_result: dict, credibility: float, diffusion):
    verdict = verification_result.get("verdict", "")
    verdict_label = verification_result.get("verdict_label", "")
    verdict_desc = verification_result.get("verdict_description", "")
    
    sources = verification_result.get('analyzed_sources', [])
    refuted_count = verification_result.get('refuted_count', sum(1 for s in sources if s['stance'] == "REFUTES"))
    supported_count = verification_result.get('supported_count', sum(1 for s in sources if s['stance'] == "SUPPORTS"))

    # Verdict prefix
    if verdict == "FAKE":
        explanation = f"🚨 FAKE NEWS DETECTED — {verdict_desc} "
    elif verdict == "VERIFIED":
        explanation = f"✅ VERIFIED FACTUAL — {verdict_desc} "
    elif verdict == "UNVERIFIED":
        explanation = f"⚠️ UNVERIFIED CLAIM — {verdict_desc} "
    else:
        explanation = f"🟡 DISPUTED CLAIM — {verdict_desc} "

    if refuted_count > 0:
        explanation += f"Contradicted/debunked by {refuted_count} reputable source(s). "
    elif supported_count > 0:
        explanation += f"Corroborated by {supported_count} source(s). "
        
    explanation += f"Account credibility index: {credibility:.2f}. "
    
    # Handle dict or float diffusion
    diffusion_score = diffusion.get("score", 0.5) if isinstance(diffusion, dict) else float(diffusion)
    local_news_risk = diffusion.get("local_news_risk", 0.0) if isinstance(diffusion, dict) else 0.0
    
    if diffusion_score > 0.6:
        explanation += "High viral velocity detected across social channels. "
    elif diffusion_score < 0.25:
        explanation += "Contained to social seeding stage. "

    if local_news_risk >= 0.5:
        explanation += f"URGENT: High risk of spilling over into regional & local language news desks ({int(local_news_risk*100)}%). "
        
    if verdict == "FAKE" or risk_tier == "Critical":
        action = "🚨 IMMEDIATE ACTION: Append prominent 'False Information / Debunked' interstitial warning, downrank viral spread algorithms, and dispatch press advisory."
    elif risk_tier == "High":
        action = "⚠️ WARNING: Downrank recommendation algorithms, append Fact-Check links, and flag for newsroom review."
    elif risk_tier == "Medium":
        action = "Contextual Clarification and verified reference links appended."
    else:
        action = "No intervention needed. Factual consensus verified."
        
    return {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "summary": explanation.strip(),
        "recommended_action": action
    }
