import plotly.graph_objects as go
import plotly.utils
import json
from app.db_utils import fetch_and_convert_data, fetch_and_convert_historicals

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



def create_line_chart():
    df = fetch_and_convert_historicals()
    # Create the line trace for Scorigami_Percent over time
    line_trace = go.Scatter(
        x=df['Snapshot'],  # Your timestamp or date column
        y=df['Scorigami_Percent'],  # Your percentage column
        mode='lines',  # 'lines' for a continuous line plot
        line=dict(width=2),  # Adjust line thickness as needed
        showlegend=False
    )

    layout = go.Layout(
        margin=dict(l=40, r=20, t=30, b=40),  # Increased left and bottom margins
        xaxis=dict(
            title='',
            showgrid=False,
            showline=True,
            showticklabels=True
        ),
        yaxis=dict(
            title='Scorigami Percent',
            showgrid=True,
            showline=True,
            showticklabels=True,
            range=[0, 100]  # Set y-axis range from 0 to 100
        ),
        template='plotly_white',
        dragmode=False,  # Disable drag mode
        showlegend=False,  # Hide legend
    )

    config = {
        'displayModeBar': False,  # Hide the mode bar with zoom options etc.
        'scrollZoom': False,  # Disable scroll zoom
    }

    fig = go.Figure(data=[line_trace], layout=layout)
    return json.dumps({'data': fig.data, 'layout': fig.layout, 'config': config}, cls=plotly.utils.PlotlyJSONEncoder)


