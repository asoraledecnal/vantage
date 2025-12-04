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
import traceback

main_bp = Blueprint('main', __name__, url_prefix='/api')

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

    return jsonify(results), 200


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
    response = assistant.answer(question, tool_hint=data.get("tool"))

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
            test = assistant._call_gemini("Say hello from Vantage assistant.", tool=None)
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
    return jsonify(domain_service.get_whois_data(host))

@main_bp.route('/geoip', methods=['POST'])
@login_required
@validate_host_from_request
def geoip_route(host):
    """Returns geolocation data for a given host."""
    return jsonify(domain_service.get_ip_geolocation(host))

@main_bp.route('/dns', methods=['POST'])
@login_required
@validate_host_from_request
def dns_route(host):
    """Returns DNS records for a given host."""
    return jsonify(domain_service.get_dns_records(host))

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
    
    return jsonify(domain_service.scan_port(host, port))

@main_bp.route('/speed', methods=['POST'])
@login_required
def speed_route():
    """Performs a network speed test."""
    return jsonify(domain_service.get_speed_test())
