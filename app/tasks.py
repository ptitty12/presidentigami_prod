import sqlite3
import ast
import json
from decimal import Decimal
from app.utils import generate_election_scenarios, check_in_historical_list
from app.db_utils import fetch_and_convert_data

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import pandas as pd
import time
from PIL import Image
import os
import hashlib
import logging
import tweepy
from PIL import Image
import io
import datetime
import time
import os
import functools
from dotenv import load_dotenv


# Configure logging (if not already configured elsewhere)
logging.basicConfig(filename='function_execution_times.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def log_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logging.info(f"{func.__name__} took {execution_time:.4f} seconds to execute.")
        return result
    return wrapper

def update_data():
    """Grabs most current view ---  odds and states---- than generates the elections"""
    with sqlite3.connect('presidentigami.db') as conn:
        current_core = pd.read_sql_query("SELECT * FROM odds_and_votes", conn)
        historical_games = pd.read_sql_query("SELECT * FROM historical_results", conn)

    current_core['Current Favorite'] = current_core['Odds'].apply(lambda x: 'Republican' if x >= 0.5 else 'Democrat') #yeah yeah 0.5 goes in favor to repubs but they never exists in the data
    historical_list = list(historical_games['Electoral_Votes'].apply(ast.literal_eval))

    # Generate election scenarios
    outcomes = generate_election_scenarios(current_core)
    outcomes['Votes_List'] = outcomes.apply(lambda row: sorted([row['Republican_Votes'], row['Democrat_Votes']], reverse=True), axis=1)
    outcomes['Is_In_Historical'] = outcomes['Votes_List'].apply(lambda x: check_in_historical_list(x, historical_list))

    # Convert dictionaries and Decimal to strings
    outcomes['Scenario'] = outcomes['Scenario'].apply(json.dumps)
    outcomes['Votes_List'] = outcomes['Votes_List'].apply(json.dumps)
    outcomes['Probability'] = outcomes['Probability'].astype(str)

    # Upload to SQLite
    with sqlite3.connect('presidentigami.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM outcomes;")
        outcomes.to_sql('outcomes', conn, if_exists='append', index=False)
        #commits most current outcomes, which is the result dict winner votes loser votes etc

    # Convert back to original types for return value
    outcomes['Scenario'] = outcomes['Scenario'].apply(json.loads)
    outcomes['Votes_List'] = outcomes['Votes_List'].apply(json.loads)
    outcomes['Probability'] = outcomes['Probability'].apply(Decimal)

    return outcomes


def fetch_election_bar(scorigami, index=0):
    """Take scorigami true or false and get us the bar chart path as .png, extremely unintutive bolean scorigami since we use 'Is_In_Historical' as the comparison point"""
    if scorigami == True:
        bolean_scorigami = False
    else:
        bolean_scorigami = True
    outcomes = fetch_and_convert_data()
    outcomes = outcomes[outcomes['Is_In_Historical']== bolean_scorigami]
    outcome_dict = outcomes.sort_values(by='Probability',ascending=False).iloc[index]
    democrat_votes = outcome_dict['Democrat_Votes']
    republican_votes = outcome_dict['Republican_Votes']
    result_string = f"static/bars/D{democrat_votes}_R{republican_votes}.png"
    return result_string


def fetch_election_map(scorigami, index=0):
    """Take in a dict which is the dict cell of the outcome of the election and return a map, see unintutive note above function"""
    if scorigami == True:
        bolean_scorigami = False
    else:
        bolean_scorigami = True
    outcomes = fetch_and_convert_data()
    outcomes = outcomes[outcomes['Is_In_Historical']== bolean_scorigami]
    outcome_dict = outcomes.sort_values(by='Probability',ascending=False).iloc[index]['Scenario']

    join_outcome_df = pd.DataFrame(outcome_dict, index=[0]).T.reset_index().rename(
        columns={'index': 'CorrectedState', 0: 'Winner'})

    votes_dict = {'Republican': '#D22532', 'Democrat': '#244999'}
    join_outcome_df['Vote'] = join_outcome_df['Winner'].map(votes_dict)

    def generate_filename(state_colors, scorigami):
        # Convert the concatenation of state ids and winners into a hash so that we can use it as a filename
        concatenated_string = ''.join(state_colors['id'] + state_colors['Winner'].str[0])
        hashed_string = hashlib.md5(concatenated_string.encode()).hexdigest()  # Using MD5 hash for simplicity
        filename = f'static/maps/{hashed_string}_{scorigami}'
        return filename

    static_nate_silver = pd.DataFrame({
        'id': ['01', '02', '04', '05', '06', '08', '09', '10', '12', '13', '15', '16', '17', '18', '19', '20', '21',
               '22', '23', '24',
               '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41',
               '42', '44', '45',
               '46', '47', '48', '49', '50', '51', '53', '54', '55', '56', 'sm_11', 'sp_M3', 'sp_M4', 'sp_N3', 'sp_N4',
               'sp_N5',
               'sp_MX', 'sp_NX'],
        'State': ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY',
                  'LA', 'ME', 'MD',
                  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR',
                  'PA', 'RI', 'SC',
                  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC', 'ME (1)', 'ME (2)', 'NE (1)',
                  'NE (2)', 'NE (3)', 'ME St', 'NE St'],
        'CorrectedState': ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut',
                           'Delaware', 'Florida',
                           'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky',
                           'Louisiana', 'Maine',
                           'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
                           'Nebraska',
                           'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina',
                           'North Dakota', 'Ohio',
                           'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
                           'Tennessee', 'Texas',
                           'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming',
                           'Washington DC',
                           'Maine (1)', 'Maine (2)', 'Nebraska (1)', 'Nebraska (2)', 'Nebraska (3)', 'Maine',
                           'Nebraska']
    })

    state_colors = pd.merge(join_outcome_df, static_nate_silver, on='CorrectedState')
    state_colors.sort_values(by='id', ascending=False, inplace=True)

    save_as = generate_filename(state_colors,scorigami)
    output_path = f'{save_as}.png'
    #check if exists


    if os.path.exists(f'{save_as}.png'):
        return output_path
    #hopefully the below never happens in production, lol
    else:

        blank_url = r"https://www.270towin.com/maps/jP4ke"

        # Set up Selenium WebDriver with headless mode
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')  # Ignore SSL errors
        options.add_argument("--headless")  # Headless mode for VPS
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1318")  # This ensures the browser window is large enough

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get(blank_url)  # Replace with the actual URL
        time.sleep(5)  # Allow the page to load

        # Hide the ads or unwanted elements using JavaScript
        ad_elements = ['fs-sticky-footer','ad_position_box']  # Replace with actual ad IDs or class names
        for ad_id in ad_elements:
            try:
                driver.execute_script(f"document.getElementById('{ad_id}').style.display='none';")
            except Exception as e:
                print(f"Didn't find {e}")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'map')))


        # Get the height
        viewport_height = driver.execute_script("return window.innerHeight")
        print(f"Viewport height: {viewport_height} pixels")

        # Scroll by a fraction of the page
        scroll_by = int(viewport_height / 15)

        driver.execute_script(f"window.scrollBy(0, {scroll_by});")

        # Function to simulate clicks or change colors based on the type of element (special case or regular state)
        def interact_with_state(state_id, color):
            try:
                # Check if the state ID is a special case (starts with 'sm_' or 'sp_')
                if state_id.startswith('sm_') or state_id.startswith('sp_'):
                    # Use ID-based XPath for the <div> or <tr> element
                    xpath = f"//*[@id='{state_id}']"

                    # Wait for the element to be present
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))

                    # Locate the element
                    state_element = driver.find_element(By.XPATH, xpath)

                    # Determine how many clicks to simulate based on the color
                    if color == '#D22532':  # If the color is #D22532, click once
                        state_element.click()
                        print(f"Single click on {state_id} (color: {color})")
                    else:  # If the color is anything else, click twice
                        state_element.click()  # First click
                        time.sleep(0.5)  # Small delay between clicks
                        state_element.click()  # Second click
                        print(f"Double click on {state_id} (color: {color})")

                else:  # Handle regular states (as paths in the SVG)
                    # Use XPath to locate the path element by its ID
                    xpath = f"//*[@id='{state_id}']"

                    # Wait for the specific path element to be available
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))

                    # Find the element and change the fill color
                    state_element = driver.find_element(By.XPATH, xpath)
                    driver.execute_script("arguments[0].setAttribute('fill', arguments[1]);", state_element, color)
                    print(f"Color changed for state {state_id} (color: {color})")

            except Exception as e:
                print(f"Error interacting with state {state_id}: {e}")

        for idx, row in state_colors.iterrows():
            state_id = row['id']
            color = row['Vote']  # Use the 'Vote' column as the color

            interact_with_state(state_id, color)

        time.sleep(5)

        # Now capture the screenshots of 'map_tools' and 'map' after ads are hidden
        def capture_element_screenshot(element_id, filename):
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, element_id)))
                element = driver.find_element(By.ID, element_id)
                element.screenshot(filename)
                print(f"Screenshot saved as {filename}")
            except Exception as e:
                print(f"Error capturing screenshot for {element_id}: {e}")

        capture_element_screenshot('split_votes_wrapper', f'map_tools_screenshot_{scorigami}.png')
        capture_element_screenshot('map', f'map_screenshot_{scorigami}.png')

        def combine_images_horizontally(image1_path, image2_path, output_path):
            # Open the two images
            image1 = Image.open(image1_path)
            image2 = Image.open(image2_path)

            # Ensure both images have the same height by resizing the second image if necessary
            height = max(image1.height, image2.height)

            # Create a new image with the combined width and the max height, using a white background
            combined_width = image1.width + image2.width
            combined_image = Image.new('RGB', (combined_width, height), color='white')

            # Paste the first image on the left
            combined_image.paste(image1, (0, 0))

            # Paste the second image on the right
            combined_image.paste(image2, (image1.width, 0))

            # Save the combined image
            combined_image.save(output_path)
            print(f"Combined image saved as {output_path}")

        # Paths to your screenshots
        image1_path = f'map_tools_screenshot_{scorigami}.png'
        image2_path = f'map_screenshot_{scorigami}.png'

        # Combine the two images
        combine_images_horizontally(image1_path, image2_path, output_path)

        try:
            os.remove(image1_path)
            print(f"{image1_path} has been deleted.")

            os.remove(image2_path)
            print(f"{image2_path} has been deleted.")
        except OSError as e:
            print(f"Error: {e.strerror}")

        time.sleep(2)
        # Close the WebDriver session
        driver.quit()

        return output_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@log_execution_time
