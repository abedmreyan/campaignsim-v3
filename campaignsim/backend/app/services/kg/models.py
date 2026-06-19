"""
Knowledge Graph data models.

These dataclasses match the shape of Zep Cloud objects so that existing
service code (zep_entity_reader, zep_tools, graph_builder, etc.) can access
attributes identically — including the Zep-style ``uuid_`` attribute pattern.
"""

from __future__ import annotations

import uuid as _uuid_mod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_uuid() -> str:
    return str(_uuid_mod.uuid4())


# ---------------------------------------------------------------------------
# Core graph objects
# ---------------------------------------------------------------------------

@dataclass
class KGNode:
    """
    A knowledge-graph node (entity).

    Exposes both ``uuid`` and ``uuid_`` so existing code that uses either
    attribute pattern works without modification.
    """
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    created_at: str = field(default_factory=_now_iso)
    embedding: Optional[List[float]] = field(default=None, repr=False)

    # Zep SDK compatibility: ``node.uuid_``
    @property
    def uuid_(self) -> str:
        return self.uuid

    @classmethod
    def create(
        cls,
        name: str,
        labels: List[str],
        summary: str = "",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> "KGNode":
        return cls(
            uuid=_new_uuid(),
            name=name,
            labels=labels,
            summary=summary,
            attributes=attributes or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes,
            "created_at": self.created_at,
        }


@dataclass
class KGEdge:
    """
    A directed relationship between two KGNodes.

    Temporal fields (``valid_at``, ``invalid_at``, ``expired_at``) mirror
    the Zep Cloud edge schema for use in ``panorama_search`` style queries.
    """
    uuid: str
    name: str                   # relation type, e.g. "TARGETS"
    fact: str                   # natural-language sentence
    source_node_uuid: str
    target_node_uuid: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    expired_at: Optional[str] = None
    episodes: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = field(default=None, repr=False)

    # Zep SDK compatibility
    @property
    def uuid_(self) -> str:
        return self.uuid

    @classmethod
    def create(
        cls,
        name: str,
        fact: str,
        source_node_uuid: str,
        target_node_uuid: str,
        attributes: Optional[Dict[str, Any]] = None,
        episode_uuid: Optional[str] = None,
    ) -> "KGEdge":
        return cls(
            uuid=_new_uuid(),
            name=name,
            fact=fact,
            source_node_uuid=source_node_uuid,
            target_node_uuid=target_node_uuid,
            attributes=attributes or {},
            episodes=[episode_uuid] if episode_uuid else [],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "fact": self.fact,
            "source_node_uuid": self.source_node_uuid,
            "target_node_uuid": self.target_node_uuid,
            "attributes": self.attributes,
            "created_at": self.created_at,
            "valid_at": self.valid_at,
            "invalid_at": self.invalid_at,
            "expired_at": self.expired_at,
            "episodes": self.episodes,
        }


@dataclass
class KGEpisode:
    """
    A raw text chunk submitted for extraction.

    ``processed`` mirrors the Zep episode polling pattern used by
    ``graph_builder._wait_for_episodes``.
    """
    uuid_: str                   # primary key — Zep convention uses ``uuid_``
    data: str
    type: str = "text"
    processed: bool = False
    created_at: str = field(default_factory=_now_iso)

    # Alias for consistency with the rest of the codebase
    @property
    def uuid(self) -> str:
        return self.uuid_

    @classmethod
    def create(cls, data: str, type_: str = "text") -> "KGEpisode":
        return cls(uuid_=_new_uuid(), data=data, type=type_)


# ---------------------------------------------------------------------------
# Search result  (mirrors Zep SearchResult shape accessed by zep_tools)
# ---------------------------------------------------------------------------

@dataclass
class KGSearchResult:
    """
    Return type of ``client.graph.search()``.

    ``edges`` and ``nodes`` are lists of KGEdge / KGNode objects so that
    callers that do ``result.edges[i].fact`` or ``result.nodes[i].summary``
    work without modification.
    """
    edges: List[KGEdge] = field(default_factory=list)
    nodes: List[KGNode] = field(default_factory=list)
    query: str = ""
    total_count: int = 0


# ---------------------------------------------------------------------------
# Ontology  (stored per graph)
# ---------------------------------------------------------------------------

@dataclass
class KGOntology:
    entity_types: List[Dict[str, Any]] = field(default_factory=list)
    edge_types: List[Dict[str, Any]] = field(default_factory=list)

    def entity_type_names(self) -> List[str]:
        return [e["name"] for e in self.entity_types]

    def edge_type_names(self) -> List[str]:
        return [e["name"] for e in self.edge_types]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_types": self.entity_types,
            "edge_types": self.edge_types,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "KGOntology":
        return cls(
            entity_types=d.get("entity_types", []),
            edge_types=d.get("edge_types", []),
        )


# ---------------------------------------------------------------------------
# Zep SDK compatibility shims  (imported by graph_builder.py)
# ---------------------------------------------------------------------------

@dataclass
class EpisodeData:
    """Drop-in replacement for ``zep_cloud.EpisodeData``."""
    data: str
    type: str = "text"


@dataclass
class EntityEdgeSourceTarget:
    """Drop-in replacement for ``zep_cloud.EntityEdgeSourceTarget``."""
    source: str
    target: str
