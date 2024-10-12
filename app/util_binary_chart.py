import pandas as pd
import ast
import plotly.graph_objects as go
import numpy as np
import os
from app.db_utils import fetch_and_convert_data
def update_grid_chartz():
    print(f"Current working directory: {os.getcwd()}")

    # Define the base directory (assuming the script is in the app folder)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Base directory: {base_dir}")

    # Load and Prepare Data
    outcomes = pd.read_csv(r"app/db_csv/all_possible_outcomes.csv")
    full_range = pd.DataFrame({'Loser': range(0, 270)})
    full_range['Winner'] = 538 - full_range['Loser']
    inputed_outcomes = pd.merge(full_range, outcomes, how='left', on=['Loser', 'Winner'])
    inputed_outcomes['Num_Ways'] = inputed_outcomes['Num_Ways'].fillna(1)

    historical_outcomes = pd.read_csv(r"app/db_csv/historic_outcomes.csv")

    # Function to convert string representation of a list to an actual list
    def convert_to_list(electoral_votes):
        if isinstance(electoral_votes, str):
            return ast.literal_eval(electoral_votes)
        return electoral_votes

    # Function to process the 'Election_Data' and extract 'Candidate' from it
    def process_election_data(election_info):
        if isinstance(election_info, str):
            foo = ast.literal_eval(election_info)
            foo = foo['Candidate']
            foo = ','.join(foo)
            foo = foo.replace(',Other: See Election Facts Below','')
            return foo
        election_info = ','.join(election_info)
        foo = election_info.replace(',Other: See Election Facts Below','')
        return foo

    # Apply the conversion to the 'Electoral_Votes' column
    historical_outcomes['Electoral_Votes'] = historical_outcomes['Electoral_Votes'].apply(convert_to_list)

    # Apply the processing to the 'Election_Data' column
    historical_outcomes['Election_Data'] = historical_outcomes['Election_Data'].apply(process_election_data)

    # Function to extract Winner and Loser, and check if their sum equals 538
    def extract_winner_loser(row):
        sorted_votes = sorted(row['Electoral_Votes'], reverse=True)
        winner = sorted_votes[0]
        loser = sorted_votes[1] if len(sorted_votes) > 1 else 0
        return pd.Series({
            'Winner': winner,
            'Loser': loser,
            '538': winner + loser == 538
        })

    # Apply the function to each row
    historical_outcomes[['Winner', 'Loser', '538']] = historical_outcomes.apply(extract_winner_loser, axis=1)

    # Sort by Winner, Loser, and Election to ensure correct data ordering
    sorted_df = historical_outcomes.sort_values(['Winner', 'Loser', 'Election'], ascending=[True, True, False])

    # Group by Winner and Loser and count occurrences
    counts = historical_outcomes.groupby(['Winner', 'Loser']).size().reset_index(name='CountHappened')

    # Get the row with the max Election for each Winner and Loser
    max_election_df = sorted_df.drop_duplicates(subset=['Winner', 'Loser'], keep='first')

    # Merge the counts with the max election data
    last_seen = max_election_df.merge(counts, on=['Winner', 'Loser'])

    # Rename columns for clarity
    last_seen = last_seen[['Winner', 'Loser', 'Election', 'Election_Data', 'CountHappened']]
    last_seen.columns = ['Winner', 'Loser', 'LastTime', 'Election_Data', 'CountHappened']

    prod_outcomes = inputed_outcomes.merge(last_seen, how='left', on=['Winner', 'Loser'])

    # Rename columns for clarity
    outcome_df = prod_outcomes.rename(columns={'Loser': 'Loser_Votes', 'Winner': 'Winner_Votes'})

    # Define color mapping
    def get_color(row):
        num_ways = row['Num_Ways']
        count_happened = row['CountHappened']

        if num_ways == 0:
            return 'orange' if pd.notnull(count_happened) and count_happened > 0 else '#404040'  # Darker grey
        elif count_happened == 1:
            return '#90EE90'  # Light Green
        elif count_happened == 2:
            return '#006400'  # Dark Green
        else:
            return 'rgba(0,0,0,0)'  # Transparent instead of white

    outcome_df['Color'] = outcome_df.apply(get_color, axis=1)

    # Get the current outcomes data frame from our database
    import_current_outcomes = fetch_and_convert_data()

    # Convert 'Votes_List' from list to tuple
    import_current_outcomes['Votes_List_Tuple'] = import_current_outcomes['Votes_List'].apply(tuple)

    # Now perform the grouping operation
    probability_df = pd.DataFrame(import_current_outcomes.groupby('Votes_List_Tuple').size()).reset_index()
    probability_df.columns = ['Votes_List_Tuple', 'Probability']

    # Convert back to list for consistency with the rest of your code
    probability_df['Votes_List'] = probability_df['Votes_List_Tuple'].apply(list)

    # Extract Winner and Loser votes
    probability_df['Winner_Votes'] = probability_df['Votes_List'].apply(lambda x: max(x))
    probability_df['Loser_Votes'] = probability_df['Votes_List'].apply(lambda x: min(x))

    # Drop the temporary column
    probability_df = probability_df.drop('Votes_List_Tuple', axis=1)

    # Merge probability data with outcome_df
    outcome_df = outcome_df.merge(probability_df[['Winner_Votes', 'Loser_Votes', 'Probability']], 
                                on=['Winner_Votes', 'Loser_Votes'], 
                                how='left')

    # Normalize probabilities
    max_probability = outcome_df['Probability'].max()
    outcome_df['Normalized_Probability'] = outcome_df['Probability'] / max_probability

    # Assign grid positions with snaking pattern
    grid_size = int(np.ceil(np.sqrt(len(outcome_df))))
    outcome_df['Row'] = outcome_df.index // grid_size
    outcome_df['Col'] = outcome_df.apply(lambda row: row.name % grid_size if row['Row'] % 2 == 0 else (grid_size - 1) - (row.name % grid_size), axis=1)

    # Create Plotly figure
    fig = go.Figure()

    # Function to get color based on probability
    def get_probability_color(probability):
        if pd.isnull(probability):
            return 'rgba(0,0,0,0)'  # Transparent for no data
        return f'rgba(0, 0, 255, {probability})'  # Blue with opacity based on probability

    # Add rectangles for each outcome (Scorigami view)
    scorigami_traces = []
    for _, row in outcome_df.iterrows():
        color = row['Color']
        
        times_occurred = int(row['CountHappened']) if pd.notnull(row['CountHappened']) else 0
        last_occurrence = int(row['LastTime']) if pd.notnull(row['LastTime']) else 'Never'
        
        if color == '#404040':
            hover_text = "This outcome is not possible with the current electoral college"
        elif color == 'orange':
            hover_text = (
                f"This result is not currently possible<br>though did occur prior<br> to the 2000 Electoral College change<br>"
                f"Times Occurred: {times_occurred}<br>"
                f"Last Occurrence: {last_occurrence}")
        else:
            hover_text = f"Times Occurred: {times_occurred}<br>Last Occurrence: {last_occurrence}"

        # Add Election_Data if available
        if pd.notnull(row['Election_Data']):
            hover_text += f"<br>Between: {row['Election_Data']}"

        trace = go.Scatter(
            x=[row['Col'], row['Col'] + 1, row['Col'] + 1, row['Col'], row['Col']],
            y=[row['Row'], row['Row'], row['Row'] + 1, row['Row'] + 1, row['Row']],
            fill="toself",
            fillcolor=color,
            line=dict(color='black'),
            mode='lines',
            hoverinfo='text',
            text=hover_text,
            showlegend=False,
            hoverlabel=dict(
                font=dict(size=12 if color == 'orange' else 14)  # 2 points smaller for orange
            ),
            visible=True
        )
        scorigami_traces.append(trace)
        fig.add_trace(trace)

        # Add text labels
        fig.add_annotation(
            x=row['Col'] + 0.5,
            y=row['Row'] + 0.5,
            text=f"{row['Winner_Votes']}<br>{row['Loser_Votes']}",
            showarrow=False,
            font=dict(
                color='white' if color in ['#404040', 'orange', '#006400'] else 'black',
                size=8
            )
        )

    # Add rectangles for each outcome (Probability view)
    probability_traces = []
    for _, row in outcome_df.iterrows():
        color = get_probability_color(row['Normalized_Probability'])
        
        hover_text = f"Probability: {row['Probability']:.2f}" if pd.notnull(row['Probability']) else "No probability data"

        trace = go.Scatter(
            x=[row['Col'], row['Col'] + 1, row['Col'] + 1, row['Col'], row['Col']],
            y=[row['Row'], row['Row'], row['Row'] + 1, row['Row'] + 1, row['Row']],
            fill="toself",
            fillcolor=color,
            line=dict(color='black'),
            mode='lines',
            hoverinfo='skip',
            text=hover_text,
            showlegend=False,
            visible=False
        )
        probability_traces.append(trace)
        fig.add_trace(trace)

    fig.update_layout(
        width=880,
        height=750,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=50, b=0),
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                active=0,
                x=0.5,  # Center horizontally
                y=1.15,  # Adjust this value to position vertically
                xanchor="center",  # Anchor point for horizontal centering
                yanchor="top",  # Anchor point for vertical positioning
                buttons=list([
                    dict(label="Show Scorigamis",
                        method="update",
                        args=[{"visible": [True]*len(scorigami_traces) + [False]*len(probability_traces)}]),
                    dict(label="Show Probabilities",
                        method="update",
                        args=[{"visible": [False]*len(scorigami_traces) + [True]*len(probability_traces)}]),
                ]),
            )
        ]
    )

    fig.update_layout(
        modebar_remove=[
            'zoom', 'pan', 'select', 'zoomIn', 'zoomOut', 'autoScale', 'resetScale',
            'toImage', 'sendDataToCloud', 'toggleHover', 'resetViews', 'toggleSpikelines',
            'hoverClosestCartesian', 'hoverCompareCartesian'
        ],
        dragmode=False
    )

    # Generate the plot HTML
    config = {'displayModeBar': False, 'showTips': False}
    plot_html = fig.to_html(include_plotlyjs=True, full_html=False, config=config)

    # Create the full HTML content with responsive tooltip logic
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Electoral Outcomes Grid</title>
        <style>
            body {{ margin: 0; padding: 0; }}
            #plotly-div {{ width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        <div id="plotly-div">
            {plot_html}
        </div>
        <script>
            function adjustTooltipSize() {{
                var tooltips = document.querySelectorAll('.hoverlayer .hovertext');
                var screenWidth = window.innerWidth;

                tooltips.forEach(function(tooltip) {{
                    if (screenWidth <= 768) {{  // Mobile devices
                        tooltip.style.fontSize = '10px';  // Smaller font size for mobile
                        tooltip.style.width = '150px';   // Narrower width for mobile
                    }} else {{
                        tooltip.style.fontSize = '14px';  // Default font size for larger screens
                        tooltip.style.width = 'auto';    // Default width for larger screens
                    }}
                }});
            }}

            // Run on page load
            window.addEventListener('load', adjustTooltipSize);

            // Run on window resize
            window.addEventListener('resize', adjustTooltipSize);

            // Run periodically to catch any dynamically created tooltips
            setInterval(adjustTooltipSize, 1000);
        </script>
    </body>
    </html>
    """

    # Assuming this script is in the 'app' directory, we'll go up one level to the main directory
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Construct the path to the /static directory
    static_dir = os.path.join(main_dir, "static")

    # Ensure the static directory exists
    os.makedirs(static_dir, exist_ok=True)

    # Construct the full file path
    file_path = os.path.join(static_dir, "electoral_outcomes_grid.html")

    # Save the full HTML content to a file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"File saved successfully at: {file_path}")

update_grid_chartz()