"""
Authentication routes for the Vantage API.

This blueprint handles user registration, session management (login/logout),
and session verification. All routes are prefixed with '/api'.
"""

import threading
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, session, current_app
from sqlalchemy import func
import uuid
from ..models import User
from ..extensions import db, bcrypt
from ..services import otp_service, email_service

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


def _to_utc(dt):
    """
    Normalize a datetime to a timezone-aware UTC datetime to avoid naive vs aware comparison errors.
    """
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Handles new user registration and sends an OTP for email verification.
    """
    try:
        session.clear()
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip()
        firstname = (data.get("firstname") or "").strip()
        lastname = (data.get("lastname") or "").strip()
        username = (data.get("username") or "").strip()
        phone = (data.get("phone") or "").strip() or None

        required_fields = {
            "email": email,
            "password": (data.get("password") or "").strip(),
            "firstname": firstname,
            "lastname": lastname,
            "username": username,
        }
        missing = [field for field, value in required_fields.items() if not value]
        if missing:
            return jsonify({"message": f"Missing required fields: {', '.join(missing)}."}), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if not existing_user.is_verified:
                otp = otp_service.generate_otp()
                existing_user.otp_hash = otp_service.hash_otp(otp)
                existing_user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
                db.session.commit()
                current_app.logger.info(f"Resent OTP to unverified user: {email}")
                threading.Thread(target=email_service.send_otp_email, args=(existing_user.email, otp)).start()
                return jsonify({
                    "message": "Account already created but not verified. A new OTP has been sent. Redirecting to verification.",
                    "email": existing_user.email,
                    "action": "verify"
                }), 200
            current_app.logger.warning(f"Signup attempt for existing email: {email}")
            return jsonify({
                "message": "An account with this email is already registered and verified. Redirecting to login.",
                "action": "login"
            }), 409

        if User.query.filter_by(username=username).first():
            current_app.logger.warning(f"Signup attempt for existing username: {username}")
            return jsonify({"message": "Username is taken. Please choose another."}), 409

        hashed_password = bcrypt.generate_password_hash(required_fields["password"]).decode("utf-8")
        
        otp = otp_service.generate_otp()
        otp_hash = otp_service.hash_otp(otp)
        otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

        new_user = User(
            username=username,
            firstname=firstname,
            lastname=lastname,
            phone=phone,
            email=email,
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
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    if not email or not data.get("otp"):
        return jsonify({"message": "Email and OTP are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        current_app.logger.warning(f"OTP verification attempt for non-existent user: {email}")
        return jsonify({"message": "User not found."}), 404
    
    if user.is_verified:
        return jsonify({"message": "Account already verified."}), 200

    expiry = _to_utc(user.otp_expiry)
    if not expiry or expiry < datetime.now(timezone.utc):
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


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """
    Resends a verification OTP for an unverified user.
    """
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"message": "Email is required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        current_app.logger.info(f"OTP resend requested for non-existent user: {email}")
        return jsonify({"message": "If an account exists, a new OTP has been sent."}), 200

    if user.is_verified:
        return jsonify({"message": "Account already verified. You can log in."}), 200

    otp = otp_service.generate_otp()
    user.otp_hash = otp_service.hash_otp(otp)
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    db.session.commit()

    current_app.logger.info(f"Resent verification OTP to user: {email}")
    threading.Thread(target=email_service.send_otp_email, args=(user.email, otp)).start()

    return jsonify({"message": "A new OTP has been sent to your email."}), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user and creates a session.
    """
    data = request.get_json(silent=True) or {}
    identifier = (data.get("login_identifier") or data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    user = None
    if identifier:
        lowered = identifier.lower()
        user = User.query.filter(func.lower(User.email) == lowered).first()
        if not user:
            user = User.query.filter(func.lower(User.username) == lowered).first()
    if not identifier or not password:
        return jsonify({"message": "Email (or username) and password are required."}), 400

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        current_app.logger.warning(f"Failed login attempt for user: {identifier}")
        return jsonify({"message": "Invalid email or password"}), 401

    if not user.is_verified:
        otp = otp_service.generate_otp()
        user.otp_hash = otp_service.hash_otp(otp)
        user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.session.commit()
        threading.Thread(target=email_service.send_otp_email, args=(user.email, otp)).start()
        current_app.logger.warning(f"Login attempt by unverified user: {user.email}. OTP resent.")
        return jsonify({
            "message": "Account not verified. A new OTP has been sent to your email.",
            "email": user.email,
            "action": "verify"
        }), 200

    session["user_id"] = str(user.id)
    current_app.logger.info(f"User logged in successfully: {user.email}")
    return jsonify({"message": "Login successful!", "user_id": user.id}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Clears the current user's session.
    """
    user_id = session.get('user_id')
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            user = User.query.get(user_uuid)
            if user:
                current_app.logger.info(f"User logged out: {user.email}")
        except (ValueError, TypeError):
            current_app.logger.warning("Invalid user_id in session during logout")
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
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"message": "Email is required."}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        otp = otp_service.generate_otp()
        user.otp_hash = otp_service.hash_otp(otp)
        user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.session.commit()

        current_app.logger.info(f"Password reset OTP dispatched for user: {email}")
        threading.Thread(target=email_service.send_password_reset_email, args=(user.email, otp)).start()
    else:
        current_app.logger.info(f"Password reset requested for non-existent user: {email}")

    # Always return a generic response to prevent account enumeration
    return jsonify({"message": "If an account with that email exists, a password reset OTP has been sent."}), 200


@auth_bp.route('/change-email', methods=['POST'])
def change_email():
    """
    Allows a logged-in user to change their email after confirming their current password.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid session"}), 401

    data = request.get_json(silent=True) or {}
    new_email = (data.get("new_email") or "").strip()
    current_password = (data.get("current_password") or "").strip()

    if not new_email or not current_password:
        return jsonify({"message": "New email and current password are required."}), 400

    user = User.query.get(user_uuid)
    if not user:
        return jsonify({"message": "User not found."}), 404

    # Verify password
    if not bcrypt.check_password_hash(user.password_hash, current_password):
        current_app.logger.warning("Change email failed: bad password for user %s", user.email)
        return jsonify({"message": "Invalid credentials."}), 401

    # Prevent duplicate emails (case-insensitive)
    lowered_email = new_email.lower()
    existing = User.query.filter(func.lower(User.email) == lowered_email, User.id != user.id).first()
    if existing:
        return jsonify({"message": "That email is already in use."}), 409

    user.email = new_email
    db.session.commit()
    current_app.logger.info("User %s changed email to %s", user.username, new_email)
    return jsonify({"message": "Email updated successfully.", "email": new_email}), 200


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """
    Allows a logged-in user to change their password by supplying the current password.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid session"}), 401

    data = request.get_json(silent=True) or {}
    current_password = (data.get("current_password") or "").strip()
    new_password = (data.get("new_password") or "").strip()

    if not current_password or not new_password:
        return jsonify({"message": "Current password and new password are required."}), 400

    user = User.query.get(user_uuid)
    if not user:
        return jsonify({"message": "User not found."}), 404

    if not bcrypt.check_password_hash(user.password_hash, current_password):
        current_app.logger.warning("Change password failed: bad password for user %s", user.email)
        return jsonify({"message": "Current password is incorrect."}), 401

    user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    # Clear any pending OTP data when password is changed directly
    user.otp_hash = None
    user.otp_expiry = None
    db.session.commit()
    current_app.logger.info("User %s changed password", user.username)
    return jsonify({"message": "Password updated successfully."}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Resets the user's password using a valid OTP.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    required_fields = ["email", "otp", "new_password"]
    if not all(field in data and data.get(field) for field in required_fields):
        return jsonify({"message": "Email, OTP, and new password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        current_app.logger.warning(f"Password reset attempt for non-existent user: {email}")
        return jsonify({"message": "Invalid email or OTP."}), 400

    if not user.is_verified:
        current_app.logger.warning(f"Password reset attempt for unverified user: {email}")
        return jsonify({"message": "Account not verified. Please verify your account first."}), 400

    expiry = _to_utc(user.otp_expiry)
    if not expiry or expiry < datetime.now(timezone.utc):
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

    # Invalidate any existing session after password reset for safety
    session.clear()

    return jsonify({"message": "Password has been reset successfully."}), 200
