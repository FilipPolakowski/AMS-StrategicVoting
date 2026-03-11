"""
ATVA-3 Experiments: Imperfect Knowledge
Fills Table 6 in the report (Section 4.3.2)

INSTRUCTIONS:
1. Save this file in the same directory as TVA.py
2. Run: python experiment_table6.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import random
import csv
import copy

from voting_schemes.plurality_voting import plurality_voting
from voting_schemes.voting_for_two import voting_for_two
from voting_schemes.antiplurality_voting import anti_plurality_voting
from voting_schemes.borda_voting import borda_voting


def generate_random_situation(voters, preferences):
    """Generate random voting situation"""
    candidates = [chr(ord('A') + i) for i in range(preferences)]
    voting_situation = [[None for _ in range(voters)] for _ in range(preferences)]
    
    for voter in range(voters):
        prefs = candidates[:]
        random.shuffle(prefs)
        for r in range(preferences):
            voting_situation[r][voter] = prefs[r]
    
    return voting_situation, candidates


def add_noise_to_preferences(voting_situation, voters, preferences, p_noise):
    """
    Add noise to preference observations
    With probability p_noise, swap each adjacent pair
    """
    noisy_situation = copy.deepcopy(voting_situation)
    
    for voter in range(voters):
        for r in range(preferences - 1):
            if random.random() < p_noise:
                # Swap adjacent ranks
                temp = noisy_situation[r][voter]
                noisy_situation[r][voter] = noisy_situation[r + 1][voter]
                noisy_situation[r + 1][voter] = temp
    
    return noisy_situation


def compute_happiness(voting_situation, winner, voters, preferences):
    """Calculate happiness for all voters"""
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
    
    avg_happiness = total_happiness / voters if voters else 0
    return happiness_per_voter, avg_happiness


def strategic_vote_with_noise(voting_func, voting_situation, candidates, voters, preferences, p_noise, K=100):
    """
    Strategic voting under imperfect knowledge
    
    Args:
        K: Number of Monte Carlo samples for expected value estimation
        p_noise: Probability of adjacent swap in belief
    """
    # Honest voting outcome
    scores, original_winner = voting_func(voting_situation, candidates, voters, preferences)
    happiness_per_voter, original_avg_happiness = compute_happiness(
        voting_situation, original_winner, voters, preferences
    )
    
    # Find voter with lowest happiness
    min_happiness = min(happiness_per_voter)
    strategic_voter = happiness_per_voter.index(min_happiness)
    
    best_swap = None
    best_expected_gain = 0
    
    # Try all single swaps
    for swap_pos in range(preferences - 1):
        # Calculate expected gain from this swap over K samples
        expected_gains = []
        
        for _ in range(K):
            # Sample noisy beliefs about others' preferences
            noisy_situation = add_noise_to_preferences(
                voting_situation, voters, preferences, p_noise
            )
            
            # Apply the swap to strategic voter
            test_situation = copy.deepcopy(noisy_situation)
            temp = test_situation[swap_pos][strategic_voter]
            test_situation[swap_pos][strategic_voter] = test_situation[swap_pos + 1][strategic_voter]
            test_situation[swap_pos + 1][strategic_voter] = temp
            
            # See new outcome under this sample
            _, new_winner = voting_func(test_situation, candidates, voters, preferences)
            
            # Calculate happiness gain (measured against TRUE preferences)
            new_happiness = 0
            for r in range(preferences):
                if voting_situation[r][strategic_voter] == new_winner:
                    new_happiness = 1 / (r + 1)
                    break
            
            gain = new_happiness - happiness_per_voter[strategic_voter]
            expected_gains.append(gain)
        
        # Average gain over samples
        avg_gain = sum(expected_gains) / K
        
        if avg_gain > best_expected_gain:
            best_expected_gain = avg_gain
            best_swap = swap_pos
    
    # If a beneficial swap exists, apply it
    changed = best_expected_gain > 0
    
    if changed:
        # Apply best swap to TRUE voting situation
        modified_situation = copy.deepcopy(voting_situation)
        temp = modified_situation[best_swap][strategic_voter]
        modified_situation[best_swap][strategic_voter] = modified_situation[best_swap + 1][strategic_voter]
        modified_situation[best_swap + 1][strategic_voter] = temp
        
        # Calculate actual outcome
        _, new_winner = voting_func(modified_situation, candidates, voters, preferences)
        _, new_avg_happiness = compute_happiness(voting_situation, new_winner, voters, preferences)
        
        risk = new_avg_happiness - original_avg_happiness
        winner_changed = (new_winner != original_winner)
    else:
        risk = 0
        winner_changed = False
    
    return {
        'changed': changed,
        'original_avg_happiness': original_avg_happiness,
        'risk': risk,
        'expected_gain': best_expected_gain,
        'winner_changed': winner_changed
    }


def run_atva3_experiments():
    """
    Run ATVA-3 experiments for Table 6
    Test all schemes at different noise levels
    """
    schemes = {
        'Plurality': plurality_voting,
        'Voting for Two': voting_for_two,
        'Anti-Plurality': anti_plurality_voting,
        'Borda': borda_voting
    }
    
    noise_levels = [0.0, 0.1, 0.3, 0.5]  # p values from Table 6
    voters = 5
    alternatives = 4
    trials = 50  # Number of random situations
    K = 100  # Monte Carlo samples per deviation
    
    results = {scheme: {p: {} for p in noise_levels} for scheme in schemes}
    
    print("="*70)
    print(f"ATVA-3 EXPERIMENTS (Table 6)")
    print(f"Configuration: n={voters}, m={alternatives}, K={K} samples")
    print("="*70)
    
    for scheme_name, voting_func in schemes.items():
        print(f"\n{scheme_name}:")
        
        for p_noise in noise_levels:
            print(f"  p={p_noise}...", end=" ")
            
            total_risk = 0
            strategic_count = 0
            winner_change_count = 0
            
            for trial in range(trials):
                voting_situation, candidates = generate_random_situation(voters, alternatives)
                
                result = strategic_vote_with_noise(
                    voting_func, voting_situation, candidates, 
                    voters, alternatives, p_noise, K
                )
                
                total_risk += result['risk']
                if result['changed']:
                    strategic_count += 1
                if result['winner_changed']:
                    winner_change_count += 1
            
            avg_risk = total_risk / trials
            strategic_percent = (strategic_count / trials) * 100
            winner_change_percent = (winner_change_count / trials) * 100
            
            results[scheme_name][p_noise] = {
                'avg_risk': avg_risk,
                'strategic_percent': strategic_percent,
                'winner_change_percent': winner_change_percent
            }
            
            print(f"R={avg_risk:+.4f}, Strategic={strategic_percent:.1f}%, Winner change={winner_change_percent:.1f}%")
    
    return results


def print_latex_table(results):
    """Print Table 6 in LaTeX format"""
    print("\n" + "="*70)
    print("LATEX TABLE 6 FORMAT (Option 1 - Risk values):")
    print("="*70)
    
    schemes_order = ['Plurality', 'Voting for Two', 'Anti-Plurality', 'Borda']
    noise_levels = [0.0, 0.1, 0.3, 0.5]
    
    for scheme in schemes_order:
        row = f"{scheme:18s} & "
        for p in noise_levels:
            r = results[scheme][p]['avg_risk']
            row += f"{r:+.4f} & "
        row = row.rstrip(" & ") + " \\\\"
        print(row)
    
    print("\n" + "="*70)
    print("LATEX TABLE 6 FORMAT (Option 2 - With winner change rate):")
    print("Scheme | p=0 | p=0.1 | p=0.3 | p=0.5")
    print("Each cell: Risk (Winner change %)")
    print("="*70)
    
    for scheme in schemes_order:
        row = f"{scheme:18s} & "
        for p in noise_levels:
            r = results[scheme][p]['avg_risk']
            w = results[scheme][p]['winner_change_percent']
            row += f"{r:+.4f} ({w:.0f}\\%) & "
        row = row.rstrip(" & ") + " \\\\"
        print(row)


def save_results(results):
    """Save to CSV"""
    filename = 'table6_atva3_imperfect_knowledge.csv'
    
    rows = []
    for scheme, noise_data in results.items():
        for p_noise, metrics in noise_data.items():
            rows.append({
                'scheme': scheme,
                'p_noise': p_noise,
                'avg_risk': metrics['avg_risk'],
                'strategic_percent': metrics['strategic_percent'],
                'winner_change_percent': metrics['winner_change_percent']
            })
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['scheme', 'p_noise', 'avg_risk', 
                                                'strategic_percent', 'winner_change_percent'])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Results saved to {filename}")


if __name__ == '__main__':
    print("\nATVA-3 Imperfect Knowledge Experiment Suite")
    print("Generating Table 6 data for the report...")
    print("This tests how noise affects strategic voting incentives\n")
    
    input("Press Enter to start experiments (this may take a few minutes)...")
    
    results = run_atva3_experiments()
    print_latex_table(results)
    save_results(results)
    
    print("\n" + "="*70)
    print("EXPERIMENTS COMPLETE!")
    print("="*70)
    print("\nInsights to discuss in Section 4.3.4:")
    print("- Does uncertainty (higher p) reduce strategic voting?")
    print("- Which scheme is most robust to noise?")
    print("- At p=0.5 (high uncertainty), does strategic voting still occur?")
    print("- How does winner change rate correlate with noise level?")
