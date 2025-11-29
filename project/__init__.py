"""
Application factory for the Vantage Flask application.

This module contains the `create_app` factory function which is responsible for
initializing the Flask application, loading the configuration, setting up
extensions (like SQLAlchemy, Bcrypt, CORS), and registering all the
blueprints for the different parts of the API.
"""

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .models import db
from .routes.auth import auth_bp
from .routes.main import main_bp
from .routes.feedback import feedback_bp

# Initialize extensions, but don't configure them yet
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

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
    
    # Load configuration from the specified config object
    app.config.from_object(config_class)

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

    return app
