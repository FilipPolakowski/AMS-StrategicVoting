def plurality_voting(voting_situation, candidates, voters, preferences):
    scores = {c: 0 for c in candidates}

    for v in range(voters):
        for r in range(preferences):
            if r == 0:  # only first rank counts because plurality
                candidate = voting_situation[r][v]
                scores[candidate] += 1

    max_score = max(scores.values())
    winners = [c for c, s in scores.items() if s == max_score]
    winner = min(winners)  # tie-breaker: lexicographically first
    
    # for candidate in candidates:
    #     print(f"Candidate {candidate} Plurality score is: {scores[candidate]}")

    print(f"\nCandidate {winner} is the Plurality winner with {max_score} points")

    return scores, winner