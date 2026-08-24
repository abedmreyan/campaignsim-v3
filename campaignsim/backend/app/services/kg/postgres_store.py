"""
Postgres-backed knowledge graph store.

Drop-in replacement for ``SQLiteStore`` (see ``store.py``) with the exact
same public interface — same method names, signatures, and return types —
so nothing outside this package needs to change. The only difference that
matters to callers: data lives in the same independent Postgres cluster the
rest of the app already uses, not on the container's own (ephemeral, wiped
on every redeploy) local disk.

All graphs share four tables (``kg_nodes``, ``kg_edges``, ``kg_episodes``,
``kg_ontology``), each scoped by a ``graph_id`` column — the Postgres
equivalent of SQLite's "one .db file per graph". A ``seq`` BIGSERIAL column
on nodes/edges/episodes replaces SQLite's ``rowid`` for the same
cursor-pagination contract ``get_nodes_page``/``get_edges_page`` already
promise (``zep_paging.py`` depends on that contract unmodified).

Uses its own connection pool via plain ``psycopg2`` — deliberately NOT
Flask-SQLAlchemy's ``db.session``/``db.engine``, since the KG extractor
(``extractor.py``) runs its own background ``ThreadPoolExecutor`` with no
Flask app/request context. Mirrors ``SQLiteStore``'s own philosophy of
managing its raw connections independently of any web framework.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Dict, List, Optional

import numpy as np
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor, Json

from .models import KGEdge, KGEpisode, KGNode, KGOntology
from ...utils.logger import get_logger

logger = get_logger("campaignsim.kg.postgres_store")

_PAGE_SIZE_DEFAULT = 100
_MAX_NODES = 2000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kg_ontology (
    graph_id      VARCHAR(255) PRIMARY KEY,
    entity_types  JSONB NOT NULL DEFAULT '[]',
    edge_types    JSONB NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS kg_nodes (
    seq         BIGSERIAL,
    graph_id    VARCHAR(255) NOT NULL,
    uuid        TEXT NOT NULL,
    name        TEXT NOT NULL,
    name_lower  TEXT NOT NULL,
    labels      JSONB NOT NULL DEFAULT '[]',
    summary     TEXT DEFAULT '',
    attributes  JSONB NOT NULL DEFAULT '{}',
    embedding   BYTEA,
    created_at  TEXT NOT NULL,
    PRIMARY KEY (graph_id, uuid)
);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_seq ON kg_nodes(graph_id, seq);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_name_lower ON kg_nodes(graph_id, name_lower);

CREATE TABLE IF NOT EXISTS kg_edges (
    seq               BIGSERIAL,
    graph_id          VARCHAR(255) NOT NULL,
    uuid              TEXT NOT NULL,
    name              TEXT NOT NULL,
    fact              TEXT DEFAULT '',
    source_node_uuid  TEXT NOT NULL,
    target_node_uuid  TEXT NOT NULL,
    attributes        JSONB NOT NULL DEFAULT '{}',
    embedding         BYTEA,
    created_at        TEXT NOT NULL,
    valid_at          TEXT,
    invalid_at        TEXT,
    expired_at        TEXT,
    episodes          JSONB NOT NULL DEFAULT '[]',
    PRIMARY KEY (graph_id, uuid)
);
CREATE INDEX IF NOT EXISTS idx_kg_edges_seq ON kg_edges(graph_id, seq);
CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON kg_edges(graph_id, source_node_uuid);
CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges(graph_id, target_node_uuid);
CREATE INDEX IF NOT EXISTS idx_kg_edges_name ON kg_edges(graph_id, name);

CREATE TABLE IF NOT EXISTS kg_episodes (
    seq         BIGSERIAL,
    graph_id    VARCHAR(255) NOT NULL,
    uuid        TEXT NOT NULL,
    data        TEXT NOT NULL,
    type        TEXT DEFAULT 'text',
    processed   BOOLEAN DEFAULT FALSE,
    created_at  TEXT NOT NULL,
    PRIMARY KEY (graph_id, uuid)
);
CREATE INDEX IF NOT EXISTS idx_kg_episodes_seq ON kg_episodes(graph_id, seq);
"""

