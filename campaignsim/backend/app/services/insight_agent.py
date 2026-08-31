"""
CampaignSim Insight Agent (Phase 3)

A multi-turn, tool-using conversational agent that helps the user understand
*why* a simulated campaign performed the way it did, and — if warranted —
propose a redesign. Modeled on designer_agent.py's resumable ReACT loop.
Grounded first in the structured campaign_report_agent.py output (inserted
as the session's first assistant message by the API layer), then in
per-variant stats, the action log, offline persona interviews, the brand's
knowledge graph, this campaign's Designer-recorded hypotheses, and — if this
campaign is part of an iteration chain — prior iterations' results.

Like the Designer agent, a redesign can only be produced via the
propose_redesign tool (never free text), using the exact same proposal
schema as DesignerAgent.propose_variants so it can be handed straight into a
new Designer session's draft.
"""

import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..config import Config
from ..models.orm import BrandBrief, CampaignRecord, CampaignVariantRecord, Segment
from .business_context import OBJECTIVES
from .campaign_lineage import get_lineage_chain
from .campaign_tools import (
    ChannelEffectivenessTool,
    ContentFormatRankTool,
    SegmentInsightTool,
    VariantComparisonTool,
)
from .designer_agent import DesignerAgent
from .kg import KGClient
from .persona_interviewer import PersonaInterviewer, load_agent_actions
from .simulation_helpers import _campaigns_dir
from ..utils.logger import get_logger

logger = get_logger("campaignsim.services.insight_agent")


INSIGHT_SYSTEM_PROMPT = """You are a senior marketing analyst helping a user understand
the results of a simulated campaign and, if warranted, redesign it. A structured
recommendation report has already been generated (shown above as your first message) —
use it as a starting point, not the final word. Dig deeper with tools before asserting
anything you can't already see in that report.

Tools available:
- variant_comparison / segment_insights / channel_effectiveness / content_format_ranking:
  the same scored-results tools behind the report, callable again for follow-up questions
- kg_search: search the brand's knowledge graph for context that might explain a result
- action_log_query: inspect the raw action log for one variant (round range, action type,
  top/bottom engaged agents, drop-off round) — use this to find *when* engagement fell off
- interview_personas: ask specific simulated personas, in character, why they did or didn't
  engage with a variant — ground "why" claims in these instead of speculating
- hypothesis_check: see the Designer agent's recorded hypothesis for each AI-proposed variant
  next to what actually happened — confirm or refute them explicitly
- compare_iterations: if this campaign has prior or later iterations, see how metrics moved
- segment_comparison: if a variant targeted an approved real-customer segment, compare its
  simulated engagement against that segment's actual historical behavior
- propose_redesign: the ONLY way to put a concrete redesign in front of the user — same
  schema as the Designer's proposals (channel, format, headline, body, cta, rationale,
  hypothesis per variant). Only call this when the user actually wants a redesign, and
  explain what you kept and what you changed, citing the evidence that justified each change.

Rules:
- Ground every explanatory claim in a tool result — action-log evidence or a persona
  interview, not assumption.
- Nothing launches from this chat. A redesign is a draft the user reviews and commits
  through the Designer flow.
- Be direct and specific — cite real numbers and quotes, not generic marketing advice.
"""


