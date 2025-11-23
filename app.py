import os
import re
import ipaddress
import uuid
from functools import wraps
import json
import whois
import dns.resolver
import requests
import socket
import speedtest

from flask import Flask, request, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Helper function for input validation ---
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

# --- App Initialization and Configuration ---
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
bcrypt = Bcrypt(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# --- Security and Session Configuration ---
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("FATAL: SECRET_KEY environment variable is not set.")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
CORS(app, resources={r"/api/*": {"origins": ["https://asoraledecnal.github.io", "http://127.0.0.1:5000", "http://127.0.0.1:8080"]}}, supports_credentials=True)

# --- Database Configuration ---
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    def __init__(self, email: str, password_hash: str, id: uuid.UUID | None = None):
        if id is not None:
            self.id = id
        self.email = email
        self.password_hash = password_hash

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    subject = db.Column(db.Text)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())

    def __init__(self, name: str, email: str, message: str, subject: str | None = None, id: uuid.UUID | None = None):
        if id is not None:
            self.id = id
        self.name = name
        self.email = email
        self.subject = subject
        self.message = message

# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Domain Analysis Tools ---
def get_whois_data(domain):
    try:
        w = whois.whois(domain)
        return {
            "domain_name": w.domain_name,
            "registrar": w.registrar,
            "creation_date": w.creation_date.isoformat() if w.creation_date else None,
            "expiration_date": w.expiration_date.isoformat() if w.expiration_date else None,
            "name_servers": w.name_servers,
            "status": w.status,
        }
    except Exception as e:
        return {"error": str(e)}

def get_dns_records(domain):
    records = {}
    record_types = ['A', 'AAAA', 'MX', 'CNAME', 'TXT']
    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            records[record_type] = [str(rdata) for rdata in answers]
        except Exception as e:
            records[record_type] = {"error": str(e)}
    return records

def get_ip_geolocation(domain):
    try:
        ip_address = socket.gethostbyname(domain)
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
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
            if result == 0:
                return {"port": port, "status": "open"}
            else:
                return {"port": port, "status": "closed"}
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
            "ping": f"{results['ping']:.2f} ms"
        }
    except Exception as e:
        return {"error": str(e)}

# --- API Endpoints ---
@app.route('/api/signup', methods=['POST'])
@limiter.limit("5 per minute")
def signup():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required!"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User with this email already exists!"}), 409
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(email=data['email'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully!"}), 201

@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data.get('password')):
        return jsonify({"message": "Invalid email or password"}), 401
    session['user_id'] = str(user.id)
    return jsonify({"message": "Login successful!", "user_id": user.id}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/check_session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({"logged_in": True}), 200
    return jsonify({"logged_in": False}), 401

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('message') or not data.get('name'):
        return jsonify({"message": "Name, email, and message are required."} ), 400
    try:
        new_feedback = Feedback(name=data['name'], email=data['email'], subject=data.get('subject'), message=data['message'])
        db.session.add(new_feedback)
        db.session.commit()
        return jsonify({"message": "Your message has been received. Thank you!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to save feedback due to an internal error: {e}"}), 500

# @app.route('/api/domain', methods=['POST'])
# @login_required
# def domain_research():
#     data = request.get_json()
#     domain = data.get('domain')
#     port = data.get('port', 80)

#     if not is_valid_host(domain):
#         return jsonify({"error": "Invalid or malicious domain provided"}), 400

#     try:
#         results = {
#             "domain": domain,
#             "whois": get_whois_data(domain),
#             "dns_records": get_dns_records(domain),
#             "ip_geolocation": get_ip_geolocation(domain),
#             "port_scan": scan_port(domain, port),
#             "speed_test": get_speed_test()
#         }
#         return jsonify(results), 200
#     except Exception as e:
#         return jsonify({"error": "An unexpected error occurred during domain research.", "details": str(e)}), 500

@app.route('/api/whois', methods=['POST'])
@login_required
def whois_route():
    data = request.get_json()
    host = data.get('host')
    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    return jsonify(get_whois_data(host))

@app.route('/api/dns_lookup', methods=['POST'])
@login_required
def dns_lookup_route():
    data = request.get_json()
    host = data.get('host')
    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    return jsonify(get_dns_records(host))

@app.route('/api/ip_geolocation', methods=['POST'])
@login_required
def ip_geolocation_route():
    data = request.get_json()
    host = data.get('host')
    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    return jsonify(get_ip_geolocation(host))

@app.route('/api/port_scan', methods=['POST'])
@login_required
def port_scan_route():
    data = request.get_json()
    host = data.get('host')
    port = data.get('port', 80)
    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    return jsonify(scan_port(host, int(port)))

@app.route('/api/speed_test', methods=['POST'])
@login_required
def speed_test_route():
    return jsonify(get_speed_test())

if __name__ == '__main__':
    app.config['SESSION_COOKIE_SECURE'] = False
    app.run(debug=True)