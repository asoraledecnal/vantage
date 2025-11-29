import os
from dotenv import load_dotenv

load_dotenv()
import re
import json
import uuid
import socket
import datetime
import ipaddress
import smtplib

from email.mime.text import MIMEText
import threading

from functools import wraps
from typing import Any, Optional

import requests
import speedtest
import dns.resolver
import whois

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.dialects.postgresql import UUID


# ============================================================
#  Helper: Validate Host
# ============================================================
def is_valid_host(host):
    if not host or not isinstance(host, str) or host.startswith('-'):
        return False
    if any(char in host for char in ";|&`$()<>"):
        return False

    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass

    hostname_regex = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$"
    )
    return hostname_regex.match(host) is not None


def send_feedback_email(name, email, subject, message):
    admin_email = os.environ.get('ADMIN_EMAIL')
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT', 587)) 
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    
    # Diagnostic print statement to check variables in Render
    print(f"DIAGNOSTIC: ADMIN_EMAIL={'present' if admin_email else 'MISSING'}, SMTP_HOST={'present' if smtp_host else 'MISSING'}, SMTP_USER={'present' if smtp_user else 'MISSING'}, SMTP_PASS={'present' if smtp_pass else 'MISSING'}")

    if not all([admin_email, smtp_host, smtp_user, smtp_pass]):
        print("SMTP environment variables not fully configured. Skipping email send.")
        return False

    smtp_pass = smtp_pass.replace(" ", "")

    email_body = f"""
    New Feedback Received:
    ----------------------
    Name: {name}
    Email: {email}
    Subject: {subject or 'N/A'}
    
    Message:
    {message}
    """

    msg = MIMEText(email_body)
    msg['Subject'] = f"New Feedback: {subject or 'No Subject'}"
    msg['From'] = smtp_user
    msg['To'] = admin_email
    
    msg.add_header('Reply-To', email) 

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls() # Secure the connection
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print("Feedback email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send feedback email: {e}")
        return False


# ============================================================
#  Flask App Initialization
# ============================================================
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

bcrypt = Bcrypt(app)
limiter = Limiter(get_remote_address, app=app,
                  default_limits=["200 per day", "50 per hour"])

CORS(app, resources={r"/api/*": {
    "origins": [
        "https://asoraledecnal.github.io",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5500"
    ]
}}, supports_credentials=True)


# ============================================================
#  Security & Session Config
# ============================================================
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("FATAL: SECRET_KEY environment variable is not set.")

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'


# ============================================================
#  Database Configuration
# ============================================================
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ============================================================
#  Database Models
# ============================================================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    subject = db.Column(db.Text)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())


