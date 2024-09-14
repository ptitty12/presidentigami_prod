from flask import Blueprint, render_template, jsonify
from app.charts import create_gauge_chart

main = Blueprint('main', __name__)

# Initialize the chart data
latest_chart_json = create_gauge_chart()

@main.route('/')
def index():
    return render_template('index.html', chart_json=latest_chart_json)

@main.route('/update_chart', methods=['POST'])
def update_chart():
    global latest_chart_json
    latest_chart_json = create_gauge_chart()
    print("Chart updated")
    return "",204