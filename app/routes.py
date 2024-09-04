from flask import Blueprint, render_template, jsonify
from app.charts import create_gauge_chart

main = Blueprint('main', __name__)

@main.route('/')
def index():
    chart_json = create_gauge_chart()
    return render_template('index.html', chart_json=chart_json)


@main.route('/chart-data')
def chart_data():
    chart_json = create_gauge_chart()
    return jsonify(chart_json)