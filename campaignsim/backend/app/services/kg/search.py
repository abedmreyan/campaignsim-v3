"""
Semantic search for the local knowledge graph.

Strategy:
  1. Cosine similarity between the query embedding and stored node/edge embeddings.
  2. BM25 keyword search over the same corpus.
  3. Reciprocal Rank Fusion (RRF) to merge both ranked lists into a single ranking.

reranker="cross_encoder" triggers an additional LLM-based relevance-scoring pass
(the LLM is asked to score each candidate 0–10).  This is more expensive but
produces higher-quality rankings for short, specific queries.

scope="nodes" searches node name+summary.
scope="edges" searches edge facts.
scope="both" merges both.

The return type is ``KGSearchResult`` whose ``.edges`` and ``.nodes`` attributes
contain ``KGEdge`` / ``KGNode`` objects — matching the Zep SDK shape accessed
by ``zep_tools.py``, ``campaign_tools.py``, and ``oasis_profile_generator.py``.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .embedder import get_embedder
from .models import KGEdge, KGNode, KGSearchResult
from .store import SQLiteStore
from ...utils.logger import get_logger

logger = get_logger("campaignsim.kg.search")

_RRF_K = 60  # standard RRF constant


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def search(
    store: SQLiteStore,
    query: str,
    limit: int = 10,
    scope: str = "edges",
    reranker: str = "rrf",
) -> KGSearchResult:
    """
    Run a combined semantic + keyword search.

    Args:
        store:    The SQLiteStore for the target graph.
        query:    Natural-language search query.
        limit:    Maximum results to return.
        scope:    ``"edges"``, ``"nodes"``, or ``"both"``.
        reranker: ``"rrf"`` (default) or ``"cross_encoder"`` (LLM reranking).

    Returns:
        KGSearchResult with populated .edges and/or .nodes lists.
    """
    if not query.strip():
        return KGSearchResult(query=query)

    query_emb = get_embedder().embed_single(query)

    result_edges: List[KGEdge] = []
    result_nodes: List[KGNode] = []

    if scope in ("edges", "both"):
        candidates = store.get_all_edges_with_embeddings()
        if not candidates:
            # Fallback: search edges without embeddings using BM25 only
            candidates = store.get_all_edges()

        ranked = _rank(query, query_emb, candidates, key_fn=_edge_text, reranker=reranker)
        top = ranked[:limit]

        if reranker == "cross_encoder" and top:
            top = _llm_rerank(query, top, key_fn=_edge_text)[:limit]

        result_edges = top

    if scope in ("nodes", "both"):
        candidates = store.get_all_nodes_with_embeddings()
        if not candidates:
            candidates = store.get_all_nodes()

        ranked = _rank(query, query_emb, candidates, key_fn=_node_text, reranker=reranker)
        top = ranked[:limit]

        if reranker == "cross_encoder" and top:
            top = _llm_rerank(query, top, key_fn=_node_text)[:limit]

        result_nodes = top

    return KGSearchResult(
        edges=result_edges,
        nodes=result_nodes,
        query=query,
        total_count=len(result_edges) + len(result_nodes),
    )


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def _rank(
    query: str,
    query_emb: List[float],
    candidates: list,
    key_fn,
    reranker: str,
) -> list:
    """Merge cosine similarity and BM25 via RRF."""
    if not candidates:
        return []

    texts = [key_fn(c) for c in candidates]

    # --- Vector ranking ---
    if query_emb and any(c.embedding is not None for c in candidates):
        q = np.array(query_emb, dtype=np.float32)
        cosine_scores: List[float] = []
        for c in candidates:
            if c.embedding is not None:
                v = np.array(c.embedding, dtype=np.float32)
                score = float(np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-10))
            else:
                score = 0.0
            cosine_scores.append(score)
        cosine_ranked = sorted(
            range(len(candidates)), key=lambda i: -cosine_scores[i]
        )
    else:
        cosine_ranked = list(range(len(candidates)))  # unranked

    # --- BM25 ranking ---
    bm25_ranked = _bm25_rank(query, texts)

    # --- RRF merge ---
    rrf_scores: Dict[int, float] = {}
    for rank, idx in enumerate(cosine_ranked):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (_RRF_K + rank + 1)
    for rank, idx in enumerate(bm25_ranked):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (_RRF_K + rank + 1)

    sorted_indices = sorted(rrf_scores, key=lambda i: -rrf_scores[i])
    return [candidates[i] for i in sorted_indices]


# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------

def _bm25_rank(query: str, texts: List[str]) -> List[int]:
    """
    Pure-Python BM25 implementation.  No external dependency required.
    Falls back to TF-IDF style keyword scoring for very small corpora.
    """
    try:
        from rank_bm25 import BM25Okapi

        tokenized_corpus = [_tokenize(t) for t in texts]
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(_tokenize(query))
        return sorted(range(len(texts)), key=lambda i: -scores[i])
    except ImportError:
        return _keyword_rank(query, texts)


def _keyword_rank(query: str, texts: List[str]) -> List[int]:
    """Simple keyword overlap fallback when rank-bm25 is not installed."""
    query_tokens = set(_tokenize(query))
    scores = []
    for text in texts:
        text_tokens = set(_tokenize(text))
        score = len(query_tokens & text_tokens)
        scores.append(score)
    return sorted(range(len(texts)), key=lambda i: -scores[i])


def _tokenize(text: str) -> List[str]:
    import re
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


# ---------------------------------------------------------------------------
# LLM cross-encoder reranking
# ---------------------------------------------------------------------------

def _llm_rerank(query: str, candidates: list, key_fn) -> list:
    """
    Ask the LLM to score each candidate's relevance to the query (0–10).
    Falls back to original order on any error.
    """
    from ...utils.llm_client import LLMClient

    try:
        llm = LLMClient()
        numbered = "\n".join(
            f"{i+1}. {key_fn(c)[:300]}" for i, c in enumerate(candidates)
        )
        prompt = (
            f"Query: {query}\n\n"
            f"Candidates:\n{numbered}\n\n"
            "Rate each candidate's relevance to the query on a scale of 0–10. "
            "Return ONLY a JSON array of numbers, one per candidate, e.g. [8, 3, 7]."
        )
        raw = llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=256,
        )
        import json, re
        match = re.search(r"\[[\d\s,\.]+\]", raw)
        if match:
            scores = json.loads(match.group(0))
            if len(scores) == len(candidates):
                return [c for _, c in sorted(zip(scores, candidates), key=lambda x: -x[0])]
    except Exception as exc:
        logger.warning(f"LLM cross-encoder reranking failed: {exc!s:.100}")
    return candidates


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def _edge_text(edge: KGEdge) -> str:
    parts = [edge.fact, edge.name]
    return " ".join(p for p in parts if p)


def _node_text(node: KGNode) -> str:
    parts = [node.name, node.summary]
    return " ".join(p for p in parts if p)

