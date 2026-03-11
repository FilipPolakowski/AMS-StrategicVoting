# counter strategic voting: Advanced TVA without restriction 2 (ATVA-2)
# this module implements a multi-round strategic voting where voters can respond
# to each other's strategic voting moves.
# it hopes to find an equilibrium state where no voter can further improve their happiness
# through strategic voting manipulation, while also detecting cycles and providing analysis
# on the impact of counter strategic voting

from copy import deepcopy
import random
from voting_schemes.strategic_voting import strategic_vote
    

def compute_happiness(voting_situation, winner, voters, preferences):
    # compute voter happiness based on true preferences
    happiness_per_voter = []
    total_happiness = 0

    for v in range(voters):
        voter_happiness = 0
        for r in range(preferences):
            if voting_situation[r][v] == winner:
                voter_happiness = 1 / (r + 1)
                break
        happiness_per_voter.append(voter_happiness)
        total_happiness += voter_happiness

    average_happiness = total_happiness / voters if voters else 0
    return happiness_per_voter, average_happiness


def get_voter_pref(voting_situation, voter_index):
    # extract one voter's preference list from the voting situation matrix
    prefs = []
    for row in voting_situation:
        prefs.append(row[voter_index])
    return prefs


def set_voter_pref(voting_situation, voter_index, pref_list):
    # update one voter's preference list in the voting situation matrix
    for r in range(len(pref_list)):
        voting_situation[r][voter_index] = pref_list[r]


def all_strategic_manipulations(pref_list):
    # generate the following strategic voting options:
    # 1. single swaps between any 2 positions
    # 2. move any candidate to the top to boost
    # 3. move any candidate to the bottom to bury
    out = []
    m = len(pref_list)
    
    # single swaps
    for i in range(m - 1):
        for j in range(i + 1, m):
            temp = pref_list[:]
            temp[i], temp[j] = temp[j], temp[i]
            out.append(temp)
    
    # boost to top
    for i in range(1, m):  # skip i=0 (already at top)
        temp = pref_list[:]
        candidate = temp.pop(i)  
        temp.insert(0, candidate)  
        out.append(temp)
    
    # bury to bottom
    for i in range(m - 1):  # skip i=m-1 (already at bottom)
        temp = pref_list[:]
        candidate = temp.pop(i) 
        temp.append(candidate) 
        out.append(temp)
    
    return out


def voting_situation_to_tuple(voting_situation):
    # convert voting situation matrix to a tuple of tuples for hasing -> allows cycle detection
    return tuple(tuple(row) for row in voting_situation)


def find_strategic_voter(voting_function, voting_situation, true_situation, 
                        candidates, voters, preferences, current_happiness):
    # find a single voter who can improve happiness by strategic voting
    # order voters by happiness (least happy first, ties broken by higher index)
    order = list(range(voters))
    order.sort(key=lambda i: (current_happiness[i], -i))
    
    for v in order:
        current_pref = get_voter_pref(voting_situation, v)
        baseline_happiness = current_happiness[v]
        
        best_tactical_pref = None
        best_trial_winner = None
        best_trial_happiness = None
        best_trial_avg = None
        best_voter_happiness = baseline_happiness
        
        # try all strategic manipulations
        for tactical_pref in all_strategic_manipulations(current_pref):
            trial = deepcopy(voting_situation)
            set_voter_pref(trial, v, tactical_pref)
            
            _, trial_winner = voting_function(trial, candidates, voters, preferences)
            trial_happiness, trial_avg = compute_happiness(true_situation, trial_winner, voters, preferences)
            
            # check if this voter happiness improved
            if trial_happiness[v] > best_voter_happiness:
                best_voter_happiness = trial_happiness[v]
                best_tactical_pref = tactical_pref
                best_trial_winner = trial_winner
                best_trial_happiness = trial_happiness
                best_trial_avg = trial_avg
        
        # return improvement if found
        if best_tactical_pref is not None:
            new_matrix = deepcopy(voting_situation)
            set_voter_pref(new_matrix, v, best_tactical_pref)
            
            return {
                "found": True,
                "voter_index": v,
                "original_pref": current_pref,
                "strategic_pref": best_tactical_pref,
                "new_voting_situation": new_matrix,
                "new_winner": best_trial_winner,
                "new_happiness": best_trial_happiness,
                "new_avg_happiness": best_trial_avg,
                "improvement": best_voter_happiness - baseline_happiness
            }
    
    #no voter can improve
    return {"found": False}