# ============================================================
#  Decorators
# ============================================================
def validate_host_from_request(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        data = request.get_json()
        host = data.get("host")

        if not host:
            return jsonify({"error": "Host is required"}), 400

        if not is_valid_host(host):
            return jsonify({"error": "Invalid or malicious host"}), 400
        
        kwargs["host"] = host
        return f(*args, **kwargs)
    return decorated


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ============================================================
#  Domain Tools
# ============================================================
def get_whois_data(domain):
    try:
        w = whois.whois(domain)

        def _get(key):
            return w.get(key) if isinstance(w, dict) else getattr(w, key, None)

        def _iso(val: Any) -> Optional[str]:
            if val is None:
                return None
            if isinstance(val, list):
                val = val[0] if val else None
                if val is None:
                    return None
            if isinstance(val, (datetime.datetime, datetime.date)):
                return val.isoformat()
            return str(val)

        return {
            "domain_name": _get("domain_name"),
            "registrar": _get("registrar"),
            "creation_date": _iso(_get("creation_date")),
            "expiration_date": _iso(_get("expiration_date")),
            "name_servers": _get("name_servers"),
            "status": _get("status"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_dns_records(domain):
    records = {}
    for record_type in ['A', 'AAAA', 'MX', 'CNAME', 'TXT']:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            records[record_type] = [str(rdata) for rdata in answers]
        except Exception as e:
            records[record_type] = {"error": str(e)}
    return records


def get_ip_geolocation(domain):
    try:
        ip_address = socket.gethostbyname(domain)
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def scan_port(domain, port):
    try:
        ip_address = socket.gethostbyname(domain)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((ip_address, port))
            return {"port": port, "status": "open" if result == 0 else "closed"}
    except Exception as e:
        return {"error": str(e)}


def get_speed_test():
    try:
        st = speedtest.Speedtest()
        st.download()
        st.upload()
        results = st.results.dict()
        return {
            "download": f"{results['download'] / 1_000_000:.2f} Mbps",
            "upload": f"{results['upload'] / 1_000_000:.2f} Mbps",
            "ping": f"{results['ping']:.2f} ms",
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================
#  AUTH ROUTES
# ============================================================
@app.route('/api/signup', methods=['POST'])
@limiter.limit("5 per minute")
def signup():
    session.clear()
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required!"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User with this email already exists!"}), 409

    hashed = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user = User(email=data["email"], password_hash=hashed)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully!"}), 201


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email")).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, data.get("password")):
        return jsonify({"message": "Invalid email or password"}), 401

    session["user_id"] = str(user.id)
    return jsonify({"message": "Login successful!", "user_id": user.id}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@app.route('/api/check_session', methods=['GET'])
def check_session():
    return jsonify({"logged_in": "user_id" in session}), 200


# ============================================================
#  FEEDBACK ROUTE
# ============================================================
@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.get_json()

    if not data or not data.get("name") or not data.get("email") or not data.get("message"):
        return jsonify({"success": False, "error": "Name, email, and message are required."}), 400

    try:
        # Save feedback to the database first
        fb = Feedback(
            name=data["name"],
            email=data["email"],
            subject=data.get("subject"),
            message=data["message"]
        )
        db.session.add(fb)
        db.session.commit()

        # Start a background thread to send the email without blocking
        thread = threading.Thread(
            target=send_feedback_email,
            args=(data["name"], data["email"], data.get("subject"), data["message"])
        )
        thread.start()

        return jsonify({"success": True}), 202  # 202 Accepted: The request has been accepted for processing

    except Exception as e:
        db.session.rollback()
        # In a real app, you'd log this error more formally
        print(f"Error in /api/contact: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500


# ============================================================
#  DOMAIN RESEARCH MAIN ROUTE
# ============================================================
@app.route('/api/domain', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def domain_research():
    data = request.get_json() or {}
    domain = data.get("domain")

    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    if not is_valid_host(domain):
        return jsonify({"error": "Invalid or malicious domain provided"}), 400

    try:
        port = int(data.get("port", 80))
        if not 1 <= port <= 65535:
            raise ValueError
    except:
        return jsonify({"error": "Port must be an integer between 1 and 65535"}), 400

    allowed_checks = {
        "whois": lambda: get_whois_data(domain),
        "dns_records": lambda: get_dns_records(domain),
        "ip_geolocation": lambda: get_ip_geolocation(domain),
        "port_scan": lambda: scan_port(domain, port),
    }

    requested = data.get("fields")
    if requested is None:
        requested = list(allowed_checks.keys())
    if isinstance(requested, str):
        requested = [requested]

    if not isinstance(requested, (list, tuple)):
        return jsonify({"error": "fields must be a list"}), 400

    results = {"domain": domain}

    for check in requested:
        if check not in allowed_checks:
            results[check] = {"error": "unknown check"}
            continue

        try:
            results[check] = allowed_checks[check]()
        except Exception as e:
            results[check] = {"error": str(e)}

    return jsonify(results), 200


# ============================================================
#  INDIVIDUAL LOOKUP ROUTES
# ============================================================
@app.route('/api/whois', methods=['POST'])
@login_required
@validate_host_from_request
def whois_route(host):

    return jsonify(get_whois_data(host))


@app.route('/api/geoip', methods=['POST'])
@login_required
@validate_host_from_request
def geoip_route(host):

    return jsonify(get_ip_geolocation(host))


@app.route('/api/dns', methods=['POST'])
@login_required
@validate_host_from_request
def dns_route(host):

    return jsonify(get_dns_records(host))


@app.route('/api/port_scan', methods=['POST'])
@login_required
@validate_host_from_request
def port_scan_route(host):
    data = request.get_json()
    port = int(data.get("port", 80))
    return jsonify(scan_port(host, port))


@app.route('/api/speed', methods=['POST'])
@login_required
def speed_route():
    return jsonify(get_speed_test())


# ============================================================
#  Run App
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
