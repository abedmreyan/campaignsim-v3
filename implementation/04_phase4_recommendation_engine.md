# Phase 4 — Recommendation Engine

## Goal

Build a campaign recommendation engine that reads the action logs from all simulation variants, scores each variant using the action weight table, ranks segments × channels × content formats, and produces a structured recommendation report with confidence scores and rationale. The engine extends CampaignSim's existing ReACT-pattern `ReportAgent` with marketing-specific tools.

**Done when:** After all variants complete, a user can click "Generate Recommendations" and receive a structured report that ranks variants, identifies the best-performing segment × channel × content combination, and explains the reasoning using evidence from the simulation.

---

## Architecture

```
Simulation action logs (JSONL)
        │
        ▼
VariantScorer              ← new: reads logs, computes per-variant engagement metrics
        │
        ▼
CampaignReportAgent        ← extends ReportAgent with 4 new marketing tools
  ├── VariantComparisonTool     ← compare variants by engagement score
  ├── SegmentInsightTool        ← which segments responded best to which content
  ├── ChannelEffectivenessTool  ← channel-level aggregated metrics
  └── ContentFormatRankTool     ← rank content formats by engagement
        │
        ▼
Recommendation Report      ← structured JSON + human-readable sections
```

---

## Step 1 — Build the Variant Scorer

**File:** `backend/app/services/variant_scorer.py` (new file)

Reads all action JSONL files for a campaign's variants and computes engagement metrics.

```python
"""
CampaignSim Variant Scorer

Reads simulation action logs and computes engagement metrics per variant.
Uses CAMPAIGN_ACTION_WEIGHTS from config to score each action.
"""

import json
import os
import glob
from typing import Dict, Any, List, Optional
from collections import defaultdict

from ..config import Config


class VariantScorer:
    """
    Reads action logs from completed simulation variants and produces
    engagement metrics used by the recommendation engine.
    """

    def score_variant(self, variant_output_dir: str, variant_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single simulation variant.

        Args:
            variant_output_dir: path to the simulation output directory for this variant
            variant_meta: dict with variant metadata (variant_id, channel, content.format,
                          target_segment, variant_name)

        Returns:
            Scored variant dict with engagement metrics

        Note on file format:
            Phase 2 writes a single `actions.jsonl` containing all actions across all rounds.
            Each line is:
              {"variant_id": "...", "channel": "...", "agent_id": 1, "action_type": "LIKE_POST",
               "info": {...}, "timestamp": "..."}
            Action type strings are real OASIS ActionType enum names (LIKE_POST, REPOST, etc.)
            and must match keys in Config.CAMPAIGN_ACTION_WEIGHTS.
        """
        actions_file = os.path.join(variant_output_dir, "actions.jsonl")

        if not os.path.exists(actions_file):
            return {
                **variant_meta,
                "status": "no_data",
                "total_actions": 0,
                "engagement_score": 0.0,
                "action_breakdown": {},
                "per_round_engagement": [],
                "per_agent_scores": {},
            }

        weights = Config.CAMPAIGN_ACTION_WEIGHTS
        total_agents = set()
        action_counts: Dict[str, int] = defaultdict(int)
        per_agent: Dict[int, float] = defaultdict(float)
        all_records: List[Dict] = []

        with open(actions_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                agent_id = record.get("agent_id")
                action_type = record.get("action_type", "DO_NOTHING")

                total_agents.add(agent_id)
                action_counts[action_type] += 1
                weight = weights.get(action_type, 0.0)
                per_agent[agent_id] += weight
                all_records.append(record)

        # Compute a rough per-round breakdown using timestamp ordering
        # Split records into 5 equal time-slices as a proxy for simulation rounds
        per_round: List[float] = []
        if all_records:
            chunk_size = max(1, len(all_records) // 5)
            for i in range(0, len(all_records), chunk_size):
                chunk = all_records[i:i + chunk_size]
                chunk_score = sum(weights.get(r.get("action_type", "DO_NOTHING"), 0.0) for r in chunk)
                per_round.append(chunk_score / len(chunk) if chunk else 0.0)

        num_agents = max(len(total_agents), 1)
        total_possible = num_agents * len(action_files)  # max 1 action per agent per round
        raw_total_score = sum(per_agent.values())
        engagement_score = raw_total_score / total_possible if total_possible > 0 else 0.0

        # Derived metrics
        positive_actions = sum(
            count for action, count in action_counts.items()
            if weights.get(action, 0.0) > 0
        )
        negative_actions = sum(
            count for action, count in action_counts.items()
            if weights.get(action, 0.0) < 0
        )
        total_actions = sum(action_counts.values())

        return {
            **variant_meta,
            "total_agents": num_agents,
            "total_actions": total_actions,
            "positive_actions": positive_actions,
            "negative_actions": negative_actions,
            "engagement_score": round(engagement_score, 4),      # 0.0–1.0 normalised
            "engagement_rate_pct": round(engagement_score * 100, 2),
            "action_breakdown": dict(action_counts),
            "per_round_engagement": per_round,
            "per_agent_scores": {str(k): round(v, 4) for k, v in per_agent.items()},
            "trend": "improving" if len(per_round) > 1 and per_round[-1] > per_round[0] else
                     "declining" if len(per_round) > 1 and per_round[-1] < per_round[0] else "flat",
        }

    def score_campaign(self, campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Score all variants of a campaign.

        Args:
            campaign: Campaign dict (from campaign.to_dict())

        Returns:
            List of scored variant dicts, sorted by engagement_score descending
        """
        scored = []
        for variant in campaign.get("variants", []):
            if variant.get("status") != "completed":
                continue
            output_dir = variant.get("output_dir")
            if not output_dir or not os.path.isdir(output_dir):
                continue

            meta = {
                "variant_id":      variant["variant_id"],
                "variant_name":    variant["variant_name"],
                "channel":         variant["channel"],
                "content_format":  variant.get("content", {}).get("format", ""),
                "target_segment":  variant.get("target_segment", "All"),
                "tone":            variant.get("content", {}).get("tone", "neutral"),
            }
            result = self.score_variant(output_dir, meta)
            scored.append(result)

        return sorted(scored, key=lambda x: x.get("engagement_score", 0), reverse=True)
```