def counter_strategic_voting(voting_function, voting_situation, candidates, voters, preferences, max_rounds=20):
    # runs counter-strategic voting for multiple rounds until we find an equilibrium or reach the max rounds limit
    
    true_situation = deepcopy(voting_situation)
    
    # initial honest results
    _, initial_winner = voting_function(voting_situation, candidates, voters, preferences)
    initial_happiness, initial_avg = compute_happiness(true_situation, initial_winner, voters, preferences)
    
    rounds = []
    current_situation = deepcopy(voting_situation)
    current_happiness = initial_happiness[:]
    current_avg = initial_avg
    
    # track already seen states for cycle detection
    seen_states = {voting_situation_to_tuple(current_situation)}
    
    # track which voters have voted strategically
    strategic_voters = set()
    
    equilibrium_type = "stable"
    
    for round_num in range(1, max_rounds + 1):
        # Find the next strategic voter
        result = find_strategic_voter(
            voting_function, 
            current_situation, 
            true_situation, 
            candidates, 
            voters, 
            preferences, 
            current_happiness
        )
        
        if not result["found"]:
            # no one can improve, meaning -> stable equilibrium reached
            equilibrium_type = "stable"
            break
        
        strategic_voters.add(result["voter_index"])
        
        round_info = {
            "round": round_num,
            "voter": result["voter_index"],
            "original_ballot": result["original_pref"],
            "strategic_ballot": result["strategic_pref"],
            "winner": result["new_winner"],
            "voter_happiness_before": current_happiness[result["voter_index"]],
            "voter_happiness_after": result["new_happiness"][result["voter_index"]],
            "improvement": result["improvement"],
            "avg_happiness": result["new_avg_happiness"]
        }
        rounds.append(round_info)
        
        # update current state
        current_situation = result["new_voting_situation"]
        current_happiness = result["new_happiness"]
        current_avg = result["new_avg_happiness"]
        
        # cycle detection
        state_tuple = voting_situation_to_tuple(current_situation)
        if state_tuple in seen_states:
            equilibrium_type = "cycle"
            break
        seen_states.add(state_tuple)
    else:
        # reached max rounds
        equilibrium_type = "max_rounds"
    
    # get final winner
    _, final_winner = voting_function(current_situation, candidates, voters, preferences)
    final_happiness, final_avg = compute_happiness(true_situation, final_winner, voters, preferences)
    
    return {
        "rounds": rounds,
        "initial_winner": initial_winner,
        "final_winner": final_winner,
        "initial_happiness": initial_happiness,
        "final_happiness": final_happiness,
        "initial_avg_happiness": initial_avg,
        "final_avg_happiness": final_avg,
        "equilibrium_type": equilibrium_type,
        "total_strategic_moves": len(rounds),
        "unique_strategic_voters": strategic_voters,
        "final_voting_situation": current_situation
    }


def print_counter_strategic_analysis(result, scheme_name):
    # concise printout of the results of counter strategic voting results

    print(f"\n{'='*70}")
    print(f"COUNTER-STRATEGIC VOTING ANALYSIS: {scheme_name}")
    print(f"{'='*70}")
    
    print(f"\nINITIAL (HONEST) VOTING:")
    print(f"Winner: {result['initial_winner']}")
    print(f"Average Happiness: {result['initial_avg_happiness']:.3f}")
    
    if result['total_strategic_moves'] == 0:
        print(f"\nSTABLE EQUILIBRIUM REACHED")
        print(f"No voter can improve through strategic voting.")
        print(f"The honest outcome is already at equilibrium!")
    else:
        print(f"\nSTRATEGIC CASCADE ({result['total_strategic_moves']} rounds):")
        print(f"{'─'*70}")
        
        for r in result['rounds']:
            print(f"\nRound {r['round']}: Voter {r['voter'] + 1} votes strategically")
            print(f"Original ballot: {' > '.join(r['original_ballot'])}")
            print(f"Strategic ballot: {' > '.join(r['strategic_ballot'])}")
            print(f"New winner: {r['winner']}")
            print(f"Voter happiness: FROM {r['voter_happiness_before']:.3f} TO {r['voter_happiness_after']:.3f} (+{r['improvement']:.3f})")
            print(f"Average happiness: {r['avg_happiness']:.3f}")
        
        print(f"\n{'─'*70}")
        print(f"\nFINAL EQUILIBRIUM:")
        print(f"Type: {result['equilibrium_type'].upper()}")
        print(f"Winner: {result['final_winner']}")
        print(f"Average Happiness: {result['final_avg_happiness']:.3f}")
        print(f"Unique strategic voters: {len(result['unique_strategic_voters'])}/{len(result['initial_happiness'])}")
        
        # analysis of winner change and happiness change due to counter-strategic voting
        print(f"\nCOUNTER-STRATEGIC VOTING IMPACT ANALYSIS:")
        winner_changed = result['initial_winner'] != result['final_winner']
        happiness_change = result['final_avg_happiness'] - result['initial_avg_happiness']
        
        if winner_changed:
            print(f"Winner changed: FROM {result['initial_winner']} TO {result['final_winner']}")
        else:
            print(f"Winner unchanged: STILL {result['final_winner']}")
        
        if happiness_change > 0:
            print(f"Average happiness increased by {happiness_change:.3f}")
        elif happiness_change < 0:
            print(f"Average happiness decreased by {abs(happiness_change):.3f}")
            print(f"TACTICAL VOTING RISK: Strategic behavior reduced overall welfare")
        else:
            print(f"Average happiness unchanged")
        
        if result['equilibrium_type'] == 'stable':
            print(f"\nStable equilibrium found: No voter can further improve their happiness through strategic voting.")
        elif result['equilibrium_type'] == 'cycle':
            print(f"\nCycle detected: Voters keep responding to each other")
        else:
            print(f"\nMaximum rounds reached: Equilibrium is not stable after {result['total_strategic_moves']} rounds.")
    
    print(f"\n{'='*70}")


