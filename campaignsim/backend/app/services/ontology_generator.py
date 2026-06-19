"""Ontology generation service
API 1: Analyze text content and generate entity/relationship type definitions for simulation"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction

logger = logging.getLogger(__name__)

def _to_pascal_case(name: str) -> str:
    """Convert any format name to PascalCase 'works_for' -> 'WorksFor', 'person' -> 'Person'"""
    parts = re.split(r'[^a-zA-Z0-9]+', name)
    #  camelCase  'camelCase' -> ['camel', 'Case']
    words = []
    for part in parts:
        words.extend(re.sub(r'([a-z])([A-Z])', r'\1_\2', part).split('_'))
    result = ''.join(word.capitalize() for word in words if word)
    return result if result else 'Unknown'

# Marketing ontology system prompt for CampaignSim
ONTOLOGY_SYSTEM_PROMPT = """You are a marketing knowledge graph expert. Your task is to
analyze the uploaded campaign brief and brand research documents and design an ontology
suited for **marketing campaign simulation**.

**IMPORTANT: Output only valid JSON. No other text.**

## Context

We are building a marketing simulation system. In this system:
- Each entity is a real-world participant that influences or is influenced by a campaign
- Entities interact: consumers react to content, competitors respond, channels carry messages
- We need to simulate how different audience segments respond to different campaign variants

## Allowed Entity Categories

**Must be concrete, real-world actors or objects — not abstract concepts.**

