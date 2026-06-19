"""
LLM-powered entity and relationship extraction pipeline.

When an episode is submitted via ``client.graph.add_batch()`` or
``client.graph.add()``, it is inserted into SQLite with ``processed=False``
and submitted to a ``ThreadPoolExecutor``.  A background worker calls the LLM,
extracts entities/relationships according to the stored ontology, upserts them
into the graph, generates embeddings for new items, and marks the episode
``processed=True``.

The polling contract (``client.graph.episode.get(uuid_=...)`` checking
``.processed``) remains identical to the Zep pattern used by
``graph_builder._wait_for_episodes``.
"""

from __future__ import annotations

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from .embedder import get_embedder
from .models import EpisodeData, KGEdge, KGEpisode, KGNode, KGOntology
from .store import SQLiteStore, get_store
from ...utils.logger import get_logger

logger = get_logger("campaignsim.kg.extractor")

_EXTRACTOR_WORKERS = 2
_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = ThreadPoolExecutor(
                    max_workers=_EXTRACTOR_WORKERS,
                    thread_name_prefix="kg-extractor",
                )
    return _executor


# ---------------------------------------------------------------------------
# Public helpers called by client.py
# ---------------------------------------------------------------------------

def submit_episode(graph_id: str, episode: KGEpisode, store: SQLiteStore) -> None:
    """Insert episode and schedule background extraction."""
    store.insert_episode(episode)
    _get_executor().submit(_safe_process_episode, graph_id, episode.uuid_, store)


def submit_episodes_batch(
    graph_id: str, episodes: List[KGEpisode], store: SQLiteStore
) -> None:
    """Insert all episodes then schedule extraction for each."""
    for ep in episodes:
        store.insert_episode(ep)
    for ep in episodes:
        _get_executor().submit(_safe_process_episode, graph_id, ep.uuid_, store)


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def _safe_process_episode(graph_id: str, episode_uuid: str, store: SQLiteStore) -> None:
    try:
        _process_episode(graph_id, episode_uuid, store)
    except Exception as exc:
        logger.error(f"Episode extraction failed [{episode_uuid[:8]}]: {exc}")
        # Still mark processed so polling doesn't hang forever
        store.mark_episode_processed(episode_uuid)


def _process_episode(graph_id: str, episode_uuid: str, store: SQLiteStore) -> None:
    episode = store.get_episode(episode_uuid)
    if episode is None or episode.processed:
        return

    ontology = store.get_ontology()
    if not ontology.entity_types:
        # No ontology yet — cannot extract typed entities; mark done
        store.mark_episode_processed(episode_uuid)
        return

    logger.debug(f"Extracting from episode [{episode_uuid[:8]}] ({len(episode.data)} chars)")

    nodes_data, edges_data = _extract_with_llm(episode.data, ontology)

    # Upsert nodes first, collect uuid map
    node_uuid_map: Dict[str, str] = {}  # name_lower -> uuid
    new_nodes: List[KGNode] = []

    for nd in nodes_data:
        node = KGNode.create(
            name=nd["name"],
            labels=[nd["type"]] if nd["type"] else [],
            summary=nd.get("summary", ""),
            attributes=nd.get("attributes", {}),
        )
        stored = store.upsert_node(node)
        node_uuid_map[nd["name"].strip().lower()] = stored.uuid
        if stored.uuid == node.uuid:  # was actually inserted (not merged)
            new_nodes.append(stored)

    # Generate embeddings for new nodes in one batch call
    if new_nodes:
        texts = [f"{n.name}: {n.summary}" for n in new_nodes]
        try:
            embeddings = get_embedder().embed_texts(texts)
            for n, emb in zip(new_nodes, embeddings):
                store.update_node_embedding(n.uuid, emb)
        except Exception as exc:
            logger.warning(f"Node embedding batch failed: {exc}")

    # Upsert edges
    new_edges: List[KGEdge] = []
    for ed in edges_data:
        src_uuid = node_uuid_map.get(ed["source"].strip().lower())
        tgt_uuid = node_uuid_map.get(ed["target"].strip().lower())

        # Attempt to resolve via store if not in local map (pre-existing nodes)
        if src_uuid is None:
            src_node = store.get_node_by_name(ed["source"])
            if src_node:
                src_uuid = src_node.uuid
        if tgt_uuid is None:
            tgt_node = store.get_node_by_name(ed["target"])
            if tgt_node:
                tgt_uuid = tgt_node.uuid

        if src_uuid is None or tgt_uuid is None:
            logger.debug(
                f"Skipping edge '{ed['type']}' — could not resolve "
                f"'{ed['source']}' or '{ed['target']}'"
            )
            continue

        edge = KGEdge.create(
            name=ed["type"],
            fact=ed.get("fact", ""),
            source_node_uuid=src_uuid,
            target_node_uuid=tgt_uuid,
            episode_uuid=episode_uuid,
        )
        stored_edge = store.upsert_edge(edge)
        if stored_edge.uuid == edge.uuid:
            new_edges.append(stored_edge)

    # Generate embeddings for new edges
    if new_edges:
        texts = [e.fact for e in new_edges]
        try:
            embeddings = get_embedder().embed_texts(texts)
            for e, emb in zip(new_edges, embeddings):
                store.update_edge_embedding(e.uuid, emb)
        except Exception as exc:
            logger.warning(f"Edge embedding batch failed: {exc}")

    store.mark_episode_processed(episode_uuid)
    logger.info(
        f"Episode [{episode_uuid[:8]}] done: "
        f"+{len(new_nodes)} nodes, +{len(new_edges)} edges"
    )


