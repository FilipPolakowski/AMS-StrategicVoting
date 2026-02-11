def anti_plurality_voting(voting_situation, candidates, voters, preferences):
    scores = []
    max_score = -1
    winner = None

    for candidate in candidates:
        score = 0

        for i in range(voters):          # voters = columns
            for j in range(preferences): # find candidate in ranking
                if voting_situation[j][i] == candidate:
                    if j != preferences - 1:  # NOT last place
                        score += 1
                    break

        scores.append(score)

        # same tie-breaking rule
        if score > max_score:
            max_score = score
            winner = candidate
        elif score == max_score and candidate < winner:
            winner = candidate

        print(f"Candidate {candidate} score is: {score}")

    print(f"\nCandidate {winner} is the winner with {max_score} points")
    print(scores)
