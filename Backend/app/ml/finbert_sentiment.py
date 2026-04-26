"""FinBERT-based sentiment analyzer for IPO/financial news.
Uses ProsusAI/finbert — fine-tuned on financial text, outputs
positive / neutral / negative probabilities per sentence.
"""
from __future__ import annotations

import re
import threading
from collections import Counter

_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "must", "can",
    "in", "of", "to", "and", "or", "but", "for", "on", "at", "by", "as",
    "with", "from", "into", "over", "after", "before", "about", "than",
    "that", "this", "these", "those", "their", "them", "they", "its",
    "more", "also", "said", "says", "amid", "amid",
    "ipo", "ltd", "limited", "pvt", "private", "india", "indian",
    "company", "firm", "group", "corp", "inc", "platform",
}


class FinBERTSentimentAnalyzer:
    MODEL_NAME = "ProsusAI/finbert"

    def __init__(self):
        self._pipeline = None
        self._lock = threading.Lock()

    def _load(self):
        # Double-checked locking: fast path avoids the lock after first load
        if self._pipeline is not None:
            return
        with self._lock:
            if self._pipeline is not None:
                return
            # Import pipeline inside the lock so only one thread ever triggers
            # the transformers lazy-module __getattr__ for the first time.
            import transformers
            hf_pipeline = transformers.pipeline
            self._pipeline = hf_pipeline(
                "text-classification",
                model=self.MODEL_NAME,
                top_k=None,   # return all label scores (transformers 5.x API)
                device=-1,    # CPU inference
            )

    def analyze(self, texts: list[str]) -> dict:
        """Analyze a list of financial text snippets.

        Returns score (0–100), label, pos/neu/neg percentages, keywords.
        Score formula: positive_pct + 0.5 × neutral_pct → range 0–100.
        """
        if not texts:
            return self._default()
        self._load()
        pos_sum = neu_sum = neg_sum = 0.0
        for text in texts:
            result = self._pipeline(text[:512])[0]
            by_label = {item["label"]: item["score"] for item in result}
            pos_sum += by_label.get("positive", 0.0)
            neu_sum += by_label.get("neutral", 0.0)
            neg_sum += by_label.get("negative", 0.0)
        n = len(texts)
        pos = round(pos_sum / n * 100, 1)
        neu = round(neu_sum / n * 100, 1)
        neg = round(neg_sum / n * 100, 1)
        score = round(min(pos + neu * 0.5, 100.0), 1)
        label = "positive" if score >= 60 else ("negative" if score < 40 else "neutral")
        return {
            "score": score,
            "label": label,
            "positive_pct": pos,
            "neutral_pct": neu,
            "negative_pct": neg,
            "top_keywords": self._keywords(texts),
            "news_volume_7d": len(texts),
        }

    def _keywords(self, texts: list[str], top_n: int = 5) -> list[str]:
        words = re.findall(r"[a-zA-Z]{4,}", " ".join(texts).lower())
        counts = Counter(w for w in words if w not in _STOP_WORDS)
        return [w for w, _ in counts.most_common(top_n)]

    @staticmethod
    def _default() -> dict:
        return {
            "score": 50.0, "label": "neutral",
            "positive_pct": 33.3, "neutral_pct": 33.4, "negative_pct": 33.3,
            "top_keywords": [], "news_volume_7d": 0,
        }
