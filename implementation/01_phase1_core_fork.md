# Phase 1 — Core Domain Adaptation ✅ COMPLETE

## Goal

Produce a running copy of CampaignSim where every domain-specific prompt, label, and UI string has been replaced with marketing equivalents, and the knowledge graph correctly extracts a marketing ontology (Brand, Persona, Channel, ContentType, Campaign, Competitor) from a real campaign brief.

**Status: COMPLETE.** The platform builds a Zep knowledge graph from a brand brief with a marketing ontology. All Chinese text removed. CampaignSim branding throughout.

The steps below document what was implemented (for thesis reference).

---

## Step 1 — Project Setup (Done)

```bash
# Project is already set up at:
# /Users/abedmreyan/Desktop/Graduation Project 2/campaignsim

cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim"
```

Remove the git history so you start clean:

```bash
rm -rf .git
git init
git add .
git commit -m "initial: CampaignSim project"
```

---

## Step 2 — Replace the Ontology Generator System Prompt

**File:** `backend/app/services/ontology_generator.py`  
**Change:** Replace `ONTOLOGY_SYSTEM_PROMPT` (line 30–173) with the marketing version below.  
**Why:** The original prompt is hard-coded around Chinese social-opinion simulation. Your system needs to extract marketing-domain entities instead.

```python
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

## Design Rules

### Entity Types — exactly 10 required

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

**Attribute naming rules (Zep reserved words — never use these as attribute names):**
`name`, `uuid`, `group_id`, `created_at`, `summary`

Use instead: `brand_name`, `full_name`, `channel_name`, `format_type`, `campaign_goal`, etc.

### Edge Types — 6 to 10 required

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
"""
```

**Also update `_build_user_message`** (line 248–274) to replace Chinese instructions with English:

```python
message += """
Please analyze the above content and design entity types and relation types suited
for marketing campaign simulation.

Rules:
1. Output exactly 10 entity types
2. Last 2 must be fallbacks: Brand and Person
3. First 8 are specific types derived from the documents
4. All entity types must be real-world actors, not abstract metrics or concepts
5. Attribute names must not use reserved words: name, uuid, group_id, created_at, summary
"""
```

---

## Step 2b — Fix `_validate_and_process` Fallback Types

**File:** `backend/app/services/ontology_generator.py`  
**Lines:** ~344–375  
**Why this matters:** The `_validate_and_process` method enforces two mandatory fallback entity types. The original code hardcodes `Organization` as the second fallback. But your new ontology prompt specifies `Brand` as the fallback — not `Organization`. If you do not fix this, the validator will silently inject an `Organization` node into every graph even though your prompt never produces one, and will never add the `Brand` fallback node that persona generation depends on.

Replace the fallback definitions block (lines 344–375):

**Before:**
```python
        # 兜底类型定义
        person_fallback = {
            "name": "Person",
            "description": "Any individual person not fitting other specific person types.",
            "attributes": [
                {"name": "full_name", "type": "text", "description": "Full name of the person"},
                {"name": "role", "type": "text", "description": "Role or occupation"}
            ],
            "examples": ["ordinary citizen", "anonymous netizen"]
        }
        
        organization_fallback = {
            "name": "Organization",
            "description": "Any organization not fitting other specific organization types.",
            "attributes": [
                {"name": "org_name", "type": "text", "description": "Name of the organization"},
                {"name": "org_type", "type": "text", "description": "Type of organization"}
            ],
            "examples": ["small business", "community group"]
        }
        
        # 检查是否已有兜底类型
        entity_names = {e["name"] for e in result["entity_types"]}
        has_person = "Person" in entity_names
        has_organization = "Organization" in entity_names
        
        # 需要添加的兜底类型
        fallbacks_to_add = []
        if not has_person:
            fallbacks_to_add.append(person_fallback)
        if not has_organization:
            fallbacks_to_add.append(organization_fallback)
```

**After:**
```python
        # Fallback entity type definitions
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
```

The rest of the method (slot trimming and final cap logic) does not change.

