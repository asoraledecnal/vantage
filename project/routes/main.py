"""
Main API routes for domain diagnostic tools.

This blueprint handles all the core functionality of the application,
including the combined domain research tool and individual lookups for
WHOIS, DNS, geolocation, etc. All routes require user authentication.
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from ..utils import is_valid_host
from ..services import domain_service
from ..services.assistant_service import DashboardAssistant
from ..services.guidance_service import DiagnosticGuidanceService
from ..models import User
from ..extensions import db
import traceback
from datetime import datetime, timezone

main_bp = Blueprint('main', __name__, url_prefix='/api')

def _set_assistant_context(tool: str, target: str, summary: str | None = None) -> None:
    """
    Persist the most recent tool context to the session so the assistant can reference it.
    """
    session["assistant_context"] = {
        "tool": tool,
        "target": target,
        "summary": summary or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@main_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "ok"}), 200

# Decorator to ensure user is logged in
def login_required(f):
    """
    A decorator to protect routes that require authentication.

    Verifies that 'user_id' is present in the session. If not, it returns
    a 401 Unauthorized error.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Decorator for host validation from request body
def validate_host_from_request(f):
    """
    A decorator to extract and validate the 'host' from a JSON request body.

    This simplifies routes by handling the repetitive logic of getting and
    validating the host parameter.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        host = data.get("host")

        if not host:
            return jsonify({"error": "Host is required"}), 400
        if not is_valid_host(host):
            return jsonify({"error": "Invalid or malicious host"}), 400
        
        # Pass the validated host to the decorated function
        kwargs['host'] = host
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/domain', methods=['POST'])
@login_required
def domain_research():
    """
    Performs a comprehensive research on a domain based on specified fields.
    """
    data = request.get_json() or {}
    domain = data.get("domain")

    if not domain:
        return jsonify({"error": "Domain is required"}), 400
    if not is_valid_host(domain):
        return jsonify({"error": "Invalid or malicious domain provided"}), 400

    try:
        port = int(data.get("port", 80))
        if not 1 <= port <= 65535:
            raise ValueError("Invalid port number")
    except (ValueError, TypeError):
        return jsonify({"error": "Port must be an integer between 1 and 65535"}), 400

    allowed_checks = {
        "whois": lambda: domain_service.get_whois_data(domain),
        "dns_records": lambda: domain_service.get_dns_records(domain),
        "ip_geolocation": lambda: domain_service.get_ip_geolocation(domain),
        "port_scan": lambda: domain_service.scan_port(domain, port),
    }

    requested_fields = data.get("fields", list(allowed_checks.keys()))
    if isinstance(requested_fields, str):
        requested_fields = [requested_fields]

    if not isinstance(requested_fields, list):
        return jsonify({"error": "fields must be a list"}), 400

    results = {"domain": domain}
    for check in requested_fields:
        if check in allowed_checks:
            try:
                results[check] = allowed_checks[check]()
            except Exception as e:
                results[check] = {"error": f"An unexpected error occurred during {check}: {e}"}
        else:
            results[check] = {"error": "unknown check"}

    _set_assistant_context("domain", domain, f"Domain research for {domain} with {', '.join(requested_fields)}")
    return jsonify(results), 200


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_management():
    """
    Allows users to fetch and update their profile information.
    """
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if request.method == 'GET':
        return jsonify({
            "id": user.id,
            "username": user.username,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "phone": user.phone,
            "email": user.email,
            "is_verified": user.is_verified
        }), 200

    elif request.method == 'POST':
        data = request.get_json()
        
        # Basic validation
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        # Update fields if provided
        if 'firstname' in data:
            user.firstname = data['firstname']
        if 'lastname' in data:
            user.lastname = data['lastname']
        if 'username' in data:
            new_username = data['username']
            if new_username != user.username and User.query.filter_by(username=new_username).first():
                return jsonify({"message": "Username already taken"}), 409
            user.username = new_username
        if 'phone' in data:
            user.phone = data['phone']
        
        try:
            db.session.commit()
            return jsonify({"message": "Profile updated successfully", "username": user.username}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500


@main_bp.route('/account-delete', methods=['DELETE'])
@login_required
def delete_account():
    """
    Allows a logged-in user to delete their own account.
    """
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        session.clear() # Clear the session after account deletion
        # Log the deletion
        from flask import current_app
        current_app.logger.info(f"User account deleted: {user.email}")
        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        # Log the error
        from flask import current_app
        current_app.logger.error(f"Error deleting user account {user.email}: {str(e)}")
        return jsonify({"message": f"An error occurred during account deletion: {str(e)}"}), 500


@main_bp.route('/tool-guidance', methods=['GET'])
@login_required
def tool_guidance():
    tool = request.args.get("tool")
    if not tool:
        return jsonify({"error": "Please specify a tool query parameter."}), 400

    guidance = DiagnosticGuidanceService().get_guidance(tool)
    return jsonify(guidance), 200


@main_bp.route('/assistant', methods=['POST'])
@login_required
def assistant():
    """
    Provides conversational help for dashboard tools.
    """
    data = request.get_json() or {}
    question = data.get("question")
    if not question:
        return jsonify({"error": "Question text is required."}), 400

    assistant = DashboardAssistant()
    response = assistant.answer(
        question,
        tool_hint=data.get("tool"),
        context=session.get("assistant_context"),
    )

    history = session.get("assistant_history", [])
    history.append({
        "question": question,
        "answer": response.get("answer"),
        "tool": response.get("tool"),
    })
    session["assistant_history"] = history[-10:]
    response["history"] = session["assistant_history"]

    return jsonify(response), 200


@main_bp.route('/assistant/status', methods=['GET'])
@login_required
def assistant_status():
    """
    Debug endpoint to check Gemini assistant readiness.
    """
    try:
        assistant = DashboardAssistant()
        configured = bool(assistant.gemini_api_key)
        test_result = None
        if configured:
            test = assistant._call_gemini("Say hello from Vantage assistant.", tool=None, context={})
            if test and test.get("answer"):
                test_result = "ok"
            else:
                test_result = "failed"
        return jsonify({
            "gemini_configured": configured,
            "model": assistant.gemini_model if configured else None,
            "test_call": test_result,
        }), 200
    except Exception:
        return jsonify({
            "gemini_configured": False,
            "error": "status check failed",
        }), 500

@main_bp.route('/whois', methods=['POST'])
@login_required
@validate_host_from_request
def whois_route(host):
    """Returns WHOIS data for a given host."""
    result = domain_service.get_whois_data(host)
    _set_assistant_context("whois", host, f"WHOIS lookup for {host}")
    return jsonify(result)

@main_bp.route('/geoip', methods=['POST'])
@login_required
@validate_host_from_request
def geoip_route(host):
    """Returns geolocation data for a given host."""
    result = domain_service.get_ip_geolocation(host)
    _set_assistant_context("ip_geolocation", host, f"IP geolocation for {host}")
    return jsonify(result)

@main_bp.route('/dns', methods=['POST'])
@login_required
@validate_host_from_request
def dns_route(host):
    """Returns DNS records for a given host."""
    result = domain_service.get_dns_records(host)
    _set_assistant_context("dns_records", host, f"DNS records lookup for {host}")
    return jsonify(result)

@main_bp.route('/port_scan', methods=['POST'])
@login_required
@validate_host_from_request
def port_scan_route(host):
    """Performs a port scan on a given host and port."""
    data = request.get_json()
    try:
        port = int(data.get("port", 80))
        if not 1 <= port <= 65535:
            raise ValueError("Invalid port number")
    except (ValueError, TypeError):
        return jsonify({"error": "Port must be an integer between 1 and 65535"}), 400
    
    result = domain_service.scan_port(host, port)
    _set_assistant_context("port_scan", f"{host}:{port}", f"Port scan on {host}:{port}")
    return jsonify(result)

@main_bp.route('/speed', methods=['POST'])
@login_required
def speed_route():
    """Performs a network speed test."""
    result = domain_service.get_speed_test()
    _set_assistant_context("speed_test", "local", "Recent speed test")
    return jsonify(result)
