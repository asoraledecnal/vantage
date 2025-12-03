"""
Authentication routes for the Vantage API.

This blueprint handles user registration, session management (login/logout),
and session verification. All routes are prefixed with '/api'.
"""

from flask import Blueprint, request, jsonify, session, current_app, url_for
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import threading # Added import for threading
from ..models import User
from ..extensions import db, bcrypt  # Import from new extensions file
from ..services.email_service import send_verification_email
from ..config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Handles new user registration and initiates email verification.

    Expects a JSON payload with 'email' and 'password'.
    Returns a success message upon creation or an error if the user exists
    or input is invalid. The user's account will be inactive until email verification.
    """
    session.clear()
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required!"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User with this email already exists!"}), 409

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    
    # Generate verification token
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(data["email"], salt=current_app.config['VERIFICATION_TOKEN_SALT'])

    new_user = User(
        email=data["email"],
        password_hash=hashed_password,
        is_verified=False, # User is not verified until email confirmation
        verification_token=token # Store the token temporarily
    )
    db.session.add(new_user)
    db.session.commit()

    # Send verification email in a background thread
    threading.Thread(
        target=send_verification_email,
        args=(new_user.email, token, Config.FRONTEND_URL)
    ).start()

    return jsonify({
        "message": "User created successfully! Please check your email to verify your account."
    }), 201


@auth_bp.route('/verify-email', methods=['GET']) # Using GET as it's a link from email
def verify_email():
    """
    Handles email verification when a user clicks the link in their email.

    Expects a 'token' query parameter. Validates the token and updates
    the user's verification status.
    """
    token = request.args.get('token')
    if not token:
        return jsonify({"message": "Verification token is missing."}), 400

    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=current_app.config['VERIFICATION_TOKEN_SALT'], max_age=3600) # Token valid for 1 hour
    except SignatureExpired:
        return jsonify({"message": "The verification token has expired."}), 400
    except BadTimeSignature:
        return jsonify({"message": "Invalid verification token."}), 400
    except Exception:
        return jsonify({"message": "An unexpected error occurred during token validation."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found."}), 404
    
    if user.is_verified:
        return jsonify({"message": "Email already verified. You can now log in."}), 200

    user.is_verified = True
    user.verification_token = None # Clear the token after successful verification
    db.session.commit()

    return jsonify({"message": "Email verified successfully! You can now log in."}), 200


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

    if not user.is_verified:
        return jsonify({"message": "Account not verified. Please check your email for a verification link."}), 403

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