---

## Step 2 — Build Marketing Report Tools

**File:** `backend/app/services/campaign_tools.py` (new file)

Four tools that the CampaignReportAgent will call during its ReACT loop. Each tool reads pre-computed scored variants and answers a specific question.

```python
"""
CampaignSim Report Agent Tools

Marketing-specific tools for the ReACT-pattern recommendation agent.
All tools take scored_variants (list of scored variant dicts) as context.
"""

import json
from typing import List, Dict, Any


class VariantComparisonTool:
    """
    Compare all variants by overall engagement score.
    Returns a ranked table of variants.
    
    Use when: The agent needs to identify the top-performing variant overall.
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
                f"Channel: {v['channel']} | Format: {v['content_format']} | "
                f"Segment: {v['target_segment']} | "
                f"Engagement: {v['engagement_rate_pct']}% | Trend: {v['trend']}"
            )

        return "Variant Rankings (by engagement rate):\n" + "\n".join(rows)


class SegmentInsightTool:
    """
    Identify which audience segments responded best to which content.
    
    Use when: The agent needs segment-level insights (e.g. which segment 
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

        output = []
        for segment, variants in by_segment.items():
            sorted_v = sorted(variants, key=lambda x: x["engagement_score"], reverse=True)
            best = sorted_v[0] if sorted_v else None
            output.append(
                f"Segment: {segment}\n"
                f"  Best variant: {best['variant_name'] if best else 'N/A'} "
                f"({best['engagement_rate_pct']}% engagement)\n"
                f"  Variants tested: {len(variants)}"
            )

        return "\n\n".join(output) if output else "No segment data available."


class ChannelEffectivenessTool:
    """
    Aggregate engagement metrics by channel.
    
    Use when: The agent needs to recommend which channel to prioritise.
    """
    name = "channel_effectiveness"
    description = (
        "Aggregate engagement rates by marketing channel. "
        "Useful for channel selection recommendations."
    )

    def run(self, scored_variants: List[Dict[str, Any]]) -> str:
        by_channel: Dict[str, List[float]] = {}
        for v in scored_variants:
            ch = v["channel"]
            by_channel.setdefault(ch, []).append(v["engagement_score"])

        output = []
        for ch, scores in sorted(by_channel.items(), key=lambda x: -sum(x[1]) / len(x[1])):
            avg = sum(scores) / len(scores)
            output.append(
                f"Channel: {ch.capitalize()} | "
                f"Avg engagement: {round(avg * 100, 2)}% | "
                f"Variants tested: {len(scores)}"
            )

        return "Channel Effectiveness:\n" + "\n".join(output) if output else "No channel data."


class ContentFormatRankTool:
    """
    Rank content formats by engagement.
    
    Use when: The agent needs to recommend whether to use video, carousel, 
    email, etc.
    """
    name = "content_format_ranking"
    description = (
        "Rank content formats (VideoAd, CarouselPost, EmailNewsletter, etc.) "
        "by engagement rate across all variants."
    )

    def run(self, scored_variants: List[Dict[str, Any]]) -> str:
        by_format: Dict[str, List[float]] = {}
        for v in scored_variants:
            fmt = v.get("content_format", "Unknown")
            by_format.setdefault(fmt, []).append(v["engagement_score"])

        output = []
        for fmt, scores in sorted(by_format.items(), key=lambda x: -sum(x[1]) / len(x[1])):
            avg = sum(scores) / len(scores)
            output.append(
                f"Format: {fmt} | Avg engagement: {round(avg * 100, 2)}% | "
                f"Variants: {len(scores)}"
            )

        return "Content Format Rankings:\n" + "\n".join(output) if output else "No format data."


class ZepBrandContextTool:
    """
    Fetch brand/market context from the Zep knowledge graph to enrich recommendations.
    Wraps the existing Zep search utilities.
    
    Use when: The agent needs brand or competitor context to explain a finding
    (e.g. why a segment responded strongly — relates to a competitor fact in the graph).
    """
    name = "brand_context"
    description = (
        "Search the brand knowledge graph for additional context. "
        "Useful for adding market intelligence to recommendations."
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
            return "Brand context:\n" + "\n".join(f"- {f}" for f in facts[:8]) if facts else "No context found."
        except Exception as e:
            return f"Graph search failed: {e}"
```

