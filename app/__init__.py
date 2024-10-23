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

    # Task execution tracking
    task_status = {
        'last_run': {},
        'last_success': {},
        'last_duration': {},
        'errors': {}
    }

    def with_timeout(timeout_seconds=300):
        """Decorator to add timeout to functions"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, *args, **kwargs)
                    try:
                        return future.result(timeout=timeout_seconds)
                    except TimeoutError:
                        raise TimeoutError(f"{func.__name__} timed out after {timeout_seconds} seconds")
            return wrapper
        return decorator

    def log_execution(task_name):
        """Decorator to log task execution details"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                task_status['last_run'][task_name] = datetime.now()
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    task_status['last_success'][task_name] = datetime.now()
                    task_status['last_duration'][task_name] = duration
                    print(f"{task_name} completed successfully in {duration:.2f} seconds")
                    return result
                except Exception as e:
                    task_status['errors'][task_name] = str(e)
                    print(f"Error in {task_name}: {e}")
                    raise
            return wrapper
        return decorator

    @with_timeout(30)  # .5 minutes timeout
    @log_execution("update_chart")
    def update_chart():
        with app.app_context():
            from app.routes import update_chart as route_update_chart
            route_update_chart()

    @with_timeout(600)  # 10 minutes timeout
    @log_execution("update_presidential_odds")
    def update_presidential_odds():
        update_presidential_odds_database()

    @with_timeout(300)  # 5 minutes timeout
    @log_execution("update_grid_charts")
    def update_grid_charts():
        update_grid_chartz()

    @with_timeout(300)  # 5 minutes timeout
    @log_execution("update_data")
    def update_app_data():
        update_data()

    def update_sequence():
        """Run all updates in sequence with independent error handling"""
        tasks = [
            ('update_presidential_odds', update_presidential_odds),
            ('update_grid_charts', update_grid_charts),
            ('update_app_data', update_app_data),
            ('update_chart', update_chart)
        ]

        for task_name, task_func in tasks:
            try:
                task_func()
            except TimeoutError:
                print(f"{task_name} timed out, moving to next task")
            except Exception as e:
                print(f"Error in {task_name}: {e}, moving to next task")

    @app.route('/task-status')
    def get_task_status():
        """Endpoint to monitor task execution status"""
        return task_status

    # Initialize scheduler
    scheduler = BackgroundScheduler()
    
    # Add jobs with fixed schedules
    scheduler.add_job(update_sequence, 
                     trigger="interval", 
                     minutes=30, 
                     id="update_sequence",
                     max_instances=1,  # Prevent overlapping
                     coalesce=True)    # Combine missed runs
    
    scheduler.add_job(shit_post, 
                     trigger="interval", 
                     days=1, 
                     id="shit_post",
                     max_instances=1,
                     coalesce=True)
    
    scheduler.start()

    # Import routes here to avoid circular imports
    from app import routes
    app.register_blueprint(routes.main)
    
    return app

app = create_app()
