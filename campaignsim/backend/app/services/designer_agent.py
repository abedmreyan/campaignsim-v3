"""
CampaignSim Designer Agent (Phase 2)

A multi-turn, tool-using conversational agent that co-designs a campaign with
the user BEFORE any simulation runs. Modeled on campaign_report_agent.py's
ReACT loop, but resumable across turns: each call to send_message() replays
the session's persisted message history, appends the new user turn, and runs
the tool-calling loop to completion.

The agent can only produce a concrete proposal via the propose_variants tool
(never as free-text) — this keeps every proposal machine-validated against
the channel registry and CampaignContent's schema before it's ever shown to
the user as an editable draft, and keeps the "commit" step a pure data
operation (no re-parsing of prose).
"""

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..config import Config
from ..extensions import db
from ..models.orm import BrandBrief, CampaignRecord, Segment, SimulationRecord
from .business_context import OBJECTIVES
from .channel_registry import get_channel, list_channels
from .kg import KGClient
from .simulation_helpers import _load_campaign
from ..utils.logger import get_logger

logger = get_logger("campaignsim.services.designer_agent")


DESIGNER_SYSTEM_PROMPT = """You are a senior marketing strategist collaborating with a
user to design a marketing campaign BEFORE it is simulated. You are having a real
conversation — ask clarifying questions when the brief or goal is ambiguous, critique
weak ideas, and ground every factual claim in tool evidence (the brand's knowledge
graph, the actual channel registry, the actual generated audience, and the user's own
past campaign results) rather than assumption.

Tools available:
- kg_search: search the brand's knowledge graph for audience/competitor/market facts
- list_channels / get_channel: see which marketing channels (and formats, action
  vocabulary, engagement weights) are actually available to simulate
- audience_overview: see the actual generated persona roster for this simulation
- segment_overview: see approved real-customer data segments (from uploaded CRM/order
  data), if any — prefer targeting a variant at a real segment (via target_segment) over
  a generic guess when one fits the campaign goal
- past_campaign_results: see how this brand's previous campaigns scored, if any
- propose_variants: the ONLY way to put a concrete campaign proposal in front of the
  user — you may not describe a proposal in free text instead of calling this tool

Rules:
- Use tools to gather evidence before proposing anything. Do not invent audience facts,
  channel capabilities, or past results — look them up.
- When you call propose_variants, each variant MUST include a `rationale` (why you
  chose this channel/format/angle, citing evidence) and a `hypothesis` — a specific,
  falsifiable claim this variant tests (e.g. "younger personas respond better to
  short-form video than carousel for this product"). The post-simulation insight agent
  checks these hypotheses against real outcomes, so vague hypotheses are not useful.
- Propose at most {max_variants} variants at a time. Prefer fewer, sharper variants
  that test a genuine hypothesis over many similar ones.
- The user reviews, edits, rejects, or asks for alternatives to whatever you propose —
  nothing is ever launched by you. After proposing, briefly explain your reasoning in
  the chat as well, but the structured proposal itself must come from the tool call.
- Be direct. Marketers need clear, evidence-backed recommendations, not hedged
  possibilities.
"""


