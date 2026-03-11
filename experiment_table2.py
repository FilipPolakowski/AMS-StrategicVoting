"""
Anti-Plurality BTVA Experiments
Fills Table 2 in the report (Section 3.1.1)
"""


import sys
import os

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import random
import csv

from voting_schemes.antiplurality_voting import anti_plurality_voting
from voting_schemes.strategic_voting import strategic_vote, compute_happiness

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


def run_anti_plurality_btva_experiments():
    """
    Run BTVA experiments for Anti-Plurality voting
    Tests configurations from Table 2
    """
    # Configurations from Table 2
    configs = [
        (3, 3),
        (5, 3),
        (5, 4),
        (10, 4),
        (10, 5),
        (20, 5)
    ]
    
    trials_per_config = 50  # As specified in report
    results = []
    
    print("="*70)
    print("ANTI-PLURALITY BTVA EXPERIMENTS (Table 2)")
    print("="*70)
    
    for voters, alternatives in configs:
        print(f"\nRunning: n={voters}, m={alternatives}...")
        
        # Metrics for this configuration
        total_happiness = 0
        strategic_count = 0
        total_risk = 0
        total_improvement = 0
        improvement_count = 0
        
        for trial in range(trials_per_config):
            # Generate random situation
            voting_situation, candidates = generate_random_situation(voters, alternatives)
            
            # Run honest voting
            scores, winner = anti_plurality_voting(
                voting_situation, candidates, voters, alternatives
            )
            happiness_per_voter, avg_happiness = compute_happiness(
                voting_situation, winner, voters, alternatives
            )
            
            # Analyze strategic voting
            strategic_result = strategic_vote(
                anti_plurality_voting, voting_situation, candidates, voters, alternatives
            )
            
            # Accumulate metrics
            total_happiness += avg_happiness
            
            if strategic_result['changed']:
                strategic_count += 1
                total_risk += (strategic_result['new_avg_happiness'] - avg_happiness)
                
                improvement = (
                    strategic_result['strategic_voter_new_happiness'] - 
                    strategic_result['strategic_voter_original_happiness']
                )
                total_improvement += improvement
                improvement_count += 1
        
        # Calculate averages
        avg_happiness = total_happiness / trials_per_config
        strategic_percent = (strategic_count / trials_per_config) * 100
        avg_risk = total_risk / trials_per_config
        avg_improvement = total_improvement / improvement_count if improvement_count > 0 else 0
        
        result = {
            'n': voters,
            'm': alternatives,
            'avg_happiness': avg_happiness,
            'strategic_percent': strategic_percent,
            'avg_risk': avg_risk,
            'avg_improvement': avg_improvement,
            'strategic_count': strategic_count,
            'trials': trials_per_config
        }
        results.append(result)
        
        print(f"  Avg H̄: {avg_happiness:.3f}")
        print(f"  % with strategic voter: {strategic_percent:.1f}%")
        print(f"  Avg R: {avg_risk:.4f}")
        print(f"  Avg ΔHi: {avg_improvement:.3f}")
    
    return results


def print_latex_table(results):
    """Print results in LaTeX table format for Table 2"""
    print("\n" + "="*70)
    print("LATEX TABLE 2 FORMAT:")
    print("="*70)
    
    for r in results:
        print(f"{r['n']:2d} & {r['m']:2d} & "
              f"{r['avg_happiness']:.3f} & "
              f"{r['strategic_percent']:.1f}\\% & "
              f"{r['avg_risk']:+.4f} & "
              f"{r['avg_improvement']:.3f} \\\\")


def save_results(results):
    """Save to CSV"""
    filename = 'table2_anti_plurality_btva.csv'
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n✓ Results saved to {filename}")


if __name__ == '__main__':
    print("\nAnti-Plurality BTVA Experiment Suite")
    print("Generating Table 2 data for the report...")
    print("This will run 50 trials per configuration (300 total trials)\n")
    
    input("Press Enter to start experiments...")
    
    results = run_anti_plurality_btva_experiments()
    print_latex_table(results)
    save_results(results)
    
    print("\n" + "="*70)
    print("EXPERIMENTS COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("1. Copy the LaTeX table output into Section 3.1.1 (Table 2)")
    print("2. Use these results for Section 3.3 (Insights)")
    print("3. Discuss patterns in Section 3.4")
