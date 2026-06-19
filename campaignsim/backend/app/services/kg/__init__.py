"""
Local Knowledge Graph engine — drop-in replacement for Zep Cloud.

Public surface::

    from app.services.kg import KGClient, EpisodeData, EntityEdgeSourceTarget

    client = KGClient(data_dir=Config.KG_DATA_DIR)
    client.graph.create(graph_id="...", name="My Graph")
    client.graph.add_batch(graph_id="...", episodes=[EpisodeData(data="...")])
    results = client.graph.search(graph_id="...", query="brand competitors")
"""

from .client import KGClient
from .models import (
    EpisodeData,
    EntityEdgeSourceTarget,
    KGEdge,
    KGEpisode,
    KGNode,
    KGOntology,
    KGSearchResult,
)

__all__ = [
    "KGClient",
    "EpisodeData",
    "EntityEdgeSourceTarget",
    "KGEdge",
    "KGEpisode",
    "KGNode",
    "KGOntology",
    "KGSearchResult",
]
