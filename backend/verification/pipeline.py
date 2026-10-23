import re
from .retriever import retrieve_sources
from .nli_classifier import get_classifier

# Known viral hoaxes, conspiracy theories, and scam patterns
KNOWN_HOAX_PATTERNS = [
    r"\bearth is flat\b", r"\bflat earth\b", r"\bice wall\b",
    r"\bmicrochip(s)? in vaccine\b", r"\bvaccine.*microchip\b", r"\bvaccine.*track(ing)?\b",
    r"\b5g.*(virus|covid|corona|cancer|sickness)\b",
    r"\bdrink(ing)? bleach\b", r"\bchlorine dioxide.*cure\b",
    r"\bfree (recharge|5000|10000|money|cash|laptop|iphone|gift).*click\b",
    r"\bwin.*lottery.*click link\b", r"\bclick link to claim\b",
    r"\basteroid.*destroy(ing)? earth tomorrow\b", r"\bearth.*destroyed tomorrow\b",
    r"\bbank(s)?.*(freeze|frozen|shutting down).*tomorrow\b",
    r"\bwho admits.*vaccine.*(microchip|poison|depopulation)\b",
    r"\bsecret alien base\b", r"\baliens landing tomorrow\b",
]

SENSATIONAL_HOAX_MARKERS = [
    "breaking news:", "urgent warning", "shocking truth", "government admits",
    "hidden truth", "they don't want you to know", "secret exposed",
    "miracle cure", "illuminati", "deep state depopulation"
]


def verify_claim(claim: str):
    """
    Retrieves sources from multiple news outlets and classifies stance to generate
    a weighted Source Consensus Metric (s_fact) and an explicit Veracity Verdict.
    """
    clean_claim = claim.strip()
    claim_lower = clean_claim.lower()

    # 1. Fast check for known viral hoaxes
    is_known_hoax = any(re.search(pat, claim_lower) for pat in KNOWN_HOAX_PATTERNS)

    sources = retrieve_sources(clean_claim, max_results=6)
    classifier = get_classifier()

    weighted_support = 0.0
    weighted_refute  = 0.0
    weighted_neutral = 0.0
    refuted_count    = 0
    supported_count  = 0

    analyzed_sources = []

    for source in sources:
        stance  = classifier.classify_stance(clean_claim, source["snippet"])
        weight  = source.get("credibility_weight", 0.5)

        if stance == "SUPPORTS":
            weighted_support += weight
            supported_count  += 1
        elif stance == "REFUTES":
            weighted_refute += weight
            refuted_count   += 1
        else:
            weighted_neutral += weight

        analyzed_sources.append({
            "title":              source.get("title", ""),
            "snippet":            source.get("snippet", ""),
            "link":               source.get("link", ""),
            "source":             source.get("source", "Web"),
            "category":           source.get("category", ""),
            "source_type":        source.get("source_type", "Web / Digital Media"),
            "credibility_weight": weight,
            "stance":             stance,
        })

    # If it's a known hoax, ensure at least one synthetic/retrieved refutation is recognized
    if is_known_hoax:
        weighted_refute = max(weighted_refute, 2.0)
        refuted_count = max(refuted_count, 1)

    # 2. Determine explicit Veracity Verdict and consensus score (s_fact)
    if is_known_hoax or (refuted_count > 0 and weighted_refute >= weighted_support):
        s_fact = 0.05 if is_known_hoax else max(0.05, round(0.18 - (weighted_refute * 0.04), 4))
        verdict = "FAKE"
        verdict_label = "🚨 FAKE NEWS / FABRICATED"
        verdict_description = f"Refuted by {refuted_count} credible source(s) or identified as a known viral hoax."
    elif supported_count > 0 and refuted_count == 0:
        s_fact = min(0.95, round(0.72 + (weighted_support * 0.08), 4))
        verdict = "VERIFIED"
        verdict_label = "✅ VERIFIED FACT"
        verdict_description = f"Corroborated by {supported_count} reputable news organization(s)."
    elif (weighted_support + weighted_refute) == 0:
        # No sources directly confirmed or refuted
        is_sensational = any(m in claim_lower for m in SENSATIONAL_HOAX_MARKERS)
        if is_sensational:
            s_fact = 0.12
            verdict = "FAKE"
            verdict_label = "🚨 LIKELY FAKE / UNSUBSTANTIATED"
            verdict_description = "Sensational viral claim with ZERO corroboration from any recognized news outlet."
        else:
            s_fact = 0.45
            verdict = "UNVERIFIED"
            verdict_label = "⚠️ UNVERIFIED CLAIM"
            verdict_description = "No corroborating or refuting reports found across monitored newsrooms."
    else:
        # Mixed support and refute
        s_fact = round((weighted_support + (0.3 * weighted_neutral)) / (weighted_support + weighted_refute + weighted_neutral), 4)
        if s_fact < 0.35:
            verdict = "FAKE"
            verdict_label = "🚨 PREDOMINANTLY FALSE"
            verdict_description = "Evidence heavily contradicts this claim."
        elif s_fact < 0.60:
            verdict = "DISPUTED"
            verdict_label = "🟡 DISPUTED / UNCONFIRMED"
            verdict_description = "Conflicting evidence from multiple sources."
        else:
            verdict = "VERIFIED"
            verdict_label = "✅ GENERALLY TRUE"
            verdict_description = "Mostly supported by credible sources."

    return {
        "s_fact":              round(s_fact, 4),
        "verdict":             verdict,
        "verdict_label":       verdict_label,
        "verdict_description": verdict_description,
        "refuted_count":       refuted_count,
        "supported_count":     supported_count,
        "analyzed_sources":    analyzed_sources,
    }