class DesignerAgent:
    """Runs one turn (or the initial turn) of a Designer session's conversation."""

    def __init__(self, user_id, brand_brief_id=None, simulation_id=None):
        self.user_id = user_id
        self.brand_brief_id = brand_brief_id
        self.simulation_id = simulation_id  # AgentSession.simulation_id (UUID FK), not the file sim_key
        self.client = OpenAI(api_key=Config.LLM_API_KEY, base_url=Config.LLM_BASE_URL)
        self.model = Config.LLM_MODEL_NAME

        self._brief: Optional[BrandBrief] = (
            BrandBrief.query.filter_by(id=brand_brief_id, user_id=user_id).first()
            if brand_brief_id else None
        )
        self._sim_record: Optional[SimulationRecord] = (
            SimulationRecord.query.filter_by(id=simulation_id, user_id=user_id).first()
            if simulation_id else None
        )

        self.tools: Dict[str, Any] = {
            "kg_search": self._tool_kg_search,
            "list_channels": self._tool_list_channels,
            "get_channel": self._tool_get_channel,
            "audience_overview": self._tool_audience_overview,
            "segment_overview": self._tool_segment_overview,
            "past_campaign_results": self._tool_past_campaign_results,
            "propose_variants": self._tool_propose_variants,
        }

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def _tool_kg_search(self, query: str) -> str:
        if not self._brief or not self._brief.graph_id:
            return "No knowledge graph is available for this brief yet."
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
            return f"Graph search failed: {e}"

    def _tool_list_channels(self) -> str:
        channels = list_channels(self.user_id)
        if not channels:
            return "No channels available."
        lines = []
        for c in channels:
            lines.append(
                f"- {c.key} ({c.name}, {c.kind}{'​, custom' if not c.is_builtin else ''}): "
                f"formats={c.formats}"
            )
        return "Available channels:\n" + "\n".join(lines)

    def _tool_get_channel(self, key: str) -> str:
        channel = get_channel(self.user_id, key)
        if not channel:
            return f"Unknown channel '{key}'."
        return (
            f"Channel '{channel.key}' ({channel.name}, kind={channel.kind}):\n"
            f"formats: {channel.formats}\n"
            f"available_actions: {channel.available_actions}\n"
            f"action_weights: {channel.action_weights}\n"
            f"funnel_map: {channel.funnel_map}\n"
            f"description: {channel.description or 'n/a'}"
        )

    def _tool_audience_overview(self) -> str:
        if not self._sim_record:
            return "No simulation is linked to this session yet — no generated audience to inspect."
        from .simulation_manager import SimulationManager

        try:
            manager = SimulationManager()
            profiles = manager.get_profiles(self._sim_record.sim_key, platform="reddit")
        except Exception as e:
            return f"Could not read the persona roster: {e}"

        personas = [p for p in profiles if str(p.get("user_id")) != "0"]
        if not personas:
            return "No personas have been generated for this simulation yet."

        ages = [p["age"] for p in personas if p.get("age")]
        genders: Dict[str, int] = {}
        professions: Dict[str, int] = {}
        topics: Dict[str, int] = {}
        for p in personas:
            if p.get("gender"):
                genders[p["gender"]] = genders.get(p["gender"], 0) + 1
            if p.get("profession"):
                professions[p["profession"]] = professions.get(p["profession"], 0) + 1
            for t in p.get("interested_topics") or []:
                topics[t] = topics.get(t, 0) + 1

        top_professions = sorted(professions.items(), key=lambda x: -x[1])[:6]
        top_topics = sorted(topics.items(), key=lambda x: -x[1])[:8]

        return (
            f"Audience: {len(personas)} personas.\n"
            f"Age range: {min(ages) if ages else '?'}-{max(ages) if ages else '?'}\n"
            f"Gender split: {genders}\n"
            f"Top professions: {top_professions}\n"
            f"Top interested topics: {top_topics}"
        )

    def _tool_segment_overview(self) -> str:
        """Real-data customer segments (Phase 4) approved for this user —
        propose variants targeting these by name in target_segment so scoring
        can tie results back to the segment's actual historical stats."""
        segments = Segment.query.filter_by(user_id=self.user_id, status="approved").all()
        if not segments:
            return (
                "No approved real-customer segments yet. Upload and segment a customer "
                "dataset (Audience section) and approve segments to target them here."
            )
        lines = []
        for s in segments:
            stats = s.stats or {}
            lines.append(
                f"- '{s.name}' ({s.size} customers): {s.description} | "
                f"avg_ltv={stats.get('avg_ltv')}, avg_age={stats.get('avg_age')}, "
                f"avg_email_open_rate={stats.get('avg_email_open_rate')}, "
                f"top_channels={stats.get('top_channels')}"
            )
        return "Approved real-customer segments (set target_segment to one of these names):\n" + "\n".join(lines)

    def _tool_past_campaign_results(self, brief_id: Optional[str] = None) -> str:
        # brief_id may arrive as a string from tool-call JSON args (or be this
        # session's own UUID field) — the brand_brief_id column is UUID-typed,
        # so a plain str value would fail SQLAlchemy's UUID bind processor.
        target_brief_id = self.brand_brief_id
        if brief_id:
            try:
                import uuid as _uuid
                target_brief_id = _uuid.UUID(str(brief_id))
            except ValueError:
                return f"'{brief_id}' is not a valid brief id."

        query = CampaignRecord.query.filter_by(user_id=self.user_id)
        if target_brief_id:
            query = query.filter_by(brand_brief_id=target_brief_id)
        records = query.order_by(CampaignRecord.created_at.desc()).limit(5).all()

        if not records:
            return "No past campaigns found for this brand."

        lines = []
        for rec in records:
            campaign = _load_campaign(rec.campaign_ref) if rec.campaign_ref else None
            report = None
            if rec.campaign_ref:
                import os
                from .simulation_helpers import _campaigns_dir
                path = os.path.join(_campaigns_dir(), f"{rec.campaign_ref}.json")
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        report = json.load(f).get("campaign_report")

            if report and report.get("scored_variants"):
                best = report["scored_variants"][0]
                lines.append(
                    f"- Campaign '{rec.brand_name}' (goal: {rec.campaign_goal}, "
                    f"objective: {rec.objective or 'unset'}): best variant "
                    f"'{best.get('variant_name')}' on {best.get('channel')} at "
                    f"{best.get('engagement_rate_pct')}% engagement."
                )
            else:
                lines.append(f"- Campaign '{rec.brand_name}' — not yet scored.")

        return "Past campaigns:\n" + "\n".join(lines)

    def _tool_propose_variants(self, proposal: Dict[str, Any]) -> str:
        errors = self.validate_proposal(proposal)
        if errors:
            return "Proposal rejected — fix these issues and call propose_variants again:\n" + "\n".join(
                f"- {e}" for e in errors
            )
        self._pending_draft = proposal
        names = ", ".join(v.get("variant_name", "?") for v in proposal.get("variants", []))
        return f"Proposal accepted and saved as the current draft: {names}"

    def validate_proposal(self, proposal: Dict[str, Any]) -> List[str]:
        errors = []
        if not isinstance(proposal, dict):
            return ["proposal must be a JSON object"]

        objective = proposal.get("objective")
        if objective and objective not in OBJECTIVES:
            errors.append(f"objective must be one of {OBJECTIVES} or omitted")

        variants = proposal.get("variants")
        if not isinstance(variants, list) or not variants:
            return errors + ["variants must be a non-empty list"]
        if len(variants) > Config.DESIGNER_AGENT_MAX_VARIANTS:
            errors.append(f"at most {Config.DESIGNER_AGENT_MAX_VARIANTS} variants are allowed per proposal")

        for i, v in enumerate(variants):
            label = v.get("variant_name") or f"variant {i + 1}"
            channel_key = v.get("channel")
            channel = get_channel(self.user_id, channel_key) if channel_key else None
            if not channel:
                errors.append(f"{label}: unknown channel '{channel_key}'")
            else:
                fmt = v.get("format", "")
                if channel.formats and fmt.lower() not in {f.lower() for f in channel.formats}:
                    errors.append(
                        f"{label}: format '{fmt}' is not valid for channel '{channel_key}' "
                        f"(valid: {channel.formats})"
                    )
            for field in ("headline", "body", "cta"):
                if not v.get(field):
                    errors.append(f"{label}: '{field}' is required")
            if not v.get("rationale"):
                errors.append(f"{label}: 'rationale' is required")
            if not v.get("hypothesis"):
                errors.append(f"{label}: 'hypothesis' is required")

        return errors

    # ------------------------------------------------------------------
    # Tool-calling loop
    # ------------------------------------------------------------------

    def _tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "kg_search",
                    "description": "Search the brand's knowledge graph for audience, competitor, or market facts.",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string", "description": "Search query"}},
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_channels",
                    "description": "List all marketing channels available to this user (builtin + custom), with their formats.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_channel",
                    "description": "Get full detail (actions, weights, funnel_map) for one channel by key.",
                    "parameters": {
                        "type": "object",
                        "properties": {"key": {"type": "string", "description": "Channel key, e.g. 'instagram'"}},
                        "required": ["key"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "audience_overview",
                    "description": "See the actual generated persona roster (demographics, professions, interests) for this session's simulation.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "segment_overview",
                    "description": "See approved real-customer data segments (from uploaded CRM/order data), with aggregate stats. Target a variant at one by name via target_segment.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "past_campaign_results",
                    "description": "See how this brand's previous campaigns scored, if any exist.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "brief_id": {"type": "string", "description": "Optional — defaults to this session's brief"}
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "propose_variants",
                    "description": (
                        "The only way to put a concrete campaign proposal in front of the user. "
                        "Validated against the channel registry — invalid proposals are rejected with "
                        "specific errors so you can self-correct and retry."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "proposal": {
                                "type": "object",
                                "properties": {
                                    "brand_name": {"type": "string"},
                                    "campaign_goal": {"type": "string"},
                                    "objective": {
                                        "type": "string",
                                        "enum": OBJECTIVES,
                                        "description": "Optional campaign objective",
                                    },
                                    "variants": {
                                        "type": "array",
                                        "maxItems": Config.DESIGNER_AGENT_MAX_VARIANTS,
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
                                                "rationale": {
                                                    "type": "string",
                                                    "description": "Why this variant, citing tool evidence",
                                                },
                                                "hypothesis": {
                                                    "type": "string",
                                                    "description": "A specific, falsifiable claim this variant tests",
                                                },
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
        if tool_name == "kg_search":
            return tool(tool_input.get("query", ""))
        if tool_name == "get_channel":
            return tool(tool_input.get("key", ""))
        if tool_name == "past_campaign_results":
            return tool(tool_input.get("brief_id"))
        if tool_name == "propose_variants":
            return tool(tool_input.get("proposal", {}))
        return tool()

    def send_message(self, messages: List[Dict[str, Any]], user_message: str) -> Dict[str, Any]:
        """
        Run one conversational turn. `messages` is the session's persisted
        history (OpenAI chat-message dicts); the new user_message is appended
        before the loop starts. Returns the updated message list, a tool-call
        log for this turn, and any draft produced by propose_variants.

        Returns:
            {
                "messages": [...],       full updated history to persist
                "reply": str,            the assistant's final text for this turn
                "tool_calls_log": [...], this turn's tool activity
                "draft": dict | None,    set only if propose_variants was called
            }
        """
        self._pending_draft = None

        working_messages = list(messages)
        if not working_messages:
            working_messages.append({
                "role": "system",
                "content": DESIGNER_SYSTEM_PROMPT.format(max_variants=Config.DESIGNER_AGENT_MAX_VARIANTS),
            })
        working_messages.append({"role": "user", "content": user_message})

        tool_calls_log: List[Dict[str, Any]] = []
        max_tool_calls = Config.DESIGNER_AGENT_MAX_TOOL_CALLS

        for _ in range(max_tool_calls + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=working_messages,
                tools=self._tool_definitions(),
                tool_choice="auto",
                temperature=Config.DESIGNER_AGENT_TEMPERATURE,
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                working_messages.append(
                    {"role": "assistant", "content": msg.content, "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in msg.tool_calls
                    ]}
                )
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_input = json.loads(tc.function.arguments)
                    except Exception:
                        tool_input = {}
                    result = self._call_tool(tool_name, tool_input)
                    tool_calls_log.append({
                        "tool": tool_name, "input": tool_input, "output_preview": result[:300],
                    })
                    working_messages.append({
                        "role": "tool", "tool_call_id": tc.id, "content": result,
                    })
            else:
                reply = msg.content or ""
                working_messages.append({"role": "assistant", "content": reply})
                return {
                    "messages": working_messages,
                    "reply": reply,
                    "tool_calls_log": tool_calls_log,
                    "draft": self._pending_draft,
                }

        logger.warning("Designer agent hit tool call limit without a final reply")
        fallback = "I gathered a lot of context but ran out of turns — could you ask me to summarize or propose variants now?"
        working_messages.append({"role": "assistant", "content": fallback})
        return {
            "messages": working_messages,
            "reply": fallback,
            "tool_calls_log": tool_calls_log,
            "draft": self._pending_draft,
        }
