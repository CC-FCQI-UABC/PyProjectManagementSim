#!/usr/bin/env python3
"""
Quick test script for the learning simulation.
"""

import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.normpath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from simulation_examples.only_learning import run_learning_simulation

if __name__ == "__main__":
    print("Testing learning simulation with 3 runs...")
    
    # Run just 3 simulations for testing
    results = run_learning_simulation(
        project_file=os.path.join(project_root, "data", "Software Development Plan.xml"),
        num_runs=3
    )
    
    print(f"Test completed! Results: {len(results)} runs")
    
    # Print first and last run stats
    if results:
        first_run = results[0]['final_stats']
        last_run = results[-1]['final_stats']
        
        print(f"\nFirst run:")
        print(f"  Tasks completed: {first_run['tasks_completed']}/{first_run['total_tasks']}")
        print(f"  Tasks failed: {first_run['tasks_failed']}")
        print(f"  Avg performance: {first_run['avg_performance']:.3f}")
        print(f"  Avg pleasure: {first_run['avg_pleasure']:.3f}")
        print(f"  Team collaboration: {first_run['team_collaboration']:.3f}")
        
        print(f"\nLast run:")
        print(f"  Tasks completed: {last_run['tasks_completed']}/{last_run['total_tasks']}")
        print(f"  Tasks failed: {last_run['tasks_failed']}")
        print(f"  Avg performance: {last_run['avg_performance']:.3f}")
        print(f"  Avg pleasure: {last_run['avg_pleasure']:.3f}")
        print(f"  Team collaboration: {last_run['team_collaboration']:.3f}")
        
        # Show improvement
        print(f"\nImprovement:")
        print(f"  Tasks completed: {last_run['tasks_completed'] - first_run['tasks_completed']:+d}")
        print(f"  Tasks failed: {last_run['tasks_failed'] - first_run['tasks_failed']:+d}")
        print(f"  Performance: {last_run['avg_performance'] - first_run['avg_performance']:+.3f}")
        print(f"  Pleasure: {last_run['avg_pleasure'] - first_run['avg_pleasure']:+.3f}")
        print(f"  Collaboration: {last_run['team_collaboration'] - first_run['team_collaboration']:+.3f}")