def generate_random_situation(num_voters, num_candidates):
    # generate a random voting situation with given number of voters and candidates for experiments
    import random
    candidates = [chr(ord('A') + i) for i in range(num_candidates)]
    voting_situation = [[None for _ in range(num_voters)] for _ in range(num_candidates)]
    
    # randomly generate preferences for each voter
    for voter in range(num_voters):
        prefs = candidates[:]
        random.shuffle(prefs)
        for preference in range(num_candidates):
            voting_situation[preference][voter] = prefs[preference]
    
    return voting_situation, candidates


def run_experiments(voting_schemes, num_situations=50, num_voters=5, num_candidates=4, seed=42):
    random.seed(seed)
    
    results = {name: {
        "rounds": [],
        "equilibrium_happiness": [],
        "btva_happiness": [],
        "winner_changes": 0,
        "total_situations": 0,
        "cycles": 0,
        "max_rounds_reached": 0
    } for name in voting_schemes.keys()}
    
    print(f"Running experiments on {num_situations} random situations...\n")
    
    for situation_num in range(num_situations):
        voting_situation, candidates = generate_random_situation(num_voters, num_candidates)
        
        for scheme_name, voting_function in voting_schemes.items():
            # run ATVA-2
            atva2_result = counter_strategic_voting(
                voting_function, 
                deepcopy(voting_situation), 
                candidates, 
                num_voters, 
                num_candidates,
                max_rounds=20
            )
            
            # run BTVA (single-round strategic)
            btva_result = strategic_vote(
                voting_function,
                deepcopy(voting_situation),
                candidates,
                num_voters,
                num_candidates
            )
            
            results[scheme_name]["rounds"].append(atva2_result["total_strategic_moves"])
            results[scheme_name]["equilibrium_happiness"].append(atva2_result["final_avg_happiness"])
            results[scheme_name]["btva_happiness"].append(btva_result["new_avg_happiness"])
            
            if atva2_result["initial_winner"] != atva2_result["final_winner"]:
                results[scheme_name]["winner_changes"] += 1
            
            if atva2_result["equilibrium_type"] == "cycle":
                results[scheme_name]["cycles"] += 1
            elif atva2_result["equilibrium_type"] == "max_rounds":
                results[scheme_name]["max_rounds_reached"] += 1
            
            results[scheme_name]["total_situations"] += 1
    
    print("Experiments complete!\n")
    return results


def print_experiment_results(results):
    # print summary of experiment results in a table format
    print(f"\n{'Voting Scheme':<20} {'Avg Rounds':<15} {'Equilibrium H̄':<15} {'BTVA H̄':<15} {'Winner Change Rate'}")
    print("-" * 80)
    
    for scheme_name, data in results.items():
        avg_rounds = sum(data["rounds"]) / len(data["rounds"])
        avg_eq_happiness = sum(data["equilibrium_happiness"]) / len(data["equilibrium_happiness"])
        avg_btva_happiness = sum(data["btva_happiness"]) / len(data["btva_happiness"])
        winner_change_rate = data["winner_changes"] / data["total_situations"]
        
        print(f"{scheme_name:<20} {avg_rounds:<15.2f} {avg_eq_happiness:<15.3f} {avg_btva_happiness:<15.3f} {winner_change_rate:.2%}")
    
    print("-" * 80)
    

if __name__ == "__main__":
    # run experiments comparing counter-strategic voting with BTVA across multiple voting schemes
    from voting_schemes.plurality_voting import plurality_voting
    from voting_schemes.voting_for_two import voting_for_two
    from voting_schemes.antiplurality_voting import anti_plurality_voting
    from voting_schemes.borda_voting import borda_voting
    
    schemes = {
        "Plurality": plurality_voting,
        "Voting for Two": voting_for_two,
        "Anti-Plurality": anti_plurality_voting,
        "Borda": borda_voting
    }
    
    print("Running ATVA-2 experiments (n=5, m=4, 50 situations)...")
    results = run_experiments(schemes, num_situations=50, num_voters=5, num_candidates=4)
    print_experiment_results(results)
