# ATVA-3: Voters have IMPERFECT knowledge of other voters' preferences.
#
# Instead of knowing everyone's true ballot, each voter only has a
# noisy estimate of others' preferences. A voter decides to deviate
# strategically only if their deviation is EXPECTED to improve their
# happiness across many noisy simulations of the election.
#
# Monte Carlo algorithm:
# - For each voter, for each possible single swap of their own ballot:
#   - Sample K_SAMPLES noisy versions of the other voters' ballots
#   - Run the election on each noisy sample with the swap applied
#   - Compute the EXPECTED happiness gain across all samples
#   - If expected gain > EPS, this swap is a candidate strategic option
# - The voter picks the swap with the highest expected happiness gain
# - Only voters whose best swap yields expected gain > EPS act strategically
# - Then we apply ALL chosen plans simultaneously and see what happens.

from copy import deepcopy
import random

from strategic_voting import (
    compute_happiness,   # computes happiness based on TRUE preferences and a winner
    _get_voter_pref,     # read a single voter's ballot from the matrix
    _set_voter_pref,     # write a single voter's ballot into the matrix
    _all_single_swaps,   # generate all single-swap neighbors of a ballot
)

# Number of noisy simulations per swap candidate per voter.
# Use K_SAMPLES=50 for development/testing, K_SAMPLES=200 for final experiments.
K_SAMPLES = 50

# Probability that any adjacent pair in another voter's ballot is swapped.
# 0.0 = perfect knowledge (equivalent to BTVA)
# 0.5 = near-complete ignorance
P_NOISE = 0.2

# Minimum expected happiness gain required to count as a strategic deviation.
# Guards against acting on differences that are just Monte Carlo sampling noise.
EPS = 1e-3


def add_noise_to_ballot(pref_list, p_noise):
    """
    Generates a noisy version of a voter's preference list.
    Each adjacent pair is independently swapped with probability p_noise.

    e.g. [A, B, C, D] with p=0.5 might become [B, A, D, C]

    Note: adjacent swaps can cascade (A<->B then B<->C), which is intentional
    and models gradual uncertainty about nearby-ranked candidates.

    p_noise=0.0 returns the original list unchanged (perfect knowledge).
    p_noise=0.5 produces near-random reorderings (near-complete ignorance).
    """
    noisy = pref_list[:]
    for i in range(len(noisy) - 1):
        if random.random() < p_noise:
            noisy[i], noisy[i + 1] = noisy[i + 1], noisy[i]
    return noisy


def build_noisy_situation(voting_situation, true_situation, voter_index,
                          voters, p_noise):
    """
    Builds one noisy version of the full preference matrix from the
    perspective of voter_index:
    - voter_index's own ballot stays EXACTLY as in voting_situation
      (they know their own preferences perfectly)
    - every other voter's ballot is a noisy version of their TRUE ballot

    This represents one possible "world" that voter_index believes
    they might be in when deciding whether to vote strategically.
    """
    noisy_situation = deepcopy(voting_situation)
    for v in range(voters):
        if v != voter_index:
            true_pref = _get_voter_pref(true_situation, v)
            noisy_pref = add_noise_to_ballot(true_pref, p_noise)
            _set_voter_pref(noisy_situation, v, noisy_pref)
    return noisy_situation


def expected_happiness_for_swap(
    voting_function,
    voting_situation,
    true_situation,
    candidates,
    voters,
    preferences,
    voter_index,
    tactical_pref,
    k_samples,
    p_noise,
):
    """
    Estimates the EXPECTED happiness for voter_index if they use
    tactical_pref, averaged over k_samples noisy simulations of
    the other voters' ballots.

    Key design choice: we evaluate real satisfaction using TRUE preferences
    even though the voter acts based on noisy beliefs. This correctly models
    a voter who is uncertain about the world but has genuine preferences.

    Returns the expected happiness as a float.
    """
    total_happiness = 0.0

    for _ in range(k_samples):

        # Build a noisy situation (other voters' ballots are uncertain)
        noisy_situation = build_noisy_situation(
            voting_situation, true_situation, voter_index, voters, p_noise
        )

        # Apply this voter's tactical ballot to the noisy situation
        _set_voter_pref(noisy_situation, voter_index, tactical_pref)

        # Run the election on the noisy situation
        _, trial_winner = voting_function(
            noisy_situation, candidates, voters, preferences
        )

        # Compute happiness on TRUE preferences (not the noisy ones)
        trial_hpv, _ = compute_happiness(
            true_situation, trial_winner, voters, preferences
        )

        total_happiness += trial_hpv[voter_index]

    return total_happiness / k_samples


