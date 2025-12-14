# Vantage - Network Surveillance Dashboard

## 1. Project Overview

Vantage is a web application designed to provide a user-friendly dashboard for network diagnostics. It features a secure user authentication system and a suite of essential network tools. 

This project is built with a focus on clean architecture, maintainability, and ease of deployment, making it a suitable foundation for further development.

## 2. Features

### Core Application
- **RESTful API:** Python/Flask backend with clean separation between routes, services, and models.
- **Asynchronous Email:** Feedback submission uses background threading to send SendGrid notifications without blocking the UI.
- **Secure Authentication:** Session-based login with bcrypt-hashed passwords, OTP verification, and logout endpoints.
- **OTP-PASSWORD RESET:** The `/api/forgot-password` and `/api/reset-password` routes use 6-digit numeric OTPs (hashed+salted, 5-minute expiry) to avoid link-based enumeration. Resetting a password invalidates any active OTP and clears the session.
- **Protected Diagnostics:** All network tools require an authenticated session; requests are rate-limited and validated for host/port safety.
- **Dashboard Assistant:** `/api/assistant` provides conversational guidance for dashboard tools, returning tips and example requests. It now carries the most recent tool context (domain/port/speed, etc.) into answers so responses reference what the user just ran. Optional Gemini or OpenAI integration is supported when `GEMINI_API_KEY` or `OPENAI_API_KEY` is set; otherwise heuristic guidance is used.

### Diagnostic Tools
- **WHOIS Lookup:** Retrieves domain registration information.
- **DNS Record Viewer:** Fetches common DNS records (A, AAAA, MX, CNAME, TXT).
- **IP Geolocation:** Provides geographical information for a given domain or IP address.
- **Port Scanner:** Checks the status of a specific port on a host.
- **Network Speed Test:** Measures server-side network performance (download, upload, ping).
- **Domain Research:** `/api/domain` bundles the above checks and lets callers specify a subset via the `fields` array.
- **Guidance Endpoint:** `/api/tool-guidance?tool=<name>` returns instructions per tool (usage tips, example payloads) powered by `project/services/guidance_service.py`, as documented in AGENTS.md.

## 3. Backend API Routes (JSON)

- `POST /api/signup` / `POST /api/verify-otp` / `POST /api/resend-otp`: account creation and email verification via 6-digit OTP.
- `POST /api/login` / `POST /api/logout` / `GET /api/check_session`: session lifecycle; sets/clears the `user_id` session cookie.
- `POST /api/forgot-password` / `POST /api/reset-password`: password reset with hashed OTP + 5-minute expiry; responses stay generic to prevent enumeration.
- `POST /api/change-email` / `POST /api/change-password`: in-session email/password updates; require current password.
- `POST /api/domain`: combined WHOIS/DNS/geoip/port checks; accepts `domain` and optional `fields`/`port`.
- `POST /api/whois`, `/api/dns`, `/api/geoip`, `/api/port_scan`, `/api/speed`: individual diagnostics; require an authenticated session.
- `GET /api/tool-guidance`: returns usage tips/examples for a given tool.
- `POST /api/assistant` / `GET /api/assistant/status`: dashboard helper answers plus optional Gemini readiness check.
- `POST /api/contact`: saves feedback and dispatches email notification.
- `GET /api/health`: basic health probe (no auth).

## 4. Technical Stack

- **Backend:** Python 3.11+, Flask
- **Database:** PostgreSQL (production), SQLite (local dev option)
- **Key Python Libraries:**
  - Flask-SQLAlchemy (ORM)
  - Flask-Bcrypt (Password Hashing)
  - Flask-Limiter (Rate Limiting)
  - Flask-Cors (Cross-Origin Resource Sharing)
  - Gunicorn (WSGI Server)
  - `requests` (for SendGrid API)
  - `python-dotenv` (Environment Variable Management)
- **Deployment:** Docker, Render

---

## 5. Project Structure

The project follows a standard package-based structure to ensure a clean separation of concerns.

```
/vantage
|-- /project/
|   |-- /routes/
|   |   |-- auth.py         # Authentication, signup/login/logout, OTP flows
|   |   |-- feedback.py     # Feedback submission route
|   |   `-- main.py         # Diagnostic tool routes + tool-guidance & assistant endpoints
|   |-- /services/
|   |   |-- domain_service.py # Business logic for WHOIS/DNS/geoip/port/speed
|   |   |-- email_service.py  # SendGrid helpers & threaded sending
|   |   |-- otp_service.py    # OTP generation, hashing, verification helpers
|   |   |-- guidance_service.py # Returns per-tool guidance payloads
|   |   `-- assistant_service.py # Interactive dashboard assistant responses
|   |-- __init__.py         # Application factory (create_app)
|   |-- config.py           # Config loading + DATABASE_URL normalization
|   |-- models.py           # SQLAlchemy database models
|   `-- utils.py            # Utility validators (host/IP sanitizers, etc.)
|
|-- .env                  # Local environment variables (GIT-IGNORED)
|-- .gitignore
|-- config.wsgi           # Gunicorn configuration for production
|-- Dockerfile
|-- README.md             # This file
|-- requirements.txt
|-- otp_verification.html # Unified OTP verification/reset page
`-- run.py                # Application entry point
```

## 6. Setup and Installation

