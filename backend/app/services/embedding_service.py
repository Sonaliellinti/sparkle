"""
Sentence-embedding service — used ONLY to compare a student's free-text
reasoning against known misconception phrasings (semantic similarity).
This is descriptive signal for the diagnosis engine, never grading:
correctness always comes from `selected_option == correct_option`.

Model: all-MiniLM-L6-v2 (sentence-transformers), loaded once as a lazy
singleton so the (relatively slow) model load only happens once per
process, not per request.

Offline fallback: sentence-transformers downloads its model weights
from the Hugging Face Hub on first use. If that download is unavailable
(no internet, blocked network, air-gapped grading box) this module
falls back to a deterministic token-overlap similarity so the rest of
the app keeps working — degraded signal quality, but never a crash.
This mirrors the same "never crash, degrade gracefully" pattern used
for the Groq integration.
"""
import re
from functools import lru_cache
from typing import Optional

import numpy as np

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None
_model_load_attempted = False


def _try_load_model():
    global _model, _model_load_attempted
    if _model_load_attempted:
        return _model
    _model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(_MODEL_NAME)
    except Exception as exc:  # noqa: BLE001 — deliberately broad: any failure = fallback
        print(f"[embedding_service] Falling back to token-overlap similarity ({exc}).")
        _model = None
    return _model


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def _token_overlap_similarity(a: str, b: str) -> float:
    """Jaccard similarity over lowercase word tokens — deterministic,
    dependency-free fallback used only if the transformer model can't load."""
    tokens_a, tokens_b = _tokenize(a), _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union else 0.0


def embed(text: str) -> Optional[np.ndarray]:
    """Returns a sentence embedding, or None if the model is unavailable
    (caller should use `similarity()` instead, which handles the fallback)."""
    model = _try_load_model()
    if model is None:
        return None
    return model.encode(text, normalize_embeddings=True)


def similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity between two texts in [0, 1] via the transformer
    model, or Jaccard token-overlap similarity if the model isn't available."""
    if not text_a.strip() or not text_b.strip():
        return 0.0

    model = _try_load_model()
    if model is not None:
        vec_a = model.encode(text_a, normalize_embeddings=True)
        vec_b = model.encode(text_b, normalize_embeddings=True)
        cosine = float(np.dot(vec_a, vec_b))
        return max(0.0, min(1.0, (cosine + 1) / 2))  # map [-1,1] -> [0,1]

    return _token_overlap_similarity(text_a, text_b)


def misconception_similarity(
    reasoning_text: str, misconceptions: list[str], threshold: float = 0.55
) -> list[tuple[str, float]]:
    """Compares a student's reasoning text against a list of known
    misconception phrasings for a concept. Returns (label, score) pairs
    that meet `threshold`, sorted by score descending. Empty list if the
    student left no reasoning or nothing matched."""
    if not reasoning_text.strip():
        return []

    scored = [(m, similarity(reasoning_text, m)) for m in misconceptions]
    matches = [(label, score) for label, score in scored if score >= threshold]
    matches.sort(key=lambda pair: pair[1], reverse=True)
    return matches
