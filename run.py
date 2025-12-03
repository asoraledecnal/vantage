"""
Entry point for the Vantage Flask application.

This script imports the application factory `create_app` from the `project`
package, creates an instance of the application, and runs the Flask
development server.

It also defines a custom CLI command `flask db-init` to initialize the database.
"""
import click
from project import create_app
from project.extensions import db
from project.models import User, Feedback

# Create an application instance using the factory
app = create_app()

@app.cli.command("db-init")
def db_init():
    """Initializes the database by creating all tables."""
    with app.app_context():
        db.create_all()
    click.echo("Database tables created.")

if __name__ == '__main__':
    # Runs the Flask development server
    # Debug mode should be False in a production environment
    app.run(debug=True)