---

## Step 3 — Build the CampaignReportAgent

**File:** `backend/app/services/campaign_report_agent.py` (new file)

Extends CampaignSim's `ReportAgent` pattern. Uses a ReACT loop with the 5 tools above.

```python
"""
CampaignSim Report Agent

ReACT-pattern agent that synthesises simulation results into a structured
campaign recommendation report.

Report structure:
  1. Executive Summary
  2. Best Performing Variant
  3. Segment Analysis
  4. Channel Effectiveness
  5. Content Format Rankings
  6. Recommendations (ranked, with confidence)
  7. Risks & Caveats
"""

import json
import logging
from typing import List, Dict, Any, Optional

from openai import OpenAI
from zep_cloud.client import Zep

from ..config import Config
from ..services.campaign_tools import (
    VariantComparisonTool,
    SegmentInsightTool,
    ChannelEffectivenessTool,
    ContentFormatRankTool,
    ZepBrandContextTool,
)

logger = logging.getLogger(__name__)


CAMPAIGN_REPORT_SYSTEM_PROMPT = """You are a senior marketing strategist and data analyst.
You have access to simulation results showing how customer personas responded to different 
campaign variants. Your job is to synthesise these results into clear, actionable 
campaign recommendations.

You have these tools available:
- variant_comparison: Get ranked table of all variants by engagement
- segment_insights: See which segments responded best to which content
- channel_effectiveness: See aggregate engagement by channel
- content_format_ranking: See which content formats performed best
- brand_context: Search the brand knowledge graph for additional market context

Use tools to gather evidence before making recommendations.
Always cite specific engagement rates when making claims.
Be direct and prescriptive — marketers need clear next steps, not hedged statements.

Report structure:
1. Executive Summary (3-4 sentences)
2. Best Performing Variant (with evidence)
3. Segment Analysis (which segment to prioritise and why)
4. Channel Recommendation (with engagement data)
5. Content Format Recommendation (with engagement data)
6. Top 3 Recommendations (ranked, with confidence level: High/Medium/Low)
7. Risks & Limitations (simulation caveats)
"""


class CampaignReportAgent:
    """
    Generates a campaign recommendation report using a ReACT loop.
    """

    def __init__(
        self,
        scored_variants: List[Dict[str, Any]],
        zep_client: Optional[Zep] = None,
        graph_id: Optional[str] = None,
    ):
        self.scored_variants = scored_variants
        self.client = OpenAI(api_key=Config.LLM_API_KEY, base_url=Config.LLM_BASE_URL)
        self.model = Config.LLM_MODEL_NAME

        # Register tools
        self.tools = {
            "variant_comparison":    VariantComparisonTool(),
            "segment_insights":      SegmentInsightTool(),
            "channel_effectiveness": ChannelEffectivenessTool(),
            "content_format_ranking": ContentFormatRankTool(),
        }
        if zep_client and graph_id:
            self.tools["brand_context"] = ZepBrandContextTool(zep_client, graph_id)

    def _call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Unknown tool: {tool_name}"

        if tool_name == "brand_context":
            return tool.run(tool_input.get("query", ""))
        else:
            return tool.run(self.scored_variants)

    def generate(self, campaign_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the ReACT loop and generate the recommendation report.

        Args:
            campaign_context: dict with brand_name, campaign_goal, etc.

        Returns:
            {
                "report_text": str,      full markdown report
                "structured": dict,      parsed sections
                "top_recommendation": dict,  best variant + rationale
                "tool_calls_log": list,  audit trail
            }
        """
        tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query (brand_context only)"}
                        } if name == "brand_context" else {},
                        "required": [],
                    },
                },
            }
            for name, tool in self.tools.items()
        ]

        messages = [
            {"role": "system", "content": CAMPAIGN_REPORT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Generate a campaign recommendation report.\n\n"
                    f"Brand: {campaign_context.get('brand_name', 'Unknown')}\n"
                    f"Campaign goal: {campaign_context.get('campaign_goal', 'Not specified')}\n"
                    f"Number of variants tested: {len(self.scored_variants)}\n\n"
                    f"Use your tools to analyse the simulation results and then write the full report."
                ),
            },
        ]

        tool_calls_log = []
        max_tool_calls = Config.REPORT_AGENT_MAX_TOOL_CALLS

        for iteration in range(max_tool_calls + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_definitions,
                tool_choice="auto",
                temperature=Config.REPORT_AGENT_TEMPERATURE,
            )
            msg = response.choices[0].message

            # If the model wants to call tools
            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_input = json.loads(tc.function.arguments)
                    except Exception:
                        tool_input = {}

                    result = self._call_tool(tool_name, tool_input)
                    tool_calls_log.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "output_preview": result[:300],
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
            else:
                # Model is done — this is the final report
                report_text = msg.content or ""

                # Parse the top recommendation from the report
                top_rec = self._extract_top_recommendation(report_text)

                return {
                    "report_text": report_text,
                    "top_recommendation": top_rec,
                    "scored_variants": self.scored_variants,
                    "tool_calls_log": tool_calls_log,
                }

        # Fallback if max iterations hit
        return {
            "report_text": "Report generation reached tool call limit. Please review scored variants directly.",
            "top_recommendation": self.scored_variants[0] if self.scored_variants else {},
            "scored_variants": self.scored_variants,
            "tool_calls_log": tool_calls_log,
        }

    def _extract_top_recommendation(self, report_text: str) -> Dict[str, Any]:
        """
        Ask the LLM to extract the structured top recommendation from the report text.
        Returns a compact dict for the UI summary card.
        """
        extraction_prompt = f"""From this marketing recommendation report, extract the top recommendation 
as a JSON object with these fields:
- best_variant_name: str
- best_channel: str  
- best_content_format: str
- best_segment: str
- engagement_rate_pct: float
- confidence: "High" | "Medium" | "Low"
- one_line_rationale: str (max 150 characters)

Report:
{report_text[:3000]}

Return only valid JSON."""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extraction_prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Top recommendation extraction failed: {e}")
            if self.scored_variants:
                best = self.scored_variants[0]
                return {
                    "best_variant_name": best.get("variant_name", ""),
                    "best_channel": best.get("channel", ""),
                    "best_content_format": best.get("content_format", ""),
                    "best_segment": best.get("target_segment", ""),
                    "engagement_rate_pct": best.get("engagement_rate_pct", 0.0),
                    "confidence": "Medium",
                    "one_line_rationale": "Best performing variant based on engagement score.",
                }
            return {}
```

