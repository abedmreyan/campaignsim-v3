"""CampaignSim Backend - Flask"""

import os
import warnings

warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .extensions import db, limiter, migrate
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask app factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Flask >= 2.3: app.json.ensure_ascii replaces JSON_AS_ASCII
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    logger = setup_logger('campaignsim')

    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("CampaignSim Backend starting...")
        logger.info("=" * 50)

    # Database / migrations / rate limiting
    db.init_app(app)
    from .models import orm  # noqa: F401 — register models with metadata
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Cookie-based auth across origins requires explicit origins + credentials
    CORS(
        app,
        resources={r"/api/*": {"origins": Config.CORS_ORIGINS}},
        supports_credentials=True,
    )

    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("simulation process cleanup registered")

    # Seed/refresh builtin channel definitions. Safe no-op if the channels
    # table doesn't exist yet (e.g. before the first migration runs).
    with app.app_context():
        try:
            from sqlalchemy import inspect as _sa_inspect
            if _sa_inspect(db.engine).has_table('channels'):
                from .services.channel_registry import seed_builtin_channels
                seed_builtin_channels()
        except Exception as e:
            logger.warning(f"Skipped builtin channel seeding: {e}")

    @app.before_request
    def log_request():
        logger = get_logger('campaignsim.request')
        logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Request body: {request.get_json(silent=True)}")

    @app.after_request
    def log_response(response):
        logger = get_logger('campaignsim.request')
        logger.debug(f"Response: {response.status_code}")
        return response

    from .api import auth_bp, briefs_bp, graph_bp, simulation_bp, report_bp, evaluation_bp, channels_bp, designer_bp, insight_bp, data_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(briefs_bp, url_prefix='/api/briefs')
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(evaluation_bp, url_prefix='/api/evaluation')
    app.register_blueprint(channels_bp, url_prefix='/api/channels')
    app.register_blueprint(designer_bp, url_prefix='/api/designer')
    app.register_blueprint(insight_bp, url_prefix='/api/insight')
    app.register_blueprint(data_bp, url_prefix='/api/data')

    # Require auth on every API blueprint except /api/auth itself.
    from .utils.auth import decode_access_token, ACCESS_COOKIE
    from flask import g, jsonify

    PROTECTED_BLUEPRINTS = {'briefs', 'graph', 'simulation', 'report', 'evaluation', 'channels', 'designer', 'insight', 'data'}

    @app.before_request
    def enforce_auth():
        if request.method == 'OPTIONS':  # CORS preflight
            return None
        if request.blueprint not in PROTECTED_BLUEPRINTS:
            return None
        token = request.cookies.get(ACCESS_COOKIE)
        user_id = decode_access_token(token) if token else None
        if not user_id:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        import uuid as _uuid
        from .models.orm import User
        try:
            user = db.session.get(User, _uuid.UUID(user_id))
        except (ValueError, TypeError):
            user = None
        if user is None:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        g.current_user = user
        return None

    @app.route('/health')
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'service': 'CampaignSim Backend'}

    if should_log_startup:
        logger.info("CampaignSim Backend startup complete")

    return app
