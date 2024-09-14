from flask import Flask
import os
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.polymarket import update_presidential_odds_database
from app.tasks import update_data


def create_app():
    app = Flask(__name__)

    # Get the path to the project root directory
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Set the database path
    app.config['DATABASE'] = os.path.join(basedir, 'presidentigami.db')

    print(f"Database path set to: {app.config['DATABASE']}")  # Debug print

    def update_chart():
        with app.app_context():
            from app.routes import update_chart as route_update_chart
            route_update_chart()
            print("Chart updated")

    # Initialize the scheduler
    scheduler = BackgroundScheduler()



    # Schedule the database update task (every 5 minutes)
    scheduler.add_job(func=update_presidential_odds_database, trigger="interval", minutes=15)

    scheduler.add_job(func=update_data, trigger="interval", minutes=17)



    # Schedule the chart update task (every 10 minutes)
    scheduler.add_job(func=update_chart, trigger="interval", minutes=20)

    scheduler.start()

    # Import routes here to avoid circular imports
    from app import routes
    app.register_blueprint(routes.main)

    return app


# Create the app instance
app = create_app()