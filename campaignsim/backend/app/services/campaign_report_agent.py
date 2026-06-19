"""
CampaignSim Campaign Report Agent

ReACT-pattern agent that synthesises simulation results into a structured
campaign recommendation report.

Report structure:
  1. Executive Summary
  2. Best Performing Variant
  3. Segment Analysis
  4. Channel Effectiveness
  5. Content Format Rankings
  6. Top 3 Recommendations (ranked, with confidence)
  7. Risks & Limitations
"""

import json
import logging
from typing import List, Dict, Any, Optional

from openai import OpenAI
from .kg import KGClient

from ..config import Config
from ..services.campaign_tools import (
    VariantComparisonTool,
    SegmentInsightTool,
    ChannelEffectivenessTool,
    ContentFormatRankTool,
    ZepBrandContextTool,
)
from ..utils.logger import get_logger

logger = get_logger("campaignsim.services.campaign_report_agent")


CAMPAIGN_REPORT_SYSTEM_PROMPT = """You are a senior marketing strategist and data analyst.
You have access to simulation results showing how customer personas responded to different
campaign variants. Your job is to synthesise these results into clear, actionable
campaign recommendations.

You have these tools available:
- variant_comparison: Get ranked table of all variants by engagement
- segment_insights: See which segments responded best to which content
- channel_effectiveness: See aggregate engagement by channel
- content_format_ranking: See which content formats performed best
- brand_context: Search the brand knowledge graph for additional market context (requires query)

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
        zep_client: Optional[KGClient] = None,
        graph_id: Optional[str] = None,
    ):
        self.scored_variants = scored_variants
        self.client = OpenAI(api_key=Config.LLM_API_KEY, base_url=Config.LLM_BASE_URL)
        self.model = Config.LLM_MODEL_NAME

        self.tools: Dict[str, Any] = {
            "variant_comparison":     VariantComparisonTool(),
            "segment_insights":       SegmentInsightTool(),
            "channel_effectiveness":  ChannelEffectivenessTool(),
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
        return tool.run(self.scored_variants)

    def generate(self, campaign_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the ReACT loop and generate the recommendation report.

        Args:
            campaign_context: dict with brand_name, campaign_goal, etc.

        Returns:
            {
                "report_text": str,          full markdown report
                "top_recommendation": dict,  parsed top result
                "scored_variants": list,     the input scores (for UI)
                "tool_calls_log": list,      audit trail
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
                            "query": {
                                "type": "string",
                                "description": "Search query string",
                            }
                        } if name == "brand_context" else {},
                        "required": ["query"] if name == "brand_context" else [],
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
                    f"Use your tools to analyse the simulation results, then write the full report."
                ),
            },
        ]

        tool_calls_log: List[Dict] = []
        max_tool_calls = Config.REPORT_AGENT_MAX_TOOL_CALLS

        for _ in range(max_tool_calls + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_definitions,
                tool_choice="auto",
                temperature=Config.REPORT_AGENT_TEMPERATURE,
            )
            msg = response.choices[0].message

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
                report_text = msg.content or ""
                top_rec = self._extract_top_recommendation(report_text)
                return {
                    "report_text": report_text,
                    "top_recommendation": top_rec,
                    "scored_variants": self.scored_variants,
                    "tool_calls_log": tool_calls_log,
                }

        # Fallback if tool call limit hit without a final text response
        logger.warning("Campaign report agent hit tool call limit without producing a final report")
        return {
            "report_text": (
                "Report generation reached the tool call limit. "
                "Please review the scored variants directly."
            ),
            "top_recommendation": self.scored_variants[0] if self.scored_variants else {},
            "scored_variants": self.scored_variants,
            "tool_calls_log": tool_calls_log,
        }

    def _extract_top_recommendation(self, report_text: str) -> Dict[str, Any]:
        """
        Ask the LLM to extract the structured top recommendation from the report text.
        Returns a compact dict for the UI summary card.
        """
        extraction_prompt = (
            "From this marketing recommendation report, extract the top recommendation "
            "as a JSON object with these fields:\n"
            "- best_variant_name: str\n"
            "- best_channel: str\n"
            "- best_content_format: str\n"
            "- best_segment: str\n"
            "- engagement_rate_pct: float\n"
            '- confidence: "High" | "Medium" | "Low"\n'
            "- one_line_rationale: str (max 150 characters)\n\n"
            f"Report:\n{report_text[:3000]}\n\nReturn only valid JSON."
        )
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
                    "best_variant_name":   best.get("variant_name", ""),
                    "best_channel":        best.get("channel", ""),
                    "best_content_format": best.get("content_format", ""),
                    "best_segment":        best.get("target_segment", ""),
                    "engagement_rate_pct": best.get("engagement_rate_pct", 0.0),
                    "confidence": "Medium",
                    "one_line_rationale": "Best performing variant based on engagement score.",
                }
            return {}
