"""
Configuration for the Flask application.

This module handles loading application configuration from environment
variables. It centralizes all configuration parameters for easier
management and distinction between different environments (e.g.,
development, production).
"""

import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """
    Base configuration class.

    Contains default configuration and settings that are common across all
    environments.
    """
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("FATAL: SECRET_KEY environment variable is not set.")

    # Session cookie settings for security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'None'

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///instance/database.db')
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS settings
    CORS_ORIGINS = [
        "https://asoraledecnal.github.io",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5500"
    ]
    
    # Email settings for feedback
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    VERIFIED_SENDER_EMAIL = os.environ.get('VERIFIED_SENDER_EMAIL', 'noreply@example.com') # Default to a generic noreply if not set

    # Email Verification settings
    VERIFICATION_TOKEN_SALT = os.environ.get('VERIFICATION_TOKEN_SALT', 'email-verification-salt')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:8080') # Default for local frontend

# For potential future use, e.g., class DevelopmentConfig(Config): ...