def find_best_swap_atva3(
    voting_function,
    voting_situation,
    true_situation,
    candidates,
    voters,
    preferences,
    voter_index,
    k_samples,
    p_noise,
):
    """
    For a single voter, finds their best strategic swap under imperfect
    knowledge by evaluating expected happiness for all single-swap
    neighbors of their current ballot.

    Returns:
        best_pref      : the best tactical ballot found
                         (or original ballot if no swap improves by > EPS)
        best_exp_h     : the expected happiness for the best tactical ballot
        baseline_exp_h : the expected happiness under their honest ballot
    """

    # Baseline: expected happiness with honest ballot
    honest_pref = _get_voter_pref(voting_situation, voter_index)
    baseline_exp_h = expected_happiness_for_swap(
        voting_function, voting_situation, true_situation,
        candidates, voters, preferences,
        voter_index, honest_pref, k_samples, p_noise
    )

    best_pref = honest_pref
    best_exp_h = baseline_exp_h

    # Try all single-swap neighbors of this voter's honest ballot
    # _all_single_swaps returns all ballots reachable by swapping
    # any two positions exactly once
    for tactical_pref in _all_single_swaps(honest_pref):
        exp_h = expected_happiness_for_swap(
            voting_function, voting_situation, true_situation,
            candidates, voters, preferences,
            voter_index, tactical_pref, k_samples, p_noise
        )
        if exp_h > best_exp_h:
            best_exp_h = exp_h
            best_pref = tactical_pref

    return best_pref, best_exp_h, baseline_exp_h