---

## Step 3 — Replace the Profile Generator (Customer Personas)

**File:** `backend/app/services/oasis_profile_generator.py`

### 3a. Replace entity type classification lists (lines 169–179)

The original lists classify Chinese social-media entity types. Replace with marketing equivalents:

```python
# Entity types that map to individual customer personas
INDIVIDUAL_ENTITY_TYPES = [
    "customerpersona", "person", "influencer", "consumer", "buyer", "user"
]

# Entity types that map to institutional / brand accounts
GROUP_ENTITY_TYPES = [
    "brand", "competitor", "marketingchannel", "organization",
    "mediaoutlet", "retailer", "agency", "market"
]
```

### 3b. Replace `_build_individual_persona_prompt` (line 677)

This prompt generates each customer persona agent. Replace with:

```python
def _build_individual_persona_prompt(
    self,
    entity_name: str,
    entity_type: str,
    entity_summary: str,
    entity_attributes: dict,
    context: str
) -> str:
    attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "none"
    context_str = context[:3000] if context else "No additional context"

    return f"""Generate a detailed customer persona profile for use in a marketing campaign simulation.

Entity name: {entity_name}
Entity type: {entity_type}
Entity summary: {entity_summary}
Entity attributes: {attrs_str}

Context from brand knowledge graph:
{context_str}

Return JSON with these fields:

1. bio: 200-character social media bio that this persona would write about themselves
2. persona: Detailed 1500-word profile (plain text, no newlines) covering:
   - Demographics (age, gender, location, income bracket, education level)
   - Psychographics (values, lifestyle, motivations, pain points)
   - Buying behaviour (decision process, research habits, brand loyalty, price sensitivity)
   - Channel behaviour (which platforms they use, how often, what content they engage with)
   - Content preferences (video vs text vs image, long-form vs short, UGC vs branded)
   - Response to advertising (ad-skipping habits, preferred ad formats, trusted voices)
   - Relationship to the brand/product being marketed (aware, considers, loyal, lapsed)
   - Memory (what this persona has already seen or done related to this campaign)
3. age: integer
4. gender: "male" or "female"
5. mbti: MBTI type string (e.g. ENFP)
6. country: country name in English
7. profession: job title or occupation
8. interested_topics: array of topics this persona cares about

Rules:
- All field values must be strings or numbers — no null, no embedded newlines
- persona must be a single continuous paragraph
- Keep consistent with the entity attributes and context provided
"""
```

### 3c. Replace `_build_group_persona_prompt` (line 727)

```python
def _build_group_persona_prompt(
    self,
    entity_name: str,
    entity_type: str,
    entity_summary: str,
    entity_attributes: dict,
    context: str
) -> str:
    attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "none"
    context_str = context[:3000] if context else "No additional context"

    return f"""Generate a detailed brand/channel account profile for use in a marketing simulation.

Entity name: {entity_name}
Entity type: {entity_type}
Entity summary: {entity_summary}
Entity attributes: {attrs_str}

Context:
{context_str}

Return JSON with these fields:

1. bio: 200-character official account bio
2. persona: Detailed 1500-word account profile (plain text, no newlines) covering:
   - Organisation overview (what they do, market position, brand voice)
   - Account purpose (what this account publishes, target audience for its content)
   - Content style (tone of voice, message pillars, visual identity cues)
   - Posting behaviour (frequency, timing, content mix)
   - Stance on campaign-relevant topics (how they respond to competitor moves, crises, trends)
   - Memory (what this brand/channel has already done in relation to this campaign)
3. age: use 0 (not applicable for institutions)
4. gender: "other"
5. mbti: MBTI describing the brand personality (e.g. ESTJ for authoritative brands)
6. country: country name in English
7. profession: describe the organisation's function (e.g. "Social Media Channel", "FMCG Brand")
8. interested_topics: array of topics this account posts about

Rules:
- All values must be strings or numbers — no null, no embedded newlines
- persona must be a single continuous paragraph
- age must be integer 0, gender must be string "other"
"""
```

