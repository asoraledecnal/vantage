"""
Feedback submission route for the Vantage API.

This blueprint handles the contact form submission, saving the feedback to the
database and triggering an asynchronous email notification.
"""
import threading
import re # Import re for regex validation
from flask import Blueprint, request, jsonify
from ..models import db, Feedback
from ..services import email_service

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api')

@feedback_bp.route('/contact', methods=['POST'])
def handle_contact():
    """
    Handles a new feedback submission.

    Saves the feedback to the database and dispatches an email notification
    in a background thread. Returns a 202 Accepted response immediately.
    Includes basic email format validation.
    """
    data = request.get_json()

    if not data or not data.get("name") or not data.get("email") or not data.get("message"):
        return jsonify({"success": False, "error": "Name, email, and message are required."}), 400

    # Basic email format validation
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, data["email"]):
        return jsonify({"success": False, "error": "Invalid email address format."}), 400

    try:
        # Save feedback to the database first
        new_feedback = Feedback(
            name=data["name"],
            email=data["email"],
            subject=data.get("subject"),
            message=data["message"]
        )
        db.session.add(new_feedback)
        db.session.commit()

        # Start a background thread to send the email without blocking
        thread = threading.Thread(
            target=email_service.send_feedback_email,
            args=(data["name"], data["email"], data.get("subject"), data["message"])
        )
        thread.start()

        return jsonify({"success": True}), 202  # 202 Accepted

    except Exception as e:
        db.session.rollback()
        print(f"Error in /api/contact: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500
