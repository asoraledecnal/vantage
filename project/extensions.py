"""
Centralized extension management for the Flask application.

This module initializes all Flask extensions (e.g., SQLAlchemy, Bcrypt)
to prevent circular import errors when they are needed in different parts
of the application, such as blueprints or models.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
bcrypt = Bcrypt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
