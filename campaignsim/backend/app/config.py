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
    
    # Knowledge graph backend: 'local' (SQLite, default) or 'zep' (Zep Cloud)
    KG_BACKEND = os.environ.get('KG_BACKEND', 'local')
    KG_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/knowledge_graphs')

    # Zep Cloud — only required when KG_BACKEND='zep'
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY', '')

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
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

    # CampaignSim: OASIS actions available to customer persona agents
    # Keys are real ActionType enum string values — do NOT invent custom strings
    CAMPAIGN_AVAILABLE_ACTIONS = [
        'CREATE_POST',    # comment on / reply to campaign content
        'LIKE_POST',      # positive engagement (like / heart)
        'REPOST',         # share campaign content to own followers
        'QUOTE_POST',     # share with added commentary
        'FOLLOW',         # follow the brand account
        'DO_NOTHING',     # ignore / scroll past
    ]

    # Engagement scoring weights — keyed on real OASIS ActionType string values
    # Used by VariantScorer (Phase 4) to compute weighted engagement rate per variant
    CAMPAIGN_ACTION_WEIGHTS = {
        'DO_NOTHING':   0.0,
        'LIKE_POST':    0.3,    # positive but lightweight signal
        'CREATE_POST':  0.35,   # comment / reply — shows active interest
        'FOLLOW':       0.45,   # follow brand — strong purchase-intent signal
        'QUOTE_POST':   0.5,    # share with commentary — social amplification
        'REPOST':       0.55,   # pure share — strongest virality signal
    }

    # Report Agent config
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    
    @classmethod
    def validate(cls):
        """..."""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY not configured")
        if cls.KG_BACKEND == 'zep' and not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY not configured (required when KG_BACKEND=zep)")
        return errors

