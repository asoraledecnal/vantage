"""
Authentication routes for the Vantage API.

This blueprint handles user registration, session management (login/logout),
and session verification. All routes are prefixed with '/api'.
"""

from flask import Blueprint, request, jsonify, session
from ..models import db, User
from .. import bcrypt  # Import bcrypt from the app factory package

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Handles new user registration.

    Expects a JSON payload with 'email' and 'password'.
    Returns a success message upon creation or an error if the user exists
    or input is invalid.
    """
    session.clear()
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required!"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User with this email already exists!"}), 409

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user = User(email=data["email"], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully!"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user and creates a session.

    Expects a JSON payload with 'email' and 'password'.
    On successful authentication, it sets the 'user_id' in the session.
    """
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email")).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, data.get("password")):
        return jsonify({"message": "Invalid email or password"}), 401

    session["user_id"] = str(user.id)
    return jsonify({"message": "Login successful!", "user_id": user.id}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Clears the current user's session.
    """
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route('/check_session', methods=['GET'])
def check_session():
    """
    Checks if a user is currently logged in.

    Returns:
        A JSON object indicating the logged-in status.
    """
    return jsonify({"logged_in": "user_id" in session}), 200
