import os
import platform
import subprocess
import socket
import re
import ipaddress
from functools import wraps
from flask import Flask, request, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import uuid
from sqlalchemy.dialects.postgresql import UUID
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pythonping import ping # Import pythonping
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
    if any(char in host for char in " ;|&`$()<>\\n\\r"):
        return False

    # Check for valid IP address format
    try:
        ipaddress.ip_address(host)
        return True  # It's a valid IP address
    except ValueError:
        pass  # Not an IP address, check if it's a hostname

    # Check for valid hostname format (simple regex)
    # Allows for domain names like 'google.com' or 'sub.domain.co.uk'
    # This regex is strict and does not allow spaces or other risky characters.
    hostname_regex = re.compile(
        r"^(?:[a-zA-Z0-9]"  # First character of a label
        r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)"  # Subsequent characters of a label
        r"+[a-zA-Z]{2,6}$"  # TLD
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

# This is the crucial configuration for secure, cross-domain sessions.
# The secret key MUST be set in the environment for production.
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("FATAL: SECRET_KEY environment variable is not set. The application cannot run in an insecure state.")

app.config['SESSION_COOKIE_SECURE'] = True  # Ensures cookies are only sent over HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Allows cross-domain cookie sending

# This enables credentials (like cookies) to be sent from your frontend domain.
# Replace 'https://asoraledecnal.github.io' with your actual frontend URL if it's different.
CORS(
    app,
    resources={r"/api/*": {"origins": ["https://asoraledecnal.github.io", "http://127.0.0.1:5000"]}},
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
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())
    diagnostic_results = db.relationship('DiagnosticResult', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = db.Column(db.Text, unique=True, nullable=False)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<Document {self.file_path}>'

class DiagnosticResult(db.Model):
    __tablename__ = 'diagnostic_results'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    tool_name = db.Column(db.Text, nullable=False)
    target = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    raw_log = db.Column(db.Text)
    executed_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())

    def __repr__(self):
        return f'<DiagnosticResult {self.tool_name} on {self.target}>'

class Incident(db.Model):
    __tablename__ = 'incidents'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.Text, nullable=False)
    narrative = db.Column(db.Text)
    status = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<Incident {self.title}>'

# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


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
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required!"}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({"message": "Invalid email or password"}), 401
    
    session['user_id'] = str(user.id) # Store UUID as string in session
    return jsonify({"message": "Login successful!", "user_id": user.id}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear() # This clears the session, logging the user out
    return jsonify({"message": "Logged out successfully"}), 200


@app.route('/api/check_session', methods=['GET'])
def check_session():
    user_id_str = session.get('user_id')
    if user_id_str:
        try:
            user_id = uuid.UUID(user_id_str) # Convert string back to UUID
            user = db.session.get(User, user_id)
            if user:
                return jsonify({"logged_in": True, "email": user.email}), 200
        except ValueError:
            # Handle cases where session user_id is not a valid UUID
            pass
    
    return jsonify({"logged_in": False}), 401


# This is an example of a protected API endpoint
@app.route('/api/dashboard_data', methods=['GET'])
@login_required
def get_dashboard_data():
    return jsonify({"message": f"Welcome to your dashboard, user #{session['user_id']}!"})


@app.route('/api/ping', methods=['POST'])
@login_required
def ping_host():
    data = request.get_json()
    host = data.get('host')

    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    
    try:
        # Use pythonping
        result = ping(host, count=1, timeout=2) # 1 packet, 2 second timeout
        
        # pythonping.ping returns a list of Response objects
        if result.success:
            status = 'online'
            # Extract relevant info from the first successful response
            response_data = {
                'ip_address': str(result.responses[0].destination_ip),
                'rtt_avg_ms': result.rtt_avg_ms
            }
            output = result.all_responses[0].success_message
        else:
            status = 'offline'
            response_data = {}
            output = result.all_responses[0].error_message
        
        return jsonify({
            'host': host,
            'status': status,
            'ip': response_data.get('ip_address'),
            'time': f"{response_data.get('rtt_avg_ms', 'N/A')}ms",
            'raw_output': output
        }), 200

    except Exception as e:
        return jsonify({'host': host, 'status': 'error', 'error': str(e)}), 500


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
            s.settimeout(1) # 1-second timeout
            result = s.connect_ex((host, port))
            if result == 0:
                status = 'open'
                output = f"Port {port} is open on {host}"
            else:
                status = 'closed'
                output = f"Port {port} is closed or filtered on {host}"

        return jsonify({'host': host, 'port': port, 'status': status, 'raw_output': output}), 200

    except socket.gaierror:
        return jsonify({'host': host, 'port': port, 'status': 'error', 'error': 'Hostname could not be resolved'}), 400
    except Exception as e:
        return jsonify({'host': host, 'port': port, 'status': 'error', 'error': str(e)}), 500


@app.route('/api/traceroute', methods=['POST'])
@login_required
def traceroute_host():
    data = request.get_json()
    host = data.get('host')

    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400

    command = ['tracert' if platform.system().lower() == 'windows' else 'traceroute', host]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return jsonify({'host': host, 'status': 'complete', 'output': result.stdout}), 200
        else:
            return jsonify({'host': host, 'status': 'failed', 'output': result.stderr}), 200
            
    except subprocess.TimeoutExpired:
        return jsonify({'host': host, 'status': 'failed', 'error': 'Traceroute timed out'}), 504
    except Exception as e:
        return jsonify({'host': host, 'status': 'error', 'error': str(e)}), 500

@app.route('/api/dns', methods=['POST'])
@login_required
def dns_lookup():
    data = request.get_json()
    host = data.get('host')

    if not is_valid_host(host):
        return jsonify({"error": "Invalid or malicious host provided"}), 400
    
    records = {}
    try:
        # A record
        a_records = dns.resolver.resolve(host, 'A')
        records['A'] = [r.to_text() for r in a_records]
        
        # AAAA record
        try:
            aaaa_records = dns.resolver.resolve(host, 'AAAA')
            records['AAAA'] = [r.to_text() for r in aaaa_records]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            records['AAAA'] = []

        # MX record
        try:
            mx_records = dns.resolver.resolve(host, 'MX')
            records['MX'] = sorted([f"{r.preference} {r.exchange.to_text()}" for r in mx_records])
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            records['MX'] = []
            
        return jsonify({'host': host, 'records': records}), 200
        
    except dns.resolver.NXDOMAIN:
        return jsonify({'host': host, 'error': 'Domain not found'}), 404
    except Exception as e:
        return jsonify({'host': host, 'error': str(e)}), 500

@app.route('/api/speed-test', methods=['POST'])
@login_required
def speed_test():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        ping_latency = st.results.ping

        return jsonify({
            'download': f"{download_speed:.2f}",
            'upload': f"{upload_speed:.2f}",
            'ping': f"{ping_latency:.2f}"
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # When running locally, Flask's development server doesn't support HTTPS,
    # so the secure cookie won't work. We use this for local testing only.
    app.config['SESSION_COOKIE_SECURE'] = False
    app.run(debug=True)

