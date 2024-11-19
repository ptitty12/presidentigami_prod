from flask import Flask
import os
import time
from datetime import datetime
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.polymarket import update_presidential_odds_database
from app.tasks import update_data, process_and_upload_historicals, shit_post
from app.util_binary_chart import update_grid_chartz




def create_app():
    app = Flask(__name__, static_folder='../static', static_url_path='/static')
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['DATABASE'] = os.path.join(basedir, 'presidentigami.db')



    # Import routes here to avoid circular imports
    from app import routes
    app.register_blueprint(routes.main)
    
    return app

app = create_app()
