"""OASIS Agent Profile
ZepOASISAgent Profile

1. Zep
2. 
3. """

import asyncio
import json
import random
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI, AsyncOpenAI
from .kg import KGClient

from ..config import Config
from ..utils.logger import get_logger
from ..utils.locale import get_language_instruction, get_locale, set_locale, t
from .zep_entity_reader import EntityNode, ZepEntityReader

logger = get_logger('campaignsim.oasis_profile')

@dataclass
class OasisAgentProfile:
    """OASIS Agent Profile"""
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str
    
    #  - Reddit
    karma: int = 1000
    
    #  - Twitter
    friend_count: int = 100
    follower_count: int = 150
    statuses_count: int = 500
    
    age: Optional[int] = None
    gender: Optional[str] = None
    mbti: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    interested_topics: List[str] = field(default_factory=list)
    
    source_entity_uuid: Optional[str] = None
    source_entity_type: Optional[str] = None
    
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def to_reddit_format(self) -> Dict[str, Any]:
        """Reddit"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,  # OASIS  username
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "created_at": self.created_at,
        }
        
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        
        return profile
    
    def to_twitter_format(self) -> Dict[str, Any]:
        """Twitter"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,  # OASIS  username
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "created_at": self.created_at,
        }
        
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        
        return profile
    
    def to_dict(self) -> Dict[str, Any]:
        """..."""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "age": self.age,
            "gender": self.gender,
            "mbti": self.mbti,
            "country": self.country,
            "profession": self.profession,
            "interested_topics": self.interested_topics,
            "source_entity_uuid": self.source_entity_uuid,
            "source_entity_type": self.source_entity_type,
            "created_at": self.created_at,
        }

