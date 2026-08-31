"""
Embedding generation for the local knowledge graph.

Primary:  OpenAI-compatible ``/v1/embeddings`` endpoint, configured via
          EMBEDDING_API_KEY/EMBEDDING_BASE_URL — separate from the chat LLM
          config, since not every chat provider (e.g. DeepSeek) exposes
          embeddings. Falls back to the chat LLM's own credentials if unset.
Fallback: feature hashing (HashingVectorizer) via scikit-learn, used when
          the embeddings endpoint is unavailable or returns an error.

Feature hashing is stateless and always produces a fixed-size vector
regardless of how many texts are passed in a call or what corpus has been
seen before — unlike a corpus-fit TF-IDF+SVD model (the previous approach
here), whose output dimensionality depended on how many texts were in each
individual call. That meant a single search query (1 text) and a batch of
graph edges (N texts) landed in *different-sized* vector spaces and could
never be compared — see the `ValueError: shapes (1,) and (8,) not aligned`
crash this replaced. Every call now lands in the same _EMBEDDING_DIM_TFIDF
dimensions, so query and index vectors are always comparable.
"""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any, Dict, List, Optional

from ...utils.logger import get_logger

logger = get_logger("campaignsim.kg.embedder")

_EMBEDDING_MODEL = "text-embedding-3-small"
_EMBEDDING_DIM_TFIDF = 256  # SVD target dimension for fallback vectors
_BATCH_SIZE = 100           # max texts per API call
_COOLDOWN_SECONDS = 60      # after a failure, skip the real API for this long before retrying


class Embedder:
    """
    Singleton-per-config embedding generator.

    Usage::

        emb = Embedder(api_key=..., base_url=..., model="text-embedding-3-small")
        vectors = emb.embed_texts(["hello world", "foo bar"])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        from ...config import Config  # lazy import to avoid circular deps

        self._api_key = api_key or Config.EMBEDDING_API_KEY or ""
        self._base_url = base_url or Config.EMBEDDING_BASE_URL or "https://api.openai.com/v1"
        self._model = model or Config.EMBEDDING_MODEL_NAME or _EMBEDDING_MODEL

        # Epoch (time.monotonic) until which the real API is skipped in favor
        # of the fallback — 0 means "never failed, always try it". A single
        # failure used to latch this off permanently for the process's whole
        # lifetime (a transient rate-limit or network blip meant every graph
        # search silently used the weaker fallback until the next restart);
        # a bounded cooldown lets it self-heal instead.
        self._unavailable_until: float = 0.0
        self._dim: Optional[int] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Return one embedding vector per text. Never raises."""
        if not texts:
            return []
        clean = [t.replace("\n", " ").strip() for t in texts]
        if time.monotonic() >= self._unavailable_until:
            try:
                result = self._embed_via_api(clean)
                self._unavailable_until = 0.0  # success — clear any prior cooldown
                return result
            except Exception as exc:
                logger.warning(
                    f"Embedding API unavailable ({exc!s:.120}), "
                    f"falling back to TF-IDF for {_COOLDOWN_SECONDS}s"
                )
                self._unavailable_until = time.monotonic() + _COOLDOWN_SECONDS

        return self._embed_via_tfidf(clean)

    def embed_single(self, text: str) -> List[float]:
        result = self.embed_texts([text])
        return result[0] if result else []

    # ------------------------------------------------------------------
    # OpenAI-shaped embeddings API (OpenAI itself, Voyage AI, or any other
    # provider whose /embeddings endpoint accepts {input, model} and returns
    # {data: [{embedding, index}]}) — called directly via requests instead of
    # the openai SDK, since the SDK's response model validates fields (e.g.
    # usage.prompt_tokens) that a third-party provider like Voyage doesn't
    # always send, and this only ever reads .data[].embedding/.index anyway.
    # ------------------------------------------------------------------

    def _embed_via_api(self, texts: List[str]) -> List[List[float]]:
        import requests

        url = f"{self._base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            response = requests.post(
                url, headers=headers, json={"input": batch, "model": self._model}, timeout=30,
            )
            response.raise_for_status()
            data = response.json()["data"]
            # Sort by index to handle any re-ordering
            sorted_data = sorted(data, key=lambda d: d["index"])
            all_embeddings.extend([d["embedding"] for d in sorted_data])

        if all_embeddings and self._dim is None:
            self._dim = len(all_embeddings[0])

        return all_embeddings

    # ------------------------------------------------------------------
    # Feature-hashing fallback
    # ------------------------------------------------------------------

    def _embed_via_tfidf(self, texts: List[str]) -> List[List[float]]:
        """
        Produce dense vectors via feature hashing (HashingVectorizer).

        Stateless and corpus-independent: the output is always exactly
        _EMBEDDING_DIM_TFIDF dimensions, whether embedding a single query
        string or a batch of hundreds of texts, so vectors from any two
        calls are always directly comparable via cosine similarity.
        """
        try:
            from sklearn.feature_extraction.text import HashingVectorizer
            from sklearn.preprocessing import normalize

            vectorizer = HashingVectorizer(
                n_features=_EMBEDDING_DIM_TFIDF,
                ngram_range=(1, 2),
                alternate_sign=False,
                norm=None,
            )
            dense = vectorizer.transform(texts).toarray()
            dense = normalize(dense, norm="l2")
            return dense.tolist()

        except ImportError:
            logger.error("scikit-learn not installed — cannot generate fallback embeddings")
            # Last resort: zero vectors so downstream code doesn't crash
            return [[0.0] * _EMBEDDING_DIM_TFIDF for _ in texts]
        except Exception as exc:
            logger.error(f"Fallback embedding failed: {exc}")
            return [[0.0] * _EMBEDDING_DIM_TFIDF for _ in texts]


# ---------------------------------------------------------------------------
# Module-level singleton (lazy, config-driven)
# ---------------------------------------------------------------------------

_singleton: Optional[Embedder] = None
_singleton_lock = threading.Lock()


def get_embedder() -> Embedder:
    """Return the shared Embedder instance (created on first call)."""
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = Embedder()
    return _singleton
