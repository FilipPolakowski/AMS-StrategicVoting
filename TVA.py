#TODO! 4 voting schemes:
#1:plurality
#2:voting for two
#3:Anti-plurality voting (veto)
#4:Borda voting

#Voting simulation

#Define happiness levels and risk of strategic voting measures


def get_voting_situation():
    voters = int(input("Enter how many voters: "))
    preferences = int(input("Enter how many preferences: "))

    # Generate candidate labels: A, B, C, ...
    candidates = [chr(ord('A') + i) for i in range(preferences)]
    print("Candidates:", candidates)

    # Create table: rows = ranks, columns = voters
    voting_situation = [[None for _ in range(voters)] for _ in range(preferences)]

    # Input preferences voter by voter
    for v in range(voters):
        while True:
            row_input = input(
                f"Enter preferences for voter {v+1} "
                f"(space-separated, e.g. A B C D): "
            )

            row = row_input.upper().split()

            # Validation
            if len(row) != preferences:
                print(f"Please enter exactly {preferences} preferences.")
                continue

            if set(row) != set(candidates):
                print(f"Please use each candidate exactly once: {candidates}")
                continue

            # Store column-wise (voter is column)
            for r in range(preferences):
                voting_situation[r][v] = row[r]

            break

    return voting_situation, candidates, voters, preferences


if __name__ == '__main__':
    voting_situation, candidates, voters, preferences = get_voting_situation()
    print(voting_situation)
    print(candidates)
    print(voters)
    print(preferences)