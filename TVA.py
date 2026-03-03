3#TODO! 4 voting schemes:
#1:plurality - Philip
#2:voting for two - Miel
#3:Anti-plurality voting (veto) - Saanch
#4:Borda voting - Panagiotis

#Voting simulation

#Define happiness levels and risk of strategic voting measures

import random

from voting_schemes.antiplurality_voting import anti_plurality_voting
from voting_schemes.borda_voting import borda_voting
from voting_schemes.plurality_voting import plurality_voting
from voting_schemes.voting_for_two import voting_for_two

from strategic_voting import strategic_vote
from strategic_voting import compute_voting_risk
from strategic_voting import compute_happiness

from ATVAs.ATVA_4 import strategic_vote_atva4, print_atva4_results


def get_voting_situation():
    voters = int(input("Enter how many voters: "))
    preferences = int(input("Enter how many preferences: "))

    # Generate candidate labels: A, B, C, ...
    candidates = [chr(ord('A') + i) for i in range(preferences)]
    print("Candidates:", candidates)

    # Create table: rows = ranks, columns = voters
    voting_situation = [[None for _ in range(voters)] for _ in range(preferences)]
    #print(voting_situation)
    print("rows:", len(voting_situation))        # 3
    print("cols:", len(voting_situation[0]))     # 4


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
    print("         ", end="")
    for v in range(voters):
        print(f"V{v+1} ", end="")
    print()

    # Rows
    for r in range(preferences):
        print(f"Rank {r+1}: ", end="")
        for v in range(voters):
            print(f" {voting_situation[r][v]} ", end="")
        print()



def run_voting_scheme(scheme_name, voting_function, voting_situation, candidates, voters, preferences):
    print(f"\n{scheme_name}:")
    scores, winner = voting_function(voting_situation, candidates, voters, preferences)
    happiness_per_voter, avg_happiness = compute_happiness(voting_situation, winner, voters, preferences)
    print(f"Average Happiness: {avg_happiness:.3f}")
    
    return scores, winner, avg_happiness


