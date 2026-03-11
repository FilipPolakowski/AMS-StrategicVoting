"""
All-Schemes BTVA Comparison
Fills Table 3 in the report (Section 3.1.2)

INSTRUCTIONS:
1. Save this file in the same directory as TVA.py
2. Run: python experiment_table3.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import random
import csv

from voting_schemes.plurality_voting import plurality_voting
from voting_schemes.voting_for_two import voting_for_two
from voting_schemes.antiplurality_voting import anti_plurality_voting
from voting_schemes.borda_voting import borda_voting

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


def run_all_schemes_comparison():
    """
    Compare all 4 voting schemes
    Configuration from Table 3: n=5, m=4, 50 trials
    """
    schemes = {
        'Plurality': plurality_voting,
        'Voting for Two': voting_for_two,
        'Anti-Plurality': anti_plurality_voting,
        'Borda': borda_voting
    }
    
    voters = 5
    alternatives = 4
    trials = 50
    
    results = {}
    
    print("="*70)
    print(f"ALL-SCHEMES BTVA COMPARISON (Table 3)")
    print(f"Configuration: n={voters}, m={alternatives}, trials={trials}")
    print("="*70)
    
    for scheme_name, voting_func in schemes.items():
        print(f"\n{scheme_name}...")
        
        total_happiness = 0
        strategic_count = 0
        total_risk = 0
        total_improvement = 0
        improvement_count = 0
        
        for trial in range(trials):
            # Generate random situation
            voting_situation, candidates = generate_random_situation(voters, alternatives)
            
            # Run honest voting
            scores, winner = voting_func(voting_situation, candidates, voters, alternatives)
            happiness_per_voter, avg_happiness = compute_happiness(
                voting_situation, winner, voters, alternatives
            )
            
            # Analyze strategic voting
            strategic_result = strategic_vote(
                voting_func, voting_situation, candidates, voters, alternatives
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
        avg_happiness = total_happiness / trials
        strategic_percent = (strategic_count / trials) * 100
        avg_risk = total_risk / trials
        avg_improvement = total_improvement / improvement_count if improvement_count > 0 else 0
        
        results[scheme_name] = {
            'avg_happiness': avg_happiness,
            'strategic_percent': strategic_percent,
            'avg_risk': avg_risk,
            'avg_improvement': avg_improvement
        }
        
        print(f"  Avg H̄: {avg_happiness:.3f}")
        print(f"  % strategic: {strategic_percent:.1f}%")
        print(f"  Avg R: {avg_risk:.4f}")
        print(f"  Avg ΔHi: {avg_improvement:.3f}")
    
    return results


def print_latex_table(results):
    """Print Table 3 in LaTeX format"""
    print("\n" + "="*70)
    print("LATEX TABLE 3 FORMAT:")
    print("="*70)
    
    scheme_order = ['Plurality', 'Voting for Two', 'Anti-Plurality', 'Borda']
    
    for scheme in scheme_order:
        r = results[scheme]
        print(f"{scheme:18s} & "
              f"{r['avg_happiness']:.3f} & "
              f"{r['strategic_percent']:.1f}\\% & "
              f"{r['avg_risk']:+.4f} & "
              f"{r['avg_improvement']:.3f} \\\\")


def save_results(results):
    """Save to CSV"""
    filename = 'table3_all_schemes_comparison.csv'
    
    rows = []
    for scheme, metrics in results.items():
        row = {'scheme': scheme}
        row.update(metrics)
        rows.append(row)
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['scheme', 'avg_happiness', 'strategic_percent', 
                                                'avg_risk', 'avg_improvement'])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Results saved to {filename}")


def analyze_results(results):
    """Generate insights for Section 3.3"""
    print("\n" + "="*70)
    print("INSIGHTS FOR SECTION 3.3:")
    print("="*70)
    
    # Find best/worst schemes
    happiness_ranking = sorted(results.items(), key=lambda x: x[1]['avg_happiness'], reverse=True)
    strategic_ranking = sorted(results.items(), key=lambda x: x[1]['strategic_percent'])
    
    print(f"\nHighest average happiness: {happiness_ranking[0][0]} ({happiness_ranking[0][1]['avg_happiness']:.3f})")
    print(f"Lowest average happiness: {happiness_ranking[-1][0]} ({happiness_ranking[-1][1]['avg_happiness']:.3f})")
    
    print(f"\nLeast susceptible to strategic voting: {strategic_ranking[0][0]} ({strategic_ranking[0][1]['strategic_percent']:.1f}%)")
    print(f"Most susceptible to strategic voting: {strategic_ranking[-1][0]} ({strategic_ranking[-1][1]['strategic_percent']:.1f}%)")
    
    print("\nKey comparisons:")
    for scheme, metrics in results.items():
        print(f"  {scheme:18s}: H̄={metrics['avg_happiness']:.3f}, "
              f"Strategic={metrics['strategic_percent']:5.1f}%, "
              f"R={metrics['avg_risk']:+.4f}")


if __name__ == '__main__':
    print("\nAll-Schemes BTVA Comparison")
    print("Generating Table 3 data for the report...")
    print("Testing: Plurality, Voting for Two, Anti-Plurality, Borda\n")
    
    input("Press Enter to start experiments...")
    
    results = run_all_schemes_comparison()
    print_latex_table(results)
    save_results(results)
    analyze_results(results)
    
    print("\n" + "="*70)
    print("EXPERIMENTS COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("1. Copy LaTeX table into Section 3.1.2 (Table 3)")
    print("2. Use insights for Section 3.3")
    print("3. Create a bar chart comparing schemes (optional)")
