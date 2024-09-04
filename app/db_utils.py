import sqlite3
import pandas as pd
import ast
from decimal import Decimal
import sqlite3
import pandas as pd
import json
from decimal import Decimal
from flask import current_app
from datetime import datetime
import sqlite3
import pandas as pd
from decimal import Decimal
import json
from flask import current_app
# this will be how we interact with sql table

def upload_to_sql(outcomes):
    with sqlite3.connect('presidentigami.db') as conn:
        cursor = conn.cursor()

        # Delete existing data
        delete_query = "DELETE FROM outcomes;"
        cursor.execute(delete_query)

        # Define the insert query
        insert_query = """
        INSERT INTO outcomes (Scenario, Probability, Republican_votes, Democrat_votes, Winner, Votes_list, Is_In_Historical)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        # Prepare data for insertion
        data_to_insert = [
            (str(row['Scenario']), str(row['Probability']), row['Republican_Votes'], row['Democrat_Votes'], row['Winner'], str(row['Votes_List']), row['Is_In_Historical'])
            for _, row in outcomes.iterrows()
        ]

        # Insert new data into table
        cursor.executemany(insert_query, data_to_insert)

        # Commit changes
        conn.commit()
        print("Data deleted and new data inserted successfully.")


import sqlite3
import pandas as pd
from decimal import Decimal
import json
from flask import current_app
import os


def fetch_and_convert_data():
    """This gives us the core, processed outcomes df"""
    try:
        # Try to get the database path from the app config
        database_path = current_app.config['DATABASE']
    except KeyError:
        # If DATABASE is not in config, use a default path
        base_dir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(base_dir, '..', 'presidentigami.db')

    print(f"Using database path: {database_path}")  # Debug print

    # Connect to SQLite database and read data
    with sqlite3.connect(database_path) as conn:
        df = pd.read_sql_query("SELECT * FROM outcomes", conn)

    # Convert JSON strings back to dictionaries/lists
    df['Scenario'] = df['Scenario'].apply(json.loads)
    df['Votes_List'] = df['Votes_List'].apply(json.loads)

    # Convert 'Probability' column from string back to Decimal
    df['Probability'] = df['Probability'].apply(Decimal)

    # Return the modified DataFrame
    return df


def upload_odds_snapshot(recently_fetched_presidential_odds):
    recent_odds = recently_fetched_presidential_odds
    snapshot_time = datetime.now().isoformat()

    with sqlite3.connect(current_app.config['DATABASE']) as conn:
        cursor = conn.cursor()

        # Insert into Historical_Odds table
        for _, row in recent_odds.iterrows():
            cursor.execute('''
            INSERT INTO historical_odds (State, Odds, Snapshot)
            VALUES (?, ?, ?)
            ''', (row['State'], row['Odds Yes'], snapshot_time))

        conn.commit()

    print("Data deleted and new data inserted successfully into Current_Odds and Historical_Odds.")