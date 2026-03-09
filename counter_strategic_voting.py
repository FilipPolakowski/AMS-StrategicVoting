"""
Counter-Strategic Voting Module (Advanced TVA - ATVA)

This module implements multi-round strategic voting where voters can respond to
each other's strategic moves. The algorithm finds an equilibrium state where no
voter can improve their happiness through further manipulation.

Algorithm:
1. Start with honest voting
2. Find the least happy voter who can improve through strategic manipulation
3. Apply their strategic vote
4. Repeat steps 2-3 with the new voting situation
5. Continue until:
   - No voter can improve (Nash-like equilibrium)
   - A cycle is detected (voters keep responding to each other)
   - Maximum rounds reached

This allows analysis of:
- Strategic cascades (chains of counter-strategic responses)
- Final equilibrium outcomes vs. honest voting
- Stability of voting schemes under strategic behavior
- Social welfare changes from strategic manipulation
"""

from copy import deepcopy


def compute_happiness(voting_situation, winner, voters, preferences):
    """Compute each voter's happiness based on TRUE preferences."""
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


def _get_voter_pref(voting_situation, voter_index):
    """Extract one voter's preference list from the voting situation matrix."""
    prefs = []
    for row in voting_situation:
        prefs.append(row[voter_index])
    return prefs


def _set_voter_pref(voting_situation, voter_index, pref_list):
    """Set one voter's preference list in the voting situation matrix."""
    for r in range(len(pref_list)):
        voting_situation[r][voter_index] = pref_list[r]


def _all_strategic_manipulations(pref_list):
    """
    Generate all possible strategic manipulations:
    1. Single swaps: swap any two positions
    2. Move to top: move any candidate to first position (boost strategy)
    3. Move to bottom: move any candidate to last position (bury strategy)
    
    For example: [A, B, C, D]
    - Swaps: [B, A, C, D], [C, B, A, D], etc.
    - Move to top: [B, A, C, D], [C, A, B, D], [D, A, B, C]
    - Move to bottom: [B, C, D, A], [A, C, D, B], [A, B, D, C]
    """
    out = []
    m = len(pref_list)
    
    # 1. All single swaps
    for i in range(m - 1):
        for j in range(i + 1, m):
            temp = pref_list[:]
            temp[i], temp[j] = temp[j], temp[i]
            out.append(temp)
    
    # 2. Move each candidate to top (position 0)
    for i in range(1, m):  # Skip i=0 (already at top)
        temp = pref_list[:]
        candidate = temp.pop(i)  # Remove from current position
        temp.insert(0, candidate)  # Insert at top
        out.append(temp)
    
    # 3. Move each candidate to bottom (last position)
    for i in range(m - 1):  # Skip i=m-1 (already at bottom)
        temp = pref_list[:]
        candidate = temp.pop(i)  # Remove from current position
        temp.append(candidate)  # Append to bottom
        out.append(temp)
    
    return out


def _voting_situation_to_tuple(voting_situation):
    """Convert voting situation to a hashable tuple for cycle detection."""
    return tuple(tuple(row) for row in voting_situation)


def find_strategic_voter(voting_function, voting_situation, true_situation, 
                        candidates, voters, preferences, current_happiness):
    """
    Find a single voter who can improve their happiness through strategic voting.
    
    Returns:
        dict with keys:
            - found: bool (whether a strategic voter was found)
            - voter_index: int (which voter can improve)
            - original_pref: list (their current ballot)
            - strategic_pref: list (their new strategic ballot)
            - new_voting_situation: matrix (updated voting situation)
            - new_winner: str (winner after strategic vote)
            - new_happiness: list (happiness per voter after strategic vote)
            - new_avg_happiness: float (average happiness after strategic vote)
            - improvement: float (how much the strategic voter improved)
    """
    
    # Order voters by happiness (least happy first, ties broken by higher index)
    order = list(range(voters))
    order.sort(key=lambda i: (current_happiness[i], -i))
    
    for v in order:
        current_pref = _get_voter_pref(voting_situation, v)
        baseline_happiness = current_happiness[v]
        
        best_tactical_pref = None
        best_trial_winner = None
        best_trial_happiness = None
        best_trial_avg = None
        best_voter_happiness = baseline_happiness
        
        # Try all strategic manipulations (swaps, move-to-top, move-to-bottom)
        for tactical_pref in _all_strategic_manipulations(current_pref):
            trial = deepcopy(voting_situation)
            _set_voter_pref(trial, v, tactical_pref)
            
            _, trial_winner = voting_function(trial, candidates, voters, preferences)
            trial_happiness, trial_avg = compute_happiness(true_situation, trial_winner, voters, preferences)
            
            # Check if this voter's happiness improved
            if trial_happiness[v] > best_voter_happiness:
                best_voter_happiness = trial_happiness[v]
                best_tactical_pref = tactical_pref
                best_trial_winner = trial_winner
                best_trial_happiness = trial_happiness
                best_trial_avg = trial_avg
        
        # If this voter found an improvement, return it
        if best_tactical_pref is not None:
            new_matrix = deepcopy(voting_situation)
            _set_voter_pref(new_matrix, v, best_tactical_pref)
            
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
    
    # No voter can improve
    return {"found": False}


