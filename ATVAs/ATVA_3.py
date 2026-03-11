# ATVA-3 (intuition-based): One voter (the least-happy under the honest outcome)
# votes "strategically" using a noisy/intuition ballot:
#   - Plurality: keep 1st choice fixed, shuffle the rest.
#   - Other schemes: keep 1st fixed AND keep last fixed, shuffle the middle.
#
# The voter has no perfect knowledge: they do ONE noisy/intuition shuffle and
# submit it (we do not search for the best shuffle).

from copy import deepcopy
import random

from strategic_voting import (
    compute_happiness,   # computes happiness based on TRUE preferences and a winner
    _get_voter_pref,     # read a single voter's ballot from the matrix
    _set_voter_pref,     # write a single voter's ballot into the matrix
)

def _intuition_ballot(pref_list, scheme_id):
    """
    Build one random 'intuition' ballot from a true preference list.

    scheme_id:
      1 = plurality  -> keep first fixed, shuffle the rest
      else          -> keep first and last fixed, shuffle the middle
    """
    m = len(pref_list)
    if m <= 1:
        return pref_list[:]

    if scheme_id == 1:
        first = pref_list[0]
        rest = pref_list[1:].copy()
        random.shuffle(rest)
        return [first] + rest

    # other schemes: keep first and last fixed
    if m <= 2:
        return pref_list[:]

    first = pref_list[0]
    last = pref_list[-1]
    middle = pref_list[1:-1].copy()
    random.shuffle(middle)
    return [first] + middle + [last]


def strategic_vote_atva3(
    voting_function,
    voting_situation,
    candidates,
    voters,
    preferences,
    scheme_id,
):
    """
    ATVA-3 (intuition-based)

    1) Run election honestly -> original winner.
    2) Compute each voter's happiness (TRUE preferences).
    3) Pick the least-happy voter (tie-break: higher index first).
    4) That voter submits ONE intuition shuffle ballot (no search / no perfect knowledge).
    5) Apply it, rerun election, compute TRUE happiness again.
    """
    true_situation = deepcopy(voting_situation)

    _, original_winner = voting_function(voting_situation, candidates, voters, preferences)
    original_hpv, original_avg = compute_happiness(true_situation, original_winner, voters, preferences)

    # least-happy voter, tie-break: higher index first
    order = list(range(voters))
    order.sort(key=lambda i: (original_hpv[i], -i))
    strategic_voter = order[0] if voters else None

    if strategic_voter is None:
        return {
            "changed": False,
            "original_winner": None,
            "original_happiness_per_voter": [],
            "original_avg_happiness": 0.0,
            "new_winner": None,
            "new_happiness_per_voter": [],
            "new_avg_happiness": 0.0,
            "new_voting_situation": voting_situation,
            "strategic_voter": None,
            "strategic_voter_original_happiness": None,
            "strategic_voter_new_happiness": None,
            "intuition_trials": 0,
        }

    # Build ONE intuition ballot and apply it
    true_pref = _get_voter_pref(true_situation, strategic_voter)
    tactical_pref = _intuition_ballot(true_pref, scheme_id=scheme_id)

    new_matrix = deepcopy(voting_situation)
    _set_voter_pref(new_matrix, strategic_voter, tactical_pref)

    _, new_winner = voting_function(new_matrix, candidates, voters, preferences)
    new_hpv, new_avg = compute_happiness(true_situation, new_winner, voters, preferences)

    any_ballot_changed = _get_voter_pref(new_matrix, strategic_voter) != _get_voter_pref(voting_situation, strategic_voter)

    return {
        "changed": (new_winner != original_winner) or any_ballot_changed,
        "original_winner": original_winner,
        "original_happiness_per_voter": original_hpv,
        "original_avg_happiness": original_avg,
        "new_winner": new_winner,
        "new_happiness_per_voter": new_hpv,
        "new_avg_happiness": new_avg,
        "new_voting_situation": new_matrix,
        "strategic_voter": strategic_voter,
        "strategic_voter_original_happiness": original_hpv[strategic_voter],
        "strategic_voter_new_happiness": new_hpv[strategic_voter],
        "intuition_trials": 1,
    }


def print_atva3_results(result, scheme_name):
    from strategic_voting import compute_voting_risk

    print(f"\n{'='*60}")
    print(f"ATVA-3 ANALYSIS (intuition-based): {scheme_name}")
    print(f"{'='*60}")

    print("\nHonest Voting Results:")
    print(f"  Winner: {result['original_winner']}")
    print(f"  Avg Happiness: {result['original_avg_happiness']:.3f}")

    print("\nATVA-3 Results (least-happy voter submits one intuition shuffle):")
    print(f"  Strategic voter: Voter {result['strategic_voter']}")
    print(f"  Intuition shuffles: {result['intuition_trials']}")

    if result["changed"] and result["new_winner"] != result["original_winner"]:
        print(f"  New Winner: {result['new_winner']}")
    else:
        print(f"  Winner unchanged: {result['new_winner']}")

    print(f"  New Avg Happiness: {result['new_avg_happiness']:.3f}")
    print(f"  Change in Avg Happiness: {result['new_avg_happiness'] - result['original_avg_happiness']:.3f}")
    print(compute_voting_risk(result['original_avg_happiness'], result['new_avg_happiness']))

    if result["strategic_voter"] is not None:
        print("\nStrategic voter happiness:")
        print(f"  Original: {result['strategic_voter_original_happiness']:.3f}")
        print(f"  New:      {result['strategic_voter_new_happiness']:.3f}")
        print(f"  Change:   {result['strategic_voter_new_happiness'] - result['strategic_voter_original_happiness']:.3f}")

    print(f"\n{'='*60}")
