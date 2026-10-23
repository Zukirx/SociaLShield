from .retriever import retrieve_sources
from .nli_classifier import get_classifier


def verify_claim(claim: str):
    """
    Retrieves sources from multiple news outlets and classifies stance to generate
    a weighted Source Consensus Metric (s_fact).

    Credible domain sources are weighted 2x vs. generic web sources (0.5x) so that
    a Reuters/BBC article carries more weight than a random blog post.
    """
    sources = retrieve_sources(claim, max_results=6)
    classifier = get_classifier()

    weighted_support = 0.0
    weighted_refute  = 0.0
    weighted_neutral = 0.0

    analyzed_sources = []

    for source in sources:
        stance  = classifier.classify_stance(claim, source["snippet"])
        weight  = source.get("credibility_weight", 0.5)

        if stance == "SUPPORTS":
            weighted_support += weight
        elif stance == "REFUTES":
            weighted_refute += weight
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

    total_weight = weighted_support + weighted_refute + weighted_neutral

    if total_weight == 0:
        s_fact = 0.5  # Neutral fallback – no sources found
    else:
        # Weighted consensus: support pushes toward 1.0, refute toward 0.0
        s_fact = (weighted_support + (0.5 * weighted_neutral)) / total_weight

    return {
        "s_fact":            round(s_fact, 4),
        "analyzed_sources":  analyzed_sources,
    }