---

## Step 4 — Add the Report Generation Endpoint

**File:** `backend/app/api/report.py`

Add a new route `/api/report/campaign_recommendations`:

```python
@report_bp.route('/campaign_recommendations', methods=['POST'])
def generate_campaign_recommendations():
    """
    Generate campaign recommendation report from completed simulation variants.

    Request: { "project_id": "...", "campaign_id": "..." }
    Returns: { "task_id": "..." }
    """
    from ..services.variant_scorer import VariantScorer
    from ..services.campaign_report_agent import CampaignReportAgent
    from ..models.task import TaskManager
    from zep_cloud.client import Zep

    data = request.json
    project_id = data.get("project_id")
    campaign_id = data.get("campaign_id")

    project = ProjectManager.get(project_id)
    campaign = project.get("campaign")
    if not campaign or campaign.get("campaign_id") != campaign_id:
        return jsonify({"error": "Campaign not found"}), 404

    task_id = TaskManager.create_task("campaign_report", campaign_id)

    def generate_in_background():
        try:
            TaskManager.update_progress(task_id, "Scoring simulation variants...")
            scorer = VariantScorer()
            scored = scorer.score_campaign(campaign)

            TaskManager.update_progress(task_id, "Generating recommendations...")
            zep = Zep(api_key=Config.ZEP_API_KEY)
            graph_id = project.get("graph_id")

            agent = CampaignReportAgent(
                scored_variants=scored,
                zep_client=zep,
                graph_id=graph_id,
            )
            result = agent.generate({
                "brand_name":    campaign.get("brand_name", ""),
                "campaign_goal": campaign.get("campaign_goal", ""),
            })

            # Save report to project
            ProjectManager.update(project_id, {"campaign_report": result})
            TaskManager.complete_task(task_id, {"report": result})

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            TaskManager.fail_task(task_id, str(e))

    import threading
    threading.Thread(target=generate_in_background, daemon=True).start()

    return jsonify({"task_id": task_id})
```

