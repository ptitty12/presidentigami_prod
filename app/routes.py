from flask import Blueprint, render_template, jsonify
from app.charts import create_gauge_chart, create_line_chart
from flask import send_file, render_template, current_app as app
import os
from app.tasks import fetch_election_map

main = Blueprint('main', __name__)

# Initialize the chart data
latest_chart_json = create_gauge_chart()
latest_line_chart_json = create_line_chart()
@main.route('/')
def index():
    gauge_chart_json = create_gauge_chart()
    line_chart_json = create_line_chart()
    print("Gauge Chart JSON:", gauge_chart_json)
    print("Line Chart JSON:", line_chart_json)
    return render_template('index.html', chart_json=gauge_chart_json, line_chart_json=line_chart_json)

@main.route('/update_chart', methods=['POST'])
def update_chart():
    global latest_chart_json
    latest_chart_json = create_gauge_chart()
    print("Chart updated")
    return "",204


@main.route('/map/true')
def update_election_map_true():
    image_path = fetch_election_map(False)

    # Navigate up one directory from the app root to reach the parent directory of 'static'
    parent_dir = os.path.dirname(app.root_path)

    # Join the parent directory with the image_path
    full_image_path = os.path.join(parent_dir, image_path)

    return send_file(full_image_path, mimetype='image/png')

@main.route('/map/false')
def update_election_map_false():
    image_path = fetch_election_map(True)

    # Navigate up one directory from the app root to reach the parent directory of 'static'
    parent_dir = os.path.dirname(app.root_path)

    # Join the parent directory with the image_path
    full_image_path = os.path.join(parent_dir, image_path)

    return send_file(full_image_path, mimetype='image/png')
