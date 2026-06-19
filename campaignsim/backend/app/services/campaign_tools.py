"""
CampaignSim Report Agent Tools

Marketing-specific tools for the ReACT-pattern recommendation agent.
All scoring tools take scored_variants (list of scored variant dicts) as context.
ZepBrandContextTool takes a query string.
"""

from typing import List, Dict, Any


class VariantComparisonTool:
    """
    Compare all variants by overall engagement score.
    Returns a ranked table of variants.

    Use when: the agent needs to identify the top-performing variant overall.
    """
    name = "variant_comparison"
    description = (
        "Compare all campaign variants by engagement score. "
        "Returns a ranked list with engagement rate, action breakdown, and trend."
    )

    def run(self, scored_variants: List[Dict[str, Any]]) -> str:
        if not scored_variants:
            return "No completed variants to compare."

        rows = []
        for i, v in enumerate(scored_variants, 1):
            rows.append(
                f"{i}. [{v['variant_name']}] "
                f"Channel: {v['channel']} | Format: {v.get('content_format', 'N/A')} | "
                f"Segment: {v.get('target_segment', 'All')} | "
                f"Engagement: {v.get('engagement_rate_pct', 0)}% | "
                f"Actions: {v.get('total_actions', 0)} | Trend: {v.get('trend', 'flat')}"
            )

        return "Variant Rankings (by engagement rate):\n" + "\n".join(rows)


class SegmentInsightTool:
    """
    Identify which audience segments responded best to which content.

    Use when: the agent needs segment-level insights (e.g. which segment
    converts best on email vs Instagram).
    """
    name = "segment_insights"
    description = (
        "Analyse engagement by audience segment. "
        "Shows which segments responded best to which channels and content formats."
    )

    def run(self, scored_variants: List[Dict[str, Any]]) -> str:
        by_segment: Dict[str, List] = {}
        for v in scored_variants:
            seg = v.get("target_segment", "All")
            by_segment.setdefault(seg, []).append(v)

        if not by_segment:
            return "No segment data available."

        output = []
        for segment, variants in by_segment.items():
            sorted_v = sorted(variants, key=lambda x: x.get("engagement_score", 0), reverse=True)
            best = sorted_v[0] if sorted_v else None
            output.append(
                f"Segment: {segment}\n"
                f"  Best variant: {best['variant_name'] if best else 'N/A'} "
                f"({best.get('engagement_rate_pct', 0)}% engagement)\n"
                f"  Variants tested: {len(variants)}"
            )

        return "\n\n".join(output)


class ChannelEffectivenessTool:
    """
    Aggregate engagement metrics by channel.

    Use when: the agent needs to recommend which channel to prioritise.
    """
    name = "channel_effectiveness"
    description = (
        "Aggregate engagement rates by marketing channel. "
        "Useful for channel selection recommendations."
    )

    def run(self, scored_variants: List[Dict[str, Any]]) -> str:
        by_channel: Dict[str, List[float]] = {}
        for v in scored_variants:
            ch = v.get("channel", "unknown")
            by_channel.setdefault(ch, []).append(v.get("engagement_score", 0.0))

        if not by_channel:
            return "No channel data available."

        output = []
        ranked = sorted(
            by_channel.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True,
        )
        for ch, scores in ranked:
            avg = sum(scores) / len(scores)
            output.append(
                f"Channel: {ch.capitalize()} | "
                f"Avg engagement: {round(avg * 100, 2)}% | "
                f"Variants tested: {len(scores)}"
            )

        return "Channel Effectiveness:\n" + "\n".join(output)


class ContentFormatRankTool:
    """
    Rank content formats by engagement.

    Use when: the agent needs to recommend whether to use video, carousel,
    email newsletter, etc.
    """
    name = "content_format_ranking"
    description = (
        "Rank content formats (VideoAd, CarouselPost, EmailNewsletter, etc.) "
        "by engagement rate across all variants."
    )

    def run(self, scored_variants: List[Dict[str, Any]]) -> str:
        by_format: Dict[str, List[float]] = {}
        for v in scored_variants:
            fmt = v.get("content_format") or "Unknown"
            by_format.setdefault(fmt, []).append(v.get("engagement_score", 0.0))

        if not by_format:
            return "No content format data available."

        output = []
        ranked = sorted(
            by_format.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True,
        )
        for fmt, scores in ranked:
            avg = sum(scores) / len(scores)
            output.append(
                f"Format: {fmt} | Avg engagement: {round(avg * 100, 2)}% | "
                f"Variants: {len(scores)}"
            )

        return "Content Format Rankings:\n" + "\n".join(output)


class ZepBrandContextTool:
    """
    Fetch brand/market context from the Zep knowledge graph to enrich recommendations.

    Use when: the agent needs brand or competitor context to explain a finding
    (e.g. why a segment responded strongly — relates to a competitor fact in the graph).
    """
    name = "brand_context"
    description = (
        "Search the brand knowledge graph for additional market context. "
        "Useful for adding brand intelligence to recommendations. "
        "Requires a 'query' parameter."
    )

    def __init__(self, zep_client, graph_id: str):
        self.zep = zep_client
        self.graph_id = graph_id

    def run(self, query: str) -> str:
        try:
            result = self.zep.graph.search(
                query=query,
                graph_id=self.graph_id,
                limit=10,
                scope="edges",
                reranker="rrf",
            )
            facts = [e.fact for e in result.edges if hasattr(e, "fact") and e.fact]
            if not facts:
                return "No relevant brand context found."
            return "Brand context:\n" + "\n".join(f"- {f}" for f in facts[:8])
        except Exception as e:
            return f"Graph search failed: {e}"
