# ATVA-4: Multiple (below-average-happiness) voters act strategically simultaneously,
# assuming that nobody else is strategic.
#
# Monte Carlo algorithm:
# - Instead of checking ALL swaps (which is expensive when voters are many),
#   each strategic voter samples a fixed number of random "swap plans" and
#   keeps the plan that maximizes THEIR own happiness (computed on TRUE prefs),
#   under the  assumption that only they vote strategically.
# - Then we apply ALL chosen plans simultaneously and see what happens.

from copy import deepcopy
import random

from strategic_voting import (
    compute_happiness,   # computes happiness based on TRUE preferences and a winner
    _get_voter_pref,     # read a single voter's ballot from the matrix
    _set_voter_pref,     # write a single voter's ballot into the matrix
    _all_single_swaps,   # generate all single-swap neighbors of a ballot
)

# Number of Monte Carlo trials per strategic voter.
# Each trial = generate one random tactical ballot + evaluate outcome/happiness.
MC_TRIALS = 10


def random_pref_by_swaps(voting_situation, voter_index, max_swaps):
    """
    Generates ONE random tactical ballot for a voter by doing #max_swaps(10)
    random single-swaps starting from their current ballot.
    """

    # Start from the voter's current ballot
    current_pref = _get_voter_pref(voting_situation, voter_index)

    # Apply up to #max_swaps(10) random single-swaps
    for _ in range(max_swaps):

        # All ballots reachable by swapping ANY two positions once
        neighbors = _all_single_swaps(current_pref)

        # Randomly move to one of the single-swap neighbors
        current_pref = random.choice(neighbors)

    # After up to max_swaps steps, return the final ballot for this trial
    return current_pref


def best_pref_by_monte_carlo(
    voting_function,
    voting_situation,
    true_situation,
    candidates,
    voters,
    preferences,
    voter_index,
    max_swaps,
    trials,
):
    """
    Monte Carlo manipulation for ONE voter

    1) Compute baseline happiness for this voter under the sincere outcome.
    2) Repeat 'trials' times:
        a) Generate one random tactical ballot (up to #max_swaps random swaps).
        b) Create a copy of the election and change ONLY this voter.
        c) Run election -> trial winner.
        d) Compute happiness on TRUE preferences (true_situation).
        e) Keep the ballot that gives this voter the highest happiness.
    3) Return best tactical ballot found (or original ballot if none improve).
    """



    # Run election honestly
    _, base_winner = voting_function(voting_situation, candidates, voters, preferences)

    # Compute happiness on TRUE preferences
    base_hpv, _ = compute_happiness(true_situation, base_winner, voters, preferences)

    # Start best = baseline (meaning "do nothing" is always an available option)
    best_h = base_hpv[voter_index]
    best_pref = _get_voter_pref(voting_situation, voter_index)

    # Monte Carlo: try random tactical ballots and keep the best
    for _ in range(trials):

        # Generate one random tactical ballot (final ballot after  max_swaps)
        tactical_pref = random_pref_by_swaps(voting_situation, voter_index, max_swaps)

        # Create a trial situation and modify ONLY this voter
        trial = deepcopy(voting_situation)
        _set_voter_pref(trial, voter_index, tactical_pref)

        # Run election with the trial ballot
        _, trial_winner = voting_function(trial, candidates, voters, preferences)

        # Compute happiness based on TRUE preferences for the trial winner
        trial_hpv, _ = compute_happiness(true_situation, trial_winner, voters, preferences)

        # If this voter is happier, remember this ballot
        if trial_hpv[voter_index] > best_h:
            best_h = trial_hpv[voter_index]
            best_pref = tactical_pref

    # Return best found (or original ballot if nothing improved)
    return best_pref, best_h


