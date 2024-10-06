import pandas as pd
import ast
import plotly.graph_objects as go
import numpy as np
import os

# Load and Prepare Data
outcomes = pd.read_csv(r"db_csv/all_possible_outcomes.csv")
full_range = pd.DataFrame({'Loser': range(0, 270)})
full_range['Winner'] = 538 - full_range['Loser']
inputed_outcomes = pd.merge(full_range, outcomes, how='left', on=['Loser', 'Winner'])
inputed_outcomes['Num_Ways'] = inputed_outcomes['Num_Ways'].fillna(0)

historical_outcomes = pd.read_csv("db_csv/historic_outcomes.csv")

# Function to convert string representation of a list to an actual list
def convert_to_list(electoral_votes):
    if isinstance(electoral_votes, str):
        # Use ast.literal_eval to safely evaluate the string to a list
        return ast.literal_eval(electoral_votes)
    return electoral_votes

# Function to process the 'Election_Data' and extract 'Candidate' from it
def process_election_data(election_info):
    if isinstance(election_info, str):
        foo = ast.literal_eval(election_info)  # Safely evaluate the string to a dictionary
        foo = foo['Candidate']  # Extract the 'Candidate' key from the dictionary
        foo = ','.join(foo)
        foo = foo.replace(',Other: See Election Facts Below','')
        return foo
    election_info = ','.join(election_info)
    foo = election_info.replace(',Other: See Election Facts Below','')
    return foo

    return election_info

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

# Step 1: Sort by Winner, Loser, and Election to ensure correct data ordering
sorted_df = historical_outcomes.sort_values(['Winner', 'Loser', 'Election'], ascending=[True, True, False])

# Step 2: Group by Winner and Loser and count occurrences
# We first count the occurrences to get 'CountHappened' before retrieving max Election
counts = historical_outcomes.groupby(['Winner', 'Loser']).size().reset_index(name='CountHappened')

# Step 3: Get the row with the max Election for each Winner and Loser
# This preserves the Election_Data and other details of the row where Election is max
max_election_df = sorted_df.drop_duplicates(subset=['Winner', 'Loser'], keep='first')

# Step 4: Merge the counts with the max election data
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

# Assign grid positions
grid_size = int(np.ceil(np.sqrt(len(outcome_df))))
outcome_df['Row'] = outcome_df.index // grid_size
outcome_df['Col'] = outcome_df.index % grid_size

# Create Plotly figure
fig = go.Figure()

# Add rectangles for each outcome
for _, row in outcome_df.iterrows():
    color = row['Color']

    times_occurred = int(row['CountHappened']) if pd.notnull(row['CountHappened']) else 0
    last_occurrence = int(row['LastTime']) if pd.notnull(row['LastTime']) else 'Never'

    if color == '#404040':
        hover_text = "This outcome is not possible with the current electoral college"
    elif color == 'orange':
        hover_text = (
            f"This result is not currently possible though did occur prior to the 2000 Electoral College change<br>"
            f"Times Occurred: {times_occurred}<br>"
            f"Last Occurrence: {last_occurrence}")
    else:
        hover_text = f"Times Occurred: {times_occurred}<br>Last Occurrence: {last_occurrence}"

    # Add Election_Data if available
    if pd.notnull(row['Election_Data']):
        hover_text += f"<br>Between: {row['Election_Data']}"

    fig.add_trace(go.Scatter(
        x=[row['Col'], row['Col'] + 1, row['Col'] + 1, row['Col'], row['Col']],
        y=[row['Row'], row['Row'], row['Row'] + 1, row['Row'] + 1, row['Row']],
        fill="toself",
        fillcolor=color,
        line=dict(color='black'),
        mode='lines',
        hoverinfo='text',
        text=hover_text,
        showlegend=False
    ))

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

# Update layout
fig.update_layout(
    width=880,  # Increased from 800 to 880 (10% larger)
    height=750,  # Increased from 800 to 880 (10% larger)
    showlegend=False,
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
    margin=dict(l=0, r=0, t=0, b=0),  # Remove margins
)

fig.update_layout(
    modebar_remove=[
        'zoom', 'pan', 'select', 'zoomIn', 'zoomOut', 'autoScale', 'resetScale',
        'toImage', 'sendDataToCloud', 'toggleHover', 'resetViews', 'toggleSpikelines',
        'hoverClosestCartesian', 'hoverCompareCartesian'
    ],
    dragmode=False
)
# I can't figure this shit out we just doing it manually
# Save the figure as a static HTML file
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(current_dir))
static_dir = os.path.join(project_dir, 'static')

# Ensure the static directory exists
os.makedirs(static_dir, exist_ok=True)

# Define the file path
file_path = os.path.join(static_dir, 'electoral_outcomes_grid.html')

config = {'displayModeBar': False, 'showTips': False}
fig.write_html(r"C:\Users\Patrick Taylor\PycharmProjects\Presidentigami_web\static\electoral_outcomes_grid.html", include_plotlyjs=True, full_html=False, config=config)

print(f"File saved successfully at: {file_path}")

#fig.show()