# ---------------------------------------------------------------------------
# Module-level connection pool (shared across all graphs/threads)
# ---------------------------------------------------------------------------

_pool: Optional["psycopg2.pool.ThreadedConnectionPool"] = None
_pool_lock = threading.Lock()
_schema_ready = False
_schema_lock = threading.Lock()


def _get_pool() -> "psycopg2.pool.ThreadedConnectionPool":
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                from ...config import Config

                _pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1, maxconn=20, dsn=Config.SQLALCHEMY_DATABASE_URI,
                )
                logger.info("Postgres KG store connection pool created")
    return _pool


def _ensure_schema() -> None:
    # Deliberately a separate lock from _pool_lock: _get_pool() below can
    # itself need to acquire _pool_lock, and threading.Lock isn't reentrant.
    global _schema_ready
    if _schema_ready:
        return
    with _schema_lock:
        if _schema_ready:
            return
        pool = _get_pool()
        conn = pool.getconn()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(_SCHEMA)
            _schema_ready = True
            logger.info("Postgres KG store schema ready")
        finally:
            pool.putconn(conn)


class _pooled_conn:
    """Context manager: borrow a connection from the pool, always return it."""

    def __enter__(self):
        _ensure_schema()
        self._conn = _get_pool().getconn()
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        _get_pool().putconn(self._conn)


# ---------------------------------------------------------------------------
# Per-graph store registry (mirrors store.py's pattern for SQLiteStore)
# ---------------------------------------------------------------------------

_registry: Dict[str, "PostgresStore"] = {}
_registry_lock = threading.Lock()


def get_store(graph_id: str) -> "PostgresStore":
    """Return (creating if necessary) the PostgresStore for *graph_id*."""
    with _registry_lock:
        if graph_id not in _registry:
            _registry[graph_id] = PostgresStore(graph_id)
        return _registry[graph_id]


def evict_store(graph_id: str) -> None:
    with _registry_lock:
        _registry.pop(graph_id, None)


# ---------------------------------------------------------------------------
# PostgresStore
# ---------------------------------------------------------------------------

