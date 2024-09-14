import sqlite3
import pandas as pd
import ast
import json
from decimal import Decimal
from app.utils import generate_election_scenarios, check_in_historical_list

def update_data():
    """This grabs the df that is most current via odds and states than generates the elections"""
    # Connect to SQLite database and read data
    with sqlite3.connect('presidentigami.db') as conn:
        current_core = pd.read_sql_query("SELECT * FROM odds_and_votes", conn)
        historical_games = pd.read_sql_query("SELECT * FROM historical_results", conn)

    current_core['Current Favorite'] = current_core['Odds'].apply(lambda x: 'Republican' if x >= 0.5 else 'Democrat')
    historical_list = list(historical_games['Electoral_Votes'].apply(ast.literal_eval))

    # Generate election scenarios
    outcomes = generate_election_scenarios(current_core)
    outcomes['Votes_List'] = outcomes.apply(lambda row: sorted([row['Republican_Votes'], row['Democrat_Votes']], reverse=True), axis=1)
    outcomes['Is_In_Historical'] = outcomes['Votes_List'].apply(lambda x: check_in_historical_list(x, historical_list))

    # Convert dictionaries and Decimal to strings
    outcomes['Scenario'] = outcomes['Scenario'].apply(json.dumps)
    outcomes['Votes_List'] = outcomes['Votes_List'].apply(json.dumps)
    outcomes['Probability'] = outcomes['Probability'].astype(str)

    # Upload to SQLite database
    with sqlite3.connect('presidentigami.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM outcomes;")
        outcomes.to_sql('outcomes', conn, if_exists='append', index=False)

    # Convert back to original types for return value
    outcomes['Scenario'] = outcomes['Scenario'].apply(json.loads)
    outcomes['Votes_List'] = outcomes['Votes_List'].apply(json.loads)
    outcomes['Probability'] = outcomes['Probability'].apply(Decimal)

    return outcomes


