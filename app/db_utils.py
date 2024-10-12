
import ast
from datetime import datetime
import sqlite3
import pandas as pd
from decimal import Decimal
import json
# this will be how we interact with sql table


def upload_to_sql(outcomes):
    with sqlite3.connect('presidentigami.db') as conn:
        cursor = conn.cursor()

        # Delete existing data
        delete_query = "DELETE FROM outcomes;"
        cursor.execute(delete_query)
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





def fetch_and_convert_data():
    """This gives us the core, processed outcomes df. Has each scenario and probability"""


    # Connect to SQLite database and read data
    with sqlite3.connect('presidentigami.db') as conn:
        df = pd.read_sql_query("SELECT * FROM outcomes", conn)

    # Convert JSON strings back to dictionaries/lists
    df['Scenario'] = df['Scenario'].apply(json.loads)
    df['Votes_List'] = df['Votes_List'].apply(json.loads)

    # Convert 'Probability' column from string back to Decimal to preserve da precision
    df['Probability'] = df['Probability'].apply(Decimal)

    # Return the DataFrame with proper data types
    return df


def upload_odds_snapshot(recently_fetched_presidential_odds):
    """Upload snapshot of oddds"""
    recent_odds = recently_fetched_presidential_odds
    snapshot_time = datetime.now().isoformat()
    with sqlite3.connect('presidentigami.db') as conn:
        cursor = conn.cursor()

        # Insert into Historical_Odds table
        for _, row in recent_odds.iterrows():
            cursor.execute('''
            INSERT INTO historical_odds (State, Odds, Snapshot)
            VALUES (?, ?, ?)
            ''', (row['State'], row['Odds Yes'], snapshot_time))

        conn.commit()

    print("New data inserted successfully into Current_Odds and Historical_Odds.")


def fetch_and_convert_historicals():
    """for line chart"""


    # Connect to SQLite database and read data
    with sqlite3.connect('presidentigami.db') as conn:
        df = pd.read_sql_query("SELECT * FROM historical_percents", conn)

    # Convert JSON strings back to dictionaries/lists
    #df['Snapshot'] = df['Snapshot'].apply(Datetime) idek what this was

    return df