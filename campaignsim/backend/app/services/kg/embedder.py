"""
Embedding generation for the local knowledge graph.

Primary:  OpenAI-compatible ``/v1/embeddings`` endpoint
          (same provider already configured for LLM calls).
Fallback: TF-IDF + SVD (latent semantic analysis) via scikit-learn,
          used when the embeddings endpoint is unavailable or returns an error.

The fallback vectors are re-fitted each call from the current corpus so they
remain in sync with newly added documents.  Performance is adequate for
corpora up to ~10 K items.
"""

from __future__ import annotations

import hashlib
import threading
from typing import Any, Dict, List, Optional

from ...utils.logger import get_logger

logger = get_logger("campaignsim.kg.embedder")

_EMBEDDING_MODEL = "text-embedding-3-small"
_EMBEDDING_DIM_TFIDF = 256  # SVD target dimension for fallback vectors
_BATCH_SIZE = 100           # max texts per API call


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

        self._api_key = api_key or Config.LLM_API_KEY or ""
        self._base_url = base_url or Config.LLM_BASE_URL or "https://api.openai.com/v1"
        self._model = model or _EMBEDDING_MODEL

        self._api_available: Optional[bool] = None  # None = not yet probed
        self._dim: Optional[int] = None
        self._lock = threading.Lock()

        # TF-IDF fallback state
        self._tfidf_vectorizer: Any = None
        self._tfidf_svd: Any = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Return one embedding vector per text. Never raises."""
        if not texts:
            return []
        clean = [t.replace("\n", " ").strip() for t in texts]
        try:
            if self._api_available is not False:
                result = self._embed_via_api(clean)
                self._api_available = True
                return result
        except Exception as exc:
            logger.warning(
                f"Embedding API unavailable ({exc!s:.120}), switching to TF-IDF fallback"
            )
            self._api_available = False

        return self._embed_via_tfidf(clean)

    def embed_single(self, text: str) -> List[float]:
        result = self.embed_texts([text])
        return result[0] if result else []

    # ------------------------------------------------------------------
    # OpenAI-compatible API
    # ------------------------------------------------------------------

    def _embed_via_api(self, texts: List[str]) -> List[List[float]]:
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            response = client.embeddings.create(input=batch, model=self._model)
            # Sort by index to handle any re-ordering
            sorted_data = sorted(response.data, key=lambda d: d.index)
            all_embeddings.extend([d.embedding for d in sorted_data])

        if all_embeddings and self._dim is None:
            self._dim = len(all_embeddings[0])

        return all_embeddings

    # ------------------------------------------------------------------
    # TF-IDF + SVD fallback
    # ------------------------------------------------------------------

    def _embed_via_tfidf(self, texts: List[str]) -> List[List[float]]:
        """
        Produce dense vectors via TF-IDF + TruncatedSVD (LSA).

        The model is re-fitted on the *current* query corpus each call so new
        documents always contribute to the vocabulary.  For retrieval tasks the
        relative similarities are what matter, not cross-call absolute positions.
        """
        try:
            from sklearn.decomposition import TruncatedSVD
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.preprocessing import normalize

            dim = min(_EMBEDDING_DIM_TFIDF, max(1, len(texts) - 1))
            vectorizer = TfidfVectorizer(
                max_features=8192, ngram_range=(1, 2), sublinear_tf=True
            )
            tfidf_matrix = vectorizer.fit_transform(texts)

            if dim >= tfidf_matrix.shape[1]:
                # corpus too small for SVD — use raw TF-IDF
                dense = tfidf_matrix.toarray()
            else:
                svd = TruncatedSVD(n_components=dim, random_state=42)
                dense = svd.fit_transform(tfidf_matrix)

            dense = normalize(dense, norm="l2")
            return dense.tolist()

        except ImportError:
            logger.error("scikit-learn not installed — cannot generate fallback embeddings")
            # Last resort: zero vectors so downstream code doesn't crash
            return [[0.0] * _EMBEDDING_DIM_TFIDF for _ in texts]
        except Exception as exc:
            logger.error(f"TF-IDF embedding failed: {exc}")
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
