from flask import Blueprint, render_template, jsonify, send_file
from app.charts import create_gauge_chart, create_line_chart
from flask import send_file, render_template, current_app as app
import os
from app.tasks import fetch_election_map, fetch_election_bar

main = Blueprint('main', __name__)

# Initialize the chart data
latest_chart_json = create_gauge_chart()
latest_line_chart_json = create_line_chart()
@main.route('/')
def index():
    gauge_chart_json = create_gauge_chart()
    line_chart_json = create_line_chart()
    return render_template('index.html', chart_json=gauge_chart_json, line_chart_json=line_chart_json)

@main.route('/update_chart', methods=['POST'])
def update_chart():
    global latest_chart_json
    latest_chart_json = create_gauge_chart()
    print("Chart updated")
    return "",204


@main.route('/map/<string:scorigami>/<int:index>')
def update_election_map(scorigami, index):
    is_scorigami = scorigami == 'scorigami'
    image_path = fetch_election_map(is_scorigami, index)
    parent_dir = os.path.dirname(app.root_path)
    full_image_path = os.path.join(parent_dir, image_path)
    return send_file(full_image_path, mimetype='image/png')

@main.route('/bar/<string:scorigami>/<int:index>')
def update_election_bar(scorigami, index):
    is_scorigami = scorigami == 'scorigami'
    image_path = fetch_election_bar(is_scorigami, index)
    parent_dir = os.path.dirname(app.root_path)
    full_image_path = os.path.join(parent_dir, image_path)
    return send_file(full_image_path, mimetype='image/png')