def strategic_vote_atva3(
    voting_function,
    voting_situation,
    candidates,
    voters,
    preferences,
    k_samples=K_SAMPLES,
    p_noise=P_NOISE,
    seed=None,
):
    """
    ATVA-3: Imperfect Knowledge

    Drops BTVA Limitation 3: voters no longer have perfect knowledge
    of other voters' true preferences. Instead each voter holds a noisy
    belief about others and evaluates strategic deviations in expectation.

    Algorithm:
    1) Run the election honestly -> original winner and happiness.
    2) For each voter:
       - Evaluate all single swaps of their ballot in expectation
         (averaged over k_samples noisy simulations of others' ballots)
       - If any swap gives expected happiness > honest ballot + EPS,
         that voter is considered strategic and will use their best swap
    3) Apply ALL strategic voters' chosen ballots simultaneously.
    4) Rerun election on the modified matrix.
    5) Compute TRUE happiness for everyone and report results.

    Parameters
    ----------
    voting_function : callable
        Any of the four voting scheme functions.
    voting_situation : list[list[str]]
        Current preference matrix (may already be manipulated upstream).
    candidates : list[str]
    voters : int
    preferences : int
    k_samples : int
        Number of Monte Carlo samples per swap evaluation.
        Use 50 for testing, 200 for final report experiments.
    p_noise : float
        Noise level for other voters' ballots.
        0.0 = perfect knowledge (BTVA equivalent).
        0.5 = near-complete ignorance.
    seed : int or None
        Random seed for reproducibility. Set a fixed value when
        running report experiments so results are consistent.
    """

    # Set random seed for reproducibility if provided
    if seed is not None:
        random.seed(seed)

    # Keep true preferences unchanged throughout
    true_situation = deepcopy(voting_situation)

    # Honest outcome
    _, original_winner = voting_function(
        voting_situation, candidates, voters, preferences
    )

    # True happiness under honest voting
    original_hpv, original_avg = compute_happiness(
        true_situation, original_winner, voters, preferences
    )

    # Find each voter's best swap under imperfect knowledge
    chosen_prefs = {}

    for v in range(voters):
        best_pref, best_exp_h, baseline_exp_h = find_best_swap_atva3(
            voting_function=voting_function,
            voting_situation=voting_situation,
            true_situation=true_situation,
            candidates=candidates,
            voters=voters,
            preferences=preferences,
            voter_index=v,
            k_samples=k_samples,
            p_noise=p_noise,
        )
        # Only act strategically if expected gain exceeds EPS threshold
        # EPS guards against acting on pure Monte Carlo sampling noise
        if best_exp_h > baseline_exp_h + EPS:
            chosen_prefs[v] = best_pref

    # Apply all strategic ballots simultaneously
    new_matrix = deepcopy(voting_situation)
    for v, pref in chosen_prefs.items():
        _set_voter_pref(new_matrix, v, pref)

    # Rerun election on modified matrix
    _, new_winner = voting_function(new_matrix, candidates, voters, preferences)

    # Compute TRUE happiness after strategic voting
    new_hpv, new_avg = compute_happiness(
        true_situation, new_winner, voters, preferences
    )

    # Count outcomes for strategic voters
    improved = 0
    decreased = 0
    same = 0

    for v in chosen_prefs:
        if new_hpv[v] > original_hpv[v]:
            improved += 1
        elif new_hpv[v] < original_hpv[v]:
            decreased += 1
        else:
            same += 1

    # Cleaner separation of what actually changed
    winner_changed = (new_winner != original_winner)
    any_ballot_changed = len(chosen_prefs) > 0

    return {
        "changed": winner_changed or any_ballot_changed,
        "winner_changed": winner_changed,
        "any_ballot_changed": any_ballot_changed,

        "original_winner": original_winner,
        "original_happiness_per_voter": original_hpv,
        "original_avg_happiness": original_avg,

        "new_winner": new_winner,
        "new_happiness_per_voter": new_hpv,
        "new_avg_happiness": new_avg,
        "new_voting_situation": new_matrix,

        "strategic_voters": list(chosen_prefs.keys()),
        "strategic_voters_count": len(chosen_prefs),

        "strategic_improved_count": improved,
        "strategic_decreased_count": decreased,
        "strategic_same_count": same,

        "k_samples": k_samples,
        "p_noise": p_noise,
        "seed": seed,
    }


def print_atva3_results(result, scheme_name):

    from strategic_voting import compute_voting_risk

    print(f"\n{'='*60}")
    print(f"ATVA-3 ANALYSIS: {scheme_name}")
    print(f"{'='*60}")
    print(f"  (p_noise={result['p_noise']}, k_samples={result['k_samples']}, "
          f"seed={result['seed']})")

    print("\nHonest Voting Results:")
    print(f"  Winner: {result['original_winner']}")
    print(f"  Avg Happiness: {result['original_avg_happiness']:.3f}")

    print("\nATVA-3 Results (imperfect knowledge, voters deviate if "
          "expected gain > EPS):")
    print(f"  New Winner: {result['new_winner']}")
    print(f"  New Avg Happiness: {result['new_avg_happiness']:.3f}")
    print(f"  Change in Avg Happiness: "
          f"{result['new_avg_happiness'] - result['original_avg_happiness']:.3f}")
    print(compute_voting_risk(result['original_avg_happiness'],
                              result['new_avg_happiness']))

    print("\nStrategic voters summary:")
    print(f"  # Strategic voters (expected gain > EPS): "
          f"{result['strategic_voters_count']}")
    print(f"  Voter indices: {result['strategic_voters']}")
    print(f"  # Improved:  {result['strategic_improved_count']}")
    print(f"  # Decreased: {result['strategic_decreased_count']}")
    print(f"  # Same:      {result['strategic_same_count']}")

    print(f"\n  Winner changed:      {result['winner_changed']}")
    print(f"  Any ballot changed:  {result['any_ballot_changed']}")

    print(f"\n{'='*60}")