class PostgresStore:
    """Postgres-backed store for a single knowledge graph, scoped by graph_id."""

    def __init__(self, graph_id: str):
        self.graph_id = graph_id
        _ensure_schema()
        with _pooled_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO kg_ontology (graph_id) VALUES (%s) ON CONFLICT (graph_id) DO NOTHING",
                (graph_id,),
            )
            conn.commit()
        logger.info(f"PostgresStore initialised: graph_id={graph_id}")

    # ------------------------------------------------------------------
    # Ontology
    # ------------------------------------------------------------------

    def set_ontology(self, ontology: KGOntology) -> None:
        with _pooled_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kg_ontology (graph_id, entity_types, edge_types)
                VALUES (%s, %s, %s)
                ON CONFLICT (graph_id) DO UPDATE
                SET entity_types = EXCLUDED.entity_types, edge_types = EXCLUDED.edge_types
                """,
                (self.graph_id, Json(ontology.entity_types), Json(ontology.edge_types)),
            )
            conn.commit()
        logger.debug(
            f"Ontology set: {len(ontology.entity_types)} entity types, "
            f"{len(ontology.edge_types)} edge types"
        )

    def get_ontology(self) -> KGOntology:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT entity_types, edge_types FROM kg_ontology WHERE graph_id=%s",
                (self.graph_id,),
            )
            row = cur.fetchone()
        if row is None:
            return KGOntology()
        return KGOntology(entity_types=row["entity_types"], edge_types=row["edge_types"])

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def upsert_node(self, node: KGNode) -> KGNode:
        name_lower = node.name.strip().lower()
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_nodes WHERE graph_id=%s AND name_lower=%s",
                (self.graph_id, name_lower),
            )
            existing = cur.fetchone()

            if existing is None:
                cur.execute(
                    """
                    INSERT INTO kg_nodes
                        (graph_id, uuid, name, name_lower, labels, summary,
                         attributes, embedding, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        self.graph_id, node.uuid, node.name, name_lower,
                        Json(node.labels), node.summary, Json(node.attributes),
                        _encode_embedding(node.embedding), node.created_at,
                    ),
                )
                conn.commit()
                return node
            else:
                merged_labels = _merge_labels(existing["labels"], node.labels)
                merged_summary = _merge_summary(existing["summary"], node.summary)
                merged_attrs = {**existing["attributes"], **node.attributes}
                emb_blob = (
                    _encode_embedding(node.embedding)
                    if node.embedding is not None
                    else existing["embedding"]
                )
                cur.execute(
                    """
                    UPDATE kg_nodes
                    SET labels=%s, summary=%s, attributes=%s, embedding=%s
                    WHERE graph_id=%s AND uuid=%s
                    """,
                    (
                        Json(merged_labels), merged_summary, Json(merged_attrs),
                        emb_blob, self.graph_id, existing["uuid"],
                    ),
                )
                conn.commit()
                return _row_to_node(existing)

    def get_node(self, node_uuid: str) -> Optional[KGNode]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_nodes WHERE graph_id=%s AND uuid=%s",
                (self.graph_id, node_uuid),
            )
            row = cur.fetchone()
        return _row_to_node(row) if row else None

    def get_node_by_name(self, name: str) -> Optional[KGNode]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_nodes WHERE graph_id=%s AND name_lower=%s",
                (self.graph_id, name.strip().lower()),
            )
            row = cur.fetchone()
        return _row_to_node(row) if row else None

    def get_nodes_page(
        self, limit: int = _PAGE_SIZE_DEFAULT, uuid_cursor: Optional[str] = None,
    ) -> List[KGNode]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            if uuid_cursor is None:
                cur.execute(
                    "SELECT * FROM kg_nodes WHERE graph_id=%s ORDER BY seq LIMIT %s",
                    (self.graph_id, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM kg_nodes
                    WHERE graph_id=%s AND seq > (
                        SELECT seq FROM kg_nodes WHERE graph_id=%s AND uuid=%s
                    )
                    ORDER BY seq LIMIT %s
                    """,
                    (self.graph_id, self.graph_id, uuid_cursor, limit),
                )
            rows = cur.fetchall()
        return [_row_to_node(r) for r in rows]

    def get_all_nodes(self, max_items: int = _MAX_NODES) -> List[KGNode]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_nodes WHERE graph_id=%s ORDER BY seq LIMIT %s",
                (self.graph_id, max_items),
            )
            rows = cur.fetchall()
        return [_row_to_node(r) for r in rows]

    def get_all_nodes_with_embeddings(self) -> List[KGNode]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_nodes WHERE graph_id=%s AND embedding IS NOT NULL ORDER BY seq",
                (self.graph_id,),
            )
            rows = cur.fetchall()
        return [_row_to_node(r) for r in rows]

    def update_node_embedding(self, node_uuid: str, embedding: List[float]) -> None:
        with _pooled_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE kg_nodes SET embedding=%s WHERE graph_id=%s AND uuid=%s",
                (_encode_embedding(embedding), self.graph_id, node_uuid),
            )
            conn.commit()

    def node_count(self) -> int:
        with _pooled_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM kg_nodes WHERE graph_id=%s", (self.graph_id,))
            return cur.fetchone()[0]

    # ------------------------------------------------------------------
    # Edges
    # ------------------------------------------------------------------

    def upsert_edge(self, edge: KGEdge) -> KGEdge:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM kg_edges
                WHERE graph_id=%s AND source_node_uuid=%s AND target_node_uuid=%s AND name=%s
                """,
                (self.graph_id, edge.source_node_uuid, edge.target_node_uuid, edge.name),
            )
            existing = cur.fetchone()

            if existing is None:
                cur.execute(
                    """
                    INSERT INTO kg_edges
                        (graph_id, uuid, name, fact, source_node_uuid, target_node_uuid,
                         attributes, embedding, created_at,
                         valid_at, invalid_at, expired_at, episodes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        self.graph_id, edge.uuid, edge.name, edge.fact,
                        edge.source_node_uuid, edge.target_node_uuid,
                        Json(edge.attributes), _encode_embedding(edge.embedding),
                        edge.created_at, edge.valid_at, edge.invalid_at,
                        edge.expired_at, Json(edge.episodes),
                    ),
                )
                conn.commit()
                return edge
            else:
                merged_episodes = list(set(existing["episodes"] + edge.episodes))
                emb_blob = (
                    _encode_embedding(edge.embedding)
                    if edge.embedding is not None
                    else existing["embedding"]
                )
                cur.execute(
                    "UPDATE kg_edges SET episodes=%s, embedding=%s WHERE graph_id=%s AND uuid=%s",
                    (Json(merged_episodes), emb_blob, self.graph_id, existing["uuid"]),
                )
                conn.commit()
                return _row_to_edge(existing)

    def get_edge(self, edge_uuid: str) -> Optional[KGEdge]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_edges WHERE graph_id=%s AND uuid=%s",
                (self.graph_id, edge_uuid),
            )
            row = cur.fetchone()
        return _row_to_edge(row) if row else None

    def get_entity_edges(self, node_uuid: str) -> List[KGEdge]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM kg_edges
                WHERE graph_id=%s AND (source_node_uuid=%s OR target_node_uuid=%s)
                ORDER BY seq
                """,
                (self.graph_id, node_uuid, node_uuid),
            )
            rows = cur.fetchall()
        return [_row_to_edge(r) for r in rows]

    def get_edges_page(
        self, limit: int = _PAGE_SIZE_DEFAULT, uuid_cursor: Optional[str] = None,
    ) -> List[KGEdge]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            if uuid_cursor is None:
                cur.execute(
                    "SELECT * FROM kg_edges WHERE graph_id=%s ORDER BY seq LIMIT %s",
                    (self.graph_id, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM kg_edges
                    WHERE graph_id=%s AND seq > (
                        SELECT seq FROM kg_edges WHERE graph_id=%s AND uuid=%s
                    )
                    ORDER BY seq LIMIT %s
                    """,
                    (self.graph_id, self.graph_id, uuid_cursor, limit),
                )
            rows = cur.fetchall()
        return [_row_to_edge(r) for r in rows]

    def get_all_edges(self) -> List[KGEdge]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM kg_edges WHERE graph_id=%s ORDER BY seq", (self.graph_id,))
            rows = cur.fetchall()
        return [_row_to_edge(r) for r in rows]

    def get_all_edges_with_embeddings(self) -> List[KGEdge]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_edges WHERE graph_id=%s AND embedding IS NOT NULL ORDER BY seq",
                (self.graph_id,),
            )
            rows = cur.fetchall()
        return [_row_to_edge(r) for r in rows]

    def update_edge_embedding(self, edge_uuid: str, embedding: List[float]) -> None:
        with _pooled_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE kg_edges SET embedding=%s WHERE graph_id=%s AND uuid=%s",
                (_encode_embedding(embedding), self.graph_id, edge_uuid),
            )
            conn.commit()

    def edge_count(self) -> int:
        with _pooled_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM kg_edges WHERE graph_id=%s", (self.graph_id,))
            return cur.fetchone()[0]

    # ------------------------------------------------------------------
    # Episodes
    # ------------------------------------------------------------------

    def insert_episode(self, episode: KGEpisode) -> None:
        with _pooled_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kg_episodes (graph_id, uuid, data, type, processed, created_at)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (graph_id, uuid) DO NOTHING
                """,
                (
                    self.graph_id, episode.uuid_, episode.data, episode.type,
                    episode.processed, episode.created_at,
                ),
            )
            conn.commit()

    def get_episode(self, episode_uuid: str) -> Optional[KGEpisode]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_episodes WHERE graph_id=%s AND uuid=%s",
                (self.graph_id, episode_uuid),
            )
            row = cur.fetchone()
        return _row_to_episode(row) if row else None

    def mark_episode_processed(self, episode_uuid: str) -> None:
        with _pooled_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE kg_episodes SET processed=TRUE WHERE graph_id=%s AND uuid=%s",
                (self.graph_id, episode_uuid),
            )
            conn.commit()

    def get_unprocessed_episodes(self) -> List[KGEpisode]:
        with _pooled_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM kg_episodes WHERE graph_id=%s AND processed=FALSE ORDER BY seq",
                (self.graph_id,),
            )
            rows = cur.fetchall()
        return [_row_to_episode(r) for r in rows]

    # ------------------------------------------------------------------
    # Graph lifecycle
    # ------------------------------------------------------------------

    def delete(self) -> None:
        """Remove all rows for this graph_id and evict from registry."""
        evict_store(self.graph_id)
        try:
            with _pooled_conn() as conn, conn.cursor() as cur:
                cur.execute("DELETE FROM kg_nodes WHERE graph_id=%s", (self.graph_id,))
                cur.execute("DELETE FROM kg_edges WHERE graph_id=%s", (self.graph_id,))
                cur.execute("DELETE FROM kg_episodes WHERE graph_id=%s", (self.graph_id,))
                cur.execute("DELETE FROM kg_ontology WHERE graph_id=%s", (self.graph_id,))
                conn.commit()
            logger.info(f"Deleted graph store: graph_id={self.graph_id}")
        except Exception as exc:
            logger.error(f"Failed to delete graph store {self.graph_id}: {exc}")