# ---------------------------------------------------------------------------
# LLM extraction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a knowledge graph extraction engine.
Given text and an ontology, extract entities and relationships.
Return ONLY valid JSON — no markdown, no explanation.
"""

_USER_TEMPLATE = """\
ONTOLOGY
Entity types (extract ONLY these): {entity_types}
Edge types (use ONLY these): {edge_types}

TEXT
{text}

Extract all entities and relationships that appear in the text and match the ontology.
Each entity must have a "name" (exact name as it appears), "type" (one of the entity types above), and a 1–2 sentence "summary".
Each relationship must have "source" (entity name), "target" (entity name), "type" (one of the edge types above), and a "fact" sentence.
Do not invent types not listed in the ontology.

Respond with ONLY this JSON structure:
{{
  "entities": [{{"name": "...", "type": "...", "summary": "..."}}],
  "relationships": [{{"source": "...", "target": "...", "type": "...", "fact": "..."}}]
}}
"""


def _extract_with_llm(
    text: str,
    ontology: KGOntology,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Call the configured LLM to extract entities and relationships.
    Returns (entities_list, relationships_list).
    Falls back to empty lists on any error.
    """
    from ...utils.llm_client import LLMClient

    entity_types_str = ", ".join(ontology.entity_type_names())
    edge_types_str = ", ".join(ontology.edge_type_names())

    user_msg = _USER_TEMPLATE.format(
        entity_types=entity_types_str,
        edge_types=edge_types_str,
        text=text[:4000],  # guard against oversized chunks
    )

    try:
        llm = LLMClient()
        raw = llm.chat(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=2048,
        )

        parsed = _parse_json_response(raw)
        entities = parsed.get("entities", [])
        relationships = parsed.get("relationships", [])

        # Validate types against ontology
        valid_entity_types = set(ontology.entity_type_names())
        valid_edge_types = set(ontology.edge_type_names())

        entities = [
            e for e in entities
            if isinstance(e, dict)
            and e.get("name")
            and e.get("type") in valid_entity_types
        ]
        relationships = [
            r for r in relationships
            if isinstance(r, dict)
            and r.get("source")
            and r.get("target")
            and r.get("type") in valid_edge_types
        ]

        return entities, relationships

    except Exception as exc:
        logger.warning(f"LLM extraction failed: {exc!s:.200}")
        return [], []


def _parse_json_response(raw: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM output.  Handles common issues:
    - Markdown code fences
    - Trailing commas
    - Partial responses
    """
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", raw).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract first JSON object
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidate = match.group(0)
        # Remove trailing commas before ] or }
        candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse LLM JSON response")
    return {}
