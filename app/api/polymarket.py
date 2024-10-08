import requests
import ast
import pandas as pd
import sqlite3
from app.db_utils import upload_odds_snapshot


def update_presidential_odds_database(limit=10000):
    def get_all_events(limit=10000):
        all_events = []
        offset = 0
        page_size = 100  # The API seems to return 100 events per request

        while len(all_events) < limit:
            url = f"https://gamma-api.polymarket.com/events?closed=false&limit={page_size}&offset={offset}"
            r = requests.get(url)

            if r.status_code != 200:
                print(f"Error: Received status code {r.status_code}")
                break

            events = r.json()

            if not events:
                break  # No more events to fetch

            all_events.extend(events)

            if len(events) < page_size:
                break  # Last page reached

            offset += len(events)

        return all_events[:limit]  # Trim to the requested limit

    def extract_state_name(full_name):
        # Remove "Presidential Election Winner" from the end
        name = full_name.replace("Will a Republican win", "")
        name = name.replace("US Presidential Election?", "")

        name = name.replace("Presidential Election?", "")
        name = name.replace("in the 2024", "")
        name = name.replace("?", "")
        if '2' in name:
            name = name.replace('2nd congressional district', "(2)")
            name = name.replace("'s", "")
        if '3' in name:
            name = name.replace('3rd congressional district', "(3)")
            name = name.replace("'s", "")

        if '1' in name:
            name = name.replace('1st congressional district', "(1)")
            name = name.replace("'s", "")

        return name.strip()

    # Fetch events
    events = get_all_events(limit)

    # Process events
    state_events = {}
    for event in events:
        if 'Presidential Election Winner' in event['title']:
            state_events[event['id']] = event

    hold_republican_odds = {}
    for event in state_events.values():
        for market in event['markets']:
            if 'Republican' in market['question']:
                hold_republican_odds[market['question']] = market['outcomePrices']

    processed_data = {key: ast.literal_eval(value)[0] for key, value in hold_republican_odds.items()}

    df = pd.DataFrame(list(processed_data.items()), columns=['Question', 'Odds Yes'])
    df['State'] = df['Question'].apply(lambda x: extract_state_name(x))

    df.drop(columns='Question', inplace=True)
    current_odds = df[df['State'].str.contains('Will any other') == False]
    current_odds.loc[:, 'Odds Yes'] = current_odds['Odds Yes'].astype(float)



    # Connect to SQLite database
    conn = sqlite3.connect('presidentigami.db')
    cursor = conn.cursor()

    # Create the current_odds table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS current_odds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        State TEXT,
        Odds DECIMAL(12,6)
    )
    ''')
    conn.commit()

    # Step 1: Delete existing data in the table
    cursor.execute('DELETE FROM current_odds')

    # Step 2: Insert new data from the DataFrame
    for _, row in current_odds.iterrows():
        cursor.execute('''
        INSERT INTO current_odds (State, Odds)
        VALUES (?, ?)
        ''', (
            row['State'],
            row['Odds Yes']
        ))

    # Step 3: Commit the transaction to save changes
    conn.commit()
    print("Data deleted and new data inserted successfully.")

    # Close the connection
    conn.close()

    upload_odds_snapshot(current_odds)
