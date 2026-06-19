"""
SQLite-backed knowledge graph store.

One ``.db`` file per graph, stored at ``{KG_DATA_DIR}/{graph_id}.db``.
All write operations are serialised through a per-store threading.Lock so
the store is safe for use from the simulation's ThreadPoolExecutor and the
ZepGraphMemoryUpdater background thread simultaneously.

Pagination mirrors the Zep cursor-based pattern so that ``zep_paging.py``
(now updated to be client-agnostic) continues to work unmodified.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .models import KGEdge, KGEpisode, KGNode, KGOntology
from ...utils.logger import get_logger

logger = get_logger("campaignsim.kg.store")

_PAGE_SIZE_DEFAULT = 100
_MAX_NODES = 2000

# ---------------------------------------------------------------------------
# Per-graph store registry
# ---------------------------------------------------------------------------

_registry: Dict[str, "SQLiteStore"] = {}
_registry_lock = threading.Lock()


def get_store(graph_id: str, data_dir: str) -> "SQLiteStore":
    """Return (creating if necessary) the SQLiteStore for *graph_id*."""
    with _registry_lock:
        if graph_id not in _registry:
            _registry[graph_id] = SQLiteStore(graph_id, data_dir)
        return _registry[graph_id]


def evict_store(graph_id: str) -> None:
    """Remove a store from the registry (called after graph deletion)."""
    with _registry_lock:
        _registry.pop(graph_id, None)


# ---------------------------------------------------------------------------
# SQLiteStore
# ---------------------------------------------------------------------------

class SQLiteStore:
    """Thread-safe SQLite store for a single knowledge graph."""

    def __init__(self, graph_id: str, data_dir: str):
        self.graph_id = graph_id
        self._data_dir = data_dir
        self._db_path = os.path.join(data_dir, f"{graph_id}.db")
        self._write_lock = threading.Lock()

        os.makedirs(data_dir, exist_ok=True)
        self._init_db()
        logger.info(f"SQLiteStore initialised: {self._db_path}")

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Return a new connection in WAL mode for concurrent read access."""
        conn = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
            timeout=30,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        with self._write_lock, self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS nodes (
                    uuid        TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    name_lower  TEXT NOT NULL,
                    labels      TEXT NOT NULL,
                    summary     TEXT DEFAULT '',
                    attributes  TEXT DEFAULT '{}',
                    embedding   BLOB,
                    created_at  TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_nodes_name_lower ON nodes(name_lower);
                CREATE INDEX IF NOT EXISTS idx_nodes_labels ON nodes(labels);

                CREATE TABLE IF NOT EXISTS edges (
                    uuid              TEXT PRIMARY KEY,
                    name              TEXT NOT NULL,
                    fact              TEXT DEFAULT '',
                    source_node_uuid  TEXT NOT NULL,
                    target_node_uuid  TEXT NOT NULL,
                    attributes        TEXT DEFAULT '{}',
                    embedding         BLOB,
                    created_at        TEXT NOT NULL,
                    valid_at          TEXT,
                    invalid_at        TEXT,
                    expired_at        TEXT,
                    episodes          TEXT DEFAULT '[]',
                    FOREIGN KEY (source_node_uuid) REFERENCES nodes(uuid),
                    FOREIGN KEY (target_node_uuid) REFERENCES nodes(uuid)
                );
                CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_node_uuid);
                CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_uuid);
                CREATE INDEX IF NOT EXISTS idx_edges_name   ON edges(name);

                CREATE TABLE IF NOT EXISTS episodes (
                    uuid        TEXT PRIMARY KEY,
                    data        TEXT NOT NULL,
                    type        TEXT DEFAULT 'text',
                    processed   INTEGER DEFAULT 0,
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ontology (
                    id           INTEGER PRIMARY KEY CHECK (id = 1),
                    entity_types TEXT DEFAULT '[]',
                    edge_types   TEXT DEFAULT '[]'
                );
                INSERT OR IGNORE INTO ontology(id, entity_types, edge_types)
                VALUES (1, '[]', '[]');
            """)

    # ------------------------------------------------------------------
    # Ontology
    # ------------------------------------------------------------------

    def set_ontology(self, ontology: KGOntology) -> None:
        with self._write_lock, self._connect() as conn:
            conn.execute(
                "UPDATE ontology SET entity_types=?, edge_types=? WHERE id=1",
                (
                    json.dumps(ontology.entity_types, ensure_ascii=False),
                    json.dumps(ontology.edge_types, ensure_ascii=False),
                ),
            )
        logger.debug(
            f"Ontology set: {len(ontology.entity_types)} entity types, "
            f"{len(ontology.edge_types)} edge types"
        )

    def get_ontology(self) -> KGOntology:
        with self._connect() as conn:
            row = conn.execute("SELECT entity_types, edge_types FROM ontology WHERE id=1").fetchone()
        if row is None:
            return KGOntology()
        return KGOntology(
            entity_types=json.loads(row["entity_types"]),
            edge_types=json.loads(row["edge_types"]),
        )

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def upsert_node(self, node: KGNode) -> KGNode:
        """
        Insert node or merge into an existing node with the same normalised name.

        On conflict: labels union, summaries concatenated (deduplicated),
        attributes merged (new values win).  Embedding updated if provided.
        Returns the stored node (which may be a pre-existing one).
        """
        name_lower = node.name.strip().lower()

        with self._write_lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM nodes WHERE name_lower=?", (name_lower,)
            ).fetchone()

            if existing is None:
                # Fresh insert
                conn.execute(
                    """
                    INSERT INTO nodes
                        (uuid, name, name_lower, labels, summary,
                         attributes, embedding, created_at)
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        node.uuid,
                        node.name,
                        name_lower,
                        json.dumps(node.labels, ensure_ascii=False),
                        node.summary,
                        json.dumps(node.attributes, ensure_ascii=False),
                        _encode_embedding(node.embedding),
                        node.created_at,
                    ),
                )
                return node
            else:
                # Merge
                merged_labels = _merge_labels(
                    json.loads(existing["labels"]), node.labels
                )
                merged_summary = _merge_summary(existing["summary"], node.summary)
                merged_attrs = {
                    **json.loads(existing["attributes"]),
                    **node.attributes,
                }
                emb_blob = (
                    _encode_embedding(node.embedding)
                    if node.embedding is not None
                    else existing["embedding"]
                )
                conn.execute(
                    """
                    UPDATE nodes
                    SET labels=?, summary=?, attributes=?, embedding=?
                    WHERE uuid=?
                    """,
                    (
                        json.dumps(merged_labels, ensure_ascii=False),
                        merged_summary,
                        json.dumps(merged_attrs, ensure_ascii=False),
                        emb_blob,
                        existing["uuid"],
                    ),
                )
                return _row_to_node(existing)

    def get_node(self, node_uuid: str) -> Optional[KGNode]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM nodes WHERE uuid=?", (node_uuid,)
            ).fetchone()
        return _row_to_node(row) if row else None

    def get_node_by_name(self, name: str) -> Optional[KGNode]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM nodes WHERE name_lower=?", (name.strip().lower(),)
            ).fetchone()
        return _row_to_node(row) if row else None

    def get_nodes_page(
        self,
        limit: int = _PAGE_SIZE_DEFAULT,
        uuid_cursor: Optional[str] = None,
    ) -> List[KGNode]:
        """Cursor-based pagination — same contract as Zep's get_by_graph_id."""
        with self._connect() as conn:
            if uuid_cursor is None:
                rows = conn.execute(
                    "SELECT * FROM nodes ORDER BY rowid LIMIT ?", (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM nodes
                    WHERE rowid > (SELECT rowid FROM nodes WHERE uuid=?)
                    ORDER BY rowid
                    LIMIT ?
                    """,
                    (uuid_cursor, limit),
                ).fetchall()
        return [_row_to_node(r) for r in rows]

    def get_all_nodes(self, max_items: int = _MAX_NODES) -> List[KGNode]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM nodes ORDER BY rowid LIMIT ?", (max_items,)
            ).fetchall()
        return [_row_to_node(r) for r in rows]

    def get_all_nodes_with_embeddings(self) -> List[KGNode]:
        """Returns only nodes that have an embedding stored."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM nodes WHERE embedding IS NOT NULL ORDER BY rowid"
            ).fetchall()
        return [_row_to_node(r) for r in rows]

    def update_node_embedding(self, node_uuid: str, embedding: List[float]) -> None:
        with self._write_lock, self._connect() as conn:
            conn.execute(
                "UPDATE nodes SET embedding=? WHERE uuid=?",
                (_encode_embedding(embedding), node_uuid),
            )

    def node_count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

    # ------------------------------------------------------------------
    # Edges
    # ------------------------------------------------------------------

    def upsert_edge(self, edge: KGEdge) -> KGEdge:
        """
        Insert edge or merge episode reference into existing identical edge.

        Two edges are considered identical if they share source+target+name.
        """
        with self._write_lock, self._connect() as conn:
            existing = conn.execute(
                """
                SELECT * FROM edges
                WHERE source_node_uuid=? AND target_node_uuid=? AND name=?
                """,
                (edge.source_node_uuid, edge.target_node_uuid, edge.name),
            ).fetchone()

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO edges
                        (uuid, name, fact, source_node_uuid, target_node_uuid,
                         attributes, embedding, created_at,
                         valid_at, invalid_at, expired_at, episodes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        edge.uuid,
                        edge.name,
                        edge.fact,
                        edge.source_node_uuid,
                        edge.target_node_uuid,
                        json.dumps(edge.attributes, ensure_ascii=False),
                        _encode_embedding(edge.embedding),
                        edge.created_at,
                        edge.valid_at,
                        edge.invalid_at,
                        edge.expired_at,
                        json.dumps(edge.episodes, ensure_ascii=False),
                    ),
                )
                return edge
            else:
                # Merge episode list
                merged_episodes = list(
                    set(json.loads(existing["episodes"]) + edge.episodes)
                )
                emb_blob = (
                    _encode_embedding(edge.embedding)
                    if edge.embedding is not None
                    else existing["embedding"]
                )
                conn.execute(
                    "UPDATE edges SET episodes=?, embedding=? WHERE uuid=?",
                    (
                        json.dumps(merged_episodes, ensure_ascii=False),
                        emb_blob,
                        existing["uuid"],
                    ),
                )
                return _row_to_edge(existing)

    def get_edge(self, edge_uuid: str) -> Optional[KGEdge]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM edges WHERE uuid=?", (edge_uuid,)
            ).fetchone()
        return _row_to_edge(row) if row else None

    def get_entity_edges(self, node_uuid: str) -> List[KGEdge]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM edges
                WHERE source_node_uuid=? OR target_node_uuid=?
                ORDER BY rowid
                """,
                (node_uuid, node_uuid),
            ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def get_edges_page(
        self,
        limit: int = _PAGE_SIZE_DEFAULT,
        uuid_cursor: Optional[str] = None,
    ) -> List[KGEdge]:
        with self._connect() as conn:
            if uuid_cursor is None:
                rows = conn.execute(
                    "SELECT * FROM edges ORDER BY rowid LIMIT ?", (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM edges
                    WHERE rowid > (SELECT rowid FROM edges WHERE uuid=?)
                    ORDER BY rowid
                    LIMIT ?
                    """,
                    (uuid_cursor, limit),
                ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def get_all_edges(self) -> List[KGEdge]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM edges ORDER BY rowid").fetchall()
        return [_row_to_edge(r) for r in rows]

    def get_all_edges_with_embeddings(self) -> List[KGEdge]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM edges WHERE embedding IS NOT NULL ORDER BY rowid"
            ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def update_edge_embedding(self, edge_uuid: str, embedding: List[float]) -> None:
        with self._write_lock, self._connect() as conn:
            conn.execute(
                "UPDATE edges SET embedding=? WHERE uuid=?",
                (_encode_embedding(embedding), edge_uuid),
            )

    def edge_count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    # ------------------------------------------------------------------
    # Episodes
    # ------------------------------------------------------------------

    def insert_episode(self, episode: KGEpisode) -> None:
        with self._write_lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO episodes (uuid, data, type, processed, created_at)
                VALUES (?,?,?,?,?)
                """,
                (
                    episode.uuid_,
                    episode.data,
                    episode.type,
                    1 if episode.processed else 0,
                    episode.created_at,
                ),
            )

    def get_episode(self, episode_uuid: str) -> Optional[KGEpisode]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM episodes WHERE uuid=?", (episode_uuid,)
            ).fetchone()
        return _row_to_episode(row) if row else None

    def mark_episode_processed(self, episode_uuid: str) -> None:
        with self._write_lock, self._connect() as conn:
            conn.execute(
                "UPDATE episodes SET processed=1 WHERE uuid=?", (episode_uuid,)
            )

    def get_unprocessed_episodes(self) -> List[KGEpisode]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM episodes WHERE processed=0 ORDER BY rowid"
            ).fetchall()
        return [_row_to_episode(r) for r in rows]

    # ------------------------------------------------------------------
    # Graph lifecycle
    # ------------------------------------------------------------------

    def delete(self) -> None:
        """Remove the DB file and evict from registry."""
        evict_store(self.graph_id)
        try:
            if os.path.exists(self._db_path):
                os.remove(self._db_path)
                logger.info(f"Deleted graph store: {self._db_path}")
        except OSError as exc:
            logger.error(f"Failed to delete graph store {self._db_path}: {exc}")


# ---------------------------------------------------------------------------
# Row → model helpers
# ---------------------------------------------------------------------------

def _row_to_node(row: sqlite3.Row) -> KGNode:
    node = KGNode(
        uuid=row["uuid"],
        name=row["name"],
        labels=json.loads(row["labels"]),
        summary=row["summary"] or "",
        attributes=json.loads(row["attributes"]),
        created_at=row["created_at"],
        embedding=_decode_embedding(row["embedding"]),
    )
    return node


def _row_to_edge(row: sqlite3.Row) -> KGEdge:
    return KGEdge(
        uuid=row["uuid"],
        name=row["name"],
        fact=row["fact"] or "",
        source_node_uuid=row["source_node_uuid"],
        target_node_uuid=row["target_node_uuid"],
        attributes=json.loads(row["attributes"]),
        created_at=row["created_at"],
        valid_at=row["valid_at"],
        invalid_at=row["invalid_at"],
        expired_at=row["expired_at"],
        episodes=json.loads(row["episodes"]),
        embedding=_decode_embedding(row["embedding"]),
    )


def _row_to_episode(row: sqlite3.Row) -> KGEpisode:
    return KGEpisode(
        uuid_=row["uuid"],
        data=row["data"],
        type=row["type"],
        processed=bool(row["processed"]),
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Embedding serialisation (numpy float32 blobs)
# ---------------------------------------------------------------------------

def _encode_embedding(embedding: Optional[List[float]]) -> Optional[bytes]:
    if embedding is None:
        return None
    return np.array(embedding, dtype=np.float32).tobytes()


def _decode_embedding(blob: Optional[bytes]) -> Optional[List[float]]:
    if blob is None:
        return None
    return np.frombuffer(blob, dtype=np.float32).tolist()


# ---------------------------------------------------------------------------
# Merge helpers
# ---------------------------------------------------------------------------

def _merge_labels(existing: List[str], incoming: List[str]) -> List[str]:
    return list(dict.fromkeys(existing + incoming))  # preserves order, deduplicates


def _merge_summary(existing: str, incoming: str) -> str:
    if not incoming or incoming == existing:
        return existing
    if not existing:
        return incoming
    # Concatenate unique sentences
    existing_sentences = set(s.strip() for s in existing.split(".") if s.strip())
    new_sentences = [s.strip() for s in incoming.split(".") if s.strip() and s.strip() not in existing_sentences]
    if new_sentences:
        return existing.rstrip(".") + ". " + ". ".join(new_sentences)
    return existing
