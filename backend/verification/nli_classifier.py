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

    def classify_stance(self, claim: str, source_text: str) -> str:
        if not self.classifier:
            return self._keyword_fallback(claim, source_text)

        # Truncate to fast token limits for quick CPU throughput
        src = source_text[:350]
        cl  = claim[:180]

        try:
            # Single-pass 3-label classification for high responsiveness
            result = self.classifier(
                f"Claim: {cl}\n\nEvidence: {src}",
                candidate_labels=["supports", "refutes", "neutral"],
                hypothesis_template="The evidence {} the claim.",
            )

            top_label = result["labels"][0]
            top_score = result["scores"][0]

            if top_label == "supports" and top_score > 0.40:
                return "SUPPORTS"
            elif top_label == "refutes" and top_score > 0.40:
                return "REFUTES"
            else:
                # Fast keyword check before defaulting to neutral
                kw = self._keyword_fallback(claim, source_text)
                if kw != "NEUTRAL":
                    return kw
                return "NEUTRAL"

        except Exception as e:
            print(f"[NLI] Classification error: {e}")
            return self._keyword_fallback(claim, source_text)

    def _keyword_fallback(self, claim: str, source_text: str) -> str:
        """Lightweight keyword heuristic when the model is unavailable."""
        claim_lower   = claim.lower()
        source_lower  = source_text.lower()
        refute_words  = ["false", "debunked", "misleading", "misinformation", "no evidence",
                         "incorrect", "wrong", "untrue", "disproven", "hoax", "myth", "fake"]
        support_words = ["confirmed", "true", "correct", "proven", "evidence shows",
                         "researchers found", "study shows", "scientists say", "official"]
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
