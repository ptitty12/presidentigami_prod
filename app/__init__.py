from flask import Flask
import os
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.polymarket import update_presidential_odds_database
from app.tasks import update_data, process_and_upload_historicals





def create_app():
    app = Flask(__name__, static_folder='../static', static_url_path='/static')

    # Get the path to the project root directory
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Set the database path
    app.config['DATABASE'] = os.path.join(basedir, 'presidentigami.db')


    def update_chart():
        with app.app_context():
            from app.routes import update_chart as route_update_chart
            route_update_chart()
            print("Chart updated")

    # Wait for the initialization to complete before setting up schedulers

    # Initialize the scheduler
    scheduler = BackgroundScheduler()

    # Schedule the database update task (every 15 minutes)
    scheduler.add_job(func=update_presidential_odds_database, trigger="interval", minutes=30)

    # Schedule the data update task (every 17 minutes)
    scheduler.add_job(func=update_data, trigger="interval", minutes=35)

    # Schedule the chart update task (every 20 minutes)
    scheduler.add_job(func=update_chart, trigger="interval", minutes=40)

    # Schedule process_and_upload_historicals to run once a day
    scheduler.add_job(func=process_and_upload_historicals, trigger="interval", days=1)

    scheduler.start()

    # Import routes here to avoid circular imports
    from app import routes
    app.register_blueprint(routes.main)

    return app

# Create the app instance
app = create_app()