# module for computing strategic voting options
# we first run the election honestly to get the TVA winner
# we then compute each voter's happinness based on their true preferences
# then, starting with the least happy voter, we try all possible strategic voting swaps
# if any swap improves the voter's personal happiness, we apply it
# this process is iterated until we find a strategic voter or exhaust all voters

from copy import deepcopy


# voting risk: If the average happiness decreases after strategic voting, we consider it a risk.
# if the average happiness increases or stays the same, we consider it no risk.
def compute_voting_risk(average_happiness_before, average_happiness_after):     
    diff = average_happiness_after - average_happiness_before

    if diff > 0:
        return f"No tactical voting risk, happiness increased by {diff:.3f}"
    elif diff == 0:
        return f"No tactical voting risk, happiness remained the same ({average_happiness_before:.3f})"
    else:
        return f"Tactical voting risk, happiness decreased by {abs(diff):.3f}"

# compute each voter's happiness based on true preferences
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
    # extract one voter's preference list from the voting situation matrix
    prefs = []
    for row in voting_situation:
        prefs.append(row[voter_index])
    return prefs


def _set_voter_pref(voting_situation, voter_index, pref_list):
    # update one voter's preference list in the voting situation matrix
    for r in range(len(pref_list)):
        voting_situation[r][voter_index] = pref_list[r]



def _all_strategic_manipulations(pref_list):
    # generate the following strategic voting options:
    # 1. single swaps between any 2 positions
    # 2. move any candidate to the top to boost
    # 3. move any candidate to the bottom to bury
    out = []
    m = len(pref_list)
    
    # single swaps
    for i in range(m - 1):
        for j in range(i + 1, m):
            temp = pref_list[:]
            temp[i], temp[j] = temp[j], temp[i]
            out.append(temp)
    
    # boost to top
    for i in range(1, m):  # skip i=0 (already at top)
        temp = pref_list[:]
        candidate = temp.pop(i)  
        temp.insert(0, candidate)  
        out.append(temp)
    
    # bury to bottom
    for i in range(m - 1):  # skip i=m-1 (already at bottom)
        temp = pref_list[:]
        candidate = temp.pop(i) 
        temp.append(candidate) 
        out.append(temp)
    
    return out


def strategic_vote(voting_function, voting_situation, candidates, voters, preferences):
    true_situation = deepcopy(voting_situation)

    # voting_function returns scores,winner but we only care about the winner here
    _, original_winner = voting_function(voting_situation, candidates, voters, preferences)

    # happiness measured on TRUE preferences
    original_hpv, original_avg = compute_happiness(true_situation, original_winner, voters, preferences)


    # order and pick the least-happy voter
    # for tie-breaks: higher voter index first
    order = list(range(voters))
    order.sort(key=lambda i: (original_hpv[i], -i))

    best_result = None 

    for v in order:

        original_pref = _get_voter_pref(voting_situation, v)
        baseline_v_happy = original_hpv[v]

        best_tactical_pref = None
        best_trial_winner = None
        best_trial_hpv = None
        best_trial_avg = None
        best_v_happy = baseline_v_happy

        for tactical_pref in _all_strategic_manipulations(original_pref):

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

            # build the new voting situation and apply the best swap we found for this voter
            new_matrix = deepcopy(voting_situation)
            _set_voter_pref(new_matrix, v, best_tactical_pref)

            # save best result 
            best_result = (
                new_matrix,
                best_trial_winner,
                best_trial_hpv,
                best_trial_avg,
                v,
                best_v_happy
            )
            break

    if best_result is None:
        return {
            "changed": False,  
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