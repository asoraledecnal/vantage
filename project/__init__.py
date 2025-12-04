"""
Application factory for the Vantage Flask application.

This module contains the `create_app` factory function which is responsible for
initializing the Flask application, loading the configuration, setting up
extensions (like SQLAlchemy, Bcrypt, CORS), and registering all the
blueprints for the different parts of the API.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

from .config import Config
from .extensions import db, bcrypt, limiter
from .routes.auth import auth_bp
from .routes.main import main_bp
from .routes.feedback import feedback_bp
from .services.assistant_service import DashboardAssistant

def create_app(config_class=Config):
    """
    Creates and configures an instance of the Flask application.

    Args:
        config_class: The configuration class to use for the application.
                      Defaults to the base Config class.

    Returns:
        The configured Flask application instance.
    """
    app = Flask(__name__)
    
    # --- Logging Configuration ---
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/vantage.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Vantage application startup')

    # Load configuration from the specified config object
    app.config.from_object(config_class)

    # Ensure the instance folder exists for SQLite defaults
    instance_path = os.path.join(os.path.dirname(app.root_path), 'instance')
    os.makedirs(instance_path, exist_ok=True)

    # --- Initialize extensions with the app ---
    db.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    
    # Configure CORS using settings from the config object
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}}, supports_credentials=True)

    # Apply ProxyFix middleware to correctly handle headers from a proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # --- Register blueprints ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(feedback_bp)

    # --- Log assistant backend availability ---
    try:
        assistant = DashboardAssistant()
        if assistant.gemini_api_key:
            app.logger.info(f"Assistant Gemini configured (model={assistant.gemini_model})")
        else:
            app.logger.info("Assistant Gemini not configured; using heuristic responses.")
    except Exception:
        app.logger.warning("Assistant initialization check failed", exc_info=True)

    return app