### Prerequisites
- Python 3.11+
- `pip` and `venv`

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/asoraledecnal/vantage
    cd vantage
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    # Create a virtual environment
    python -m venv .venv

    # Activate it (macOS/Linux)
    source .venv/bin/activate

    # Activate it (Windows PowerShell)
    # .\.venv\Scripts\Activate.ps1
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Environment Variables:**
    Create a `.env` file in the project root. This file is ignored by Git and should not be committed. Populate it with your local configuration:
    ```ini
    # Flask Secret Key
    SECRET_KEY='a_very_strong_and_random_secret_key'

    # Database URL (use SQLite for simple local setup)
    DATABASE_URL='sqlite:///database.db'

    # SendGrid API Key for sending emails
    SENDGRID_API_KEY='YOUR_SENDGRID_API_KEY'
    
    # The email address you verified as a Sender Identity in SendGrid
    VERIFIED_SENDER_EMAIL='your-verified-email@example.com'

    # The admin email address that will receive feedback notifications
    ADMIN_EMAIL='your-admin-email@example.com'

    # Optional: Gemini assistant (if configured)
    GEMINI_API_KEY='your-gemini-key'   # leave unset to use heuristic assistant only
    GEMINI_MODEL='gemini-2.5-flash'    # optional override

    # Optional: OpenAI assistant (if configured)
    OPENAI_API_KEY='your-openai-key'   # leave unset to skip OpenAI-backed replies
    OPENAI_MODEL='gpt-4o-mini'         # optional override
    ```

5.  **Initialize the Database:**
    ```bash
    flask shell
    ```
    Then inside the shell:
    ```python
    from project.models import db
    db.create_all()
    exit()
    ```

### Running the Application Locally

```bash
python run.py
```
The backend will listen on `http://127.0.0.1:5000`. After logging in (or calling `/api/signup` + OTP verification), manually test:
1. `/api/login` – confirm session cookie is issued (if the account exists but is unverified the app will resend an OTP and redirect to `otp_verification.html?mode=verify`).
2. `/api/domain` – try combinations of WHOIS/DNS/port checks via `fields`.
3. `/api/tool-guidance?tool=whois` – verify the guidance payload for each tool.
4. `/api/assistant` – send `{"question":"What does the DNS tool do?"}` to receive interactive tips and endpoint examples.
5. `/api/forgot-password` and `/api/reset-password` – ensure OTP flow works (check logs or email service).
6. `otp_verification.html?mode=verify&email=<your-email>` (or `mode=reset`) – open the shared OTP page manually to confirm both banners and API calls behave as expected.

> **Debug helper**: The new `console_buffer.js` script (loaded by login/signup/forgot_password/otp pages) keeps a rolling history of the last 100 console messages in localStorage and shows a little drawer in the bottom-right so you can see logs even after the page reloads. Use it to capture the OTP redirect URL or error responses.

Use the Mongo-style guidance data to power helpers or UI tooltips; call `/api/tool-guidance` with valid `tool` query values (`whois`, `dns_records`, `ip_geolocation`, `port_scan`, `speed`, `domain`).

---

## 7. Deployment on Render

This project is configured for deployment on **Render** using Docker.

1.  **Push to GitHub:** Ensure your refactored code is pushed to your GitHub repository.
2.  **Create a New Web Service:** On the Render dashboard, create a new "Web Service" and connect it to your repository.
3.  **Environment Variables:** Before deploying, go to the **"Environment"** tab for your new service and add the same environment variables as your `.env` file, but with your production values:
    - `SECRET_KEY` (Render can generate a secure one for you)
    - `DATABASE_URL` (Render will provide this automatically if you also create a Render PostgreSQL database)
    - `SENDGRID_API_KEY`
    - `VERIFIED_SENDER_EMAIL`
    - `ADMIN_EMAIL`
    - `OTP_SALT` (required; used to hash OTPs securely)
    - Optional: `GEMINI_API_KEY`, `GEMINI_MODEL`, and `ASSISTANT_EXPERIMENTAL_GEMINI=1` if you intentionally want Gemini-enabled replies (defaults to heuristic if not set).
4.  **Deploy:** Trigger a manual deployment. Render will use the `Dockerfile` to build and deploy your application.

### Render deployment checklist (to match local behavior)
- **HTTPS & sessions:** `SESSION_COOKIE_SECURE=True` and `SESSION_COOKIE_SAMESITE=None` mean you must access the Render app over HTTPS or cookies won’t stick. Keep `SECRET_KEY` stable between deploys.
- **CORS:** `CORS_ORIGINS` currently whitelists local hosts and `https://asoraledecnal.github.io`. Add your deployed frontend origin if different to avoid browser CORS blocks.
- **Database:** Ensure tables are created on Render (run the `db-init` command or equivalent) and point `DATABASE_URL` to Postgres, not SQLite.
- **Outbound egress:** WHOIS (port 43), DNS lookups, port scans, `http://ip-api.com` (GeoIP), and speed tests need outbound network access. If egress is restricted, these endpoints will return errors.
- **Email:** SendGrid credentials plus a verified sender are required; otherwise OTP and feedback emails will be skipped.
- **Rate limits:** Defaults are 200/day and 50/hour per IP. Behind a proxy, many users may share one IP—adjust if necessary.
- **Optional heavy endpoints:** `/api/speed` can be slow/expensive; consider restricting or warning in production if resources are tight.
