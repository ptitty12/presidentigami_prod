import plotly.graph_objects as go
import plotly.utils
import json
from app.db_utils import fetch_and_convert_data

def create_gauge_chart():
    our_data = fetch_and_convert_data()
    current_probability = float(our_data[our_data['Is_In_Historical'] == False]['Probability'].sum())
    current_percent = current_probability * 100
    print(current_percent)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_percent,
        number={
            'suffix': '%',
            'valueformat': '.2f',
                },
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': current_percent
            }
        }
    ))

    fig.update_layout(
        title={'text': "Current Chance", 'x': 0.5, 'xanchor': 'center'},
        font={'color': "black", 'family': "Arial"},
        margin=dict(l=20, r=20, t=40, b=20),
        autosize=True,
        height=500,
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)



