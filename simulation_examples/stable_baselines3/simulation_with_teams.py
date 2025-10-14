#!/usr/bin/env python3
"""
Simulation script with team experience selection via command line
Usage: python simulation_examples/simulation_with_teams.py [beginner|expert|custom] [num_runs]
"""

import os
import sys
import shutil
from datetime import datetime
import json
import numpy as np

# Ensure the project root is in the sys.path for imports to work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.normpath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from simulation_examples.only_learning_sb3 import run_learning_simulation_sb3

def setup_team_data(experience_level):
    """Setup the appropriate team data file."""
    if experience_level == 'beginner':
        source_file = os.path.join(project_root, "core", "generated", "agent_learning_data_beginner_sb3.pkl")
        target_file = os.path.join(project_root, "core", "generated", "agent_learning_data_sb3.pkl")
        team_type = "BEGINNER"
    elif experience_level == 'expert':
        source_file = os.path.join(project_root, "core", "generated", "agent_learning_data_expert_sb3.pkl")
        target_file = os.path.join(project_root, "core", "generated", "agent_learning_data_sb3.pkl")
        team_type = "EXPERT"
    else:  # custom
        target_file = os.path.join(project_root, "core", "generated", "agent_learning_data_sb3.pkl")
        if os.path.exists(target_file):
            team_type = "CUSTOM (existing data)"
        else:
            print("No existing learning data found. Using default beginner settings.")
            team_type = "DEFAULT"
        return team_type
    
    # Copy the appropriate data file
    if os.path.exists(source_file):
        shutil.copy2(source_file, target_file)
        print(f"Loaded {team_type} team data successfully!")
    else:
        print(f"Warning: {source_file} not found. Using default settings.")
        team_type = "DEFAULT"
    
    return team_type

def print_usage():
    """Print usage information."""
    print("=" * 60)
    print("  SIMULATION WITH TEAM SELECTION")
    print("=" * 60)
    print("Usage: python simulation_examples/simulation_with_teams.py [team_type] [num_runs]")
    print()
    print("Team types:")
    print("  beginner - New team with no experience")
    print("             Low skill levels (0.25-0.35)")
    print("             Low collaboration (0.15-0.25)")
    print("             High exploration, learns from scratch")
    print()
    print("  expert   - Experienced project managers")
    print("             High skill levels (0.88-0.94)")
    print("             High collaboration (0.82-0.88)")
    print("             Low exploration, uses experience")
    print()
    print("  custom   - Use existing learning data")
    print("             Uses current agent_learning_data_sb3.pkl")
    print()
    print("Examples:")
    print("  python simulation_examples/simulation_with_teams.py beginner 3")
    print("  python simulation_examples/simulation_with_teams.py expert 5")
    print("  python simulation_examples/simulation_with_teams.py custom")
    print("=" * 60)

def run_simulation(experience_level='beginner', num_runs=3):
    """Run the simulation with selected team."""
    print(f"\nStarting simulation with {experience_level.upper()} team...")
    print(f"Number of runs: {num_runs}")
    print("=" * 60)
    
    # Setup team data
    team_type = setup_team_data(experience_level)
    
    # Run simulation
    results = run_learning_simulation_sb3(
        project_file=os.path.join(project_root, "data", "Software Development Plan.xml"),
        num_runs=num_runs
    )
    
    print(f"\nSimulation completed! Results: {len(results)} runs")
    
    # Print results
    if results:
        first_run = results[0]['final_stats']
        last_run = results[-1]['final_stats']
        
        print(f"\nFirst run:")
        print(f"  Tasks completed: {first_run['tasks_completed']}/{first_run['total_tasks']}")
        print(f"  Tasks failed: {first_run['tasks_failed']}")
        print(f"  Avg performance: {first_run['avg_performance']:.3f}")
        print(f"  Avg pleasure: {first_run['avg_pleasure']:.3f}")
        print(f"  Team collaboration: {first_run['team_collaboration']:.3f}")
        print(f"  Total steps: {first_run['total_steps']}")
        
        if len(results) > 1:
            print(f"\nLast run:")
            print(f"  Tasks completed: {last_run['tasks_completed']}/{last_run['total_tasks']}")
            print(f"  Tasks failed: {last_run['tasks_failed']}")
            print(f"  Avg performance: {last_run['avg_performance']:.3f}")
            print(f"  Avg pleasure: {last_run['avg_pleasure']:.3f}")
            print(f"  Team collaboration: {last_run['team_collaboration']:.3f}")
            print(f"  Total steps: {last_run['total_steps']}")
            
            # Show improvement
            print(f"\nImprovement:")
            print(f"  Tasks completed: {last_run['tasks_completed'] - first_run['tasks_completed']:+d}")
            print(f"  Tasks failed: {last_run['tasks_failed'] - first_run['tasks_failed']:+d}")
            print(f"  Performance: {last_run['avg_performance'] - first_run['avg_performance']:+.3f}")
            print(f"  Pleasure: {last_run['avg_pleasure'] - first_run['avg_pleasure']:+.3f}")
            print(f"  Collaboration: {last_run['team_collaboration'] - first_run['team_collaboration']:+.3f}")
        
        print(f"\nTeam type used: {team_type}")
        print(f"RL Model: DQN (Stable Baselines3)")
        print(f"Learning enabled: True")

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    experience_level = sys.argv[1].lower()
    if experience_level not in ['beginner', 'expert', 'custom']:
        print(f"Error: Invalid team type '{experience_level}'")
        print_usage()
        sys.exit(1)
    
    num_runs = 3  # default
    if len(sys.argv) > 2:
        try:
            num_runs = int(sys.argv[2])
            if num_runs <= 0:
                print("Error: Number of runs must be positive")
                sys.exit(1)
        except ValueError:
            print("Error: Number of runs must be an integer")
            sys.exit(1)
    
    try:
        run_simulation(experience_level, num_runs)
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
    except Exception as e:
        print(f"\nError during simulation: {e}")
        import traceback
        traceback.print_exc()
