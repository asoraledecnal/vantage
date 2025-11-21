# Project Vantage: A Web-Based Network Monitoring Dashboard

## Project Overview

Project Vantage is a web application designed to provide a user-friendly dashboard for monitoring network hosts. It features a secure user authentication system and a modular, extensible architecture for adding new monitoring tools. The frontend is built with standard HTML, CSS, and JavaScript, while the backend is powered by a Python Flask server with a persistent SQLite database for user data.

## Features

### Frontend
*   **Homepage:** A modern, responsive landing page providing an overview of the project.
*   **User Authentication Pages:** Dedicated and styled pages for user registration (`signup.html`) and login (`login.html`).
*   **Interactive Forms:** Client-side JavaScript handles form submissions asynchronously, providing real-time feedback without page reloads.
*   **Dashboard:** A secure page accessible only after login, designed to host monitoring widgets.
*   **Ping Utility:** The first monitoring widget, allowing users to ping a specified host and view live status and output.
*   **Logout Functionality:** A logout button on the dashboard to end the user session.

### Backend
*   **RESTful API:** A set of API endpoints to handle user authentication and monitoring tasks.
    *   `POST /api/signup`: Handles new user registration with password hashing.
    *   `POST /api/login`: Authenticates users against the database.
    *   `POST /api/ping`: Executes a system-level ping command to a target host and returns the result.
*   **Persistent Database:** Utilizes an SQLite database via the Flask-SQLAlchemy extension to permanently store user credentials.
*   **Password Security:** Passwords are never stored in plain text. They are securely hashed using `werkzeug.security`.
*   **CORS Configuration:** Enabled to allow cross-origin requests from the frontend to the backend server.
*   **Production-Ready Setup:** Includes `gunicorn` in its dependencies, a production-grade WSGI server suitable for deployment.

---

## Technical Stack

*   **Frontend:** HTML5, CSS3, JavaScript (ES6+)
*   **Backend:** Python 3, Flask
*   **Database:** SQLite
*   **Libraries/Extensions:** Flask-Cors, Flask-SQLAlchemy, Werkzeug, Gunicorn

---

## Project Setup and Installation

### Prerequisites
*   Python 3.8+
*   `pip` (Python package installer)

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/project-vantage.git
    cd project-vantage
    ```

2.  **Set Up the Backend:**
    Navigate to the backend directory to set up the environment and dependencies.
    ```bash
    cd backend
    ```

3.  **Create and Activate a Virtual Environment:**
    *   **Windows (PowerShell):**
        ```powershell
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        ```
    *   **macOS / Linux (Bash):-**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Initialize the Database:**
    From the `backend` directory:
    ```bash
    # Set the Flask app environment variable
    export FLASK_APP=app.py # (Use 'set FLASK_APP=app.py' in Windows CMD)
    
    # Run the shell
    flask shell
    ```
    In the Python shell (`>>>`), run:
    ```python
    from app import db
    db.create_all()
    exit()
    ```
    This will create a `database.db` file inside the `backend` directory.

6.  **Run the Backend Development Server:**
    ```bash
    flask run --debug
    ```
    The backend will be running on `http://127.0.0.1:5000`. Keep this terminal open.

7.  **Launch the Frontend:**
    In a separate terminal, navigate to the `frontend` directory and open the `index.html` file in a web browser.
    ```bash
    cd ../frontend
    # open index.html
    ```

---

## Deployment Strategy

### Backend Deployment (e.g., on Render)
1.  Ensure all code is pushed to a GitHub repository.
2.  Create a new "Web Service" on Render and connect it to the repository.
3.  Render will automatically detect the `render.yaml` file and configure the service. It uses the `backend/Dockerfile` to build and deploy the application.

### Frontend Deployment (e.g., on GitHub Pages or Netlify)
1.  The static files in the `frontend` directory can be served by any static hosting provider.
2.  Point the hosting service to the `frontend` directory as the root/publish directory.
3.  **Crucially**, before deploying, ensure the `BACKEND_URL` constant in `frontend/dashboard.js` and other JS files is updated from the local `http://127.0.0.1:5000` to the public backend URL provided by Render.
