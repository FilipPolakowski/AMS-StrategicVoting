def voting_for_two(voting_situation, candidates, voters, preferences):
    scores = []
    max_score = -1
    winner = None

    for candidate in candidates:
        score = 0
        for i in range(voters):          # voters are columns
            for j in range(preferences): # find candidate in that column with desc order of preferences
                if voting_situation[j][i] == candidate:
                    if j < 2:  # Only top 2 candidates get a point
                        score += 1
                    break
        scores.append(score)


        # tie-breaker for candidates with the same score (A beats B, B beats C, etc.)
        if score > max_score:
            max_score = score
            winner = candidate
        elif score == max_score and candidate < winner: # In python strings are compared lexicographically in ASCII, so
            winner = candidate                          # B (66) < A (65) is False, but A (65) < B (66) is True
            
        
        # print(f"Candidate {candidate} Voting for Two score is: {score}")

    print(f"\nCandidate {winner} is the Voting for Two winner with {max_score} points")

    return scores, winner