def process_and_upload_historicals():
    """Processes current odds and snapshots to generate and upload historical outcomes."""
    try:
        # Connect to SQLite database with a timeout to handle locked database scenarios, testing this out, probably needed elsewhere
        with sqlite3.connect('presidentigami.db', timeout=10) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_percents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Snapshot TEXT UNIQUE,
                    Scorigami_Percent DECIMAL(12,6)
                )
            ''')

            # Fetch records that haven't been processed yet via the left join being empty, BI skills finally being used
            not_processed_yet = pd.read_sql_query("""
                    SELECT r.Snapshot, r.Odds, r.State, v.Votes as Electoral_Votes
                    FROM historical_odds r
                    LEFT JOIN votes_per_state v 
                        ON r.State = v.State
                    WHERE DATE(r.Snapshot) NOT IN (
                        SELECT DATE(l.Snapshot)
                        FROM historical_percents l
                    );

            """, conn)

            if not not_processed_yet.empty:
                historical_games = pd.read_sql_query("SELECT * FROM historical_results", conn)
                historical_list = list(historical_games['Electoral_Votes'].apply(ast.literal_eval))

                for snapshot in not_processed_yet['Snapshot'].unique():
                    temp_df = not_processed_yet[not_processed_yet['Snapshot'] == snapshot].copy()

                    # Determine the current favorite based on Odds
                    temp_df['Current Favorite'] = temp_df['Odds'].apply(
                        lambda x: 'Republican' if x >= 0.5 else 'Democrat')

                    # Generate election scenarios
                    outcomes = generate_election_scenarios(temp_df)
                    outcomes['Votes_List'] = outcomes.apply(
                        lambda row: sorted([row['Republican_Votes'], row['Democrat_Votes']], reverse=True), axis=1)
                    outcomes['Is_In_Historical'] = outcomes['Votes_List'].apply(
                        lambda x: check_in_historical_list(x, historical_list))

                    # Convert dictionaries and Decimal to strings
                    outcomes['Scenario'] = outcomes['Scenario'].apply(json.dumps)
                    outcomes['Votes_List'] = outcomes['Votes_List'].apply(json.dumps)

                    # Calculate the current percentage
                    current_probability = float(outcomes[outcomes['Is_In_Historical'] == False]['Probability'].sum())
                    current_percent = current_probability * 100

                    # Insert new data into historical_percents
                    cursor.execute('''
                        INSERT INTO historical_percents (Snapshot, Scorigami_Percent)
                        VALUES (?, ?)
                    ''', (snapshot, current_percent))

                    # Commit after each snapshot
                    conn.commit()

                logging.info("Calculated and uploaded historical percentages successfully.")
            else:
                logging.info("No new snapshots to process.")

    except sqlite3.OperationalError as e:
        if 'database is locked' in str(e).lower():
            logging.error("Database is locked. Exiting the function gracefully.")
            return  # Exit the function without continuing
        else:
            logging.exception("An unexpected SQLite operational error occurred.")
            raise  # Re-raise the exception for any other OperationalError
    except Exception as e:
        logging.exception("An unexpected error occurred during processing.")
        raise  # Re-raise the exception for any other unexpected errors


# fuck it dude we just adding everything to tasks
def shit_post():
    # Calculate the current scorigami percent
    our_data = fetch_and_convert_data()
    current_probability = float(our_data[our_data['Is_In_Historical'] == False]['Probability'].sum())
    current_percent = current_probability * 100

    # Load Twitter credentials from environment variables
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
    consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
    consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    
    
    client = tweepy.Client(
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        access_token=access_token, access_token_secret=access_token_secret
    )
    
    def get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret) -> tweepy.API:
        """Get twitter conn 1.1"""
    
        auth = tweepy.OAuth1UserHandler(api_key, api_secret)
        auth.set_access_token(
            access_token,
            access_token_secret,
        )
        return tweepy.API(auth)
    
    client_v1 = get_twitter_conn_v1(consumer_key, consumer_secret, access_token, access_token_secret)
    
    
    
    def take_screenshot(url, class_name):
        # Set up Selenium WebDriver with headless mode
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1318")
    
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        try:
            # Navigate to the URL
            driver.get(url)
            time.sleep(5)  # Allow the page to load
            
            # Wait for the elements to be present and select the first one
            elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, class_name))
            )
            
            # Get the first element with the specified class name
            element = elements[0]
            
            # Get the location and size of the element
            location = element.location
            size = element.size
            
            # Take a screenshot of the entire page
            png = driver.get_screenshot_as_png()
            
            # Use PIL to open the screenshot
            im = Image.open(io.BytesIO(png))
            
            # Define the region to crop
            left = location['x']
            top = location['y']
            right = location['x'] + size['width']
            bottom = location['y'] + size['height']
            
            # Crop the image
            im = im.crop((left, top, right, bottom))
            
            # Generate filename with current date
            filename = datetime.datetime.now().strftime("%Y%m%d") + ".png"
            
            # Save the cropped image
            im.save(filename)
            print(f"Screenshot saved as {filename}")
            
        finally:
            driver.quit()


    
    # Usage
    url = "https://presidentigami.com"
    class_name = "chart-map-pair"
    take_screenshot(url, class_name)
    
    
    
    
    media_path = datetime.datetime.now().strftime("%Y%m%d") + ".png"
    media = client_v1.media_upload(filename=media_path)
    media_id = media.media_id
    
    now = datetime.datetime.now()
    
    # election day
    target_date = datetime.datetime(now.year, 11, 5)
    
    # dif in days
    days_difference = (target_date - now).days
    response = client.create_tweet(
        text= f"{days_difference} days until election \n\nCurrent Scorigami Percent: {current_percent:.2f}%\n\nMost Likely Scorigami: ",
        media_ids  = [media_id]
    )
    print(f"https://twitter.com/user/status/{response.data['id']}")