### 3d. Fix `_generate_profile_rule_based` (line 774)

Replace the Chinese-specific fallback cases with marketing equivalents:

```python
def _generate_profile_rule_based(
    self,
    entity_name: str,
    entity_type: str,
    entity_summary: str,
    entity_attributes: dict,
) -> dict:
    et = entity_type.lower()

    if et in ["customerpersona", "person", "consumer", "buyer"]:
        return {
            "bio": f"Consumer interested in products like {entity_name}.",
            "persona": f"{entity_name} is a consumer who researches products carefully before buying, is active on social media, and responds well to authentic content.",
            "age": random.randint(22, 45),
            "gender": random.choice(["male", "female"]),
            "mbti": random.choice(self.MBTI_TYPES),
            "country": "US",
            "profession": "Professional",
            "interested_topics": ["Shopping", "Lifestyle", "Technology"],
        }
    elif et in ["influencer"]:
        return {
            "bio": f"Content creator and opinion leader. Partnering with brands I believe in.",
            "persona": f"{entity_name} is a content creator with an engaged following. They are selective about brand partnerships and prioritise authenticity.",
            "age": random.randint(22, 35),
            "gender": random.choice(["male", "female"]),
            "mbti": random.choice(["ENFP", "ESFP", "ENFJ"]),
            "country": "US",
            "profession": "Content Creator",
            "interested_topics": ["Content Creation", "Brand Partnerships", "Lifestyle"],
        }
    elif et in ["brand", "competitor", "organization"]:
        return {
            "bio": f"Official account of {entity_name}.",
            "persona": f"{entity_name} is a brand account that shares product news, engages with customers, and communicates brand values.",
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
            "persona": f"This is the {entity_name} channel representation. It reflects the norms and audience behaviour typical of this platform.",
            "age": 0,
            "gender": "other",
            "mbti": "ISTP",
            "country": "US",
            "profession": "Marketing Channel",
            "interested_topics": ["Digital Marketing", "Content", "Advertising"],
        }
    else:
        return {
            "bio": entity_summary[:150] if entity_summary else f"{entity_type}: {entity_name}",
            "persona": entity_summary or f"{entity_name} is a {entity_type} participating in the campaign simulation.",
            "age": random.randint(25, 50),
            "gender": random.choice(["male", "female"]),
            "mbti": random.choice(self.MBTI_TYPES),
            "country": "US",
            "profession": entity_type,
            "interested_topics": ["Marketing", "Business"],
        }
```

---

## Step 4 — Update Config Constants

**File:** `backend/app/config.py`

Add the following below the existing OASIS action sets (after line 59).

**Important:** OASIS only supports a fixed set of action types defined by the `ActionType` enum in the library. The keys in `CAMPAIGN_ACTION_WEIGHTS` must match the string values of those enum members exactly, because the simulation stores them in SQLite as enum value strings. Do not invent custom action names — they will never appear in simulation output.

Real OASIS action types (from `ActionType` enum):
- `CREATE_POST` — agent posts a comment/response to the campaign content
- `LIKE_POST` — agent likes the campaign post (positive signal)
- `REPOST` — agent shares/retweets the campaign post (strong virality signal)
- `QUOTE_POST` — agent shares with added commentary
- `FOLLOW` — agent follows the brand account
- `DO_NOTHING` — agent scrolls past / ignores

```python
# OASIS simulation actions available to customer persona agents
# These must be ActionType enum members — do NOT add custom strings
CAMPAIGN_AVAILABLE_ACTIONS = [
    'CREATE_POST',    # comment on or reply to campaign content
    'LIKE_POST',      # like / positive engagement
    'REPOST',         # share to own followers
    'QUOTE_POST',     # share with commentary
    'FOLLOW',         # follow the brand account
    'DO_NOTHING',     # ignore / scroll past
]

# Engagement scoring weights — keyed on OASIS ActionType string values
# Used by VariantScorer in Phase 4 to compute a weighted engagement rate
CAMPAIGN_ACTION_WEIGHTS = {
    'DO_NOTHING':   0.0,
    'LIKE_POST':    0.3,    # positive but lightweight signal
    'CREATE_POST':  0.35,   # comment / reply — shows active interest
    'FOLLOW':       0.45,   # follow brand — strong intent signal
    'QUOTE_POST':   0.5,    # share with commentary — social amplification
    'REPOST':       0.55,   # pure share — strongest virality signal
}
```

