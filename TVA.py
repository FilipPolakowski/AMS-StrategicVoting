#TODO! 4 voting schemes:
#1:plurality
#2:voting for two
#3:Anti-plurality voting (veto)
#4:Borda voting

#Voting simulation

#Define happiness levels and risk of strategic voting measures

import random


def get_voting_situation():
    voters = int(input("Enter how many voters: "))
    preferences = int(input("Enter how many preferences: "))

    # Generate candidate labels: A, B, C, ...
    candidates = [chr(ord('A') + i) for i in range(preferences)]
    print("Candidates:", candidates)

    # Create table: rows = ranks, columns = voters
    voting_situation = [[None for _ in range(voters)] for _ in range(preferences)]

    mode = input("Choose input mode - random (r) or manual (m): ").strip().lower()

    if mode == 'm':
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
    elif mode == 'r':
        # Randomly generate preferences
        for voter in range(voters):
            prefs = candidates[:]
            random.shuffle(prefs)
            for preference in range(preferences):
                voting_situation[preference][voter] = prefs[preference]
    else:
        print("Invalid mode selected. Please choose 'r' or 'm'.")
        return None, None, None, None

    return voting_situation, candidates, voters, preferences
def print_voting_situation(voting_situation, voters, preferences):
    print("\nVoting situation (rows = ranks, columns = voters):")

    # Header
    print("      ", end="")
    for v in range(voters):
        print(f"V{v+1} ", end="")
    print()

    # Rows
    for r in range(preferences):
        print(f"Rank {r+1}: ", end="")
        for v in range(voters):
            print(f" {voting_situation[r][v]} ", end="")
        print()

if __name__ == '__main__':
    voting_situation, candidates, voters, preferences = get_voting_situation()
    
    print("\nGenerated Voting Situation:")
    print(voting_situation)
    print(candidates)
    print(voters)
    print(preferences)
    print_voting_situation(voting_situation,voters, preferences)