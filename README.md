# Project Vantage: A Web-Based Network Monitoring Dashboard

## Project Overview

Project Vantage is a web application designed to provide a user-friendly dashboard for monitoring network hosts. It features a secure user authentication system and a modular, extensible architecture for adding new monitoring tools. The frontend is a modern, responsive application built with Next.js and Tailwind CSS, while the backend is powered by a Python Flask server with a persistent PostgreSQL database (with a fallback to SQLite).

## Features

### Frontend
*   **Modern UI:** A responsive and interactive user interface built with Next.js and styled with Tailwind CSS.
*   **Component-Based Architecture:** Utilizes React and Radix UI for a modular and maintainable component structure.
*   **User Authentication Pages:** Dedicated and styled pages for user registration and login.
*   **Interactive Forms:** Client-side JavaScript handles form submissions asynchronously, providing real-time feedback without page reloads.
*   **Dashboard:** A secure page accessible only after login, designed to host monitoring widgets.
*   **Monitoring Tools:** Includes Ping, Port Scan, and Traceroute utilities.
*   **Logout Functionality:** A logout button on the dashboard to end the user session.

### Backend
*   **RESTful API:** A set of API endpoints to handle user authentication and monitoring tasks.
    *   `POST /api/signup`: Handles new user registration with password hashing.
    *   `POST /api/login`: Authenticates users against the database.
    *   `POST /api/logout`: Clears the user session.
    *   `GET /api/check_session`: Checks if a user is logged in.
    *   `POST /api/ping`: Executes a ping to a target host.
    *   `POST /api/port_scan`: Scans a specific port on a target host.
    *   `POST /api/traceroute`: Performs a traceroute to a target host.
*   **Database:** Utilizes a PostgreSQL database via Flask-SQLAlchemy for user data, with SQLite as a fallback for local development.
*   **Password Security:** Passwords are securely hashed using Flask-Bcrypt.
*   **Rate Limiting:** Implemented using Flask-Limiter to prevent abuse.
*   **CORS Configuration:** Enabled to allow cross-origin requests from the frontend.
*   **Production-Ready Setup:** Includes `gunicorn` for deployment.

---

## Technical Stack

*   **Frontend:** Next.js (React), Tailwind CSS, Radix UI
*   **Backend:** Python 3, Flask
*   **Database:** PostgreSQL (primary), SQLite (fallback)
*   **Libraries/Extensions:** Flask-Bcrypt, Flask-Cors, Flask-Limiter, Flask-SQLAlchemy, Gunicorn, pythonping

---

## Project Setup and Installation

### Prerequisites
*   Python 3.8+
*   `pip` (Python package installer)
*   Node.js and `npm` (or `yarn`/`pnpm`)

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/asoraledecnal/project-vantage.git
    cd project-vantage
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
    *   **Initialize the Database:**
        ```bash
        export FLASK_APP=app.py # (Use 'set FLASK_APP=app.py' in Windows CMD)
        flask shell
        ```
        In the Python shell (`>>>`), run:
        ```python
        from app import db
        db.create_all()
        exit()
        ```

3.  **Set Up the Frontend:**
    *   **Install Node.js Dependencies:**
        ```bash
        npm install
        ```

### Running the Application

1.  **Run the Backend Development Server:**
    ```bash
    flask run
    ```
    The backend will be running on `http://127.0.0.1:5000`. Keep this terminal open.

2.  **Run the Frontend Development Server:**
    In a separate terminal, run:
    ```bash
    npm run dev
    ```
    The frontend will be running on `http://localhost:3000`.

---

## Deployment Strategy

### Backend Deployment (e.g., on Render)
1.  Ensure all code is pushed to a GitHub repository.
2.  Create a new "Web Service" on Render and connect it to the repository.
3.  Render can use the `render.yaml` file to configure the service.

### Frontend Deployment (e.g., on Vercel or Netlify)
1.  The frontend is a Next.js application and can be deployed to any platform that supports Next.js, such as Vercel (recommended) or Netlify.
2.  Connect your repository to the hosting provider.
3.  Before deploying, ensure the backend URL in your frontend code points to the public URL of your deployed backend.