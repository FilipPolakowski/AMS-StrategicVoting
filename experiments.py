import random
import csv
import os

from ATVAs.ATVA_1 import ATVA_1

from voting_schemes.plurality_voting import plurality_voting
from voting_schemes.borda_voting import borda_voting
from voting_schemes.antiplurality_voting import anti_plurality_voting
from voting_schemes.voting_for_two import voting_for_two

from voting_schemes.strategic_voting import strategic_vote as BTVA

# Voting rules dictionary
VOTING_RULES = {
    "Plurality": plurality_voting,
    "Voting for Two": voting_for_two,
    "Anti-Plurality": anti_plurality_voting,
    "Borda": borda_voting
}

# Voting situation generator
def get_voting_situation(voters, preferences):
    """
    Generate a random voting situation
    Rows = ranks
    Columns = voters
    """
    candidates = [chr(ord('A') + i) for i in range(preferences)]
    voting_situation = [[None for _ in range(voters)] for _ in range(preferences)]

    for voter in range(voters):
        prefs = candidates[:]
        random.shuffle(prefs)
        for r in range(preferences):
            voting_situation[r][voter] = prefs[r]

    return voting_situation, candidates, voters, preferences

# Generate fixed elections
def generate_elections(num_elections, voters, preferences):
    elections = []
    for seed in range(num_elections):
        random.seed(seed)
        elections.append(get_voting_situation(voters, preferences))
    return elections

def run_experiment(max_coalition_size, elections):
    num_elections = len(elections)
    results = {}

    for rule_name, rule_func in VOTING_RULES.items():
        btva_count = 0
        atva_count = 0
        new_coalitions = 0
        total_gain = 0
        gain_count = 0
        csv_rows = []

        for i, (voting_situation, candidates, voters, preferences) in enumerate(elections, 1):

            # BTVA: single voter manipulation
            btva_result = BTVA(rule_func, voting_situation, candidates, voters, preferences)
            btva_found = btva_result["changed"]
            if btva_found:
                btva_count += 1

            # ATVA-1: coalition manipulation
            atva_result = ATVA_1(rule_func, voting_situation, candidates, voters, preferences, max_coalition_size=max_coalition_size)
            if atva_result["collusion_found"]:
                atva_count += 1
                total_gain += atva_result["improvement"]
                gain_count += 1
                if not btva_found:
                    new_coalitions += 1

            # Save per-election data for CSV
            csv_rows.append({
                "Election": i,
                "BTVA_found": int(btva_found),
                "ATVA_found": int(atva_result["collusion_found"]),
                "Improvement": atva_result.get("improvement", 0)
            })

        # Summary metrics
        R = btva_count / num_elections
        R_prime = atva_count / num_elections
        percent_new = (new_coalitions / num_elections) * 100
        avg_gain = total_gain / gain_count if gain_count > 0 else 0

        results[rule_name] = {
            "R": R,
            "R_prime": R_prime,
            "new_coalitions_percent": percent_new,
            "avg_gain": avg_gain
        }

        # Save CSV
        os.makedirs("results_csv", exist_ok=True)
        csv_file = f"results_csv/{rule_name.replace(' ', '_')}_coalition_{max_coalition_size}_voters_{voters}_prefs_{preferences}.csv"
        with open(csv_file, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["Election", "BTVA_found", "ATVA_found", "Improvement"])
            writer.writeheader()
            for row in csv_rows:
                writer.writerow(row)

    return results

def print_results(results, coalition_size, voters, preferences):
    print(f"\n===== Results (max coalition size = {coalition_size}, voters = {voters}, preferences = {preferences}) =====")
    for rule, r in results.items():
        print(
            f"{rule:18} | "
            f"R={r['R']:.2f} | "
            f"R'={r['R_prime']:.2f} | "
            f"New coalitions={r['new_coalitions_percent']:.1f}% | "
            f"Avg gain={r['avg_gain']:.3f}"
        )


if __name__ == "__main__":

    num_elections = 50
    max_coalition_sizes = [2, 3]

    # Loop over different voter and preference sizes
    for voters in range(4, 8):        # 4 to 7
        for preferences in range(4, 8):  # 4 to 7
            print(f"\n=== Running experiments: voters={voters}, preferences={preferences} ===")
            elections = generate_elections(num_elections, voters, preferences)

            for max_size in max_coalition_sizes:
                results = run_experiment(max_size, elections)
                print_results(results, max_size, voters, preferences)

    print("\nCSV files saved in ./results_csv/")