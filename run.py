"""
Entry point for the Vantage Flask application.

This script imports the application factory `create_app` from the `project`
package, creates an instance of the application, and runs the Flask
development server.

To run the application:
    - Ensure all dependencies from requirements.txt are installed.
    - Ensure the .env file with all required environment variables is present.
    - Execute `python run.py` in the terminal.
"""

from project import create_app

# Create an application instance using the factory
app = create_app()

if __name__ == '__main__':
    # Runs the Flask development server
    # Debug mode should be False in a production environment
    app.run(debug=True)
