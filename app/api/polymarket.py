import requests
import ast
import pandas as pd
import sqlite3
from app.db_utils import upload_odds_snapshot
import time


import requests
import ast
import pandas as pd
import sqlite3
import time

# List of specific event IDs to fetch
all_56_states = [
    '903665', '903679', '903683', '903666', '903667', '903674', '903650',
    '903658', '903636', '10170', '903669', '903639', '903660', '903649',
    '903637', '903646', '903640', '903648', '903655', '903641', '903643',
    '903664', '10169', '903684', '903631', '903633', '903677', '903635',
    '903657', '903681', '903656', '903654', '10172', '903662', '10382',
    '903642', '903663', '10173', '10164', '10175', '903653', '903672',
    '903682', '903651', '903661', '903676', '903673', '903659', '903638',
    '903671', '903634', '903652', '903668', '903670', '10166', '10174',
    '903636', '903648', '903665', '903637', '903650', '903667', '903683'
]

def update_presidential_odds_database():
    def get_all_events(event_ids):
        state_events = []
        for event_id in event_ids:
            url = f"https://gamma-api.polymarket.com/events/{event_id}"
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise an error for bad status codes
                event = response.json()
                state_events.append(event)
                print(f"Successfully fetched event {event_id}")
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred for event {event_id}: {http_err}")
            except Exception as err:
                print(f"Other error occurred for event {event_id}: {err}")
        print(f"Total events fetched: {len(state_events)}")
        return state_events

    def extract_state_name(full_name):
        # Clean and extract the state name from the event title
        name = full_name.replace("Will a Republican win", "")
        name = name.replace("US Presidential Election?", "")
        name = name.replace("Presidential Election?", "")
        name = name.replace("in the 2024", "")
        name = name.replace("?", "")
        
        # Handle congressional districts
        if '2nd congressional district' in name:
            name = name.replace('2nd congressional district', "(2)")
            name = name.replace("'s", "")
        if '3rd congressional district' in name:
            name = name.replace('3rd congressional district', "(3)")
            name = name.replace("'s", "")
        if '1st congressional district' in name:
            name = name.replace('1st congressional district', "(1)")
            name = name.replace("'s", "")
        
        return name.strip()

    # Fetch events using specific event IDs
    events = get_all_events(all_56_states)
    
    # Process events into a dictionary for easier access
    state_events = {event['id']: event for event in events}

    hold_republican_odds = {}
    for event in state_events.values():
        for market in event.get('markets', []):
            question = market.get('question', '')
            if 'Republican' in question:
                hold_republican_odds[question] = market.get('outcomePrices', '{}')

    # Safely evaluate the outcomePrices string to a dictionary or list and extract the first price
    processed_data = {}
    for question, prices_str in hold_republican_odds.items():
        try:
            # Attempt to evaluate the string
            prices_data = ast.literal_eval(prices_str)
            
            # Handle if prices_data is a dict
            if isinstance(prices_data, dict):
                if prices_data:
                    first_price = list(prices_data.values())[0]
                else:
                    print(f"No prices available for question '{question}'.")
                    continue  # Skip if dict is empty
            # Handle if prices_data is a list
            elif isinstance(prices_data, list):
                if prices_data:
                    first_price = prices_data[0]
                else:
                    print(f"No prices available for question '{question}'.")
                    continue  # Skip if list is empty
            else:
                print(f"Unexpected data type for prices of question '{question}': {type(prices_data)}")
                continue  # Skip unexpected data types
            
            # Assign the first price to processed_data
            processed_data[question] = first_price

        except (ValueError, SyntaxError) as e:
            print(f"Error parsing prices for question '{question}': {e}")
        except Exception as e:
            print(f"Unexpected error for question '{question}': {e}")

    # Create a DataFrame from the processed data
    df = pd.DataFrame(list(processed_data.items()), columns=['Question', 'Odds Yes'])
    df['State'] = df['Question'].apply(extract_state_name)

    # Clean the DataFrame
    df.drop(columns='Question', inplace=True)
    current_odds = df[~df['State'].str.contains('Will any other')]
    
    # Convert 'Odds Yes' to float with error handling
    try:
        current_odds['Odds Yes'] = current_odds['Odds Yes'].astype(float)
    except ValueError as e:
        print(f"Error converting 'Odds Yes' to float: {e}")
        # Optionally, handle or clean the data here
        return  # Exit the function if conversion fails

    print(f"Number of current odds entries: {len(current_odds)}")
    
    # Check if all 56 states have been processed
    if len(current_odds) == 56:
        #print(current_odds)
        retries = 5
        while retries > 0:
            try:
                with sqlite3.connect('presidentigami.db', timeout=10) as conn:
                    cursor = conn.cursor()

                    # Create the table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS current_odds (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            State TEXT,
                            Odds DECIMAL(12,6)
                        )
                    ''')

                    # Clear existing data
                    cursor.execute('DELETE FROM current_odds')

                    # Insert new data
                    data_to_insert = current_odds[['State', 'Odds Yes']].values.tolist()
                    cursor.executemany('''
                        INSERT INTO current_odds (State, Odds)
                        VALUES (?, ?)
                    ''', data_to_insert)

                    # Commit the transaction
                    conn.commit()

                    print("Data deleted and new data inserted successfully.")
                break  # Exit the retry loop on success
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    print("Database is locked, retrying...")
                    retries -= 1
                    time.sleep(2)  # Wait before retrying
                else:
                    raise  # Re-raise if it's a different operational error

        if retries == 0:
            print("Failed to update database after multiple attempts due to locking issues.")
        else:
            print("Database updated successfully.")
            upload_odds_snapshot(current_odds)
