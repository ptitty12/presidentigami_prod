from flask import Flask
import os
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.polymarket import update_presidential_odds_database
from app.tasks import update_data, process_and_upload_historicals, shit_post
from app.util_binary_chart import update_grid_chartz




def create_app():
    app = Flask(__name__, static_folder='../static', static_url_path='/static')

    # project root directory
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Set database path
    app.config['DATABASE'] = os.path.join(basedir, 'presidentigami.db')


    def update_chart():
        with app.app_context():
            from app.routes import update_chart as route_update_chart
            route_update_chart()
            print("Chart updated")

    # Initialize scheduler
    scheduler = BackgroundScheduler()

    def update_presidential_odds_database_job():
        update_presidential_odds_database()
        scheduler.add_job(update_grid_chartz_job, trigger="date")

    def update_grid_chartz_job():
        update_grid_chartz()
        scheduler.add_job(update_data_job, trigger="date")

    def update_data_job():
        update_data()
        scheduler.add_job(update_chart_job, trigger="date")

    def update_chart_job():
        update_chart()
        scheduler.add_job(update_presidential_odds_database_job, trigger="interval", minutes=30)

    scheduler.add_job(shit_post, trigger="interval", days=1)
    scheduler.add_job(update_presidential_odds_database_job, trigger="interval", minutes=30)
    scheduler.start()

    # Import routes here to avoid circular imports
    from app import routes
    app.register_blueprint(routes.main)

    return app

app = create_app()