if __name__ == '__main__':
    voting_situation, candidates, voters, preferences = get_voting_situation()
    
    print("Voting Situation :")
    print(f"Number of candidates: {len(candidates)}")
    print(f"Number of voters: {voters}")
    print_voting_situation(voting_situation, voters, preferences)
    
    # Ask user which voting scheme to use
    print("\nSELECT VOTING SCHEME")
    print("1. Plurality")
    print("2. Voting for Two")
    print("3. Anti-Plurality")
    print("4. Borda")
    print("5. All (compare all schemes)")
    print("6. Strategic Voting Analysis")
    print("7. ATVA Analysis")
    
    scheme = input("\nEnter your choice (1-7): ").strip()
    
    if scheme == '1':
        run_voting_scheme("PLURALITY VOTING", plurality_voting, voting_situation, candidates, voters, preferences)
        
    elif scheme == '2':
        run_voting_scheme("VOTING FOR TWO", voting_for_two, voting_situation, candidates, voters, preferences)
        
    elif scheme == '3':
        run_voting_scheme("ANTI-PLURALITY VOTING", anti_plurality_voting, voting_situation, candidates, voters, preferences)
        
    elif scheme == '4':
        run_voting_scheme("BORDA VOTING", borda_voting, voting_situation, candidates, voters, preferences)
        
    elif scheme == '5':
        # Run all voting schemes
        plurality_scores, plurality_winner, plurality_avg_happiness = run_voting_scheme("PLURALITY VOTING", plurality_voting, voting_situation, candidates, voters, preferences)
        
        vft_scores, vft_winner, vft_avg_happiness = run_voting_scheme("VOTING FOR TWO", voting_for_two, voting_situation, candidates, voters, preferences)
        
        anti_scores, anti_winner, anti_avg_happiness = run_voting_scheme("ANTI-PLURALITY VOTING", anti_plurality_voting, voting_situation, candidates, voters, preferences)
        
        borda_scores, borda_winner, borda_avg_happiness = run_voting_scheme("BORDA VOTING", borda_voting, voting_situation, candidates, voters, preferences)
        
        # Summary comparison
        print("\nSUMMARY:")
        print(f"Plurality:      Winner = {plurality_winner}, Avg Happiness = {plurality_avg_happiness:.3f}")
        print(f"Voting for Two: Winner = {vft_winner}, Avg Happiness = {vft_avg_happiness:.3f}")
        print(f"Anti-Plurality: Winner = {anti_winner}, Avg Happiness = {anti_avg_happiness:.3f}")
        print(f"Borda:          Winner = {borda_winner}, Avg Happiness = {borda_avg_happiness:.3f}")
    
    elif scheme == '6':
        # Strategic voting analysis
        print("\nSTRATEGIC VOTING ANALYSIS")
        print("Select voting scheme to analyze for strategic voting:")
        print("1. Plurality")
        print("2. Voting for Two")
        print("3. Anti-Plurality")
        print("4. Borda")
        
        sv_scheme = input("\nEnter your choice (1-4): ").strip()
        
        scheme_map = {
            '1': ("Plurality", plurality_voting),
            '2': ("Voting for Two", voting_for_two),
            '3': ("Anti-Plurality", anti_plurality_voting),
            '4': ("Borda", borda_voting)
        }
        
        if sv_scheme in scheme_map:
            scheme_name, voting_func = scheme_map[sv_scheme]
            print(f"\nAnalyzing {scheme_name} for strategic voting...")
            5050
            result = strategic_vote(voting_func, voting_situation, candidates, voters, preferences)
            
            print(f"\n{'='*60}")
            print(f"STRATEGIC VOTING ANALYSIS: {scheme_name}")
            print(f"{'='*60}")
            print(f"\nHonest Voting Results:")
            print(f"  Winner: {result['original_winner']}")
            print(f"  Avg Happiness: {result['original_avg_happiness']:.3f}")
            
            if result['changed']:
                print(f"\nStrategic Voter Found: Voter {result['strategic_voter']} can improve!")
                print(f"  Original Happiness: {result['strategic_voter_original_happiness']:.3f}")
                print(f"  New Happiness: {result['strategic_voter_new_happiness']:.3f}")
                print(f"  Improvement: {result['strategic_voter_new_happiness'] - result['strategic_voter_original_happiness']:.3f}")
                print(f"\nAfter Strategic Vote:")
                print(f"  New Winner: {result['new_winner']}")
                print(f"  New Avg Happiness: {result['new_avg_happiness']:.3f}")
                print(f"  Change in Avg Happiness: {result['new_avg_happiness'] - result['original_avg_happiness']:.3f}")
                print(compute_voting_risk(result['original_avg_happiness'], result['new_avg_happiness']))
            else:
                print(f"\nNo voter can improve his/her happiness strategically voting through single swaps...")
                print("No tactical voting risk, nobody votes strategically because voters are already as happy as they can be with their honest vote.")

            print(f"\n{'='*60}")
        else:
            print("Invalid choice. Please run the program again and select 1-4.")
    elif scheme == '7':
        print("\nADVANCED TACTICAL VOTING ANALYSIS (ATVA)")
        print("Choose ATVA variant:")
        print("1. ATVA-1 ")
        print("2. ATVA-2 ")
        print("3. ATVA-3 ")
        print("4. ATVA-4 (many voters vote strategically)")

        atva_choice = input("\nEnter your choice (1-4): ").strip()

        print("\nSelect voting scheme for ATVA:")
        print("1. Plurality")
        print("2. Voting for Two")
        print("3. Anti-Plurality")
        print("4. Borda")
        sv_scheme = input("\nEnter your choice (1-4): ").strip()

        scheme_map = {
        '1': ("Plurality", plurality_voting),
        '2': ("Voting for Two", voting_for_two),
        '3': ("Anti-Plurality", anti_plurality_voting),
        '4': ("Borda", borda_voting),
    }

        if sv_scheme not in scheme_map:
            print("Invalid scheme choice.")

        scheme_name, voting_func = scheme_map[sv_scheme]

        if atva_choice == '4':
            print(f"\nRunning ATVA-4 on {scheme_name}...")
            result = strategic_vote_atva4(
                voting_func, voting_situation, candidates, voters, preferences
            )

            print_atva4_results(result, scheme_name)

    else:
        print("Invalid choice. Please run the program again and select 1-7.")
    