---

## Step 5 — Build the Recommendation Report UI

**File:** `frontend/src/views/ReportView.vue` (extend existing)

Add a recommendations section to the existing report view:

```
┌─────────────────────────────────────────────────────┐
│  Campaign Recommendations                            │
├─────────────────────────────────────────────────────┤
│  ⭐ TOP RECOMMENDATION                               │
│  ┌─────────────────────────────────────────────┐    │
│  │  VideoAd on Instagram — Millennials          │    │
│  │  Engagement: 34.2% | Confidence: High        │    │
│  │  "Video format drove 2.4x higher engagement  │    │
│  │   than carousel among 25-38 urban segment"   │    │
│  └─────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│  Variant Rankings                                    │
│  1. VideoAd / Instagram / Millennials    34.2% ████  │
│  2. Carousel / Instagram / Gen Z         28.7% ███   │
│  3. Email / All segments                 19.1% ██    │
├─────────────────────────────────────────────────────┤
│  Full Report                                         │
│  [Executive Summary]                                 │
│  [Segment Analysis]                                  │
│  [Channel Effectiveness]                             │
│  [Content Format Rankings]                           │
│  [Risks & Caveats]                                   │
├─────────────────────────────────────────────────────┤
│  [💬 Ask a Question]   [📥 Export Report]            │
└─────────────────────────────────────────────────────┘
```

The "Ask a Question" button opens the existing `InteractionView` chat interface, now connected to the `CampaignReportAgent` for follow-up Q&A.

---

## Step 6 — Add Export Functionality

**File:** `backend/app/api/report.py`

Add a route to export the recommendation report as PDF or JSON:

```python
@report_bp.route('/export/<project_id>', methods=['GET'])
def export_report(project_id):
    """
    Export the campaign recommendation report.
    Query params: format=json|markdown
    """
    fmt = request.args.get("format", "json")
    project = ProjectManager.get(project_id)
    report = project.get("campaign_report", {})

    if fmt == "markdown":
        from flask import Response
        return Response(
            report.get("report_text", "No report generated."),
            mimetype="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=campaign_report.md"}
        )
    else:
        return jsonify(report)
```

---

## Checklist

- [x] `backend/app/services/variant_scorer.py` created — reads num_rounds from simulation_config.json; checks actions.jsonl existence for completion; scores by (raw_score / num_agents × num_rounds)
- [x] `CAMPAIGN_ACTION_WEIGHTS` correctly applied (positive and negative weights from Config)
- [x] `backend/app/services/campaign_tools.py` created — VariantComparisonTool, SegmentInsightTool, ChannelEffectivenessTool, ContentFormatRankTool, ZepBrandContextTool
- [x] `backend/app/services/campaign_report_agent.py` created — ReACT loop with tool_choice="auto", extraction fallback, max_tool_calls guard
- [x] `POST /api/simulation/campaign_recommendations` endpoint — background thread, TaskManager, saves report to campaign JSON
- [x] `GET /api/simulation/campaign_report/<campaign_id>` endpoint — retrieves report; supports `?format=markdown` for export
- [x] Report saved to campaign JSON via `_save_campaign()` after generation
- [ ] Recommendation summary card shown in UI (deferred — UI phase)
- [ ] Variant ranking bar chart shown in UI (deferred — UI phase)
- [ ] Full report text rendered in collapsible sections (deferred — UI phase)
- [ ] "Ask a Question" chat connected to CampaignReportAgent (deferred — UI phase)
- [ ] End-to-end test: 2+ variants → score → report → top recommendation extracted
