import os
import sys
import random
from copy import deepcopy

# ensure the parent directory (workspace root) is on sys.path so that
# `strategic_voting` and other top-level modules can be imported when
# this script is run from inside the `experiments/` folder.
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from strategic_voting import strategic_vote
from ATVAs.ATVA_4 import strategic_vote_atva4
import pprint
from statistics import mean


def generate_random_situation(num_voters, num_candidates):
    candidates = [chr(ord('A') + i) for i in range(num_candidates)]
    voting_situation = [[None for _ in range(num_voters)] for _ in range(num_candidates)]

    for voter in range(num_voters):
        prefs = candidates[:]
        random.shuffle(prefs)
        for preference in range(num_candidates):
            voting_situation[preference][voter] = prefs[preference]

    return voting_situation, candidates


def run_atva4_experiments(voting_schemes, num_situations=50, num_voters=5, num_candidates=4, seed=42):
    random.seed(seed)

    results = {
        name: {
            "winner_changes": 0,
            "btva_happiness": [],
            "avg_happiness_changes": [],
            "strategic_voter_changes": [],
            "gain_per_strategic_voter": [],
            "total_situations": 0,
        }
        for name in voting_schemes.keys()
    }

    print(f"Running ATVA-4 experiments on {num_situations} random situations...\n")

    for _ in range(num_situations):
        voting_situation, candidates = generate_random_situation(num_voters, num_candidates)

        for scheme_name, voting_function in voting_schemes.items():
            atva4_result = strategic_vote_atva4(
                voting_function,
                deepcopy(voting_situation),
                candidates,
                num_voters,
                num_candidates,
            )

            btva_result = strategic_vote(
                voting_function,
                deepcopy(voting_situation),
                candidates,
                num_voters,
                num_candidates,
            )

            # Winner change rate
            if atva4_result["new_winner"] != atva4_result["original_winner"]:
                results[scheme_name]["winner_changes"] += 1

            # BTVA average happiness
            results[scheme_name]["btva_happiness"].append(btva_result["new_avg_happiness"])

            # Change in average happiness for ATVA-4
            happiness_gain = (
                atva4_result["new_avg_happiness"] - atva4_result["original_avg_happiness"]
            )
            results[scheme_name]["avg_happiness_changes"].append(happiness_gain)

            # Change in number of strategic voters: ATVA-4 - BTVA
            atva4_sv_count = atva4_result["strategic_voters_count"]
            btva_sv_count = 1 if btva_result["strategic_voter"] is not None else 0

            results[scheme_name]["strategic_voter_changes"].append(
                atva4_sv_count - btva_sv_count
)

            # Option 1:
            # ATVA-4 happiness gain per ATVA-4 strategic voter
            # Skip cases where ATVA-4 uses 0 strategic voters
            if atva4_result["strategic_voters_count"] > 0:
                gain_per_sv = happiness_gain / atva4_result["strategic_voters_count"]
                results[scheme_name]["gain_per_strategic_voter"].append(gain_per_sv)

            results[scheme_name]["total_situations"] += 1

    print("Experiments complete!\n")
    return results


def print_atva4_experiment_results(results):
    print(
        f"\n{'Voting Scheme':<20} "
        f"{'Winner Change Rate':<22} "
        f"{'BTVA Avg H̄':<15} "
        f"{'Δ Avg H̄ (ATVA-4)':<20} "
        f"{'Δ Avg. # Strategic Voters':<26} "
        f"{'Gain per Strategic Voter':<26}"
    )
    print("-" * 150)

    for scheme_name, data in results.items():
        winner_change_rate = data["winner_changes"] / data["total_situations"]
        btva_avg_happiness = sum(data["btva_happiness"]) / len(data["btva_happiness"])
        avg_happiness_change = sum(data["avg_happiness_changes"]) / len(data["avg_happiness_changes"])
        avg_strategic_voter_change = (
            sum(data["strategic_voter_changes"]) / len(data["strategic_voter_changes"])
        )

        if len(data["gain_per_strategic_voter"]) > 0:
            avg_gain_per_sv = (
                sum(data["gain_per_strategic_voter"]) / len(data["gain_per_strategic_voter"])
            )
            gain_per_sv_str = f"{avg_gain_per_sv:.3f}"
        else:
            gain_per_sv_str = "N/A"

        print(
            f"{scheme_name:<20} "
            f"{winner_change_rate:<22.2%} "
            f"{btva_avg_happiness:<15.3f} "
            f"{avg_happiness_change:<20.3f} "
            f"{avg_strategic_voter_change:<26.3f} "
            f"{gain_per_sv_str:<26}"
        )

    print("-" * 150)


if __name__ == "__main__":
    from voting_schemes.plurality_voting import plurality_voting
    from voting_schemes.voting_for_two import voting_for_two
    from voting_schemes.antiplurality_voting import anti_plurality_voting
    from voting_schemes.borda_voting import borda_voting

    schemes = {
        "Plurality": plurality_voting,
        "Voting for Two": voting_for_two,
        "Anti-Plurality": anti_plurality_voting,
        "Borda": borda_voting,
    }

    results = run_atva4_experiments(
        voting_schemes=schemes,
        num_situations=50,
        num_voters=20,
        num_candidates=7,
        seed=42,
    )

    print_atva4_experiment_results(results)

    

    with open("/Users/panagiotis/Desktop/AMS_final/working_on/results/atva4_results_full.txt", "w", encoding="utf-8") as f:
        f.write("FULL RESULTS DICTIONARY\n")
        f.write("=" * 80 + "\n")
        f.write(pprint.pformat(results, sort_dicts=False))
        f.write("\n\n")

        f.write("SUMMARY RESULTS\n")
        f.write("=" * 80 + "\n")

        for scheme, row in results.items():
            winner_change_rate = row["winner_changes"] / row["total_situations"]
            btva_avg_happiness = mean(row["btva_happiness"])
            delta_avg_happiness = mean(row["avg_happiness_changes"])
            delta_strategic_voters = mean(row["strategic_voter_changes"])
            gain_per_strategic_voter = mean(row["gain_per_strategic_voter"])

            f.write(f"{scheme}\n")
            f.write(f"Winner Change Rate = {winner_change_rate:.2%}\n")
            f.write(f"BTVA Avg H = {btva_avg_happiness:.3f}\n")
            f.write(f"Delta Avg H (ATVA-4) = {delta_avg_happiness:.3f}\n")
            f.write(f"Delta Avg # Strategic Voters = {delta_strategic_voters:.3f}\n")
            f.write(f"Gain per Strategic Voter = {gain_per_strategic_voter:.3f}\n")
            f.write("\n")


        