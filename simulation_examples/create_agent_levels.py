#!/usr/bin/env python3
"""
Script to create different agent experience levels
"""

import os
import sys
import pickle
import numpy as np
from typing import Dict, Any

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.normpath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def create_beginner_agents_data():
    """Create learning data for beginner agents."""
    
    # Path to the learning data file
    learning_file = os.path.join(project_root, "core", "generated", "agent_learning_data_beginner_sb3.pkl")
    
    # Create beginner agent data
    beginner_data = {
        'agent_0': {
            'q_table': {},
            'learning_rate': 0.1,  # Higher learning rate for beginners
            'discount_factor': 0.9,
            'epsilon': 0.3,  # Higher exploration for beginners
            'experience_count': 0,  # No experience
            'success_rate': 0.3,  # Low success rate
            'collaboration_level': 0.2,  # Low collaboration
            'skill_level': 0.3,  # Low skill
            'emotional_stability': 0.4,  # Low emotional stability
            'stress_resistance': 0.3,  # Low stress resistance
            'task_completion_history': [0.3] * 10,  # Poor completion history
            'team_work_history': [0.2] * 10,  # Poor teamwork history
            'performance_history': [0.3] * 10,  # Low performance history
            'personality': {
                'conscientiousness': 0.4,
                'openness': 0.5,
                'extraversion': 0.6,
                'agreeableness': 0.4,
                'neuroticism': 0.7,
                'resilience': 0.3,
                'sociability': 0.5
            }
        },
        'agent_1': {
            'q_table': {},
            'learning_rate': 0.1,
            'discount_factor': 0.9,
            'epsilon': 0.3,
            'experience_count': 0,
            'success_rate': 0.25,
            'collaboration_level': 0.15,
            'skill_level': 0.25,
            'emotional_stability': 0.35,
            'stress_resistance': 0.25,
            'task_completion_history': [0.25] * 10,
            'team_work_history': [0.15] * 10,
            'performance_history': [0.25] * 10,
            'personality': {
                'conscientiousness': 0.35,
                'openness': 0.6,
                'extraversion': 0.7,
                'agreeableness': 0.3,
                'neuroticism': 0.8,
                'resilience': 0.25,
                'sociability': 0.6
            }
        },
        'agent_2': {
            'q_table': {},
            'learning_rate': 0.1,
            'discount_factor': 0.9,
            'epsilon': 0.3,
            'experience_count': 0,
            'success_rate': 0.35,
            'collaboration_level': 0.25,
            'skill_level': 0.35,
            'emotional_stability': 0.45,
            'stress_resistance': 0.35,
            'task_completion_history': [0.35] * 10,
            'team_work_history': [0.25] * 10,
            'performance_history': [0.35] * 10,
            'personality': {
                'conscientiousness': 0.45,
                'openness': 0.4,
                'extraversion': 0.5,
                'agreeableness': 0.5,
                'neuroticism': 0.6,
                'resilience': 0.35,
                'sociability': 0.4
            }
        },
        'agent_3': {
            'q_table': {},
            'learning_rate': 0.1,
            'discount_factor': 0.9,
            'epsilon': 0.3,
            'experience_count': 0,
            'success_rate': 0.28,
            'collaboration_level': 0.18,
            'skill_level': 0.28,
            'emotional_stability': 0.38,
            'stress_resistance': 0.28,
            'task_completion_history': [0.28] * 10,
            'team_work_history': [0.18] * 10,
            'performance_history': [0.28] * 10,
            'personality': {
                'conscientiousness': 0.38,
                'openness': 0.55,
                'extraversion': 0.65,
                'agreeableness': 0.35,
                'neuroticism': 0.75,
                'resilience': 0.28,
                'sociability': 0.55
            }
        },
        'agent_4': {
            'q_table': {},
            'learning_rate': 0.1,
            'discount_factor': 0.9,
            'epsilon': 0.3,
            'experience_count': 0,
            'success_rate': 0.32,
            'collaboration_level': 0.22,
            'skill_level': 0.32,
            'emotional_stability': 0.42,
            'stress_resistance': 0.32,
            'task_completion_history': [0.32] * 10,
            'team_work_history': [0.22] * 10,
            'performance_history': [0.32] * 10,
            'personality': {
                'conscientiousness': 0.42,
                'openness': 0.45,
                'extraversion': 0.55,
                'agreeableness': 0.45,
                'neuroticism': 0.65,
                'resilience': 0.32,
                'sociability': 0.45
            }
        },
        'agent_5': {
            'q_table': {},
            'learning_rate': 0.1,
            'discount_factor': 0.9,
            'epsilon': 0.3,
            'experience_count': 0,
            'success_rate': 0.26,
            'collaboration_level': 0.16,
            'skill_level': 0.26,
            'emotional_stability': 0.36,
            'stress_resistance': 0.26,
            'task_completion_history': [0.26] * 10,
            'team_work_history': [0.16] * 10,
            'performance_history': [0.26] * 10,
            'personality': {
                'conscientiousness': 0.36,
                'openness': 0.65,
                'extraversion': 0.75,
                'agreeableness': 0.25,
                'neuroticism': 0.85,
                'resilience': 0.26,
                'sociability': 0.65
            }
        },
        'agent_6': {
            'q_table': {},
            'learning_rate': 0.1,
            'discount_factor': 0.9,
            'epsilon': 0.3,
            'experience_count': 0,
            'success_rate': 0.34,
            'collaboration_level': 0.24,
            'skill_level': 0.34,
            'emotional_stability': 0.44,
            'stress_resistance': 0.34,
            'task_completion_history': [0.34] * 10,
            'team_work_history': [0.24] * 10,
            'performance_history': [0.34] * 10,
            'personality': {
                'conscientiousness': 0.44,
                'openness': 0.35,
                'extraversion': 0.45,
                'agreeableness': 0.55,
                'neuroticism': 0.55,
                'resilience': 0.34,
                'sociability': 0.35
            }
        },
        'agent_7': {
            'q_table': {},
            'learning_rate': 0.1,
            'discount_factor': 0.9,
            'epsilon': 0.3,
            'experience_count': 0,
            'success_rate': 0.29,
            'collaboration_level': 0.19,
            'skill_level': 0.29,
            'emotional_stability': 0.39,
            'stress_resistance': 0.29,
            'task_completion_history': [0.29] * 10,
            'team_work_history': [0.19] * 10,
            'performance_history': [0.29] * 10,
            'personality': {
                'conscientiousness': 0.39,
                'openness': 0.5,
                'extraversion': 0.6,
                'agreeableness': 0.4,
                'neuroticism': 0.7,
                'resilience': 0.29,
                'sociability': 0.5
            }
        }
    }
    
    # Save the beginner agent data
    with open(learning_file, 'wb') as f:
        pickle.dump(beginner_data, f)
    
    print(f"Created beginner agents data!")
    print(f"Saved to: {learning_file}")
    print(f"\nBeginner agent characteristics:")
    print(f"- Low skill levels (0.25-0.35)")
    print(f"- Low collaboration (0.15-0.25)")
    print(f"- Low success rates (0.25-0.35)")
    print(f"- High exploration (epsilon=0.3)")
    print(f"- No experience (0 steps)")
    print(f"- Poor task completion history")
    print(f"- Low emotional stability and stress resistance")

