import os
import sys
import sqlite3
from decimal import Decimal

project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import app
from app.tasks import update_data
from app.api.polymarket import update_presidential_odds_database  # Import the new function


def test_database_connection():
    try:
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            tables = ['Current_Odds', 'Historical_Results', 'Votes_Per_State', 'Outcomes']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"Table '{table}' has {count} rows.")
    except sqlite3.Error as e:
        print(f"Error connecting to the database: {e}")


def test_update_odds_and_data():
    try:
        with app.app_context():
            print("Updating presidential odds database...")
            update_presidential_odds_database()
            print("Presidential odds updated successfully.")

            print("\nRunning update_data function...")
            outcomes_df = update_data()

        print(f"Successfully ran update_data. Resulting DataFrame shape: {outcomes_df.shape}")
        print("\nFirst few rows of the outcomes:")
        print(outcomes_df.head())

        total_probability = outcomes_df['Probability'].sum()
        print(f"\nTotal probability: {total_probability}")
        if abs(Decimal(str(total_probability)) - Decimal('1')) < Decimal('0.01'):
            print("Probabilities sum to approximately 1, which is correct.")
        else:
            print("Warning: Probabilities do not sum to 1. This might indicate an issue.")

        print("\nChecking for unexpected values...")
        print(f"Unique winners: {outcomes_df['Winner'].unique()}")
        print(
            f"Range of republican votes: {outcomes_df['Republican_Votes'].min()} to {outcomes_df['Republican_Votes'].max()}")
        print(
            f"Range of democrat votes: {outcomes_df['Democrat_Votes'].min()} to {outcomes_df['Democrat_Votes'].max()}")
    except Exception as e:
        print(f"Error in update process: {str(e)}")


if __name__ == "__main__":
    test_database_connection()
    test_update_odds_and_data()