These weights are used in Phase 4's `VariantScorer`. The channel (Instagram vs Email context) is encoded in the campaign content prompt given to agents, not in the action types themselves — OASIS provides one social simulation layer that we contextualise through the agent personas and the initial post content.

---

## Step 5 — Replace English Locale Strings

**File:** `locales/en.json`

Find any strings that mention "opinion simulation", "social media simulation", "public sentiment", etc. and replace with marketing equivalents.

Key strings to find and replace:

| Original (Chinese context) | Replacement (Marketing) |
|---|---|
| "Build Knowledge Graph from documents" | "Build Market Knowledge Graph from brand documents" |
| "Generate Ontology" | "Extract Marketing Entities" |
| "Simulation Requirement" | "Campaign Goal" |
| "Agent Profiles" | "Customer Personas" |
| "Simulation Rounds" | "Campaign Simulation Rounds" |
| "Generate Report" | "Generate Campaign Recommendations" |
| "Interview Agents" | "Interview Personas" |

---

## Step 6 — Rename UI Workflow Steps

**Files:** `frontend/src/components/Step1GraphBuild.vue` through `Step5Interaction.vue`

The step titles are driven by locale strings. Update `locales/en.json` step labels:

```json
"steps": {
    "step1": "1. Upload & Extract Market Entities",
    "step2": "2. Build Market Knowledge Graph",
    "step3": "3. Generate Customer Personas",
    "step4": "4. Simulate Campaign",
    "step5": "5. Recommendations & Insights"
}
```

---

## Step 7 — Verify End-to-End

Use this sample campaign brief as a test input (save as `test_brief.txt`):

```
Brand: FreshBrew Coffee
Product: Cold Brew Concentrate (new launch)
Target Market: Urban professionals aged 25–40, health-conscious, premium spenders
Key Message: Premium quality, zero sugar, ready in seconds
Campaign Goal: Drive trial purchase among new customers
Channels to test: Instagram, Email marketing
Competitors: Starbucks RTD, La Colombe Draft Latte, Minor Figures
Brand Voice: Clean, confident, modern
Budget: $50,000
```

Expected outputs after completing Phase 1:
- Ontology with entities: `Product`, `CustomerPersona`, `MarketingChannel`, `Competitor`, `Campaign`, `ContentFormat`, `Brand`, `Person` (plus 2 fallbacks)
- Zep knowledge graph nodes for: FreshBrew Coffee, Cold Brew Concentrate, Urban Professionals, Instagram, Email, Starbucks, La Colombe, Minor Figures
- 8–12 customer persona profiles generated from the graph entities
- All UI text in English marketing terminology

---

## Checklist

- [ ] CampaignSim copied and git-initialized in working directory
- [ ] `ONTOLOGY_SYSTEM_PROMPT` replaced with marketing version
- [ ] `_build_user_message` instructions updated to English
- [ ] `_validate_and_process` fallback changed from `Organization` → `Brand` (Step 2b)
- [ ] `INDIVIDUAL_ENTITY_TYPES` and `GROUP_ENTITY_TYPES` updated
- [ ] `_build_individual_persona_prompt` replaced with customer persona version
- [ ] `_build_group_persona_prompt` replaced with brand account version
- [ ] `_generate_profile_rule_based` updated for marketing entity types
- [ ] `CAMPAIGN_AVAILABLE_ACTIONS` and `CAMPAIGN_ACTION_WEIGHTS` added to `config.py`
- [ ] `locales/en.json` strings updated to marketing terminology
- [ ] Step labels in Vue components updated
- [ ] End-to-end test with sample brief passes
