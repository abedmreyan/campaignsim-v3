"""Offline persona interviews (Phase 3).

The insight agent runs well after a variant's simulation subprocess has
exited, so there's no live OASIS environment to relay questions through (the
IPC path used by api/interviews.py during an active run). Instead this
rebuilds enough of the persona's context — its generated profile, the
variant content it was shown, and its own logged actions on that variant —
to re-prompt the LLM in character and get a plausible answer to "why did you
(not) engage with this".
"""

import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger("campaignsim.services.persona_interviewer")


def load_agent_actions(variant_output_dir: str, agent_id) -> List[Dict[str, Any]]:
    """All actions this agent took in this variant, in round order."""
    path = os.path.join(variant_output_dir, "actions.jsonl")
    if not os.path.exists(path):
        return []
    actions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(rec.get("agent_id")) == str(agent_id):
                actions.append(rec)
    actions.sort(key=lambda r: r.get("round_num", 0))
    return actions


class PersonaInterviewer:
    def __init__(self):
        self.client = OpenAI(api_key=Config.LLM_API_KEY, base_url=Config.LLM_BASE_URL)
        self.model = Config.LLM_MODEL_NAME

    def interview(
        self,
        profile: Dict[str, Any],
        actions: List[Dict[str, Any]],
        variant_content: Dict[str, Any],
        channel: str,
        question: str,
    ) -> str:
        action_summary = (
            ", ".join(f"round {a.get('round_num', '?')}: {a.get('action_type')}" for a in actions)
            if actions
            else "took no recorded actions (did not engage)"
        )

        system_prompt = (
            f"You are role-playing as a simulated persona named {profile.get('name', 'Unknown')} "
            f"({profile.get('username', '')}), a {profile.get('age', 'N/A')}-year-old "
            f"{profile.get('profession', 'person')}. Bio: {profile.get('bio', 'n/a')}. "
            f"Persona notes: {profile.get('persona', 'n/a')}. "
            f"Interested in: {', '.join(profile.get('interested_topics') or []) or 'unspecified'}.\n\n"
            f"You were shown this {channel} campaign content:\n"
            f"Headline: {variant_content.get('headline', '')}\n"
            f"Body: {variant_content.get('body', '')}\n"
            f"CTA: {variant_content.get('cta', '')}\n\n"
            f"Your recorded actions on this content: {action_summary}.\n\n"
            "Answer the marketer's question in first person, in character, giving a specific, "
            "grounded reason tied to your profile and what you saw — not a generic answer. "
            "Keep it to 2-4 sentences."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Offline persona interview failed for agent {profile.get('user_id')}: {e}")
            return f"(interview failed: {e})"