def counter_strategic_voting(voting_function, voting_situation, candidates, voters, preferences, max_rounds=20):
    """
    Execute multi-round counter-strategic voting until equilibrium is reached.
    
    Args:
        voting_function: The voting scheme function to use
        voting_situation: Initial voting situation matrix
        candidates: List of candidate names
        voters: Number of voters
        preferences: Number of preferences (candidates)
        max_rounds: Maximum number of strategic rounds to prevent infinite loops
    
    Returns:
        dict containing:
            - rounds: List of all strategic moves
            - initial_winner: Winner with honest voting
            - final_winner: Winner at equilibrium
            - initial_avg_happiness: Average happiness with honest voting
            - final_avg_happiness: Average happiness at equilibrium
            - equilibrium_type: "stable", "cycle", or "max_rounds"
            - total_strategic_moves: Number of strategic votes that occurred
            - unique_strategic_voters: Set of voters who voted strategically
    """
    
    # Keep true preferences for happiness calculations
    true_situation = deepcopy(voting_situation)
    
    # Get initial honest results
    _, initial_winner = voting_function(voting_situation, candidates, voters, preferences)
    initial_happiness, initial_avg = compute_happiness(true_situation, initial_winner, voters, preferences)
    
    # Track all rounds
    rounds = []
    current_situation = deepcopy(voting_situation)
    current_happiness = initial_happiness[:]
    current_avg = initial_avg
    
    # For cycle detection
    seen_states = {_voting_situation_to_tuple(current_situation)}
    
    # Track which voters have voted strategically
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
            # No one can improve - stable equilibrium reached
            equilibrium_type = "stable"
            break
        
        # Record this strategic move
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
        
        # Update current state
        current_situation = result["new_voting_situation"]
        current_happiness = result["new_happiness"]
        current_avg = result["new_avg_happiness"]
        
        # Check for cycles
        state_tuple = _voting_situation_to_tuple(current_situation)
        if state_tuple in seen_states:
            equilibrium_type = "cycle"
            break
        seen_states.add(state_tuple)
    else:
        # Reached max rounds
        equilibrium_type = "max_rounds"
    
    # Get final winner
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
    """
    Pretty-print the results of counter-strategic voting analysis.
    """
    print(f"\n{'='*70}")
    print(f"COUNTER-STRATEGIC VOTING ANALYSIS: {scheme_name}")
    print(f"{'='*70}")
    
    print(f"\nINITIAL (HONEST) VOTING:")
    print(f"  Winner: {result['initial_winner']}")
    print(f"  Average Happiness: {result['initial_avg_happiness']:.3f}")
    
    if result['total_strategic_moves'] == 0:
        print(f"\n✓ STABLE EQUILIBRIUM REACHED")
        print(f"  No voter can improve through strategic voting.")
        print(f"  The honest outcome is already at equilibrium!")
    else:
        print(f"\nSTRATEGIC CASCADE ({result['total_strategic_moves']} rounds):")
        print(f"{'─'*70}")
        
        for r in result['rounds']:
            print(f"\n  Round {r['round']}: Voter {r['voter'] + 1} votes strategically")
            print(f"    Original ballot: {' > '.join(r['original_ballot'])}")
            print(f"    Strategic ballot: {' > '.join(r['strategic_ballot'])}")
            print(f"    New winner: {r['winner']}")
            print(f"    Voter happiness: {r['voter_happiness_before']:.3f} → {r['voter_happiness_after']:.3f} (+{r['improvement']:.3f})")
            print(f"    Average happiness: {r['avg_happiness']:.3f}")
        
        print(f"\n{'─'*70}")
        print(f"\nFINAL EQUILIBRIUM:")
        print(f"  Type: {result['equilibrium_type'].upper()}")
        print(f"  Winner: {result['final_winner']}")
        print(f"  Average Happiness: {result['final_avg_happiness']:.3f}")
        print(f"  Unique strategic voters: {len(result['unique_strategic_voters'])}/{len(result['initial_happiness'])}")
        
        # Analysis
        print(f"\nIMPACT ANALYSIS:")
        winner_changed = result['initial_winner'] != result['final_winner']
        happiness_change = result['final_avg_happiness'] - result['initial_avg_happiness']
        
        if winner_changed:
            print(f"  ⚠ Winner changed: {result['initial_winner']} → {result['final_winner']}")
        else:
            print(f"  ✓ Winner unchanged: {result['final_winner']}")
        
        if happiness_change > 0:
            print(f"  ↑ Average happiness increased by {happiness_change:.3f}")
        elif happiness_change < 0:
            print(f"  ↓ Average happiness decreased by {abs(happiness_change):.3f}")
            print(f"  ⚠ TACTICAL VOTING RISK: Strategic behavior reduced overall welfare")
        else:
            print(f"  → Average happiness unchanged")
        
        if result['equilibrium_type'] == 'stable':
            print(f"\n  ✓ Stable equilibrium: No voter can further improve")
        elif result['equilibrium_type'] == 'cycle':
            print(f"\n  ⚠ Cycle detected: Voters keep responding to each other")
        else:
            print(f"\n  ⚠ Maximum rounds reached: Equilibrium may not be stable")
    
    print(f"\n{'='*70}")
