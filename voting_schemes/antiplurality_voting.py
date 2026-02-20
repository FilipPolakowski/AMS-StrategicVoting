def anti_plurality_voting(voting_situation, candidates, voters, preferences):
    scores = []
    max_score = -1
    winner = None

    for candidate in candidates:
        score = 0

        for i in range(voters):          
            for j in range(preferences): 
                if voting_situation[j][i] == candidate:
                    if j != preferences - 1:  
                        score += 1
                    break

        scores.append(score)


        if score > max_score:
            max_score = score
            winner = candidate
        elif score == max_score and candidate < winner:
            winner = candidate

        # print(f"Candidate {candidate} Antiplurality score is: {score}")

    print(f"\nCandidate {winner} is the Antiplurality winner with {max_score} points")

    return scores, winner
