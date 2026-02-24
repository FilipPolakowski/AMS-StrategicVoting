

""" 
1) Run the election honestly to get the winner. --> (TVA.py)
2) Compute each voter's happiness (based on TRUE preferences). """ # --> def compute_happiness() line 32
"""3) Pick the least-happy voter (tie-break: higher voter index first)."""# --> order.sort(key=lambda i: (original_hpv[i], -i)) line 94
"""4) Let that voter try simple manipulations (all single swaps of two ranks).""" #--> def _all_single_swaps() line 66
""" - Re-run the election for each manipulation (using the manipulated ballots).
   - If the voter's happiness improves (measured on TRUE preferences), remember the best one."""
"""5) If no manipulation improves happiness, move to the next least-happy voter.""" #--> for v in order: line 98 and the loop continues to the next voter if no improvement is found.
"""6) Go to 4) until we find a strategic voter or exhaust all voters. """
"""7) If not strategic voters are found, we consider it a "success" that no one can improve their happiness by voting strategically.""" #--> if best_result is None: return {"changed": False, ...} line 144



from copy import deepcopy


# Voting risk: If the average happiness decreases after strategic voting, we consider it a risk.
# If the average happiness increases or stays the same, we consider it no risk.
def compute_voting_risk(average_happiness_before, average_happiness_after):     
    diff = average_happiness_after - average_happiness_before

    if diff > 0:
        return f"No tactical voting risk, happiness increased by {diff:.3f}"
    elif diff == 0:
        return f"No tactical voting risk, happiness remained the same ({average_happiness_before:.3f})"
    else:
        return f"Tactical voting risk, happiness decreased by {abs(diff):.3f}"

# Compute each voter's happiness (based on TRUE preferences).
def compute_happiness(voting_situation, winner, voters, preferences):           
    happiness_per_voter = []
    total_happiness = 0

    for v in range(voters):
        voter_happiness = 0
        for r in range(preferences):
            if voting_situation[r][v] == winner:
                voter_happiness = 1 / (r + 1)
                break
        happiness_per_voter.append(voter_happiness)
        total_happiness += voter_happiness

    average_happiness = total_happiness / voters if voters else 0
    return happiness_per_voter, average_happiness


def _get_voter_pref(voting_situation, voter_index):
    prefs = []
    for row in voting_situation:
        prefs.append(row[voter_index])
    return prefs


def _set_voter_pref(voting_situation, voter_index, pref_list):
    for r in range(len(pref_list)):
        voting_situation[r][voter_index] = pref_list[r]

"""
Voter swaps two positions at at time and does
 all the possible swaps (e.g. ABC -> BAC, CBA, ACB, etc.)
 to find a better outcome for themselves.
"""

def _all_single_swaps(pref_list):                                               # 
    out = []
    m = len(pref_list)
    for i in range(m - 1):
        for j in range(i + 1, m):
            temp = pref_list[:]  # copy
            temp[i], temp[j] = temp[j], temp[i]
            out.append(temp)
    return out


def strategic_vote(voting_function, voting_situation, candidates, voters, preferences):

    #  Keep an unchangable list of the original voting situation(TRUE preferences)
    #  We will use this to compute happiness based on TRUE preferences even after
    #  we manipulate the voting situation for strategic voting.
    true_situation = deepcopy(voting_situation)

    # voting_function returns scores,winner but we only care about the winner here
    _, original_winner = voting_function(voting_situation, candidates, voters, preferences)

    # Happiness measured on TRUE preferences
    original_hpv, original_avg = compute_happiness(true_situation, original_winner, voters, preferences)


    
    order = list(range(voters))
    # Pick the least-happy voter (tie-break: higher voter index first).
    order.sort(key=lambda i: (original_hpv[i], -i))

    best_result = None  # (new_matrix, new_winner, new_hpv(true), new_avg(true), voter_index, voter_new_hi)

    for v in order:

        original_pref = _get_voter_pref(voting_situation, v)
        baseline_v_happy = original_hpv[v]

        best_tactical_pref = None
        best_trial_winner = None
        best_trial_hpv = None
        best_trial_avg = None
        best_v_happy = baseline_v_happy

        for tactical_pref in _all_single_swaps(original_pref):

            trial = deepcopy(voting_situation)
            _set_voter_pref(trial, v, tactical_pref)

            _, trial_winner = voting_function(trial, candidates, voters, preferences)
            trial_hpv, trial_avg = compute_happiness(true_situation, trial_winner, voters, preferences)

            if trial_hpv[v] > best_v_happy:
                best_v_happy = trial_hpv[v]
                best_tactical_pref = tactical_pref
                best_trial_winner = trial_winner
                best_trial_hpv = trial_hpv
                best_trial_avg = trial_avg

        if best_tactical_pref is not None:

            # Build the manipulated voting situation and apply the best swap we found for this voter
            new_matrix = deepcopy(voting_situation)
            _set_voter_pref(new_matrix, v, best_tactical_pref)

            # Save best result 
            best_result = (
                new_matrix,          # new voting situation after manipulation
                best_trial_winner,   # winner after manipulation
                best_trial_hpv,      # happiness per voter (computed on TRUE preferences)
                best_trial_avg,      # average happiness (computed on TRUE preferences)
                v,                   # strategic voter index
                best_v_happy         # strategic voter's new happiness
            )
            break


    

    if best_result is None:
        return {
            "changed": False,  # No change, but we consider it a "success" that no one can improve their happiness by voting strategically
            "original_winner": original_winner,
            "original_happiness_per_voter": original_hpv,
            "original_avg_happiness": original_avg,

            "new_winner": original_winner,
            "new_happiness_per_voter": original_hpv,
            "new_avg_happiness": original_avg,
            "new_voting_situation": voting_situation,

            "strategic_voter": None,
            "strategic_voter_original_happiness": None,
            "strategic_voter_new_happiness": None
        }

    new_matrix, new_winner, new_hpv, new_avg, v, v_new_hi = best_result

    return {
        "changed": True,
        "original_winner": original_winner,
        "original_happiness_per_voter": original_hpv,
        "original_avg_happiness": original_avg,

        "new_winner": new_winner,
        "new_happiness_per_voter": new_hpv,
        "new_avg_happiness": new_avg,
        "new_voting_situation": new_matrix,

        "strategic_voter": v,
        "strategic_voter_original_happiness": original_hpv[v],
        "strategic_voter_new_happiness": v_new_hi,
    }