def strategic_vote_atva4(
    voting_function,
    voting_situation,
    candidates,
    voters,
    preferences,
):
    """
    ATVA-4

    1) Run the election honestly -> original winner.
    2) Compute each voter's happiness (based on TRUE preferences).
    3) Strategic set S = voters with happiness < average happiness.
    4) For each voter in S:
        - assume they are the ONLY strategic voter
        - sample MC_TRIALS random tactical ballots
          (each built by up to floor(m/2) random single swaps, where m = #candidates)
        - pick the tactical ballot that maximizes THEIR happiness
    5) Apply ALL chosen ballots simultaneously.
    6) Rerun election, compute TRUE happiness again.
    7) Among strategic voters S, count: improved / decreased / same.

    """


    # We need it to compute happiness on TRUE preferences even after we manipulate ballots.
    true_situation = deepcopy(voting_situation)

    # Honest outcome (we only care about the winner here, not the scores)
    _, original_winner = voting_function(voting_situation, candidates, voters, preferences)

    # Happiness measured on TRUE preferences 
    original_hpv, original_avg = compute_happiness(true_situation, original_winner, voters, preferences)

    # Pick strategic voters ( below-average hapiness)
    strategic_voters = [i for i in range(voters) if original_hpv[i] < original_avg]

    # Allow up to floor(m/2) swaps 
    # 10 candidates -> max_swaps = 5
    # 3 candidates -> max_swaps = 1
    max_swaps = preferences // 2


    
    chosen_prefs = {}  

    for v in strategic_voters:
        best_pref, _ = best_pref_by_monte_carlo(
            voting_function = voting_function,
            voting_situation = voting_situation,
            true_situation = true_situation,
            candidates = candidates,
            voters = voters,
            preferences = preferences,
            voter_index = v,
            max_swaps = max_swaps,
            trials = MC_TRIALS,
        )
        chosen_prefs[v] = best_pref

    # Apply all chosen ballots at the same time
    new_matrix = deepcopy(voting_situation)
    for v, pref in chosen_prefs.items():
        _set_voter_pref(new_matrix, v, pref)

    # Rerun election after strategic voting
    _, new_winner = voting_function(new_matrix, candidates, voters, preferences)

    # To compare hapiness of original vs new voting situation
    new_hpv, new_avg = compute_happiness(true_situation, new_winner, voters, preferences)

    improved = 0
    decreased = 0
    same = 0

    for v in strategic_voters:
        if new_hpv[v] > original_hpv[v]:
            improved += 1
        elif new_hpv[v] < original_hpv[v]:
            decreased += 1
        else:
            same += 1

    any_ballot_changed = any(
        _get_voter_pref(new_matrix, v) != _get_voter_pref(voting_situation, v)
        for v in strategic_voters
    )

    # ---- 11) Return a structured result object ----
    return {
        # changed = election winner changed OR some strategic voter changed their ballot
        "changed": (new_winner != original_winner) or any_ballot_changed,

        "original_winner": original_winner,
        "original_happiness_per_voter": original_hpv,
        "original_avg_happiness": original_avg,

        "new_winner": new_winner,
        "new_happiness_per_voter": new_hpv,
        "new_avg_happiness": new_avg,
        "new_voting_situation": new_matrix,

        "strategic_voters": strategic_voters,
        "strategic_voters_count": len(strategic_voters),

        "strategic_improved_count": improved,
        "strategic_decreased_count": decreased,
        "strategic_same_count": same,

        "max_swaps_per_strategic_voter": max_swaps,
        "mc_trials_per_strategic_voter": MC_TRIALS,
    }



def print_atva4_results(result, scheme_name):

    from strategic_voting import compute_voting_risk

    print(f"\n{'='*60}")
    print(f"ATVA-4 ANALYSIS: {scheme_name}")
    print(f"{'='*60}")

    print("\nHonest Voting Results:")
    print(f"  Winner: {result['original_winner']}")
    print(f"  Avg Happiness: {result['original_avg_happiness']:.3f}")

    print("\nATVA-4 Results (below-average voters act strategically, myopic):")
    print(f"  New Winner: {result['new_winner']}")
    print(f"  New Avg Happiness: {result['new_avg_happiness']:.3f}")
    print(f"  Change in Avg Happiness: {result['new_avg_happiness'] - result['original_avg_happiness']:.3f}")
    print(compute_voting_risk(result['original_avg_happiness'], result['new_avg_happiness']))

    print("\nStrategic voters summary:")
    print(f"  # Strategic voters (below avg initially): {result['strategic_voters_count']}")
    print(f"  # Improved:  {result['strategic_improved_count']}")
    print(f"  # Decreased: {result['strategic_decreased_count']}")
    print(f"  # Same:      {result['strategic_same_count']}")

    print(f"\n{'='*60}")