# ---------------------------------------------------------------------------
# Row -> model helpers
# ---------------------------------------------------------------------------

def _row_to_node(row) -> KGNode:
    return KGNode(
        uuid=row["uuid"],
        name=row["name"],
        labels=row["labels"],
        summary=row["summary"] or "",
        attributes=row["attributes"],
        created_at=row["created_at"],
        embedding=_decode_embedding(row["embedding"]),
    )


def _row_to_edge(row) -> KGEdge:
    return KGEdge(
        uuid=row["uuid"],
        name=row["name"],
        fact=row["fact"] or "",
        source_node_uuid=row["source_node_uuid"],
        target_node_uuid=row["target_node_uuid"],
        attributes=row["attributes"],
        created_at=row["created_at"],
        valid_at=row["valid_at"],
        invalid_at=row["invalid_at"],
        expired_at=row["expired_at"],
        episodes=row["episodes"],
        embedding=_decode_embedding(row["embedding"]),
    )


def _row_to_episode(row) -> KGEpisode:
    return KGEpisode(
        uuid_=row["uuid"],
        data=row["data"],
        type=row["type"],
        processed=bool(row["processed"]),
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Embedding serialisation (identical to store.py — reused as-is conceptually,
# duplicated here rather than imported to keep this module import-independent
# of the SQLite store implementation)
# ---------------------------------------------------------------------------

def _encode_embedding(embedding: Optional[List[float]]):
    if embedding is None:
        return None
    return psycopg2.Binary(np.array(embedding, dtype=np.float32).tobytes())


def _decode_embedding(blob) -> Optional[List[float]]:
    if blob is None:
        return None
    return np.frombuffer(bytes(blob), dtype=np.float32).tolist()


# ---------------------------------------------------------------------------
# Merge helpers (identical logic to store.py)
# ---------------------------------------------------------------------------

def _merge_labels(existing: List[str], incoming: List[str]) -> List[str]:
    return list(dict.fromkeys(existing + incoming))


def _merge_summary(existing: str, incoming: str) -> str:
    if not incoming or incoming == existing:
        return existing
    if not existing:
        return incoming
    existing_sentences = set(s.strip() for s in existing.split(".") if s.strip())
    new_sentences = [
        s.strip() for s in incoming.split(".")
        if s.strip() and s.strip() not in existing_sentences
    ]
    if new_sentences:
        return existing.rstrip(".") + ". " + ". ".join(new_sentences)
    return existing
