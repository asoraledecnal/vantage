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

main_bp = Blueprint('main', __name__, url_prefix='/api')

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