class OasisProfileGenerator:
    """    OASIS Profile
    
    ZepOASISAgent Profile
    
    1. Zep
    2. 
    3. """
    
    # MBTI
    MBTI_TYPES = [
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
        "ISTP", "ISFP", "ESTP", "ESFP"
    ]
    
    COUNTRIES = [
        "China", "US", "UK", "Japan", "Germany", "France", 
        "Canada", "Australia", "Brazil", "India", "South Korea"
    ]
    
    # Individual entity types — generate a customer persona profile
    INDIVIDUAL_ENTITY_TYPES = [
        "customerpersona", "person", "influencer", "consumer", "buyer",
        "user", "shopper", "subscriber", "prospect"
    ]

    # Group / institutional entity types — generate a brand account profile
    GROUP_ENTITY_TYPES = [
        "brand", "competitor", "marketingchannel", "organization",
        "mediaoutlet", "retailer", "agency", "market", "contentformat",
        "campaign", "product"
    ]
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        zep_api_key: Optional[str] = None,
        graph_id: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY not configured")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Knowledge graph client
        self.zep_client = KGClient(data_dir=Config.KG_DATA_DIR)
        self.graph_id = graph_id
    
    def generate_profile_from_entity(
        self, 
        entity: EntityNode, 
        user_id: int,
        use_llm: bool = True
    ) -> OasisAgentProfile:
        """        ZepOASIS Agent Profile
        
        Args:
            entity: Zep
            user_id: IDOASIS
            use_llm: LLM
            
        Returns:
            OasisAgentProfile"""
        entity_type = entity.get_entity_type() or "Entity"
        
        name = entity.name
        user_name = self._generate_username(name)
        
        context = self._build_entity_context(entity)
        
        if use_llm:
            # LLM
            profile_data = self._generate_profile_with_llm(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes,
                context=context
            )
        else:
            profile_data = self._generate_profile_rule_based(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes
            )
        
        return OasisAgentProfile(
            user_id=user_id,
            user_name=user_name,
            name=name,
            bio=profile_data.get("bio", f"{entity_type}: {name}"),
            persona=profile_data.get("persona", entity.summary or f"A {entity_type} named {name}."),
            karma=profile_data.get("karma", random.randint(500, 5000)),
            friend_count=profile_data.get("friend_count", random.randint(50, 500)),
            follower_count=profile_data.get("follower_count", random.randint(100, 1000)),
            statuses_count=profile_data.get("statuses_count", random.randint(100, 2000)),
            age=profile_data.get("age"),
            gender=profile_data.get("gender"),
            mbti=profile_data.get("mbti"),
            country=profile_data.get("country"),
            profession=profile_data.get("profession"),
            interested_topics=profile_data.get("interested_topics", []),
            source_entity_uuid=entity.uuid,
            source_entity_type=entity_type,
        )
    
    def _generate_username(self, name: str) -> str:
        """..."""
        username = name.lower().replace(" ", "_")
        username = ''.join(c for c in username if c.isalnum() or c == '_')
        
        suffix = random.randint(100, 999)
        return f"{username}_{suffix}"
    
    def _search_zep_for_entity(self, entity: EntityNode) -> Dict[str, Any]:
        """        Zep
        
        Zepedgesnodes
        
        Args:
            entity: 
            
        Returns:
            facts, node_summaries, context"""
        import concurrent.futures
        
        if not self.zep_client:
            return {"facts": [], "node_summaries": [], "context": ""}
        
        entity_name = entity.name
        
        results = {
            "facts": [],
            "node_summaries": [],
            "context": ""
        }
        
        # graph_id
        if not self.graph_id:
            logger.debug(f"Skipping Zep retrieval: graph_id not set")
            return results
        
        comprehensive_query = t('progress.zepSearchQuery', name=entity_name)
        
        def search_edges():
            """/- """
            max_retries = 3
            last_exception = None
            delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=30,
                        scope="edges",
                        reranker="rrf"
                    )
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.debug(f"Zep edge search attempt {attempt + 1} failed: {str(e)[:80]}, retrying...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep edge search: failed after {max_retries} attempts, still failing: {e}")
            return None
        
        def search_nodes():
            """- """
            max_retries = 3
            last_exception = None
            delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=20,
                        scope="nodes",
                        reranker="rrf"
                    )
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.debug(f"Zep node search attempt {attempt + 1} failed: {str(e)[:80]}, retrying...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep node search: failed after {max_retries} attempts, still failing: {e}")
            return None
        
        try:
            # edgesnodes
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                edge_future = executor.submit(search_edges)
                node_future = executor.submit(search_nodes)
                
                edge_result = edge_future.result(timeout=30)
                node_result = node_future.result(timeout=30)
            
            all_facts = set()
            if edge_result and hasattr(edge_result, 'edges') and edge_result.edges:
                for edge in edge_result.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        all_facts.add(edge.fact)
            results["facts"] = list(all_facts)
            
            all_summaries = set()
            if node_result and hasattr(node_result, 'nodes') and node_result.nodes:
                for node in node_result.nodes:
                    if hasattr(node, 'summary') and node.summary:
                        all_summaries.add(node.summary)
                    if hasattr(node, 'name') and node.name and node.name != entity_name:
                        all_summaries.add(f"Entity: {node.name}")
            results["node_summaries"] = list(all_summaries)
            
            context_parts = []
            if results["facts"]:
                context_parts.append(":\n" + "\n".join(f"- {f}" for f in results["facts"][:20]))
            if results["node_summaries"]:
                context_parts.append(":\n" + "\n".join(f"- {s}" for s in results["node_summaries"][:10]))
            results["context"] = "\n\n".join(context_parts)
            
            logger.info(f"Zep: {entity_name}, {len(results['facts'])} , {len(results['node_summaries'])} ")
            
        except concurrent.futures.TimeoutError:
            logger.warning(f"Zep ({entity_name})")
        except Exception as e:
            logger.warning(f"Zep ({entity_name}): {e}")
        
        return results
    
    def _build_entity_context(self, entity: EntityNode) -> str:
        """        1. 
        2. 
        3. Zep"""
        context_parts = []
        
        # 1.
        if entity.attributes:
            attrs = []
            for key, value in entity.attributes.items():
                if value and str(value).strip():
                    attrs.append(f"- {key}: {value}")
            if attrs:
                context_parts.append("### \n" + "\n".join(attrs))
        
        # 2. /
        existing_facts = set()
        if entity.related_edges:
            relationships = []
            for edge in entity.related_edges:
                fact = edge.get("fact", "")
                edge_name = edge.get("edge_name", "")
                direction = edge.get("direction", "")
                
                if fact:
                    relationships.append(f"- {fact}")
                    existing_facts.add(fact)
                elif edge_name:
                    if direction == "outgoing":
                        relationships.append(f"- {entity.name} --[{edge_name}]--> ()")
                    else:
                        relationships.append(f"- () --[{edge_name}]--> {entity.name}")
            
            if relationships:
                context_parts.append("### \n" + "\n".join(relationships))
        
        # 3.
        if entity.related_nodes:
            related_info = []
            for node in entity.related_nodes:
                node_name = node.get("name", "")
                node_labels = node.get("labels", [])
                node_summary = node.get("summary", "")
                
                custom_labels = [l for l in node_labels if l not in ["Entity", "Node"]]
                label_str = f" ({', '.join(custom_labels)})" if custom_labels else ""
                
                if node_summary:
                    related_info.append(f"- **{node_name}**{label_str}: {node_summary}")
                else:
                    related_info.append(f"- **{node_name}**{label_str}")
            
            if related_info:
                context_parts.append("### \n" + "\n".join(related_info))
        
        # 4. Zep
        zep_results = self._search_zep_for_entity(entity)
        
        if zep_results.get("facts"):
            new_facts = [f for f in zep_results["facts"] if f not in existing_facts]
            if new_facts:
                context_parts.append("### Zep\n" + "\n".join(f"- {f}" for f in new_facts[:15]))
        
        if zep_results.get("node_summaries"):
            context_parts.append("### Zep\n" + "\n".join(f"- {s}" for s in zep_results["node_summaries"][:10]))
        
        return "\n\n".join(context_parts)
    
    def _is_individual_entity(self, entity_type: str) -> bool:
        """..."""
        return entity_type.lower() in self.INDIVIDUAL_ENTITY_TYPES
    
    def _is_group_entity(self, entity_type: str) -> bool:
        """/"""
        return entity_type.lower() in self.GROUP_ENTITY_TYPES
    
    def _generate_profile_with_llm(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """        LLM
        
        - 
        - /"""
        
        is_individual = self._is_individual_entity(entity_type)
        
        if is_individual:
            prompt = self._build_individual_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )
        else:
            prompt = self._build_group_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )

        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(is_individual)},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)
                    # max_tokensLLM
                )
                
                content = response.choices[0].message.content
                
                # finish_reason'stop'
                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'length':
                    logger.warning(f"LLM (attempt {attempt+1}), ...")
                    content = self._fix_truncated_json(content)
                
                # JSON
                try:
                    result = json.loads(content)
                    
                    if "bio" not in result or not result["bio"]:
                        result["bio"] = entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}"
                    if "persona" not in result or not result["persona"]:
                        result["persona"] = entity_summary or f"{entity_name}{entity_type}"
                    
                    return result
                    
                except json.JSONDecodeError as je:
                    logger.warning(f"JSON (attempt {attempt+1}): {str(je)[:80]}")
                    
                    # JSON
                    result = self._try_fix_json(content, entity_name, entity_type, entity_summary)
                    if result.get("_fixed"):
                        del result["_fixed"]
                        return result
                    
                    last_error = je
                    
            except Exception as e:
                logger.warning(f"LLM (attempt {attempt+1}): {str(e)[:80]}")
                last_error = e
                import time
                time.sleep(1 * (attempt + 1))
        
        logger.warning(f"LLM{max_attempts}: {last_error}, ")
        return self._generate_profile_rule_based(
            entity_name, entity_type, entity_summary, entity_attributes
        )
    
    def _fix_truncated_json(self, content: str) -> str:
        """JSONmax_tokens"""
        import re
        
        # JSON
        content = content.strip()
        
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')
        
        if content and content[-1] not in '",}]':
            content += '"'
        
        content += ']' * open_brackets
        content += '}' * open_braces
        
        return content
    
    def _try_fix_json(self, content: str, entity_name: str, entity_type: str, entity_summary: str = "") -> Dict[str, Any]:
        """JSON"""
        import re
        
        # 1.
        content = self._fix_truncated_json(content)
        
        # 2. JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group()
            
            # 3.
            def fix_string_newlines(match):
                s = match.group(0)
                s = s.replace('\n', ' ').replace('\r', ' ')
                s = re.sub(r'\s+', ' ', s)
                return s
            
            # JSON
            json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string_newlines, json_str)
            
            # 4.
            try:
                result = json.loads(json_str)
                result["_fixed"] = True
                return result
            except json.JSONDecodeError as e:
                # 5.
                try:
                    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                    json_str = re.sub(r'\s+', ' ', json_str)
                    result = json.loads(json_str)
                    result["_fixed"] = True
                    return result
                except:
                    pass
        
        # 6.
        bio_match = re.search(r'"bio"\s*:\s*"([^"]*)"', content)
        persona_match = re.search(r'"persona"\s*:\s*"([^"]*)', content)
        
        bio = bio_match.group(1) if bio_match else (entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}")
        persona = persona_match.group(1) if persona_match else (entity_summary or f"{entity_name}{entity_type}")
        
        if bio_match or persona_match:
            logger.info(f"JSON")
            return {
                "bio": bio,
                "persona": persona,
                "_fixed": True
            }
        
        # 7.
        logger.warning(f"JSON")
        return {
            "bio": entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}",
            "persona": entity_summary or f"{entity_name}{entity_type}"
        }
    
    def _get_system_prompt(self, is_individual: bool) -> str:
        """Return system prompt for persona generation."""
        if is_individual:
            return ("You are a marketing customer persona generation expert. "
                    "Generate detailed, realistic customer persona profiles for marketing campaign simulation. "
                    "Return only valid JSON. All string values must not contain unescaped newlines.")
        else:
            return ("You are a marketing brand account profile generation expert. "
                    "Generate detailed brand and channel account profiles for marketing campaign simulation. "
                    "Return only valid JSON. All string values must not contain unescaped newlines.")

    def _build_individual_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> str:
        """Build the prompt for generating a customer persona agent profile."""
        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "none"
        context_str = context[:3000] if context else "No additional context"

        return f"""Generate a detailed customer persona profile for use in a marketing campaign simulation.

Entity name: {entity_name}
Entity type: {entity_type}
Entity summary: {entity_summary}
Entity attributes: {attrs_str}

Context from brand knowledge graph:
{context_str}

Return JSON with these exact fields:

1. bio: 200-character social media bio this persona would write about themselves
2. persona: Detailed 1500-word profile (plain text, NO newlines) covering:
   - Demographics (age, gender, location, income bracket, education level)
   - Psychographics (values, lifestyle, motivations, pain points)
   - Buying behaviour (decision process, research habits, brand loyalty, price sensitivity)
   - Channel behaviour (which platforms they use, how often, what content they engage with)
   - Content preferences (video vs text vs image, long-form vs short, UGC vs branded)
   - Response to advertising (ad-skipping habits, preferred ad formats, trusted voices)
   - Relationship to the brand/product being marketed (aware, considers, loyal, lapsed)
   - Memory (what this persona has already seen or done related to this campaign)
3. age: integer (e.g. 28)
4. gender: string — must be "male" or "female"
5. mbti: MBTI type string (e.g. "ENFP")
6. country: country name in English (e.g. "US")
7. profession: job title or occupation
8. interested_topics: array of topic strings this persona cares about

Rules:
- All field values must be strings or numbers — no null, no embedded newlines
- persona must be a single continuous paragraph
- age must be a valid integer, gender must be "male" or "female"
- Keep consistent with the entity attributes and context provided
"""

    def _build_group_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> str:
        """Build the prompt for generating a brand / channel account profile."""
        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "none"
        context_str = context[:3000] if context else "No additional context"

        return f"""Generate a detailed brand or channel account profile for use in a marketing campaign simulation.

Entity name: {entity_name}
Entity type: {entity_type}
Entity summary: {entity_summary}
Entity attributes: {attrs_str}

Context:
{context_str}

Return JSON with these exact fields:

1. bio: 200-character official account bio (professional, on-brand)
2. persona: Detailed 1500-word account profile (plain text, NO newlines) covering:
   - Organisation overview (what they do, market position, brand voice)
   - Account purpose (what this account publishes, target audience for its content)
   - Content style (tone of voice, message pillars, visual identity cues)
   - Posting behaviour (frequency, timing, content mix)
   - Stance on campaign-relevant topics (how they respond to competitor moves, trends)
   - Memory (what this brand/channel has already done in relation to this campaign)
3. age: integer 0 (not applicable for brand/institutional accounts)
4. gender: string "other" (institutional accounts are not individuals)
5. mbti: MBTI string describing the brand personality (e.g. "ESTJ" for authoritative brands)
6. country: country name in English (e.g. "US")
7. profession: describe the organisation's function (e.g. "FMCG Brand", "Social Media Channel")
8. interested_topics: array of topics this account posts about

Rules:
- All values must be strings or numbers — no null, no embedded newlines
- persona must be a single continuous paragraph
- age must be integer 0, gender must be string "other"
"""
    
    def _generate_profile_rule_based(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a baseline profile using rules (fallback when LLM is unavailable)."""
        et = entity_type.lower()

        if et in ["customerpersona", "person", "consumer", "buyer", "shopper", "prospect"]:
            return {
                "bio": f"Consumer interested in products like {entity_name}.",
                "persona": (
                    f"{entity_name} is a consumer who researches products carefully before buying, "
                    "is active on social media, and responds well to authentic content. "
                    "They are value-conscious but willing to pay a premium for quality products "
                    "that fit their lifestyle."
                ),
                "age": random.randint(22, 45),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": "US",
                "profession": "Professional",
                "interested_topics": ["Shopping", "Lifestyle", "Technology"],
            }

        elif et in ["influencer", "creator"]:
            return {
                "bio": f"Content creator and opinion leader. Partnering with brands I believe in.",
                "persona": (
                    f"{entity_name} is a content creator with an engaged following. "
                    "They are selective about brand partnerships and prioritise authenticity. "
                    "Their audience trusts their recommendations on lifestyle, products, and trends."
                ),
                "age": random.randint(22, 35),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(["ENFP", "ESFP", "ENFJ"]),
                "country": "US",
                "profession": "Content Creator",
                "interested_topics": ["Content Creation", "Brand Partnerships", "Lifestyle"],
            }

        elif et in ["brand", "competitor"]:
            return {
                "bio": f"Official account of {entity_name}.",
                "persona": (
                    f"{entity_name} is a brand account that shares product news, engages with customers, "
                    "and communicates brand values. The account maintains a consistent brand voice and "
                    "responds to customer feedback in a timely manner."
                ),
                "age": 0,
                "gender": "other",
                "mbti": "ESTJ",
                "country": "US",
                "profession": "Brand Account",
                "interested_topics": ["Products", "Brand News", "Customer Engagement"],
            }

        elif et in ["marketingchannel"]:
            return {
                "bio": f"Official {entity_name} channel presence.",
                "persona": (
                    f"This is the {entity_name} channel representation. It reflects the norms and "
                    "audience behaviour typical of this platform. Content here is optimised for the "
                    "platform's algorithm and audience engagement patterns."
                ),
                "age": 0,
                "gender": "other",
                "mbti": "ISTP",
                "country": "US",
                "profession": "Marketing Channel",
                "interested_topics": ["Digital Marketing", "Content", "Advertising"],
            }

        elif et in ["campaign", "product", "contentformat", "market"]:
            return {
                "bio": f"Campaign/product entity: {entity_name}.",
                "persona": (
                    f"{entity_name} is a {entity_type} participating in the campaign simulation. "
                    f"{entity_summary or 'It represents a key component of the marketing strategy.'}"
                ),
                "age": 0,
                "gender": "other",
                "mbti": "ISTJ",
                "country": "US",
                "profession": entity_type,
                "interested_topics": ["Marketing", "Advertising", "Business"],
            }

        else:
            return {
                "bio": entity_summary[:150] if entity_summary else f"{entity_type}: {entity_name}",
                "persona": (
                    entity_summary or
                    f"{entity_name} is a {entity_type} participating in the campaign simulation."
                ),
                "age": random.randint(25, 50),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": "US",
                "profession": entity_type,
                "interested_topics": ["Marketing", "Business"],
            }
    
    def set_graph_id(self, graph_id: str):
        """IDZep"""
        self.graph_id = graph_id

    # ── Async variants ────────────────────────────────────────────────────────

    async def _search_zep_for_entity_async(self, entity: EntityNode) -> Dict[str, Any]:
        """Async version of _search_zep_for_entity — wraps sync Zep calls in threads."""
        if not self.zep_client or not self.graph_id:
            return {"facts": [], "node_summaries": [], "context": ""}

        entity_name = entity.name
        comprehensive_query = t('progress.zepSearchQuery', name=entity_name)

        def _search_edges():
            max_retries, delay = 3, 2.0
            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=30,
                        scope="edges",
                        reranker="rrf"
                    )
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep edge search failed after {max_retries} attempts: {e}")
            return None

        def _search_nodes():
            max_retries, delay = 3, 2.0
            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=20,
                        scope="nodes",
                        reranker="rrf"
                    )
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep node search failed after {max_retries} attempts: {e}")
            return None

        results = {"facts": [], "node_summaries": [], "context": ""}
        try:
            edge_result, node_result = await asyncio.gather(
                asyncio.to_thread(_search_edges),
                asyncio.to_thread(_search_nodes),
            )

            all_facts = set()
            if edge_result and hasattr(edge_result, 'edges') and edge_result.edges:
                for edge in edge_result.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        all_facts.add(edge.fact)
            results["facts"] = list(all_facts)

            all_summaries = set()
            if node_result and hasattr(node_result, 'nodes') and node_result.nodes:
                for node in node_result.nodes:
                    if hasattr(node, 'summary') and node.summary:
                        all_summaries.add(node.summary)
                    if hasattr(node, 'name') and node.name and node.name != entity_name:
                        all_summaries.add(f"Entity: {node.name}")
            results["node_summaries"] = list(all_summaries)

            context_parts = []
            if results["facts"]:
                context_parts.append(":\n" + "\n".join(f"- {f}" for f in results["facts"][:20]))
            if results["node_summaries"]:
                context_parts.append(":\n" + "\n".join(f"- {s}" for s in results["node_summaries"][:10]))
            results["context"] = "\n\n".join(context_parts)

            logger.info(f"Zep async: {entity_name}, {len(results['facts'])} facts, {len(results['node_summaries'])} nodes")
        except Exception as e:
            logger.warning(f"Zep async search failed ({entity_name}): {e}")

        return results

    async def _build_entity_context_async(self, entity: EntityNode) -> str:
        """Async version of _build_entity_context."""
        context_parts = []

        if entity.attributes:
            attrs = []
            for key, value in entity.attributes.items():
                if value and str(value).strip():
                    attrs.append(f"- {key}: {value}")
            if attrs:
                context_parts.append("### \n" + "\n".join(attrs))

        existing_facts = set()
        if entity.related_edges:
            relationships = []
            for edge in entity.related_edges:
                fact = edge.get("fact", "")
                edge_name = edge.get("edge_name", "")
                direction = edge.get("direction", "")
                if fact:
                    relationships.append(f"- {fact}")
                    existing_facts.add(fact)
                elif edge_name:
                    if direction == "outgoing":
                        relationships.append(f"- {entity.name} --[{edge_name}]--> ()")
                    else:
                        relationships.append(f"- () --[{edge_name}]--> {entity.name}")
            if relationships:
                context_parts.append("### \n" + "\n".join(relationships))

        if entity.related_nodes:
            related_info = []
            for node in entity.related_nodes:
                node_name = node.get("name", "")
                node_labels = node.get("labels", [])
                node_summary = node.get("summary", "")
                custom_labels = [l for l in node_labels if l not in ["Entity", "Node"]]
                label_str = f" ({', '.join(custom_labels)})" if custom_labels else ""
                if node_summary:
                    related_info.append(f"- **{node_name}**{label_str}: {node_summary}")
                else:
                    related_info.append(f"- **{node_name}**{label_str}")
            if related_info:
                context_parts.append("### \n" + "\n".join(related_info))

        zep_results = await self._search_zep_for_entity_async(entity)

        if zep_results.get("facts"):
            new_facts = [f for f in zep_results["facts"] if f not in existing_facts]
            if new_facts:
                context_parts.append("### Zep\n" + "\n".join(f"- {f}" for f in new_facts[:15]))
        if zep_results.get("node_summaries"):
            context_parts.append("### Zep\n" + "\n".join(f"- {s}" for s in zep_results["node_summaries"][:10]))

        return "\n\n".join(context_parts)

    async def _generate_profile_with_llm_async(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """Async LLM profile generation using AsyncOpenAI."""
        is_individual = self._is_individual_entity(entity_type)
        if is_individual:
            prompt = self._build_individual_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )
        else:
            prompt = self._build_group_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )

        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(is_individual)},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)
                )

                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'length':
                    logger.warning(f"LLM truncated (attempt {attempt+1}) for {entity_name}")
                    content = self._fix_truncated_json(content)

                try:
                    result = json.loads(content)
                    if "bio" not in result or not result["bio"]:
                        result["bio"] = entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}"
                    if "persona" not in result or not result["persona"]:
                        result["persona"] = entity_summary or f"{entity_name} {entity_type}"
                    return result
                except json.JSONDecodeError as je:
                    logger.warning(f"JSON decode error (attempt {attempt+1}): {str(je)[:80]}")
                    result = self._try_fix_json(content, entity_name, entity_type, entity_summary)
                    if result.get("_fixed"):
                        del result["_fixed"]
                        return result
                    last_error = je

            except Exception as e:
                logger.warning(f"Async LLM error (attempt {attempt+1}): {str(e)[:80]}")
                last_error = e
                await asyncio.sleep(1 * (attempt + 1))

        logger.warning(f"All {max_attempts} LLM attempts failed for {entity_name}, using rule-based fallback")
        return self._generate_profile_rule_based(entity_name, entity_type, entity_summary, entity_attributes)

    async def _generate_profile_from_entity_async(
        self,
        entity: EntityNode,
        user_id: int,
        use_llm: bool = True
    ) -> OasisAgentProfile:
        """Async version of generate_profile_from_entity."""
        entity_type = entity.get_entity_type() or "Entity"
        name = entity.name
        user_name = self._generate_username(name)
        context = await self._build_entity_context_async(entity)

        if use_llm:
            profile_data = await self._generate_profile_with_llm_async(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes,
                context=context
            )
        else:
            profile_data = self._generate_profile_rule_based(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes
            )

        return OasisAgentProfile(
            user_id=user_id,
            user_name=user_name,
            name=name,
            bio=profile_data.get("bio", f"{entity_type}: {name}"),
            persona=profile_data.get("persona", entity.summary or f"A {entity_type} named {name}."),
            karma=profile_data.get("karma", random.randint(500, 5000)),
            friend_count=profile_data.get("friend_count", random.randint(50, 500)),
            follower_count=profile_data.get("follower_count", random.randint(100, 1000)),
            statuses_count=profile_data.get("statuses_count", random.randint(100, 2000)),
            age=profile_data.get("age"),
            gender=profile_data.get("gender"),
            mbti=profile_data.get("mbti"),
            country=profile_data.get("country"),
            profession=profile_data.get("profession"),
            interested_topics=profile_data.get("interested_topics", []),
            source_entity_uuid=entity.uuid,
            source_entity_type=entity_type,
        )

    # Semaphore cap: max simultaneous LLM+Zep calls regardless of total persona count.
    # Tune via the max_concurrent parameter; default of 25 safely fits DeepSeek's
    # standard rate limits while still being ~5x faster than the old thread pool.
    DEFAULT_MAX_CONCURRENT = 25

    def generate_profiles_from_entities(
        self,
        entities: List[EntityNode],
        use_llm: bool = True,
        progress_callback: Optional[callable] = None,
        graph_id: Optional[str] = None,
        parallel_count: int = 5,
        realtime_output_path: Optional[str] = None,
        output_platform: str = "reddit",
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
    ) -> List[OasisAgentProfile]:
        """Generate OASIS Agent Profiles with bounded async concurrency.

        Uses asyncio.gather with a semaphore so at most `max_concurrent` LLM
        calls are in-flight at once. Safe for any number of personas — scales
        from 5 to 5000 without rate-limit explosions.

        Args:
            entities: entity nodes to generate profiles for
            use_llm: if False, falls back to rule-based generation
            progress_callback: called as (current, total, message) after each profile
            graph_id: Zep graph ID override
            parallel_count: legacy parameter (kept for API compatibility, ignored)
            realtime_output_path: path to write partial results after each completion
            output_platform: "reddit" (JSON) or "twitter" (CSV)
            max_concurrent: max simultaneous LLM calls (default 25)

        Returns:
            list of OasisAgentProfile in entity order
        """
        from threading import Lock

        if graph_id:
            self.graph_id = graph_id

        total = len(entities)
        profiles: List[Optional[OasisAgentProfile]] = [None] * total
        completed_count = [0]
        lock = Lock()
        current_locale = get_locale()

        def save_profiles_realtime():
            if not realtime_output_path:
                return
            with lock:
                existing = [p for p in profiles if p is not None]
                if not existing:
                    return
                try:
                    if output_platform == "reddit":
                        data = [p.to_reddit_format() for p in existing]
                        with open(realtime_output_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                    else:
                        import csv
                        data = [p.to_twitter_format() for p in existing]
                        if data:
                            fieldnames = list(data[0].keys())
                            with open(realtime_output_path, 'w', encoding='utf-8', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                                writer.writerows(data)
                except Exception as e:
                    logger.warning(f"Realtime profile save failed: {e}")

        async def generate_one(sem: asyncio.Semaphore, idx: int, entity: EntityNode):
            async with sem:  # blocks until a slot is free
                set_locale(current_locale)
                entity_type = entity.get_entity_type() or "Entity"
                try:
                    profile = await self._generate_profile_from_entity_async(
                        entity=entity, user_id=idx, use_llm=use_llm
                    )
                    self._print_generated_profile(entity.name, entity_type, profile)
                except Exception as e:
                    logger.error(f"Profile generation failed for {entity.name}: {e}")
                    profile = OasisAgentProfile(
                        user_id=idx,
                        user_name=self._generate_username(entity.name),
                        name=entity.name,
                        bio=f"{entity_type}: {entity.name}",
                        persona=entity.summary or "A participant in social discussions.",
                        source_entity_uuid=entity.uuid,
                        source_entity_type=entity_type,
                    )

            profiles[idx] = profile
            with lock:
                completed_count[0] += 1
                current = completed_count[0]

            save_profiles_realtime()

            if progress_callback:
                progress_callback(
                    current,
                    total,
                    f"Generated {current}/{total}: {entity.name} ({entity_type})"
                )
            logger.info(f"[{current}/{total}] Done: {entity.name} ({entity_type})")

        async def run_all():
            sem = asyncio.Semaphore(max_concurrent)
            await asyncio.gather(*(generate_one(sem, i, e) for i, e in enumerate(entities)))

        logger.info(
            f"Starting async generation for {total} agents "
            f"(max {max_concurrent} concurrent)..."
        )
        print(f"\n{'='*60}")
        print(f"Async Agent Generation — {total} profiles, {max_concurrent} concurrent slots")
        print(f"{'='*60}\n")

        asyncio.run(run_all())

        print(f"\n{'='*60}")
        print(f"Generated {len([p for p in profiles if p])} agent profiles")
        print(f"{'='*60}\n")

        return profiles
    
    def _print_generated_profile(self, entity_name: str, entity_type: str, profile: OasisAgentProfile):
        """..."""
        separator = "-" * 70
        
        topics_str = ', '.join(profile.interested_topics) if profile.interested_topics else ''
        
        output_lines = [
            f"\n{separator}",
            t('progress.profileGenerated', name=entity_name, type=entity_type),
            f"{separator}",
            f": {profile.user_name}",
            f"",
            f"",
            f"{profile.bio}",
            f"",
            f"",
            f"{profile.persona}",
            f"",
            f"",
            f": {profile.age} | : {profile.gender} | MBTI: {profile.mbti}",
            f": {profile.profession} | : {profile.country}",
            f": {topics_str}",
            separator
        ]
        
        output = "\n".join(output_lines)
        
        # logger
        print(output)
    
    def save_profiles(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """        Profile
        
        OASIS
        - Twitter: CSV
        - Reddit: JSON
        
        Args:
            profiles: Profile
            file_path: 
            platform:  ("reddit"  "twitter")"""
        if platform == "twitter":
            self._save_twitter_csv(profiles, file_path)
        else:
            self._save_reddit_json(profiles, file_path)
    
    def _save_twitter_csv(self, profiles: List[OasisAgentProfile], file_path: str):
        """        Twitter ProfileCSVOASIS
        
        OASIS TwitterCSV
        - user_id: IDCSV0
        - name: 
        - username: 
        - user_char: LLMAgent
        - description: 
        
        user_char vs description 
        - user_char: LLMAgent
        - description: """
        import csv
        
        # .csv
        if not file_path.endswith('.csv'):
            file_path = file_path.replace('.json', '.csv')
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # OASIS
            headers = ['user_id', 'name', 'username', 'user_char', 'description']
            writer.writerow(headers)
            
            for idx, profile in enumerate(profiles):
                # user_char: bio + personaLLM
                user_char = profile.bio
                if profile.persona and profile.persona != profile.bio:
                    user_char = f"{profile.bio} {profile.persona}"
                # CSV
                user_char = user_char.replace('\n', ' ').replace('\r', ' ')
                
                # description:
                description = profile.bio.replace('\n', ' ').replace('\r', ' ')
                
                row = [
                    idx,  # user_id: 0ID
                    profile.name,  # name:
                    profile.user_name,  # username:
                    user_char,  # user_char: LLM
                    description  # description:
                ]
                writer.writerow(row)
        
        logger.info(f" {len(profiles)} Twitter Profile {file_path} (OASIS CSV)")
    
    def _normalize_gender(self, gender: Optional[str]) -> str:
        """        genderOASIS
        
        OASIS: male, female, other"""
        if not gender:
            return "other"
        
        gender_lower = gender.lower().strip()
        
        gender_map = {
            "": "male",
            "": "female",
            "": "other",
            "": "other",
            "male": "male",
            "female": "female",
            "other": "other",
        }
        
        return gender_map.get(gender_lower, "other")
    
    def _save_reddit_json(self, profiles: List[OasisAgentProfile], file_path: str):
        """        Reddit ProfileJSON
        
         to_reddit_format()  OASIS 
         user_id  OASIS agent_graph.get_agent() 
        
        - user_id: ID initial_posts  poster_agent_id
        - username: 
        - name: 
        - bio: 
        - persona: 
        - age: 
        - gender: "male", "female",  "other"
        - mbti: MBTI
        - country: """
        data = []
        for idx, profile in enumerate(profiles):
            #  to_reddit_format()
            item = {
                "user_id": profile.user_id if profile.user_id is not None else idx,  #  user_id
                "username": profile.user_name,
                "name": profile.name,
                "bio": profile.bio[:150] if profile.bio else f"{profile.name}",
                "persona": profile.persona or f"{profile.name} is a participant in social discussions.",
                "karma": profile.karma if profile.karma else 1000,
                "created_at": profile.created_at,
                # OASIS -
                "age": profile.age if profile.age else 30,
                "gender": self._normalize_gender(profile.gender),
                "mbti": profile.mbti if profile.mbti else "ISTJ",
                "country": profile.country if profile.country else "",
            }
            
            if profile.profession:
                item["profession"] = profile.profession
            if profile.interested_topics:
                item["interested_topics"] = profile.interested_topics
            
            data.append(item)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f" {len(profiles)} Reddit Profile {file_path} (JSONuser_id)")
    
    def save_profiles_to_json(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """[]  save_profiles() """
        logger.warning("save_profiles_to_jsonsave_profiles")
        self.save_profiles(profiles, file_path, platform)

    def assign_segments(
        self,
        profiles: List["OasisAgentProfile"],
        segment_definitions: List[Dict[str, Any]],
    ) -> Dict[str, List["OasisAgentProfile"]]:
        """
        Assign persona profiles to named segments using LLM classification.

        Sends all profiles in a single batched prompt so the LLM classifies
        each persona against the defined segments at once, avoiding N separate
        API calls.

        Args:
            profiles: generated persona profiles (individual personas only)
            segment_definitions: list of {"name": "...", "description": "..."}
                e.g. [
                    {"name": "MillennialProfessionals", "description": "Age 28-38, urban, high income"},
                    {"name": "GenZConsumers", "description": "Age 18-26, digital natives"},
                ]

        Returns:
            dict mapping segment_name -> list of matching OasisAgentProfile objects.
            Unmatched profiles go to "Unassigned".
        """
        if not segment_definitions:
            return {"Unassigned": list(profiles)}

        segments: Dict[str, List] = {s["name"]: [] for s in segment_definitions}
        segments["Unassigned"] = []
        valid_names = set(segments.keys())

        BATCH_SIZE = 20
        for batch_start in range(0, len(profiles), BATCH_SIZE):
            batch = profiles[batch_start: batch_start + BATCH_SIZE]

            profiles_text = "\n".join(
                f"{i + 1}. {p.name} | Age: {p.age} | Profession: {p.profession} | "
                f"Bio: {p.bio[:120]} | Topics: {p.interested_topics[:80]}"
                for i, p in enumerate(batch)
            )
            segments_text = "\n".join(
                f"- {s['name']}: {s['description']}" for s in segment_definitions
            )

            prompt = (
                "You are a marketing segmentation assistant.\n\n"
                "Assign each persona below to the best-matching segment. "
                "Reply with ONLY a JSON array of objects, one per persona, "
                "in the same order. Each object must have exactly two keys: "
                '"index" (1-based integer) and "segment" (exact segment name or "Unassigned").\n\n'
                f"Segments:\n{segments_text}\n\n"
                f"Personas:\n{profiles_text}\n\n"
                'Reply with ONLY the JSON array, no commentary.'
            )

            try:
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=len(batch) * 30 + 50,
                )
                raw = resp.choices[0].message.content.strip()
                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                assignments = json.loads(raw)
                for item in assignments:
                    idx = int(item.get("index", 0)) - 1
                    seg_name = item.get("segment", "Unassigned")
                    if 0 <= idx < len(batch):
                        target = seg_name if seg_name in valid_names else "Unassigned"
                        segments[target].append(batch[idx])
            except Exception as e:
                logger.warning(f"Segment assignment batch failed: {e} — assigning batch to Unassigned")
                segments["Unassigned"].extend(batch)

        return segments