def create_expert_agents_data():
    """Create learning data for expert agents."""
    
    # Path to the learning data file
    learning_file = os.path.join(project_root, "core", "generated", "agent_learning_data_expert_sb3.pkl")
    
    # Create expert agent data
    expert_data = {
        'agent_0': {
            'q_table': {},
            'learning_rate': 0.01,  # Lower learning rate for experts
            'discount_factor': 0.95,
            'epsilon': 0.05,  # Lower exploration for experts
            'experience_count': 20000,  # High experience
            'success_rate': 0.9,  # High success rate
            'collaboration_level': 0.85,  # High collaboration
            'skill_level': 0.92,  # High skill
            'emotional_stability': 0.9,  # High emotional stability
            'stress_resistance': 0.88,  # High stress resistance
            'task_completion_history': [1.0] * 100,  # Perfect completion history
            'team_work_history': [0.85] * 100,  # Good teamwork history
            'performance_history': [0.92] * 100,  # High performance history
            'personality': {
                'conscientiousness': 0.92,
                'openness': 0.85,
                'extraversion': 0.75,
                'agreeableness': 0.85,
                'neuroticism': 0.1,
                'resilience': 0.92,
                'sociability': 0.85
            }
        },
        'agent_1': {
            'q_table': {},
            'learning_rate': 0.01,
            'discount_factor': 0.95,
            'epsilon': 0.05,
            'experience_count': 20000,
            'success_rate': 0.88,
            'collaboration_level': 0.88,
            'skill_level': 0.94,
            'emotional_stability': 0.88,
            'stress_resistance': 0.9,
            'task_completion_history': [1.0] * 100,
            'team_work_history': [0.88] * 100,
            'performance_history': [0.94] * 100,
            'personality': {
                'conscientiousness': 0.94,
                'openness': 0.88,
                'extraversion': 0.78,
                'agreeableness': 0.88,
                'neuroticism': 0.08,
                'resilience': 0.94,
                'sociability': 0.88
            }
        },
        'agent_2': {
            'q_table': {},
            'learning_rate': 0.01,
            'discount_factor': 0.95,
            'epsilon': 0.05,
            'experience_count': 20000,
            'success_rate': 0.87,
            'collaboration_level': 0.82,
            'skill_level': 0.89,
            'emotional_stability': 0.85,
            'stress_resistance': 0.87,
            'task_completion_history': [1.0] * 100,
            'team_work_history': [0.82] * 100,
            'performance_history': [0.89] * 100,
            'personality': {
                'conscientiousness': 0.89,
                'openness': 0.82,
                'extraversion': 0.8,
                'agreeableness': 0.82,
                'neuroticism': 0.12,
                'resilience': 0.89,
                'sociability': 0.82
            }
        },
        'agent_3': {
            'q_table': {},
            'learning_rate': 0.01,
            'discount_factor': 0.95,
            'epsilon': 0.05,
            'experience_count': 20000,
            'success_rate': 0.86,
            'collaboration_level': 0.88,
            'skill_level': 0.91,
            'emotional_stability': 0.88,
            'stress_resistance': 0.86,
            'task_completion_history': [1.0] * 100,
            'team_work_history': [0.88] * 100,
            'performance_history': [0.91] * 100,
            'personality': {
                'conscientiousness': 0.91,
                'openness': 0.88,
                'extraversion': 0.72,
                'agreeableness': 0.88,
                'neuroticism': 0.09,
                'resilience': 0.91,
                'sociability': 0.88
            }
        },
        'agent_4': {
            'q_table': {},
            'learning_rate': 0.01,
            'discount_factor': 0.95,
            'epsilon': 0.05,
            'experience_count': 20000,
            'success_rate': 0.89,
            'collaboration_level': 0.83,
            'skill_level': 0.93,
            'emotional_stability': 0.83,
            'stress_resistance': 0.89,
            'task_completion_history': [1.0] * 100,
            'team_work_history': [0.83] * 100,
            'performance_history': [0.93] * 100,
            'personality': {
                'conscientiousness': 0.93,
                'openness': 0.83,
                'extraversion': 0.78,
                'agreeableness': 0.83,
                'neuroticism': 0.11,
                'resilience': 0.93,
                'sociability': 0.83
            }
        },
        'agent_5': {
            'q_table': {},
            'learning_rate': 0.01,
            'discount_factor': 0.95,
            'epsilon': 0.05,
            'experience_count': 20000,
            'success_rate': 0.84,
            'collaboration_level': 0.86,
            'skill_level': 0.88,
            'emotional_stability': 0.86,
            'stress_resistance': 0.84,
            'task_completion_history': [1.0] * 100,
            'team_work_history': [0.86] * 100,
            'performance_history': [0.88] * 100,
            'personality': {
                'conscientiousness': 0.88,
                'openness': 0.86,
                'extraversion': 0.73,
                'agreeableness': 0.86,
                'neuroticism': 0.13,
                'resilience': 0.88,
                'sociability': 0.86
            }
        },
        'agent_6': {
            'q_table': {},
            'learning_rate': 0.01,
            'discount_factor': 0.95,
            'epsilon': 0.05,
            'experience_count': 20000,
            'success_rate': 0.87,
            'collaboration_level': 0.84,
            'skill_level': 0.90,
            'emotional_stability': 0.84,
            'stress_resistance': 0.87,
            'task_completion_history': [1.0] * 100,
            'team_work_history': [0.84] * 100,
            'performance_history': [0.90] * 100,
            'personality': {
                'conscientiousness': 0.90,
                'openness': 0.84,
                'extraversion': 0.76,
                'agreeableness': 0.84,
                'neuroticism': 0.14,
                'resilience': 0.90,
                'sociability': 0.84
            }
        },
        'agent_7': {
            'q_table': {},
            'learning_rate': 0.01,
            'discount_factor': 0.95,
            'epsilon': 0.05,
            'experience_count': 20000,
            'success_rate': 0.85,
            'collaboration_level': 0.87,
            'skill_level': 0.89,
            'emotional_stability': 0.87,
            'stress_resistance': 0.85,
            'task_completion_history': [1.0] * 100,
            'team_work_history': [0.87] * 100,
            'performance_history': [0.89] * 100,
            'personality': {
                'conscientiousness': 0.89,
                'openness': 0.87,
                'extraversion': 0.74,
                'agreeableness': 0.87,
                'neuroticism': 0.10,
                'resilience': 0.89,
                'sociability': 0.87
            }
        }
    }
    
    # Save the expert agent data
    with open(learning_file, 'wb') as f:
        pickle.dump(expert_data, f)
    
    print(f"Created expert agents data!")
    print(f"Saved to: {learning_file}")
    print(f"\nExpert agent characteristics:")
    print(f"- High skill levels (0.88-0.94)")
    print(f"- High collaboration (0.82-0.88)")
    print(f"- High success rates (0.84-0.90)")
    print(f"- Low exploration (epsilon=0.05)")
    print(f"- High experience (20000 steps)")
    print(f"- Perfect task completion history")
    print(f"- High emotional stability and stress resistance")

if __name__ == "__main__":
    print("Creating agent experience levels...")
    print("\n1. Creating BEGINNER agents...")
    create_beginner_agents_data()
    print("\n2. Creating EXPERT agents...")
    create_expert_agents_data()
    print("\nDone! Now you can choose between beginner and expert teams.")