class InsightAgent:
    def __init__(self, user_id, campaign_id):
        self.user_id = user_id
        self.client = OpenAI(api_key=Config.LLM_API_KEY, base_url=Config.LLM_BASE_URL)
        self.model = Config.LLM_MODEL_NAME

        self._campaign_record: Optional[CampaignRecord] = CampaignRecord.query.filter_by(
            id=campaign_id, user_id=user_id
        ).first()
        if not self._campaign_record:
            raise ValueError("Campaign not found")

        campaign_path = os.path.join(_campaigns_dir(), f"{self._campaign_record.campaign_ref}.json")
        with open(campaign_path, "r", encoding="utf-8") as f:
            self._campaign_dict: Dict[str, Any] = json.load(f)

        self._report: Dict[str, Any] = self._campaign_dict.get("campaign_report") or {}
        self.scored_variants: List[Dict[str, Any]] = self._report.get("scored_variants") or []
        self._variants_by_id: Dict[str, Dict[str, Any]] = {
            v.get("variant_id"): v for v in self._campaign_dict.get("variants", [])
        }
        self.parent_sim_key: str = self._campaign_dict.get("simulation_id", "")

        self._brief: Optional[BrandBrief] = (
            BrandBrief.query.filter_by(id=self._campaign_record.brand_brief_id, user_id=user_id).first()
            if self._campaign_record.brand_brief_id else None
        )

        self._pending_draft: Optional[Dict[str, Any]] = None
        self._interviewer = PersonaInterviewer()

        self.tools: Dict[str, Any] = {
            "variant_comparison": self._tool_variant_comparison,
            "segment_insights": self._tool_segment_insights,
            "channel_effectiveness": self._tool_channel_effectiveness,
            "content_format_ranking": self._tool_content_format_ranking,
            "kg_search": self._tool_kg_search,
            "action_log_query": self._tool_action_log_query,
            "interview_personas": self._tool_interview_personas,
            "hypothesis_check": self._tool_hypothesis_check,
            "compare_iterations": self._tool_compare_iterations,
            "segment_comparison": self._tool_segment_comparison,
            "propose_redesign": self._tool_propose_redesign,
        }

    def initial_report_message(self) -> str:
        """The already-generated report text, inserted as the session's first
        assistant turn so the conversation starts grounded (FR3.1)."""
        return self._report.get("report_text") or "No structured report was found for this campaign."

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def _tool_variant_comparison(self) -> str:
        return VariantComparisonTool().run(self.scored_variants)

    def _tool_segment_insights(self) -> str:
        return SegmentInsightTool().run(self.scored_variants)

    def _tool_channel_effectiveness(self) -> str:
        return ChannelEffectivenessTool().run(self.scored_variants)

    def _tool_content_format_ranking(self) -> str:
        return ContentFormatRankTool().run(self.scored_variants)

    def _tool_kg_search(self, query: str) -> str:
        if not self._brief or not self._brief.graph_id:
            return "No knowledge graph is available for this brief."
        try:
            kg_client = KGClient(data_dir=Config.KG_DATA_DIR)
            result = kg_client.graph.search(
                query=query, graph_id=self._brief.graph_id, limit=10, scope="edges", reranker="rrf",
            )
            facts = [e.fact for e in result.edges if hasattr(e, "fact") and e.fact]
            if not facts:
                return "No relevant brand context found for that query."
            return "Brand knowledge graph facts:\n" + "\n".join(f"- {f}" for f in facts[:8])
        except Exception as e:
            logger.exception(f"kg_search failed for graph {self._brief.graph_id}: {e}")
            return f"Graph search failed: {e}"

    def _variant_output_dir(self, variant_id: str) -> Optional[str]:
        variant = self._variants_by_id.get(variant_id)
        if not variant:
            return None
        output_dir = variant.get("output_dir")
        return output_dir if output_dir and os.path.isdir(output_dir) else None

    def _read_actions(self, variant_id: str) -> Optional[List[Dict[str, Any]]]:
        output_dir = self._variant_output_dir(variant_id)
        if not output_dir:
            return None
        path = os.path.join(output_dir, "actions.jsonl")
        if not os.path.exists(path):
            return []
        actions = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    actions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return actions

    def _tool_action_log_query(
        self,
        variant_id: str,
        action_type: Optional[str] = None,
        round_min: Optional[int] = None,
        round_max: Optional[int] = None,
    ) -> str:
        actions = self._read_actions(variant_id)
        if actions is None:
            return f"Unknown variant_id '{variant_id}' or no output directory found."
        if not actions:
            return f"Variant '{variant_id}' has no logged actions."

        filtered = actions
        if action_type:
            filtered = [a for a in filtered if a.get("action_type") == action_type]
        if round_min is not None:
            filtered = [a for a in filtered if (a.get("round_num") or 0) >= round_min]
        if round_max is not None:
            filtered = [a for a in filtered if (a.get("round_num") or 0) <= round_max]

        if not filtered:
            return "No actions match those filters."

        per_round: Dict[int, int] = defaultdict(int)
        per_agent: Dict[str, int] = defaultdict(int)
        for a in filtered:
            per_round[a.get("round_num") or 0] += 1
            per_agent[str(a.get("agent_id"))] += 1

        rounds_sorted = sorted(per_round.items())
        drop_off_round = None
        if len(rounds_sorted) >= 2:
            peak = max(count for _, count in rounds_sorted)
            for round_num, count in rounds_sorted:
                if count <= peak * 0.4:
                    drop_off_round = round_num
                    break

        top_agents = sorted(per_agent.items(), key=lambda kv: kv[1], reverse=True)[:5]
        bottom_agents = sorted(per_agent.items(), key=lambda kv: kv[1])[:5]

        lines = [
            f"Variant '{variant_id}': {len(filtered)} matching actions across {len(per_agent)} agents.",
            "Per-round counts: " + ", ".join(f"r{r}={c}" for r, c in rounds_sorted),
        ]
        if drop_off_round is not None:
            lines.append(f"Engagement drop-off around round {drop_off_round} (fell below 40% of peak).")
        lines.append("Most active agents: " + ", ".join(f"agent {a} ({c})" for a, c in top_agents))
        lines.append("Least active agents: " + ", ".join(f"agent {a} ({c})" for a, c in bottom_agents))
        return "\n".join(lines)

    def _tool_interview_personas(
        self,
        variant_id: str,
        question: str,
        agent_ids: Optional[List[Any]] = None,
        selector: Optional[str] = None,
        count: int = 3,
    ) -> str:
        actions = self._read_actions(variant_id)
        if actions is None:
            return f"Unknown variant_id '{variant_id}' or no output directory found."

        output_dir = self._variant_output_dir(variant_id)
        count = max(1, min(int(count or 3), Config.INSIGHT_AGENT_MAX_INTERVIEWS))

        target_ids: List[str]
        if agent_ids:
            target_ids = [str(a) for a in agent_ids][:count]
        else:
            per_agent: Dict[str, int] = defaultdict(int)
            for a in actions:
                per_agent[str(a.get("agent_id"))] += 1
            ranked = sorted(per_agent.items(), key=lambda kv: kv[1], reverse=(selector == "highest_engagement"))
            target_ids = [agent_id for agent_id, _ in ranked[:count]]

        if not target_ids:
            return "No agents found for this variant to interview."

        if not self.parent_sim_key:
            return "No parent simulation on record — cannot load persona profiles."

        from .simulation_manager import SimulationManager

        try:
            profiles = SimulationManager().get_profiles(self.parent_sim_key, platform="reddit")
        except Exception as e:
            logger.exception(f"interview_personas failed to load profiles for simulation {self.parent_sim_key}: {e}")
            return f"Could not load persona profiles: {e}"
        profiles_by_id = {str(p.get("user_id")): p for p in profiles}

        variant = self._variants_by_id.get(variant_id) or {}
        content = variant.get("content") or {}
        channel = variant.get("channel", "")

        answers = []
        for agent_id in target_ids:
            profile = profiles_by_id.get(agent_id)
            if not profile:
                answers.append(f"Agent {agent_id}: profile not found.")
                continue
            agent_actions = load_agent_actions(output_dir, agent_id) if output_dir else []
            answer = self._interviewer.interview(profile, agent_actions, content, channel, question)
            answers.append(f"{profile.get('name', f'Agent {agent_id}')} (agent {agent_id}): {answer}")

        return "\n\n".join(answers)

    def _tool_hypothesis_check(self) -> str:
        variant_records = CampaignVariantRecord.query.filter_by(campaign_id=self._campaign_record.id).all()
        scored_by_ref = {v.get("variant_id"): v for v in self.scored_variants}

        lines = []
        for record in variant_records:
            if not record.hypothesis:
                continue
            scored = scored_by_ref.get(record.variant_ref)
            if not scored:
                lines.append(f"- {record.variant_name}: hypothesis recorded but not yet scored.")
                continue
            rank = sorted(self.scored_variants, key=lambda v: v.get("engagement_score", 0), reverse=True)
            position = next((i + 1 for i, v in enumerate(rank) if v.get("variant_id") == record.variant_ref), None)
            lines.append(
                f"- {record.variant_name} (rank {position}/{len(rank)}, "
                f"{scored.get('engagement_rate_pct', 0)}% engagement)\n"
                f"  Hypothesis: {record.hypothesis}\n"
                f"  Rationale: {record.rationale}"
            )
        if not lines:
            return "No AI-proposed variants with recorded hypotheses on this campaign."
        return "Hypothesis vs. outcome:\n" + "\n".join(lines)

    def _tool_compare_iterations(self) -> str:
        chain = get_lineage_chain(self._campaign_record)
        if len(chain) <= 1:
            return "This campaign has no other iterations yet."
        lines = []
        for entry in chain:
            marker = " (this campaign)" if entry["id"] == str(self._campaign_record.id) else ""
            avg = entry["avg_engagement_rate_pct"]
            lines.append(
                f"Iteration {entry['iteration']}{marker}: "
                f"{'avg engagement ' + str(avg) + '%' if avg is not None else 'not yet scored'}"
                f"{', best variant ' + entry['best_variant_name'] if entry.get('best_variant_name') else ''}"
            )
        return "Campaign iteration lineage:\n" + "\n".join(lines)

    def _tool_segment_comparison(self) -> str:
        """For each scored variant whose target_segment matches an approved
        real-customer segment (Phase 4) by name, compare the simulated
        engagement against that segment's actual historical stats."""
        segments_by_name = {
            s.name: s for s in Segment.query.filter_by(user_id=self.user_id, status="approved").all()
        }
        if not segments_by_name:
            return "No approved real-customer segments on record for this user."

        lines = []
        for v in self.scored_variants:
            target = v.get("target_segment")
            segment = segments_by_name.get(target) if target else None
            if not segment:
                continue
            stats = segment.stats or {}
            lines.append(
                f"- Variant '{v.get('variant_name')}' targeted segment '{target}' "
                f"({segment.size} real customers):\n"
                f"  Simulated engagement: {v.get('engagement_rate_pct', 0)}%\n"
                f"  Segment's historical avg_email_open_rate: {stats.get('avg_email_open_rate')}, "
                f"avg_ltv: {stats.get('avg_ltv')}, avg_order_count: {stats.get('avg_order_count')}"
            )
        if not lines:
            return "No scored variants in this campaign targeted an approved real-customer segment by name."
        return "Simulated results vs. segment historical data:\n" + "\n".join(lines)

    def _tool_propose_redesign(self, proposal: Dict[str, Any]) -> str:
        errors = DesignerAgent(user_id=self.user_id).validate_proposal(proposal)
        if errors:
            return "Redesign rejected — fix these issues and call propose_redesign again:\n" + "\n".join(
                f"- {e}" for e in errors
            )
        self._pending_draft = proposal
        names = ", ".join(v.get("variant_name", "?") for v in proposal.get("variants", []))
        return f"Redesign accepted and saved as the current draft: {names}"

    # ------------------------------------------------------------------
    # Tool-calling loop
    # ------------------------------------------------------------------

    def _tool_definitions(self) -> List[Dict[str, Any]]:
        no_args = {"type": "object", "properties": {}}
        return [
            {"type": "function", "function": {"name": "variant_comparison", "description": VariantComparisonTool.description, "parameters": no_args}},
            {"type": "function", "function": {"name": "segment_insights", "description": SegmentInsightTool.description, "parameters": no_args}},
            {"type": "function", "function": {"name": "channel_effectiveness", "description": ChannelEffectivenessTool.description, "parameters": no_args}},
            {"type": "function", "function": {"name": "content_format_ranking", "description": ContentFormatRankTool.description, "parameters": no_args}},
            {
                "type": "function",
                "function": {
                    "name": "kg_search",
                    "description": "Search the brand's knowledge graph for context that might explain a result.",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "action_log_query",
                    "description": "Inspect the raw action log for one variant: per-round counts, drop-off round, most/least active agents.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "variant_id": {"type": "string"},
                            "action_type": {"type": "string", "description": "Optional OASIS action_type filter, e.g. 'like_post'"},
                            "round_min": {"type": "integer"},
                            "round_max": {"type": "integer"},
                        },
                        "required": ["variant_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "interview_personas",
                    "description": (
                        "Ask specific simulated personas, in character, why they did or didn't engage with a "
                        "variant. Provide agent_ids explicitly, or a selector ('lowest_engagement' | "
                        "'highest_engagement') to auto-pick agents by their action count on this variant."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "variant_id": {"type": "string"},
                            "question": {"type": "string"},
                            "agent_ids": {"type": "array", "items": {"type": "string"}},
                            "selector": {"type": "string", "enum": ["lowest_engagement", "highest_engagement"]},
                            "count": {"type": "integer", "description": f"Max {Config.INSIGHT_AGENT_MAX_INTERVIEWS}"},
                        },
                        "required": ["variant_id", "question"],
                    },
                },
            },
            {"type": "function", "function": {"name": "hypothesis_check", "description": "Compare each AI-proposed variant's recorded hypothesis to its actual scored outcome.", "parameters": no_args}},
            {"type": "function", "function": {"name": "compare_iterations", "description": "See how metrics moved across this campaign's prior/later iterations, if any.", "parameters": no_args}},
            {"type": "function", "function": {"name": "segment_comparison", "description": "Compare simulated engagement for variants targeting an approved real-customer segment against that segment's actual historical behavior stats.", "parameters": no_args}},
            {
                "type": "function",
                "function": {
                    "name": "propose_redesign",
                    "description": (
                        "The only way to put a concrete redesign in front of the user. Same schema as the "
                        "Designer agent's proposals. Validated against the channel registry."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "proposal": {
                                "type": "object",
                                "properties": {
                                    "brand_name": {"type": "string"},
                                    "campaign_goal": {"type": "string"},
                                    "objective": {"type": "string", "enum": OBJECTIVES},
                                    "variants": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "variant_name": {"type": "string"},
                                                "channel": {"type": "string"},
                                                "format": {"type": "string"},
                                                "headline": {"type": "string"},
                                                "body": {"type": "string"},
                                                "cta": {"type": "string"},
                                                "visual_desc": {"type": "string"},
                                                "email_subject": {"type": "string"},
                                                "tone": {"type": "string"},
                                                "target_segment": {"type": "string"},
                                                "rationale": {"type": "string", "description": "What changed vs. the prior iteration and why, citing evidence"},
                                                "hypothesis": {"type": "string"},
                                            },
                                            "required": ["variant_name", "channel", "format", "headline", "body", "cta", "rationale", "hypothesis"],
                                        },
                                    },
                                },
                                "required": ["variants"],
                            },
                        },
                        "required": ["proposal"],
                    },
                },
            },
        ]

    def _call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Unknown tool: {tool_name}"
        if tool_name == "propose_redesign":
            return tool(tool_input.get("proposal", {}))
        return tool(**tool_input)

    def send_message(self, messages: List[Dict[str, Any]], user_message: str) -> Dict[str, Any]:
        self._pending_draft = None

        working_messages = list(messages)
        if not working_messages:
            working_messages.append({"role": "system", "content": INSIGHT_SYSTEM_PROMPT})
            working_messages.append({"role": "assistant", "content": self.initial_report_message()})
        working_messages.append({"role": "user", "content": user_message})

        tool_calls_log: List[Dict[str, Any]] = []
        max_tool_calls = Config.INSIGHT_AGENT_MAX_TOOL_CALLS

        for _ in range(max_tool_calls + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=working_messages,
                tools=self._tool_definitions(),
                tool_choice="auto",
                temperature=Config.INSIGHT_AGENT_TEMPERATURE,
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                working_messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in msg.tool_calls
                    ],
                })
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_input = json.loads(tc.function.arguments)
                    except Exception:
                        logger.warning(
                            f"Malformed tool-call arguments for '{tool_name}': {tc.function.arguments!r}"
                        )
                        tool_input = {}
                    try:
                        result = self._call_tool(tool_name, tool_input)
                    except Exception as e:
                        logger.exception(f"Tool '{tool_name}' failed with input {tool_input}: {e}")
                        result = f"Tool '{tool_name}' failed: {e}"
                    tool_calls_log.append({"tool": tool_name, "input": tool_input, "output_preview": result[:300]})
                    working_messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            else:
                reply = msg.content or ""
                working_messages.append({"role": "assistant", "content": reply})
                return {
                    "messages": working_messages,
                    "reply": reply,
                    "tool_calls_log": tool_calls_log,
                    "draft": self._pending_draft,
                }

        logger.warning("Insight agent hit tool call limit without a final response")
        fallback = "I gathered a lot of context but ran out of turns to respond. Ask me to continue."
        working_messages.append({"role": "assistant", "content": fallback})
        return {"messages": working_messages, "reply": fallback, "tool_calls_log": tool_calls_log, "draft": None}
