"""
Authentication routes for the Vantage API.

This blueprint handles user registration, session management (login/logout),
and session verification. All routes are prefixed with '/api'.
"""

import threading
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, current_app
from ..models import User
from ..extensions import db, bcrypt
from ..services import otp_service, email_service

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Handles new user registration and sends an OTP for email verification.
    """
    try:
        session.clear()
        data = request.get_json()
        email = data.get("email")
        username = data.get("username")

        if not all([email, data.get("password"), username]):
            return jsonify({"message": "Username, email, and password are required!"}), 400

        if User.query.filter_by(email=email).first():
            current_app.logger.warning(f"Signup attempt for existing email: {email}")
            return jsonify({"message": "User with this email already exists!"}), 409
        
        if User.query.filter_by(username=username).first():
            current_app.logger.warning(f"Signup attempt for existing username: {username}")
            return jsonify({"message": "User with this username already exists!"}), 409

        hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        
        otp = otp_service.generate_otp()
        otp_hash = otp_service.hash_otp(otp)
        otp_expiry = datetime.utcnow() + timedelta(minutes=5)

        new_user = User(
            email=email,
            username=username,
            password_hash=hashed_password,
            is_verified=False,
            otp_hash=otp_hash,
            otp_expiry=otp_expiry
        )
        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"New user created: {email}. Sending OTP.")
        threading.Thread(target=email_service.send_otp_email, args=(new_user.email, otp)).start()

        return jsonify({
            "message": "User created successfully! Please check your email for an OTP to verify your account."
        }), 201
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during signup: {e}", exc_info=True)
        return jsonify({"message": "An internal server error occurred."}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Handles OTP verification for a user's account.
    """
    data = request.get_json()
    email = data.get("email")
    if not email or not data.get("otp"):
        return jsonify({"message": "Email and OTP are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        current_app.logger.warning(f"OTP verification attempt for non-existent user: {email}")
        return jsonify({"message": "User not found."}), 404
    
    if user.is_verified:
        return jsonify({"message": "Account already verified."}), 200

    if user.otp_expiry < datetime.utcnow():
        current_app.logger.warning(f"Expired OTP attempt for user: {email}")
        return jsonify({"message": "OTP has expired."}), 400

    if not otp_service.verify_otp(data["otp"], user.otp_hash):
        current_app.logger.warning(f"Invalid OTP attempt for user: {email}")
        return jsonify({"message": "Invalid OTP."}), 400

    user.is_verified = True
    user.otp_hash = None
    user.otp_expiry = None
    db.session.commit()
    current_app.logger.info(f"Account successfully verified for user: {email}")

    return jsonify({"message": "Account verified successfully! You can now log in."}), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user via email or username and creates a session.
    """
    data = request.get_json()
    login_identifier = data.get("login_identifier")
    password = data.get("password")

    if not login_identifier or not password:
        return jsonify({"message": "Email/username and password are required"}), 400

    # Determine if the identifier is an email or a username
    if '@' in login_identifier:
        user = User.query.filter_by(email=login_identifier).first()
    else:
        user = User.query.filter_by(username=login_identifier).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        current_app.logger.warning(f"Failed login attempt for identifier: {login_identifier}")
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.is_verified:
        current_app.logger.warning(f"Login attempt by unverified user: {user.email}")
        return jsonify({"message": "Account not verified. Please check your email for an OTP to verify your account."}), 403

    session["user_id"] = str(user.id)
    current_app.logger.info(f"User logged in successfully: {user.username} ({user.email})")
    return jsonify({"message": "Login successful!", "user_id": user.id}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Clears the current user's session.
    """
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        current_app.logger.info(f"User logged out: {user.email}")
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route('/check_session', methods=['GET'])
def check_session():
    """
    Checks if a user is currently logged in.
    """
    return jsonify({"logged_in": "user_id" in session}), 200


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Initiates the password reset process by sending an OTP to the user's email.
    """
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"message": "Email is required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        current_app.logger.info(f"Password reset request for non-existent user: {email}")
        return jsonify({"message": "If an account with that email exists, a password reset OTP has been sent."}), 200

    otp = otp_service.generate_otp()
    user.otp_hash = otp_service.hash_otp(otp)
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    db.session.commit()

    current_app.logger.info(f"Password reset OTP sent to user: {email}")
    threading.Thread(target=email_service.send_password_reset_email, args=(user.email, otp)).start()

    return jsonify({"message": "If an account with that email exists, a password reset OTP has been sent."}), 200





@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Resets the user's password using a valid OTP.
    """
    data = request.get_json()
    email = data.get("email")
    required_fields = ["email", "otp", "new_password"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Email, OTP, and new password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        current_app.logger.warning(f"Password reset attempt for non-existent user: {email}")
        return jsonify({"message": "Invalid email or OTP."}), 400

    if not user.otp_expiry or user.otp_expiry < datetime.utcnow():
        current_app.logger.warning(f"Expired password reset OTP for user: {email}")
        return jsonify({"message": "OTP has expired."}), 400

    if not user.otp_hash or not otp_service.verify_otp(data["otp"], user.otp_hash):
        current_app.logger.warning(f"Invalid password reset OTP for user: {email}")
        return jsonify({"message": "Invalid email or OTP."}), 400

    user.password_hash = bcrypt.generate_password_hash(data["new_password"]).decode("utf-8")
    user.otp_hash = None
    user.otp_expiry = None
    db.session.commit()
    current_app.logger.info(f"Password successfully reset for user: {email}")

    return jsonify({"message": "Password has been reset successfully."}), 200