Allowed:
- A brand or product (the advertiser's brand, competitor brands)
- A customer persona / audience segment
- A marketing channel (Instagram, Email, TikTok, LinkedIn, Google Ads, TV, etc.)
- A content format (VideoAd, CarouselPost, EmailNewsletter, SearchAd, InfluencerPost)
- A campaign or promotion
- A competitor
- An influencer or creator
- A market / geography

NOT allowed:
- Abstract concepts (e.g. "brand awareness", "engagement", "sentiment")
- Metrics (e.g. "CTR", "ROI")
- Lifecycle stages (e.g. "awareness stage")

## Output Format

```json
{
    "entity_types": [
        {
            "name": "EntityTypeName (PascalCase, English)",
            "description": "Short description under 100 characters",
            "attributes": [
                {
                    "name": "attribute_name (snake_case, English)",
                    "type": "text",
                    "description": "What this attribute captures"
                }
            ],
            "examples": ["Example entity 1", "Example entity 2"]
        }
    ],
    "edge_types": [
        {
            "name": "RELATION_NAME (UPPER_SNAKE_CASE, English)",
            "description": "Short description under 100 characters",
            "source_targets": [
                {"source": "SourceEntityType", "target": "TargetEntityType"}
            ],
            "attributes": []
        }
    ],
    "analysis_summary": "Brief summary of what was found in the documents"
}
```

## Design Rules (Critical)

### 1. Entity Types — exactly 10 required

**Last 2 must always be these fallbacks:**
- `Brand`: Any brand or company not fitting a more specific type
- `Person`: Any individual not fitting a more specific type

**First 8: domain-specific types derived from the uploaded documents.**
Suggested starting set (adapt based on what the documents contain):
- `CustomerPersona`: A defined audience segment with demographics and psychographics
- `MarketingChannel`: A specific distribution channel (Instagram, Email, etc.)
- `ContentFormat`: A content type (VideoAd, CarouselPost, SearchAd, etc.)
- `Campaign`: A marketing campaign or promotion
- `Competitor`: A competing brand or product
- `Product`: A specific product or service being marketed
- `Influencer`: A creator or KOL used in campaigns
- `Market`: A geographic market or industry vertical

### 2. Edge Types — 6 to 10 required

Suggested marketing relations:
- TARGETS: Campaign → CustomerPersona
- DISTRIBUTED_ON: Campaign → MarketingChannel
- USES_FORMAT: Campaign → ContentFormat
- COMPETES_WITH: Brand → Brand (or Competitor)
- INFLUENCES: Influencer → CustomerPersona
- RESPONDS_TO: CustomerPersona → ContentFormat
- ACTIVE_ON: CustomerPersona → MarketingChannel
- PROMOTED_BY: Product → Campaign
- BENCHMARKED_AGAINST: Brand → Competitor

### 3. Attribute Design Rules

- 1–3 key attributes per entity type
- **NEVER use these reserved Zep attribute names:** `name`, `uuid`, `group_id`, `created_at`, `summary`
- Use instead: `brand_name`, `channel_name`, `format_type`, `campaign_goal`, `segment_description`, etc.
"""

class OntologyGenerator:
    """..."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
    
    def generate(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """        Args:
            document_texts: Document
            simulation_requirement: 
            additional_context: 
            
        Returns:
            entity_types, edge_types"""
        user_message = self._build_user_message(
            document_texts, 
            simulation_requirement,
            additional_context
        )
        
        lang_instruction = get_language_instruction()
        system_prompt = f"{ONTOLOGY_SYSTEM_PROMPT}\n\n{lang_instruction}\nIMPORTANT: Entity type names MUST be in English PascalCase (e.g., 'PersonEntity', 'MediaOrganization'). Relationship type names MUST be in English UPPER_SNAKE_CASE (e.g., 'WORKS_FOR'). Attribute names MUST be in English snake_case. Only description fields and analysis_summary should use the specified language above."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # LLM
        result = self.llm_client.chat_json(
            messages=messages,
            temperature=0.3,
            max_tokens=4096
        )
        
        result = self._validate_and_process(result)
        
        return result
    
    #  LLM 5
    MAX_TEXT_LENGTH_FOR_LLM = 50000
    
    def _build_user_message(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str]
    ) -> str:
        """..."""
        
        combined_text = "\n\n---\n\n".join(document_texts)
        original_length = len(combined_text)
        
        # 5LLM
        if len(combined_text) > self.MAX_TEXT_LENGTH_FOR_LLM:
            combined_text = combined_text[:self.MAX_TEXT_LENGTH_FOR_LLM]
            combined_text += f"\n\n...(original {original_length} chars, truncated to {self.MAX_TEXT_LENGTH_FOR_LLM} chars for ontology)..."
        
        message = f"""## Campaign Goal

{simulation_requirement}

## Document Content

{combined_text}
"""

        if additional_context:
            message += f"""
## Additional Context

{additional_context}
"""

        message += """
Please analyze the above content and design entity types and relation types suited
for marketing campaign simulation.

Rules:
1. Output exactly 10 entity types
2. Last 2 must be fallbacks: Brand (brand/company fallback) and Person (individual fallback)
3. First 8 are specific types derived from the documents
4. All entity types must be real-world actors or objects — not abstract metrics or concepts
5. Attribute names must not use reserved words: name, uuid, group_id, created_at, summary
   Use instead: brand_name, channel_name, format_type, campaign_goal, segment_description, etc.
"""
        
        return message
    
    def _validate_and_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """..."""
        
        if "entity_types" not in result:
            result["entity_types"] = []
        if "edge_types" not in result:
            result["edge_types"] = []
        if "analysis_summary" not in result:
            result["analysis_summary"] = ""
        
        #  PascalCase  edge  source_targets
        entity_name_map = {}
        for entity in result["entity_types"]:
            #  entity name  PascalCaseZep API
            if "name" in entity:
                original_name = entity["name"]
                entity["name"] = _to_pascal_case(original_name)
                if entity["name"] != original_name:
                    logger.warning(f"Entity type name '{original_name}' auto-converted to '{entity['name']}'")
                entity_name_map[original_name] = entity["name"]
            if "attributes" not in entity:
                entity["attributes"] = []
            if "examples" not in entity:
                entity["examples"] = []
            # description100
            if len(entity.get("description", "")) > 100:
                entity["description"] = entity["description"][:97] + "..."
        
        for edge in result["edge_types"]:
            #  edge name  SCREAMING_SNAKE_CASEZep API
            if "name" in edge:
                original_name = edge["name"]
                edge["name"] = original_name.upper()
                if edge["name"] != original_name:
                    logger.warning(f"Edge type name '{original_name}' auto-converted to '{edge['name']}'")
            #  source_targets  PascalCase
            for st in edge.get("source_targets", []):
                if st.get("source") in entity_name_map:
                    st["source"] = entity_name_map[st["source"]]
                if st.get("target") in entity_name_map:
                    st["target"] = entity_name_map[st["target"]]
            if "source_targets" not in edge:
                edge["source_targets"] = []
            if "attributes" not in edge:
                edge["attributes"] = []
            if len(edge.get("description", "")) > 100:
                edge["description"] = edge["description"][:97] + "..."
        
        # Zep API  10  10
        MAX_ENTITY_TYPES = 10
        MAX_EDGE_TYPES = 10

        #  name
        seen_names = set()
        deduped = []
        for entity in result["entity_types"]:
            name = entity.get("name", "")
            if name and name not in seen_names:
                seen_names.add(name)
                deduped.append(entity)
            elif name in seen_names:
                logger.warning(f"Duplicate entity type '{name}' removed during validation")
        result["entity_types"] = deduped

        # Fallback entity type definitions (marketing domain)
        person_fallback = {
            "name": "Person",
            "description": "Any individual person not fitting a more specific persona type.",
            "attributes": [
                {"name": "full_name", "type": "text", "description": "Full name of the person"},
                {"name": "role", "type": "text", "description": "Role or occupation"}
            ],
            "examples": ["consumer", "buyer", "individual user"]
        }

        brand_fallback = {
            "name": "Brand",
            "description": "Any brand or company not fitting a more specific entity type.",
            "attributes": [
                {"name": "brand_name", "type": "text", "description": "Name of the brand"},
                {"name": "brand_category", "type": "text", "description": "Industry or product category"}
            ],
            "examples": ["advertiser brand", "competitor brand", "retailer"]
        }

        # Check which fallbacks are already present
        entity_names = {e["name"] for e in result["entity_types"]}
        has_person = "Person" in entity_names
        has_brand = "Brand" in entity_names

        # Build list of fallbacks to inject
        fallbacks_to_add = []
        if not has_person:
            fallbacks_to_add.append(person_fallback)
        if not has_brand:
            fallbacks_to_add.append(brand_fallback)
        
        if fallbacks_to_add:
            current_count = len(result["entity_types"])
            needed_slots = len(fallbacks_to_add)
            
            #  10
            if current_count + needed_slots > MAX_ENTITY_TYPES:
                to_remove = current_count + needed_slots - MAX_ENTITY_TYPES
                result["entity_types"] = result["entity_types"][:-to_remove]
            
            result["entity_types"].extend(fallbacks_to_add)
        
        if len(result["entity_types"]) > MAX_ENTITY_TYPES:
            result["entity_types"] = result["entity_types"][:MAX_ENTITY_TYPES]
        
        if len(result["edge_types"]) > MAX_EDGE_TYPES:
            result["edge_types"] = result["edge_types"][:MAX_EDGE_TYPES]
        
        return result
    
    def generate_python_code(self, ontology: Dict[str, Any]) -> str:
        """
        Convert ontology definition to Python code (Zep EntityModel/EdgeModel classes).

        Args:
            ontology: Ontology definition dict with entity_types and edge_types.

        Returns:
            Python source code string.
        """
        code_lines = [
            '"""',
            'Custom marketing entity type definitions',
            'Auto-generated by CampaignSim for marketing campaign simulation',
            '"""',
            '',
            'from pydantic import Field',
            'from app.services.kg.models import KGNode, KGEdge  # local KG engine',
            '',
            '',
            '# ============== Entity Type Definitions ==============',
            '',
        ]

        # Generate entity types
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            desc = entity.get("description", f"A {name} entity.")
            
            code_lines.append(f'class {name}(EntityModel):')
            code_lines.append(f'    """{desc}"""')
            
            attrs = entity.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')
            
            code_lines.append('')
            code_lines.append('')
        
        code_lines.append('# ============== Relationship Type Definitions ==============')
        code_lines.append('')
        
        # Generate relationship types
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            # Convert to PascalCase class name
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            desc = edge.get("description", f"A {name} relationship.")
            
            code_lines.append(f'class {class_name}(EdgeModel):')
            code_lines.append(f'    """{desc}"""')
            
            attrs = edge.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')
            
            code_lines.append('')
            code_lines.append('')
        
        # Generate type registry
        code_lines.append('# ============== Type Registry ==============')
        code_lines.append('')
        code_lines.append('ENTITY_TYPES = {')
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            code_lines.append(f'    "{name}": {name},')
        code_lines.append('}')
        code_lines.append('')
        code_lines.append('EDGE_TYPES = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            code_lines.append(f'    "{name}": {class_name},')
        code_lines.append('}')
        code_lines.append('')
        
        # source_targets
        code_lines.append('EDGE_SOURCE_TARGETS = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            source_targets = edge.get("source_targets", [])
            if source_targets:
                st_list = ', '.join([
                    f'{{"source": "{st.get("source", "Entity")}", "target": "{st.get("target", "Entity")}"}}'
                    for st in source_targets
                ])
                code_lines.append(f'    "{name}": [{st_list}],')
        code_lines.append('}')
        
        return '\n'.join(code_lines)

