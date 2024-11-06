import pandas as pd
import numpy as np
from decimal import Decimal, getcontext
import time
from itertools import product

# generate election outcomes

# Set precision for Decimal calculations
getcontext().prec = 50


def generate_election_scenarios(df, certainty_threshold=Decimal('0.87')):
    start_time = time.time()

    # Convert Odds to Decimal for precision
    df['Odds'] = df['Odds'].apply(Decimal)

    df['Electoral_Votes'] = pd.to_numeric(df['Electoral_Votes'], errors='coerce')


    # Step 1: Separate certain and uncertain states
    certain_states = df[(df['Odds'] >= certainty_threshold) | (df['Odds'] <= (1 - certainty_threshold))].copy()
    uncertain_states = df[(df['Odds'] < certainty_threshold) & (df['Odds'] > (1 - certainty_threshold))].copy()

    # Assign parties to certain states
    certain_states['Outcome'] = np.where(certain_states['Odds'] >= Decimal('0.5'), 'Republican', 'Democrat')

    # Calculate certain electoral votes
    certain_rep_votes = certain_states[certain_states['Outcome'] == 'Republican']['Electoral_Votes'].sum()
    certain_dem_votes = certain_states[certain_states['Outcome'] == 'Democrat']['Electoral_Votes'].sum()

    # Convert certain states to dictionary for consistent scenario inclusion
    certain_state_dict = dict(zip(certain_states['State'], certain_states['Outcome']))

    # Step 2: Generate all possible combinations for uncertain states
    uncertain_states_list = uncertain_states['State'].tolist()
    combinations = list(product(['Republican', 'Democrat'], repeat=len(uncertain_states_list)))

    # Step 3 & 4: Calculate probability, electoral votes, and determine winner for each scenario
    scenarios = []
    for combo in combinations:
        scenario_uncertain = uncertain_states.copy()
        scenario_uncertain['Outcome'] = combo

        # Calculate probability (only for uncertain states)
        prob = Decimal(1)  # Start with a probability of 1 (neutral element for multiplication)
        for index, row in scenario_uncertain.iterrows():
            if row['Outcome'] == 'Republican':
                prob *= row['Odds']
            else:
                prob *= (Decimal('1') - row['Odds'])

        # Calculate electoral votes (including certain states)
        rep_votes = certain_rep_votes + scenario_uncertain[scenario_uncertain['Outcome'] == 'Republican'][
            'Electoral_Votes'].sum()
        dem_votes = certain_dem_votes + scenario_uncertain[scenario_uncertain['Outcome'] == 'Democrat'][
            'Electoral_Votes'].sum()

        # Determine winner
        if rep_votes > dem_votes:
            winner = 'Republican'
        elif dem_votes > rep_votes:
            winner = 'Democrat'
        else:
            winner = 'Tie'

        # Combine certain and uncertain states into a single scenario dictionary
        scenario_dict = {**certain_state_dict, **dict(zip(scenario_uncertain['State'], scenario_uncertain['Outcome']))}

        scenarios.append({
            'Scenario': scenario_dict,
            'Probability': prob,
            'Republican_Votes': rep_votes,
            'Democrat_Votes': dem_votes,
            'Winner': winner
        })

    results = pd.DataFrame(scenarios)

    # Normalize probabilities, don't think this really matters since we are no longer using the aggregate probability but we will keep it since I think it helps with grabbing probz later
    total_prob = sum(results['Probability'])
    results['Probability'] = results['Probability'].apply(lambda x: x / total_prob)

    end_time = time.time()
    print(f"\nExecution time: {end_time - start_time:.2f} seconds")

    return results


def check_in_historical_list(votes_list, historical_list):
    # Convert votes_list to a set for easier subset checking
    votes_set = set(votes_list)
    return any(votes_set.issubset(h) for h in historical_list)



