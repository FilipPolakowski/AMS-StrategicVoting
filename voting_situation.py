import random
import string

print("Random Voting Situation Generator")
print("----------------------------------")

print("Enter amount of voters:")
num_voters = int(input().strip())
print("Enter amount of candidates:")
num_candidates = int(input().strip())

print("amount of voters: " + str(num_voters) + ", amount of candidates: " + str(num_candidates))

voting_situation = [
    [None for _ in range(num_voters)]
    for _ in range(num_candidates)
]

alphabet = list(string.ascii_uppercase)

ballots = []

for voter in range(num_voters):
    preferences = alphabet[:num_candidates]
    preferences_random = random.sample(preferences, len(preferences))
    ballots.append(preferences_random)
    for candidate in range(num_candidates):
        voting_situation[candidate][voter] = preferences_random[candidate]

print("\nVoting Situation:")

header = "Preference"
for voter in range(num_voters):
    header += f" | V{voter}"
print(header)
print("-" * (10 + num_voters * 6))

for preference_number in range(num_candidates):
    row = f"{preference_number + 1}".ljust(10)
    for voter in range(num_voters):
        row += f" |  {ballots[voter][preference_number]}"
    print(row)

print("\nVoting Situation Array:")
for row in voting_situation:
    print(row)
