"""Configuration management
Loads configuration from the project root .env file"""

import os
from dotenv import load_dotenv

#  .env
# : CampaignSim/.env ( backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    #  .env
    load_dotenv(override=True)

class Config:
    """Flask"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'campaignsim-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # JSON - ASCII \uXXXX
    JSON_AS_ASCII = False
    
    # LLMOpenAI
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Platform database (Postgres) — identity, briefs, personas, campaign metadata
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://cs_user:cs_dev_password@localhost:5432/campaignsim'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Auth / JWT
    JWT_SECRET = os.environ.get('JWT_SECRET', 'campaignsim-dev-jwt-secret-change-me')
    JWT_ACCESS_TTL_MINUTES = int(os.environ.get('JWT_ACCESS_TTL_MINUTES', '15'))
    JWT_REFRESH_TTL_DAYS = int(os.environ.get('JWT_REFRESH_TTL_DAYS', '30'))
    # Local dev runs plain HTTP → SameSite=Lax without Secure; production
    # (FLASK_ENV=production, HTTPS via tunnel) → SameSite=None + Secure.
    AUTH_COOKIE_SECURE = os.environ.get('FLASK_ENV', 'development') == 'production'
    AUTH_COOKIE_SAMESITE = 'None' if AUTH_COOKIE_SECURE else 'Lax'
    CORS_ORIGINS = [
        o.strip() for o in os.environ.get(
            'CORS_ORIGINS',
            'http://localhost:3006,http://localhost:5173'
        ).split(',') if o.strip()
    ]

    # Knowledge graph backend: 'local' (SQLite, default) or 'zep' (Zep Cloud)
    KG_BACKEND = os.environ.get('KG_BACKEND', 'local')
    KG_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/knowledge_graphs')

    # Zep Cloud — only required when KG_BACKEND='zep'
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY', '')

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    # Phase 4 — customer dataset intake (CSV/XLSX only)
    DATASET_ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50
    
    # OASIS
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS platform action configs (original — kept for compatibility)
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Legacy fallback engagement weights, used by VariantScorer only when a
    # variant's simulation_config.json has no channel_def block (i.e. it ran
    # before the Phase 1 channel registry existed). New variants get their
    # weights from the channel registry (app/data/builtin_channels.json).
    #
    # Keys are real OASIS ActionType.value strings (lowercase snake_case) —
    # actions.jsonl's action_type field is always this exact lowercase format
    # (it's copied verbatim from the OASIS trace table). Do NOT use uppercase
    # keys here — VariantScorer's weights.get(action_type, 0.0) lookup is
    # case-sensitive and silently scores every action 0.0 on a mismatch.
    CAMPAIGN_ACTION_WEIGHTS = {
        'do_nothing':  0.0,
        'like_post':   0.3,     # positive but lightweight signal
        'create_post': 0.35,    # comment / reply — shows active interest
        'follow':      0.45,    # follow brand — strong purchase-intent signal
        'quote_post':  0.5,     # share with commentary — social amplification
        'repost':      0.55,    # pure share — strongest virality signal
    }

    # Report Agent config
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    # Designer Agent config (Phase 2 — pre-simulation campaign co-design)
    DESIGNER_AGENT_MAX_TOOL_CALLS = int(os.environ.get('DESIGNER_AGENT_MAX_TOOL_CALLS', '8'))
    DESIGNER_AGENT_TEMPERATURE = float(os.environ.get('DESIGNER_AGENT_TEMPERATURE', '0.6'))
    DESIGNER_AGENT_MAX_VARIANTS = int(os.environ.get('DESIGNER_AGENT_MAX_VARIANTS', '6'))

    # Insight Agent config (Phase 3 — post-simulation analysis + redesign)
    INSIGHT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('INSIGHT_AGENT_MAX_TOOL_CALLS', '8'))
    INSIGHT_AGENT_TEMPERATURE = float(os.environ.get('INSIGHT_AGENT_TEMPERATURE', '0.6'))
    INSIGHT_AGENT_MAX_INTERVIEWS = int(os.environ.get('INSIGHT_AGENT_MAX_INTERVIEWS', '5'))
    
    @classmethod
    def validate(cls):
        """..."""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY not configured")
        if cls.KG_BACKEND == 'zep' and not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY not configured (required when KG_BACKEND=zep)")
        return errors

