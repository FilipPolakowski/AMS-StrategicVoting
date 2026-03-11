def ATVA_1(
        voting_func,
        voting_situation,
        candidates,
        voters,
        preferences,
        max_coalition_size=3
):
    """
    ATVA-1 Collusion: Coalitions up to max_coalition_size can manipulate together.
    Each coalition member tries all single swaps of their ballot.
    Returns the coalition with the best improvement in average happiness.
    """
    import itertools, copy
    from voting_schemes.strategic_voting import compute_happiness

    # Honest outcome
    original_scores, original_winner = voting_func(
        voting_situation, candidates, voters, preferences
    )
    happiness_per_voter, original_avg = compute_happiness(
        voting_situation, original_winner, voters, preferences
    )

    best_result = {
        "original_winner": original_winner,
        "original_avg_happiness": original_avg,
        "collusion_found": False,
        "coalition": None,
        "coalition_size": None,
        "new_winner": None,
        "new_avg_happiness": None,
        "improvement": 0
    }

    max_size = min(max_coalition_size, voters)

    # Try coalition sizes 2..max_size
    for size in range(2, max_size + 1):
        for coalition in itertools.combinations(range(voters), size):

            # Generate all single swaps for each coalition member
            voter_swaps_options = []
            for voter in coalition:
                original_ballot = [voting_situation[r][voter] for r in range(preferences)]
                swaps = []

                # all single swaps
                for i in range(preferences):
                    for j in range(i + 1, preferences):
                        new_ballot = original_ballot[:]
                        new_ballot[i], new_ballot[j] = new_ballot[j], new_ballot[i]
                        swaps.append(new_ballot)
                voter_swaps_options.append(swaps)

            # Cartesian product across coalition members
            for ballots_combo in itertools.product(*voter_swaps_options):
                new_situation = copy.deepcopy(voting_situation)

                # Apply ballots
                for idx, voter in enumerate(coalition):
                    for r in range(preferences):
                        new_situation[r][voter] = ballots_combo[idx][r]

                # Compute new winner from manipulated ballots
                new_scores, new_winner = voting_func(new_situation, candidates, voters, preferences)

                # Compute happiness using original preferences (voting_situation), but new winner
                new_happiness_per_voter, new_avg = compute_happiness(
                    voting_situation,  # ORIGINAL preferences, not the swapped ballots
                    new_winner,
                    voters,
                    preferences
                )

                # Check if all coalition members strictly improve
                if all(new_happiness_per_voter[v] > happiness_per_voter[v] for v in coalition):
                    improvement = new_avg - original_avg
                    if improvement > best_result["improvement"]:
                        # Update best coalition
                        best_result.update({
                            "collusion_found": True,
                            "coalition": coalition,
                            "coalition_size": size,
                            "new_winner": new_winner,
                            "new_avg_happiness": new_avg,
                            "improvement": improvement
                        })

    return best_result