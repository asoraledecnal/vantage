# Vantage - Network Surveillance Dashboard

## Project Overview

Vantage is a web application designed to provide a user-friendly dashboard for network diagnostics. It features a secure user authentication system and a suite of essential network tools. The frontend is a lightweight, single-page application built with **vanilla HTML, CSS, and JavaScript**, while the backend is powered by a robust **Python Flask** server with a persistent PostgreSQL database.

This project prioritizes security, maintainability, and ease of deployment.

## Features

### Frontend
*   **Minimalist UI:** A clean and responsive user interface built with standard HTML and CSS.
*   **Dynamic Tabs:** A tab-based interface to switch between different network tools without page reloads.
*   **Asynchronous Tools:** Client-side JavaScript uses the Fetch API to interact with the backend, providing real-time results for all network tools.
*   **User Authentication:** Dedicated pages for user signup and login.
*   **Secure Dashboard:** A protected dashboard accessible only after a successful login.
*   **Core Network Tools:** Includes Ping, Port Scan, Traceroute, DNS Lookup, and a Network Speed Test.
*   **Notifications:** Displays clear success or error messages for a better user experience.

### Backend
*   **RESTful API:** A set of secure API endpoints for user authentication and network diagnostics.
*   **Secure Authentication:**
    *   `POST /api/signup`: Registers new users with securely hashed passwords.
    *   `POST /api/login`: Authenticates users and manages sessions.
    *   `POST /api/logout`: Securely terminates user sessions.
    *   `GET /api/check_session`: Verifies a user's logged-in status.
*   **Protected Endpoints:** All diagnostic tools require a valid user session.
*   **Input Validation:** Implements strict validation on all user inputs (e.g., hostnames, ports) to prevent command injection and other attacks.
*   **Database:** Uses PostgreSQL via Flask-SQLAlchemy for reliable data persistence.
*   **Security Measures:**
    *   Passwords are hashed with Flask-Bcrypt.
    *   Rate limiting is enforced with Flask-Limiter to prevent abuse.
    *   Secure cookie settings (HTTPOnly, SameSite) are used for session management.
*   **Production-Ready:** Deploys with a `gunicorn` WSGI server inside a Docker container.

---

## Technical Stack

*   **Frontend:** HTML, CSS, JavaScript (Vanilla)
*   **Backend:** Python 3.11, Flask
*   **Database:** PostgreSQL
*   **Key Python Libraries:** Flask-SQLAlchemy, Flask-Bcrypt, Flask-Limiter, gunicorn, pythonping, dnspython, speedtest-cli
*   **Deployment:** Docker, Render

---

## Project Setup and Installation

### Prerequisites
*   Python 3.11+
*   `pip` (Python package installer)
*   A tool to run a local web server (e.g., VS Code's "Live Server" extension or Python's `http.server` module).

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/asoraledecnal/vantage
    cd vantage
    ```

2.  **Set Up the Backend:**
    *   **Create and Activate a Virtual Environment:**
        *   **Windows (PowerShell):**
            ```powershell
            python -m venv .venv
            .\.venv\Scripts\Activate.ps1
            ```
        *   **macOS / Linux (Bash):**
            ```bash
            python3 -m venv .venv
            source .venv/bin/activate
            ```
    *   **Install Python Dependencies:**
        ```bash
        pip install -r requirements.txt
        ```
    *   **Set Environment Variables:**
        Create a `.env` file in the root directory and add the following variables. This is crucial for security.
        ```
        SECRET_KEY='a_very_strong_and_random_secret_key'
        DATABASE_URL='sqlite:///database.db' # For local development
        ```
    *   **Initialize the Database:**
        ```bash
        # On macOS/Linux
        export FLASK_APP=app.py
        flask shell

        # On Windows CMD
        set FLASK_APP=app.py
        flask shell
        ```
        In the Python shell that opens, run the following commands:
        ```python
        from app import db
        db.create_all()
        exit()
        ```

### Running the Application Locally

1.  **Run the Backend Server:**
    In your terminal, with the virtual environment activated, run:
    ```bash
    python app.py
    ```
    The backend will be running at `http://127.0.0.1:5000`.

2.  **Run the Frontend:**
    Since the frontend consists of static HTML, CSS, and JS files, you need to serve them via a local web server.
    *   **Option A (Recommended): Using VS Code's Live Server Extension:**
        Right-click on `index.html` and select "Open with Live Server".
    *   **Option B: Using Python's built-in server:**
        Open a **new terminal** and run:
        ```bash
        python -m http.server 8080
        ```
        Then, open your browser and navigate to `http://127.0.0.1:8080`.

---

## Deployment on Render

This project is configured for easy deployment on **Render** using Docker.

1.  **Push to GitHub:** Ensure all your code is pushed to a public or private GitHub repository.
2.  **Create a New Web Service:** On the Render dashboard, create a new "Web Service" and connect it to your GitHub repository.
3.  **Automatic Configuration:** Render will automatically detect the `render.yaml` file in your repository. This file configures everything for you:
    *   It builds the Docker image from your `Dockerfile`.
    *   It creates a **PostgreSQL database** and automatically injects the `DATABASE_URL`.
    *   It generates a secure `SECRET_KEY` for your production environment.
4.  **Deploy:** Click "Create Web Service" and wait for the deployment to complete.

Your application backend will be live at the URL provided by Render. You can then host the static frontend files on a service like **GitHub Pages** or any static hosting provider, making sure to configure the `API_BASE_URL` in `dashboard.js` to point to your live Render backend URL.