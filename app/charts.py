import plotly.graph_objects as go
import plotly.utils
import json
from app.db_utils import fetch_and_convert_data, fetch_and_convert_historicals
from datetime import datetime, timedelta

def create_gauge_chart():
    our_data = fetch_and_convert_data()
    current_probability = float(our_data[our_data['Is_In_Historical'] == False]['Probability'].sum())
    current_percent = current_probability * 100
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
        plot_bgcolor ='rgba(0,0,0,0)',
        paper_bgcolor = 'rgba(0,0,0,0)',

    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)



from datetime import datetime, timedelta
import json
import plotly.graph_objects as go
import plotly.utils
import pandas as pd

def create_line_chart():
    df = fetch_and_convert_historicals()
    
    # Convert 'Snapshot' from string format to datetime
    df['Snapshot'] = pd.to_datetime(df['Snapshot'], errors='coerce')
    
    # Sort the DataFrame by 'Snapshot'
    df = df.sort_values(by='Snapshot')
    
    # Calculate the date two days ago
    two_days_ago = datetime.now() - timedelta(days=2)
    
    # Filter the DataFrame to only include data from the last two days
    df = df[df['Snapshot'] >= two_days_ago]

    # Create the line trace for Scorigami_Percent over time
    line_trace = go.Scatter(
        x=df['Snapshot'],
        y=df['Scorigami_Percent'],
        mode='lines',
        line=dict(width=2),
        showlegend=False
    )

    layout = go.Layout(
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(
            title='',
            showgrid=False,
            showline=True,
            showticklabels=True,
            linecolor='#34495e',
            tickfont=dict(color='#34495e'),
            tickmode='array',
            tickvals=[two_days_ago, df['Snapshot'].max()],
            ticktext=[two_days_ago.strftime('%Y-%m-%d'), df['Snapshot'].max().strftime('%Y-%m-%d')]
        ),
        yaxis=dict(
            title='%',
            showgrid=False,
            gridcolor='rgba(52, 73, 94, 0.1)',
            showline=False,
            showticklabels=False,
            range=[0, 100],
            linecolor='#34495e',
            tickfont=dict(color='#34495e')
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        dragmode=False,
        showlegend=False,
    )

    config = {
        'displayModeBar': False,
        'scrollZoom': False,
    }

    fig = go.Figure(data=[line_trace], layout=layout)

    return json.dumps({'data': fig.data, 'layout': fig.layout, 'config': config}, cls=plotly.utils.PlotlyJSONEncoder)




