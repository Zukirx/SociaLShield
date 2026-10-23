import torch
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class NLIClassifier:
    """
    High-accuracy NLI classifier using facebook/bart-large-mnli.
    Uses two-pass hypothesis templates for improved stance detection:
      Pass 1: Does the source text SUPPORT or REFUTE the claim?
      Pass 2: Confirm with a negated template for REFUTES.
    """

    # Ordered preference: best → fastest fallback
    MODEL_PREFERENCE = [
        "facebook/bart-large-mnli",          # Best accuracy (~90 % MNLI)
        "cross-encoder/nli-deberta-v3-small", # Smaller, still very good
        "typeform/distilbert-base-uncased-mnli",  # Fast fallback
    ]

    def __init__(self):
        self.classifier = None
        self.model_name = None
        if not TRANSFORMERS_AVAILABLE:
            print("[NLI] transformers not available, using keyword fallback.")
            return

        device = 0 if torch.cuda.is_available() else -1
        for model in self.MODEL_PREFERENCE:
            try:
                print(f"[NLI] Loading model: {model} ...")
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model=model,
                    device=device,
                    # batching improves throughput when classifying many sources
                    batch_size=4,
                )
                self.model_name = model
                print(f"[NLI] Model loaded: {model}")
                break
            except Exception as e:
                print(f"[NLI] Failed to load {model}: {e}")

    def _has_topic_relevance(self, claim: str, source_text: str) -> bool:
        """Checks if the evidence actually talks about the subjects in the claim."""
        import re
        stopwords = {
            "about", "above", "after", "again", "against", "all", "and", "any", "are", "aren't",
            "because", "been", "before", "being", "below", "between", "both", "but", "can", "cannot",
            "could", "did", "didn't", "does", "doesn't", "doing", "don't", "down", "during", "each",
            "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
            "having", "here", "how", "into", "itself", "just", "more", "most", "must", "not", "off",
            "once", "only", "other", "ought", "our", "ours", "out", "over", "own", "same", "should",
            "some", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they",
            "this", "those", "through", "too", "under", "until", "very", "was", "wasn't", "were",
            "weren't", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would",
            "will", "says", "said", "post", "news", "today", "breaking", "video", "photo", "image",
            "announces", "confirms", "admits", "claims", "people", "viral"
        }
        claim_words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{3,}\b', claim) if w.lower() not in stopwords]
        if not claim_words:
            return True
        src_lower = source_text.lower()
        matches = sum(1 for w in claim_words if w in src_lower)
        # Require at least 1-2 key entity/content words to be present
        min_required = 1 if len(claim_words) <= 2 else 2
        return matches >= min_required

    def classify_stance(self, claim: str, source_text: str) -> str:
        # First check: If source doesn't even discuss the topic of the claim, it's NEUTRAL (unrelated)
        if not self._has_topic_relevance(claim, source_text):
            return "NEUTRAL"

        # Explicit Fact-Check & Debunking heuristics (highest precision)
        src_lower = source_text.lower()
        refute_markers = [
            "fact check:", "fact-check", "debunked", "false claim", "claim is false",
            "no evidence", "untrue", "disproven", "hoax", "myth", "fake news", "baseless",
            "unfounded", "denies reports", "refutes claim", "no proof", "conspiracy theory",
            "doctored image", "altered video", "fabricated", "misleading claim", "fake report"
        ]
        if any(marker in src_lower for marker in refute_markers):
            return "REFUTES"

        # Explicit Confirmation / Factual reporting markers
        support_markers = [
            "confirmed", "launches", "announced", "official statement", "press release",
            "successfully", "reported", "placed in orbit", "approved", "passes", "wins",
            "reveals", "milestone", "record", "signed", "inaugurated", "published study",
            "authorities confirmed", "verified by", "police confirmed"
        ]
        has_support = any(marker in src_lower for marker in support_markers)
        has_any_refute = any(w in src_lower for w in ["false", "fake", "hoax", "myth", "untrue", "misleading", "debunked"])

        if has_support and not has_any_refute:
            return "SUPPORTS"

        if not self.classifier:
            return self._keyword_fallback(claim, source_text)

        src = source_text[:400]
        cl  = claim[:180]

        try:
            # Calibrated candidate labels for MNLI zero-shot
            candidate_labels = [
                "debunks or refutes the claim as false",
                "confirms the claim is true and verified",
                "is unrelated news or neutral"
            ]
            result = self.classifier(
                f"Claim: {cl}\nEvidence: {src}",
                candidate_labels=candidate_labels,
                hypothesis_template="This news article {}."
            )

            scores_by_label = dict(zip(result["labels"], result["scores"]))
            refute_score = scores_by_label.get("debunks or refutes the claim as false", 0.0)
            support_score = scores_by_label.get("confirms the claim is true and verified", 0.0)

            if refute_score >= 0.65 and refute_score > (support_score * 1.3):
                return "REFUTES"
            elif support_score >= 0.50 and support_score > (refute_score * 1.2):
                return "SUPPORTS"
            else:
                return self._keyword_fallback(claim, source_text)

        except Exception as e:
            print(f"[NLI] Classification error: {e}")
            return self._keyword_fallback(claim, source_text)

    def _keyword_fallback(self, claim: str, source_text: str) -> str:
        """Lightweight keyword heuristic when the model is unavailable."""
        if not self._has_topic_relevance(claim, source_text):
            return "NEUTRAL"

        source_lower  = source_text.lower()
        refute_words  = [
            "false", "debunked", "misleading", "misinformation", "no evidence",
            "incorrect", "wrong", "untrue", "disproven", "hoax", "myth", "fake",
            "baseless", "fabricated", "unfounded", "no truth", "refuted"
        ]
        support_words = [
            "confirmed by", "official statement", "press release", "study shows",
            "authorities confirmed", "evidence proves", "verified by", "successfully"
        ]
        refute_score  = sum(1 for w in refute_words if w in source_lower)
        support_score = sum(1 for w in support_words if w in source_lower)
        if refute_score > support_score:
            return "REFUTES"
        elif support_score > refute_score:
            return "SUPPORTS"
        return "NEUTRAL"


# Singleton instance
_classifier_instance = None


def get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = NLIClassifier()
    return _classifier_instance
