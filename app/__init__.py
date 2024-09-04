from flask import Flask
import os


def create_app():
    app = Flask(__name__)

    # Get the path to the project root directory
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Set the database path
    app.config['DATABASE'] = os.path.join(basedir, 'presidentigami.db')

    print(f"Database path set to: {app.config['DATABASE']}")  # Debug print

    from app import routes
    app.register_blueprint(routes.main)

    return app


# Create the app instance
app = create_app()