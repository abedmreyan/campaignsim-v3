"""
KGClient — drop-in replacement for ``zep_cloud.client.Zep``.

Mirrors the nested namespace that existing services rely on:

    client.graph.create(graph_id, name, description)
    client.graph.delete(graph_id)
    client.graph.set_ontology(graph_ids, entities, edges)
    client.graph.add(graph_id, type, data)
    client.graph.add_batch(graph_id, episodes)
    client.graph.search(graph_id, query, limit, scope, reranker)
    client.graph.node.get(uuid_)
    client.graph.node.get_by_graph_id(graph_id, limit, uuid_cursor)
    client.graph.node.get_entity_edges(node_uuid)
    client.graph.edge.get_by_graph_id(graph_id, limit, uuid_cursor)
    client.graph.episode.get(uuid_)

All methods return the same types (KGNode, KGEdge, KGEpisode, KGSearchResult)
and expose the same attribute names used by existing code.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from .extractor import submit_episode, submit_episodes_batch
from .models import (
    EpisodeData,
    KGEdge,
    KGEpisode,
    KGNode,
    KGOntology,
    KGSearchResult,
)
from .search import search as _search
from .store import SQLiteStore, evict_store, get_store
from ...utils.logger import get_logger

logger = get_logger("campaignsim.kg.client")


# ---------------------------------------------------------------------------
# Sub-namespaces
# ---------------------------------------------------------------------------

class _EpisodeNamespace:
    def __init__(self, client: "KGClient"):
        self._c = client

    def get(self, uuid_: str) -> Optional[KGEpisode]:
        """
        Fetch episode by UUID.  Used by ``graph_builder._wait_for_episodes``
        to poll ``.processed``.
        """
        # We need the graph_id to look up the store.  Since episodes are
        # globally unique (uuid4) we search all open stores.
        for store in self._c._open_stores():
            ep = store.get_episode(uuid_)
            if ep is not None:
                return ep
        return None


class _NodeNamespace:
    def __init__(self, client: "KGClient"):
        self._c = client

    def get(self, uuid_: str) -> Optional[KGNode]:
        """Fetch a single node by UUID — used by ``ZepEntityReader``."""
        for store in self._c._open_stores():
            node = store.get_node(uuid_)
            if node is not None:
                return node
        return None

    def get_by_graph_id(
        self,
        graph_id: str,
        limit: int = 100,
        uuid_cursor: Optional[str] = None,
    ) -> List[KGNode]:
        """
        Cursor-paginated node list — mirrors Zep's ``graph.node.get_by_graph_id()``.
        Used by ``zep_paging.fetch_all_nodes``.
        """
        store = self._c._store(graph_id)
        return store.get_nodes_page(limit=limit, uuid_cursor=uuid_cursor)

    def get_entity_edges(self, node_uuid: str) -> List[KGEdge]:
        """All edges connected to a node — used by ``ZepEntityReader``."""
        for store in self._c._open_stores():
            node = store.get_node(node_uuid)
            if node is not None:
                return store.get_entity_edges(node_uuid)
        return []


class _EdgeNamespace:
    def __init__(self, client: "KGClient"):
        self._c = client

    def get_by_graph_id(
        self,
        graph_id: str,
        limit: int = 100,
        uuid_cursor: Optional[str] = None,
    ) -> List[KGEdge]:
        """
        Cursor-paginated edge list — mirrors Zep's ``graph.edge.get_by_graph_id()``.
        Used by ``zep_paging.fetch_all_edges``.
        """
        store = self._c._store(graph_id)
        return store.get_edges_page(limit=limit, uuid_cursor=uuid_cursor)


class _GraphNamespace:
    """Mirrors the ``client.graph`` namespace of the Zep SDK."""

    def __init__(self, client: "KGClient"):
        self._c = client
        self.node = _NodeNamespace(client)
        self.edge = _EdgeNamespace(client)
        self.episode = _EpisodeNamespace(client)

    # ------------------------------------------------------------------
    # Graph lifecycle
    # ------------------------------------------------------------------

    def create(
        self,
        graph_id: str,
        name: str = "",
        description: str = "",
    ) -> None:
        """
        Create (initialise) a new graph store.  The graph_id is generated
        externally by ``graph_builder.create_graph()`` (uuid4 hex).
        """
        store = get_store(graph_id, self._c._data_dir)
        logger.info(f"Graph created: {graph_id} ({name!r})")

    def delete(self, graph_id: str) -> None:
        """Permanently delete the graph — removes the SQLite DB file."""
        store = self._c._store(graph_id)
        store.delete()
        logger.info(f"Graph deleted: {graph_id}")

    def set_ontology(
        self,
        graph_ids: List[str],
        entities: Optional[Any] = None,
        edges: Optional[Any] = None,
    ) -> None:
        """
        Store the ontology for each listed graph.

        ``entities`` is a dict of {type_name: PydanticClass|dict|str} — we
        extract just the type names (keys).
        ``edges`` is a dict of {type_name: (EdgeClass, [EntityEdgeSourceTarget])|dict|str}.

        The raw ontology passed in from ``graph_builder.set_ontology()`` is
        already structured — we normalise it here and persist as JSON.
        """
        entity_types = self._extract_ontology_entity_types(entities or {})
        edge_types = self._extract_ontology_edge_types(edges or {})

        ontology = KGOntology(entity_types=entity_types, edge_types=edge_types)

        for graph_id in (graph_ids or []):
            store = self._c._store(graph_id)
            store.set_ontology(ontology)
            logger.info(
                f"Ontology set for {graph_id}: "
                f"{len(entity_types)} entity types, {len(edge_types)} edge types"
            )

    # ------------------------------------------------------------------
    # Episode ingestion
    # ------------------------------------------------------------------

    def add(self, graph_id: str, type: str = "text", data: str = "") -> None:
        """
        Add a single text episode — called by ``ZepGraphMemoryUpdater`` for
        every batch of agent action logs.
        """
        ep = KGEpisode.create(data=data, type_=type)
        store = self._c._store(graph_id)
        submit_episode(graph_id, ep, store)

    def add_batch(
        self,
        graph_id: str,
        episodes: List[EpisodeData],
    ) -> List[KGEpisode]:
        """
        Batch-ingest text chunks — called by ``graph_builder.add_text_batches()``.

        Returns ``KGEpisode`` objects whose ``.uuid_`` can be polled via
        ``client.graph.episode.get(uuid_=...)``.
        """
        store = self._c._store(graph_id)
        kg_episodes = [KGEpisode.create(data=ep.data, type_=ep.type) for ep in episodes]
        submit_episodes_batch(graph_id, kg_episodes, store)
        logger.info(f"Batch submitted: {len(kg_episodes)} episodes for graph {graph_id}")
        return kg_episodes

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        graph_id: str,
        query: str,
        limit: int = 10,
        scope: str = "edges",
        reranker: str = "rrf",
    ) -> KGSearchResult:
        """
        Semantic + keyword search over the graph.

        Return type mirrors Zep's search result — ``.edges`` and ``.nodes``
        are lists of objects with ``.fact``, ``.uuid_``, etc.
        """
        store = self._c._store(graph_id)
        result = _search(store, query=query, limit=limit, scope=scope, reranker=reranker)
        logger.debug(
            f"Search [{scope}] q={query[:40]!r}: "
            f"{len(result.edges)} edges, {len(result.nodes)} nodes"
        )
        return result

    # ------------------------------------------------------------------
    # Ontology normalisation helpers
    # ------------------------------------------------------------------

    def _extract_ontology_entity_types(self, entities: Any) -> List[Dict[str, Any]]:
        """
        Accept several formats:
        - dict of {name: PydanticClass} (from graph_builder)
        - dict of {name: {"description": ...}}
        - list of {"name": ..., "description": ...}
        - KGOntology object
        """
        if isinstance(entities, KGOntology):
            return entities.entity_types

        if isinstance(entities, list):
            return [
                {"name": e["name"], "description": e.get("description", ""), "attributes": e.get("attributes", [])}
                for e in entities if isinstance(e, dict) and "name" in e
            ]

        if isinstance(entities, dict):
            result = []
            for name, value in entities.items():
                if isinstance(value, dict):
                    result.append({"name": name, "description": value.get("description", ""), "attributes": []})
                else:
                    # Pydantic class or other — use __doc__ as description
                    doc = getattr(value, "__doc__", "") or ""
                    result.append({"name": name, "description": doc, "attributes": []})
            return result

        return []

    def _extract_ontology_edge_types(self, edges: Any) -> List[Dict[str, Any]]:
        """
        Accept:
        - dict of {name: (EdgeClass, [EntityEdgeSourceTarget])} (from graph_builder)
        - dict of {name: {"description": ..., "source_targets": [...]}}
        - list of {"name": ..., "description": ...}
        """
        if isinstance(edges, list):
            return [
                {"name": e["name"], "description": e.get("description", ""), "source_targets": e.get("source_targets", []), "attributes": []}
                for e in edges if isinstance(e, dict) and "name" in e
            ]

        if isinstance(edges, dict):
            result = []
            for name, value in edges.items():
                if isinstance(value, tuple) and len(value) == 2:
                    # (EdgeClass, [EntityEdgeSourceTarget]) — from graph_builder
                    edge_class, source_targets = value
                    st_list = [
                        {"source": getattr(st, "source", "Entity"), "target": getattr(st, "target", "Entity")}
                        for st in source_targets
                    ]
                    doc = getattr(edge_class, "__doc__", "") or ""
                    result.append({"name": name, "description": doc, "source_targets": st_list, "attributes": []})
                elif isinstance(value, dict):
                    result.append({"name": name, "description": value.get("description", ""), "source_targets": [], "attributes": []})
                else:
                    result.append({"name": name, "description": "", "source_targets": [], "attributes": []})
            return result

        return []


# ---------------------------------------------------------------------------
# KGClient
# ---------------------------------------------------------------------------

class KGClient:
    """
    Drop-in replacement for ``zep_cloud.client.Zep``.

    Usage (matches existing code)::

        client = KGClient(data_dir="/path/to/graphs")
        client.graph.create(graph_id="...", name="...")
        nodes = client.graph.node.get_by_graph_id("...")
    """

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self.graph = _GraphNamespace(self)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _store(self, graph_id: str) -> SQLiteStore:
        return get_store(graph_id, self._data_dir)

    def _open_stores(self) -> List[SQLiteStore]:
        """Return all currently open stores (for cross-graph lookups)."""
        from .store import _registry
        return list(_registry.values())
