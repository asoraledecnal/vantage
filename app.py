import os
import re
import socket
import ipaddress
import time
import requests
import uuid
from functools import wraps

from flask import Flask, request, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import dns.resolver
import speedtest

# --- Helper function for input validation ---
def is_valid_host(host):
    """
    Validates if the provided host is a valid hostname or IP address.
    Prevents argument injection by disallowing leading hyphens and other special characters.
    """
    if not host or not isinstance(host, str) or host.startswith('-'):
        return False
    # Disallow characters that could be used for command injection
    if any(char in host for char in " ;|&`$()<>\n\r"):
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
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# --- Security and Session Configuration ---
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("FATAL: SECRET_KEY environment variable is not set.")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
CORS(
    app,
    resources={r"/api/*": {"origins": ["https://asoraledecnal.github.io", "http://127.0.0.1:5000", "http://127.0.0.1:8080"]}},
    supports_credentials=True
)

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

# ... (other models remain the same) ...
class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = db.Column(db.Text, unique=True, nullable=False)
    title = db.Column(db.Text)
    description = db.Column(db.Text)

class DiagnosticResult(db.Model):
    __tablename__ = 'diagnostic_results'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    tool_name = db.Column(db.Text, nullable=False)
    target = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    raw_log = db.Column(db.Text)

class Incident(db.Model):
    __tablename__ = 'incidents'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.Text, nullable=False)
    narrative = db.Column(db.Text)
    status = db.Column(db.Text, nullable=False)


# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


# --- API Endpoints ---
# ... (Auth endpoints: signup, login, logout, check_session remain the same) ...
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


# --- NEW/UPDATED DIAGNOSTIC TOOLS ---

@app.route('/api/tcp_ping', methods=['POST'])
@login_required
def tcp_ping():
    data = request.get_json()
    host = data.get('host')
    port_str = data.get('port')

    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    try:
        port = int(port_str)
        if not 1 <= port <= 65535:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Port must be a valid integer between 1 and 65535"}), 400

    try:
        start_time = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)  # 2-second timeout
            s.connect((host, port))
        end_time = time.time()
        
        return jsonify({
            'host': host,
            'port': port,
            'status': 'reachable',
            'time': f"{(end_time - start_time) * 1000:.2f}ms"
        }), 200

    except (socket.timeout, ConnectionRefusedError):
        return jsonify({'host': host, 'port': port, 'status': 'unreachable'}), 200
    except socket.gaierror:
        return jsonify({'host': host, 'port': port, 'status': 'error', 'error': 'Hostname could not be resolved'}), 400
    except Exception as e:
        return jsonify({'host': host, 'port': port, 'status': 'error', 'error': str(e)}), 500


@app.route('/api/geoip', methods=['POST'])
@login_required
def geoip_lookup():
    data = request.get_json()
    host = data.get('host')
    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400

    try:
        # First, resolve the host to an IP if it's not already one
        ip_address = socket.gethostbyname(host)
    except socket.gaierror:
        return jsonify({'host': host, 'error': 'Hostname could not be resolved'}), 400

    try:
        # Use a free, public GeoIP API. No API key required.
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()

        if data.get('status') == 'fail':
            return jsonify({'host': host, 'ip_address': ip_address, 'error': 'Could not retrieve geolocation data.'}), 404

        return jsonify({
            'host': host,
            'ip_address': ip_address,
            'country': data.get('country'),
            'city': data.get('city'),
            'region': data.get('regionName'),
            'isp': data.get('isp'),
            'organization': data.get('org'),
            'latitude': data.get('lat'),
            'longitude': data.get('lon')
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'host': host, 'ip_address': ip_address, 'error': f'Failed to connect to geolocation service: {e}'}), 503
    except Exception as e:
        return jsonify({'host': host, 'ip_address': ip_address, 'error': str(e)}), 500


# --- EXISTING FUNCTIONAL TOOLS ---

@app.route('/api/port_scan', methods=['POST'])
@login_required
def port_scan():
    data = request.get_json()
    host = data.get('host')
    port_str = data.get('port')
    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    try:
        port = int(port_str)
        if not 1 <= port <= 65535:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Port must be a valid integer between 1 and 65535"}), 400

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            status = 'open' if result == 0 else 'closed'
            output = f"Port {port} is {status} on {host}"
        return jsonify({'host': host, 'port': port, 'status': status, 'raw_output': output}), 200
    except socket.gaierror:
        return jsonify({'host': host, 'port': port, 'status': 'error', 'error': 'Hostname could not be resolved'}), 400
    except Exception as e:
        return jsonify({'host': host, 'port': port, 'status': 'error', 'error': str(e)}), 500


@app.route('/api/dns', methods=['POST'])
@login_required
def dns_lookup():
    data = request.get_json()
    host = data.get('host')
    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    
    try:
        records = {}
        # A, AAAA, MX records
        for rec_type in ['A', 'AAAA', 'MX']:
            try:
                answers = dns.resolver.resolve(host, rec_type)
                if rec_type == 'MX':
                    records[rec_type] = sorted([f"{r.preference} {r.exchange.to_text()}" for r in answers])
                else:
                    records[rec_type] = [r.to_text() for r in answers]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                records[rec_type] = []
        return jsonify({'host': host, 'records': records}), 200
    except dns.resolver.NXDOMAIN:
        return jsonify({'host': host, 'error': 'Domain not found'}), 404
    except Exception as e:
        return jsonify({'host': host, 'error': str(e)}), 500


@app.route('/api/speed-test', methods=['POST'])
@login_required
def speed_test():
    try:
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        st.download()
        st.upload()
        res = st.results.dict()
        return jsonify({
            'download': f"{res['download'] / 1_000_000:.2f}",
            'upload': f"{res['upload'] / 1_000_000:.2f}",
            'ping': f"{res['ping']:.2f}"
        }), 200
    except Exception as e:
        return jsonify({'error': f"Speed test failed: {e}"}), 500


if __name__ == '__main__':
    app.config['SESSION_COOKIE_SECURE'] = False
    app.run(debug=True)