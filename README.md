# Vantage - Network Surveillance Dashboard

## 1. Project Overview

Vantage is a web application designed to provide a user-friendly dashboard for network diagnostics. It features a secure user authentication system and a suite of essential network tools. 

This project is built with a focus on clean architecture, maintainability, and ease of deployment, making it a suitable foundation for further development.

## 2. Features

### Core Application
- **RESTful API:** A robust backend API built with Python and the Flask framework.
- **Asynchronous Email:** The feedback submission endpoint uses background threading to send email notifications via the SendGrid API, ensuring non-blocking, fast responses.
- **Secure Authentication:** A complete user management system with secure password hashing (Bcrypt) and session-based authentication.
- **Protected Endpoints:** All diagnostic tool endpoints require a valid user session.
- **Input Validation:** Strict validation is implemented for all user-provided data, such as hostnames and ports, to prevent common vulnerabilities.
- **Rate Limiting:** Endpoints are protected against abuse with IP-based rate limiting.

### Diagnostic Tools
- **WHOIS Lookup:** Retrieves domain registration information.
- **DNS Record Viewer:** Fetches common DNS records (A, AAAA, MX, CNAME, TXT).
- **IP Geolocation:** Provides geographical information for a given domain or IP address.
- **Port Scanner:** Checks the status of a specific port on a host.
- **Network Speed Test:** Measures server-side network performance (download, upload, ping).

## 3. Technical Stack

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

## 4. Project Structure

The project follows a standard package-based structure to ensure a clean separation of concerns.

```
/vantage
|-- /project/
|   |-- /routes/
|   |   |-- auth.py         # Authentication routes (signup, login, etc.)
|   |   |-- feedback.py     # Feedback submission route
|   |   `-- main.py         # Core diagnostic tool routes
|   |-- /services/
|   |   |-- domain_service.py # Business logic for domain tools
|   |   `-- email_service.py  # Logic for sending emails via SendGrid
|   |-- __init__.py         # Application factory (create_app)
|   |-- config.py         # Configuration loading
|   |-- models.py         # SQLAlchemy database models
|   `-- utils.py          # Utility functions (e.g., host validator)
|
|-- .env                  # Local environment variables (GIT-IGNORED)
|-- .gitignore
|-- config.wsgi           # Gunicorn configuration for production
|-- Dockerfile
|-- README.md             # This file
|-- requirements.txt
`-- run.py                # Application entry point
```

## 5. Setup and Installation

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
    ```

5.  **Initialize the Database:**
    Open a terminal with the virtual environment activated and run the Flask shell:
    ```bash
    flask shell
    ```
    In the Python shell that opens, create the database tables:
    ```python
    from project.models import db
    db.create_all()
    exit()
    ```

### Running the Application Locally

With your virtual environment activated, run the application from the root directory:
```bash
python run.py
```
The backend server will start on `http://127.0.0.1:5000`.

---

## 6. Deployment on Render

This project is configured for deployment on **Render** using Docker.

1.  **Push to GitHub:** Ensure your refactored code is pushed to your GitHub repository.
2.  **Create a New Web Service:** On the Render dashboard, create a new "Web Service" and connect it to your repository.
3.  **Environment Variables:** Before deploying, go to the **"Environment"** tab for your new service and add the same environment variables as your `.env` file, but with your production values:
    - `SECRET_KEY` (Render can generate a secure one for you)
    - `DATABASE_URL` (Render will provide this automatically if you also create a Render PostgreSQL database)
    - `SENDGRID_API_KEY`
    - `VERIFIED_SENDER_EMAIL`
    - `ADMIN_EMAIL`
4.  **Deploy:** Trigger a manual deployment. Render will use the `Dockerfile` to build and deploy your application.
