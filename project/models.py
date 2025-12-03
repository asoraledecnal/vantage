"""
Database models for the Vantage application.

This module defines the SQLAlchemy data models for the application,
including the User and Feedback tables. These models represent the
structure of the database and the relationships between different data
entities.
"""

import uuid
from sqlalchemy.dialects.postgresql import UUID
from .extensions import db

class User(db.Model):
    """
    Represents a user in the system.

    Attributes:
        id (uuid): The primary key for the user, a UUID.
        email (str): The user's unique email address.
        password_hash (str): The user's securely hashed password.
    """
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<User {self.email}>"

class Feedback(db.Model):
    """
    Represents a feedback submission from a user.

    Attributes:
        id (uuid): The primary key for the feedback entry, a UUID.
        name (str): The name of the person submitting feedback.
        email (str): The email of the person submitting feedback.
        subject (str): The subject line of the feedback message.
        message (str): The main content of the feedback message.
        created_at (datetime): The timestamp when the feedback was created.
    """
    __tablename__ = 'feedback'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    subject = db.Column(db.Text)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())

    def __repr__(self):
        return f"<Feedback from {self.name} on {self.created_at}>"
