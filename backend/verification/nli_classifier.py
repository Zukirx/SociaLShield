import torch
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class NLIClassifier:
    """
    Direct Natural Language Inference (NLI) classifier using native MNLI premise-hypothesis pairs.
    Evaluates:
      Premise:   The evidence snippet from a news organization or fact checker
      Hypothesis: The user's submitted claim
    Directly predicts: Entailment (SUPPORTS), Contradiction (REFUTES), or Neutral.
    """

    MODEL_NAME = "facebook/bart-large-mnli"

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.contra_idx = 0
        self.neutral_idx = 1
        self.entail_idx = 2

        if not TRANSFORMERS_AVAILABLE:
            print("[NLI] transformers not available, using keyword fallback.")
            return

        try:
            device = 0 if torch.cuda.is_available() else -1
            print(f"[NLI] Loading native MNLI model: {self.MODEL_NAME} ...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
            if device >= 0:
                self.model = self.model.to(device)
            self.model.eval()

            # Map config id2label
            id2label = {int(k): v.lower() for k, v in self.model.config.id2label.items()}
            label2id = {v: k for k, v in id2label.items()}
            self.contra_idx = label2id.get("contradiction", 0)
            self.neutral_idx = label2id.get("neutral", 1)
            self.entail_idx = label2id.get("entailment", 2)
            print("[NLI] Native MNLI model loaded successfully.")
        except Exception as e:
            print(f"[NLI] Failed to load model: {e}")
            self.model = None

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
        min_required = 1 if len(claim_words) <= 2 else 2
        return matches >= min_required

    def classify_stance(self, claim: str, source_text: str, title: str = "") -> str:
        src_lower = (source_text + " " + title).lower()

        # 1. Check for headline corroboration
        # When a news outlet's title directly reports the claim without debunking words, it is corroboration
        import re
        stopwords = {
            "about", "after", "all", "and", "are", "for", "from", "has", "have", "into",
            "not", "the", "their", "this", "with", "news", "today", "breaking", "amid"
        }
        claim_words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{3,}\b', claim) if w.lower() not in stopwords]
        title_lower = title.lower()
        has_debunk = any(w in src_lower for w in ["false", "debunk", "hoax", "myth", "fake", "fact-check", "fact check", "misleading", "disproven"])

        if claim_words and title_lower and not has_debunk:
            title_matches = sum(1 for w in claim_words if w in title_lower)
            if title_matches >= max(2, int(len(claim_words) * 0.5)):
                return "SUPPORTS"

        # 2. Check topic relevance
        if not self._has_topic_relevance(claim, source_text):
            return "NEUTRAL"

        # 3. Explicit Fact-Check & Debunking heuristics
        refute_markers = [
            "fact check:", "fact-check", "debunked", "false claim", "claim is false",
            "no evidence", "untrue", "disproven", "hoax", "myth", "fake news", "baseless",
            "unfounded", "denies reports", "refutes claim", "no proof", "conspiracy theory",
            "doctored image", "altered video", "fabricated", "misleading claim", "fake report"
        ]
        if any(marker in src_lower for marker in refute_markers):
            return "REFUTES"

        # 4. If transformer model is not loaded, use keyword heuristic
        if not self.model or not self.tokenizer:
            return self._keyword_fallback(claim, source_text)

        # 5. Direct MNLI inference
        # Premise = Evidence (source snippet), Hypothesis = Claim
        try:
            premise = source_text[:450]
            hypothesis = claim[:200]
            device = next(self.model.parameters()).device

            inputs = self.tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]

            p_contra = probs[self.contra_idx].item()
            p_neutral = probs[self.neutral_idx].item()
            p_entail = probs[self.entail_idx].item()

            # For an article to REFUTE, it must either have debunking terms OR directly contradict the same entities
            has_debunk_words = any(w in src_lower for w in ["false", "fake", "hoax", "myth", "debunk", "untrue", "misleading", "baseless", "denies", "denied", "no evidence"])
            
            # Extract proper nouns from claim
            proper_nouns = [w.lower() for w in re.findall(r'\b[A-Z][a-z0-9]+\b', claim) if len(w) > 3 and w.lower() not in {"delhi", "india", "news", "today", "police", "court"}]
            has_same_entities = all(p in src_lower for p in proper_nouns) if proper_nouns else True

            if has_debunk_words and p_contra > 0.40:
                return "REFUTES"
            elif p_contra >= 0.75 and p_contra > (p_entail * 2.0) and has_same_entities:
                return "REFUTES"
            elif p_entail >= 0.15 and p_entail > p_contra:
                return "SUPPORTS"
            else:
                return self._keyword_fallback(claim, source_text)

        except Exception as e:
            print(f"[NLI] Inference error: {e}")
            return self._keyword_fallback(claim, source_text)

    def _keyword_fallback(self, claim: str, source_text: str) -> str:
        """Lightweight keyword heuristic."""
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
            "authorities confirmed", "evidence proves", "verified by", "successfully",
            "launches", "announced", "reported", "placed in orbit"
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
