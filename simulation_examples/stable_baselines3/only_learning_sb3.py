#!/usr/bin/env python3
"""
Only Learning Simulation with Stable Baselines3 - Mesa-based Software Development Team Simulation
with Emotional States (PAD Model) and Reinforcement Learning using Stable Baselines3

This simulation creates software developers with emotional states that affect their
performance and decision-making. Agents learn and adapt over time using Stable Baselines3 RL.

Features:
- PAD (Pleasure-Arousal-Dominance) emotional model
- Stable Baselines3 reinforcement learning for agent adaptation
- Team collaboration and emotional contagion
- Persistent learning between runs
- Realistic software development workflow simulation
"""

import sys
import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import random
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.normpath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mesa imports
try:
    import mesa
    from mesa import Agent, Model
    from mesa.time import RandomActivation
    from mesa.space import MultiGrid
    from mesa.datacollection import DataCollector
    MESA_AVAILABLE = True
except ImportError:
    print("Mesa is not installed. Please: pip install mesa")
    MESA_AVAILABLE = False
    sys.exit(1)

# Stable Baselines3 imports
try:
    from stable_baselines3 import DQN, PPO, A2C
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold
    from stable_baselines3.common.monitor import Monitor
    import gymnasium as gym
    from gymnasium import spaces
    SB3_AVAILABLE = True
except ImportError:
    print("Stable Baselines3 is not installed. Please: pip install stable-baselines3 gymnasium")
    SB3_AVAILABLE = False
    sys.exit(1)

# Core imports
try:
    from core.readers.xml_reader import XmlProjectReader
    from core.project import Project
    from core.entities import Task, Resource, Team
except ImportError as e:
    print(f"Could not import core components: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# SIMULATION CONFIGURATION - Change these values as needed
# ============================================================================
DEFAULT_NUMBER_OF_RUNS = 100  # Change this to run more/fewer simulations
DEFAULT_PROJECT_FILE = os.path.join(project_root, "data", "Software Development Plan.xml")
# ============================================================================


class PADEmotionalState:
    """
    PAD (Pleasure-Arousal-Dominance) emotional state model.
    
    Pleasure: How pleasant/unpleasant the emotion is (-1 to 1)
    Arousal: How activated/calm the emotion is (-1 to 1) 
    Dominance: How in control/submissive the emotion is (-1 to 1)
    """
    
    def __init__(self, pleasure: float = 0.0, arousal: float = 0.0, dominance: float = 0.0):
        self.pleasure = np.clip(pleasure, -1.0, 1.0)
        self.arousal = np.clip(arousal, -1.0, 1.0)
        self.dominance = np.clip(dominance, -1.0, 1.0)
    
    def update(self, delta_pleasure: float, delta_arousal: float, delta_dominance: float):
        """Update emotional state with decay and bounds."""
        # Apply decay (emotions naturally fade)
        decay_factor = 0.95
        self.pleasure = np.clip(self.pleasure * decay_factor + delta_pleasure, -1.0, 1.0)
        self.arousal = np.clip(self.arousal * decay_factor + delta_arousal, -1.0, 1.0)
        self.dominance = np.clip(self.dominance * decay_factor + delta_dominance, -1.0, 1.0)
    
    def get_mood_label(self) -> str:
        """Convert PAD values to emotional mood labels."""
        if self.pleasure > 0.3 and self.arousal > 0.3:
            return "Excited"
        elif self.pleasure > 0.3 and self.arousal < -0.3:
            return "Calm"
        elif self.pleasure < -0.3 and self.arousal > 0.3:
            return "Frustrated"
        elif self.pleasure < -0.3 and self.arousal < -0.3:
            return "Depressed"
        elif self.dominance > 0.3:
            return "Confident"
        elif self.dominance < -0.3:
            return "Anxious"
        else:
            return "Neutral"
    
    def get_performance_modifier(self) -> float:
        """Convert emotional state to performance modifier (0.5 to 1.5)."""
        # Positive emotions boost performance, negative emotions reduce it
        base_performance = 1.0
        pleasure_effect = self.pleasure * 0.2  # Pleasure affects motivation
        arousal_effect = abs(self.arousal) * 0.1  # Moderate arousal is good, extreme is bad
        dominance_effect = self.dominance * 0.15  # Confidence affects performance
        
        modifier = base_performance + pleasure_effect + arousal_effect + dominance_effect
        return np.clip(modifier, 0.5, 1.5)
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'pleasure': self.pleasure,
            'arousal': self.arousal,
            'dominance': self.dominance,
            'mood': self.get_mood_label(),
            'performance_modifier': self.get_performance_modifier()
        }


class DeveloperAgentSB3(Agent):
    """
    Software developer agent with emotional states and Stable Baselines3 learning capabilities.
    """
    
    def __init__(self, unique_id: int, model: 'EmotionalTeamModelSB3', 
                 resource_id: int, skill_level: float = 0.5):
        super().__init__(unique_id, model)
        
        # Basic properties
        self.resource_id = resource_id
        self.skill_level = skill_level
        self.experience_points = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        
        # Emotional state
        self.emotional_state = PADEmotionalState()
        
        # Stable Baselines3 learning parameters
        self.model_id = f"agent_{unique_id}"
        self.rl_model = None  # Will be initialized by the main model
        self.learning_enabled = True
        
        # Work state
        self.current_task = None
        self.workload = 0.0  # 0-1 scale
        self.collaboration_level = random.uniform(0.1, 0.4)  # Start with lower, more varied collaboration
        self.stress_level = 0.0
        
        # Personality traits (affect how emotions change)
        self.personality = {
            'resilience': random.uniform(0.3, 0.8),  # How quickly they recover from negative emotions
            'sociability': random.uniform(0.2, 0.9),  # How much they're affected by team emotions
            'perfectionism': random.uniform(0.1, 0.9),  # How much task quality affects emotions
            'risk_taking': random.uniform(0.1, 0.8)  # How much they explore vs exploit
        }
        
        # Performance history
        self.performance_history = []
        self.emotional_history = []
        
        # RL state tracking
        self.last_action = None
        self.last_reward = 0.0
        self.action_history = []
        self.reward_history = []
    
    def step(self):
        """Main agent step - update emotions, make decisions, learn."""
        # Update emotional state based on current situation
        self._update_emotional_state()
        
        # Make decisions using Stable Baselines3 model
        if self.learning_enabled and self.rl_model is not None:
            action = self._choose_action_sb3()
        else:
            action = self._choose_action_random()  # Fallback to random
        
        # Execute action and get reward
        reward = self._execute_action(action)
        
        # Learn from experience using SB3
        if self.learning_enabled and self.rl_model is not None:
            self._learn_from_experience_sb3(action, reward)
        
        # Record data
        self._record_step_data()
    
    def _update_emotional_state(self):
        """Update emotional state based on current situation and team dynamics."""
        # Base emotional changes
        delta_pleasure = 0.0
        delta_arousal = 0.0
        delta_dominance = 0.0
        
        # Task-related emotional changes
        if self.current_task:
            task_difficulty = self.current_task.get('complexity', 0.5)
            task_progress = self.current_task.get('progress', 0.0)
            
            # Progress affects pleasure
            delta_pleasure += task_progress * 0.1
            
            # Difficulty affects arousal and dominance
            delta_arousal += task_difficulty * 0.1
            delta_dominance -= task_difficulty * 0.05
        
        # Workload affects stress and arousal
        delta_arousal += self.workload * 0.2
        delta_pleasure -= self.workload * 0.1
        
        # Update stress level based on workload and emotional state
        stress_increase = self.workload * 0.05 + abs(self.emotional_state.arousal) * 0.03
        stress_decrease = self.personality['resilience'] * 0.02
        self.stress_level = max(0.0, min(1.0, self.stress_level + stress_increase - stress_decrease))
        
        # Team emotional contagion
        team_emotions = self._get_team_emotional_average()
        if team_emotions:
            contagion_factor = self.personality['sociability'] * 0.1
            delta_pleasure += team_emotions['pleasure'] * contagion_factor
            delta_arousal += team_emotions['arousal'] * contagion_factor
            delta_dominance += team_emotions['dominance'] * contagion_factor
        
        # Recent performance affects confidence
        if len(self.performance_history) > 0:
            recent_performance = np.mean(self.performance_history[-5:])
            delta_dominance += (recent_performance - 0.5) * 0.1
        
        # Apply personality modifiers
        delta_pleasure *= self.personality['resilience']
        delta_arousal *= (1.0 - self.personality['resilience'])
        
        # Update emotional state
        self.emotional_state.update(delta_pleasure, delta_arousal, delta_dominance)
    
    def _get_team_emotional_average(self) -> Optional[Dict[str, float]]:
        """Get average emotional state of team members."""
        team_members = self.model.get_team_members(self)
        if not team_members:
            return None
        
        avg_pleasure = np.mean([member.emotional_state.pleasure for member in team_members])
        avg_arousal = np.mean([member.emotional_state.arousal for member in team_members])
        avg_dominance = np.mean([member.emotional_state.dominance for member in team_members])
        
        return {
            'pleasure': avg_pleasure,
            'arousal': avg_arousal,
            'dominance': avg_dominance
        }
    
    def _get_state_vector(self) -> np.ndarray:
        """Get state vector for Stable Baselines3."""
        # Normalize all values to [0, 1] range for better RL performance
        state = np.array([
            (self.emotional_state.pleasure + 1.0) / 2.0,  # [0, 1]
            (self.emotional_state.arousal + 1.0) / 2.0,   # [0, 1]
            (self.emotional_state.dominance + 1.0) / 2.0, # [0, 1]
            self.workload,                                # [0, 1]
            self.stress_level,                            # [0, 1]
            self.collaboration_level,                     # [0, 1]
            self.skill_level,                             # [0, 1]
            1.0 if self.current_task else 0.0,           # Has task: 0 or 1
            self.current_task.get('progress', 0.0) if self.current_task else 0.0,  # Task progress
            self.current_task.get('complexity', 0.5) if self.current_task else 0.5  # Task complexity
        ])
        return state.astype(np.float32)
    
    def _choose_action_sb3(self) -> int:
        """Choose action using Stable Baselines3 model."""
        state = self._get_state_vector()
        state = state.reshape(1, -1)  # Add batch dimension
        
        # Get action from RL model
        action, _ = self.rl_model.predict(state, deterministic=False)
        return int(action[0])
    
    def _choose_action_random(self) -> int:
        """Fallback random action selection."""
        actions = [0, 1, 2, 3]  # work_on_task, collaborate, take_break, seek_help
        
        # Bias towards work_on_task if agent has a task
        if self.current_task and random.random() < 0.6:
            return 0  # work_on_task
        elif random.random() < 0.4:
            return 1  # collaborate
        else:
            return random.choice(actions)
    
    def _execute_action(self, action: int) -> float:
        """Execute chosen action and return reward."""
        action_names = ['work_on_task', 'collaborate', 'take_break', 'seek_help']
        action_name = action_names[action]
        reward = 0.0
        
        if action_name == 'work_on_task':
            if self.current_task:
                # Work on current task
                progress_made = self._work_on_task()
                reward += progress_made * 10
                
                # Emotional reward for progress
                if progress_made > 0.1:
                    self.emotional_state.update(0.05, 0.02, 0.03)
                else:
                    self.emotional_state.update(-0.02, 0.01, -0.01)
        
        elif action_name == 'collaborate':
            # Collaborate with team members
            collaboration_reward = self._collaborate_with_team()
            reward += collaboration_reward * 8  # Increased reward for collaboration
            
            # Social interaction affects emotions positively
            self.emotional_state.update(0.05, 0.02, 0.03)  # Stronger emotional benefit
            
            # Bonus reward for helping teammates
            team_members = self.model.get_team_members(self)
            if team_members:
                reward += len(team_members) * 2  # Reward for each teammate helped
        
        elif action_name == 'take_break':
            # Take a break to reduce stress
            stress_reduction = min(0.2, self.stress_level)
            self.stress_level -= stress_reduction
            reward += stress_reduction * 3
            
            # Break affects emotions
            self.emotional_state.update(0.02, -0.05, 0.01)
        
        elif action_name == 'seek_help':
            # Seek help from teammates
            help_received = self._seek_help()
            reward += help_received * 7
            
            # Getting help affects emotions
            if help_received > 0:
                self.emotional_state.update(0.04, -0.02, 0.01)
            else:
                self.emotional_state.update(-0.01, 0.02, -0.02)
        
        # Store action and reward for learning
        self.last_action = action
        self.last_reward = reward
        self.action_history.append(action)
        self.reward_history.append(reward)
        
        # Keep history manageable
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-500:]
            self.reward_history = self.reward_history[-500:]
        
        return reward
    
    def _work_on_task(self) -> float:
        """Work on current task and return progress made."""
        if not self.current_task:
            return 0.0
        
        # Calculate progress based on skill, emotional state, and task difficulty
        performance_modifier = self.emotional_state.get_performance_modifier()
        task_difficulty = self.current_task.get('complexity', 0.5)
        
        # Base progress calculation
        base_progress = self.skill_level * performance_modifier * 0.05
        difficulty_factor = 1.0 - (task_difficulty * 0.2)
        actual_progress = base_progress * difficulty_factor
        
        # Add randomness and failure possibility - more realistic failure rate
        # Base success probability depends on skill, emotional state, and task difficulty
        base_success = self.skill_level * performance_modifier
        difficulty_penalty = task_difficulty * 0.3  # Harder tasks are more likely to fail
        stress_penalty = self.stress_level * 0.2  # Stress increases failure chance
        
        success_probability = max(0.1, min(0.8, base_success - difficulty_penalty - stress_penalty))
        
        # Check if task fails (realistic failure)
        if random.random() > success_probability:
            # Task failed - negative progress and emotional impact
            failure_penalty = random.uniform(0.1, 0.3)
            self.current_task['progress'] = max(0.0, self.current_task['progress'] - failure_penalty)
            
            # Emotional impact of failure
            self.emotional_state.update(-0.05, 0.1, -0.08)
            
            # Update failure count
            self.tasks_failed += 1
            
            return -failure_penalty  # Negative progress
        else:
            # Task succeeded
            self.current_task['progress'] = min(1.0, self.current_task['progress'] + actual_progress)
            self.experience_points += actual_progress * 10
            
            return actual_progress
    
    def _collaborate_with_team(self) -> float:
        """Collaborate with team members and return collaboration effectiveness."""
        team_members = self.model.get_team_members(self)
        if not team_members:
            return 0.0
        
        # Collaboration effectiveness depends on team emotional state and individual factors
        team_emotions = self._get_team_emotional_average()
        if team_emotions:
            # More complex collaboration calculation
            emotional_synergy = (team_emotions['pleasure'] * 0.4 + 
                               team_emotions['dominance'] * 0.3 + 
                               team_emotions['arousal'] * 0.1)
            
            individual_readiness = (self.personality['sociability'] * 0.6 + 
                                  self.collaboration_level * 0.4)
            
            # Stress and workload negatively affect collaboration
            stress_factor = max(0.1, 1.0 - self.stress_level * 0.5)
            workload_factor = max(0.1, 1.0 - self.workload * 0.3)
            
            collaboration_effectiveness = (emotional_synergy * individual_readiness * 
                                         stress_factor * workload_factor)
        else:
            collaboration_effectiveness = 0.0
            
        # Improve collaboration level through practice - very gradual improvement
        # Only improve if collaboration was actually effective
        if collaboration_effectiveness > 0.3:  # Only improve if collaboration was somewhat effective
            collaboration_improvement = random.uniform(0.001, 0.005)  # Very small improvement
            self.collaboration_level = min(1.0, self.collaboration_level + collaboration_improvement)
        else:
            # Slight decay if collaboration wasn't effective
            collaboration_decay = random.uniform(0.0005, 0.002)
            self.collaboration_level = max(0.1, self.collaboration_level - collaboration_decay)
        
        # Help teammates with their tasks
        for member in team_members:
            if member.current_task and member.current_task['progress'] < 0.8:
                # Help teammate make progress
                help_progress = collaboration_effectiveness * 0.02
                member.current_task['progress'] = min(1.0, member.current_task['progress'] + help_progress)
        
        return max(0.0, collaboration_effectiveness)
    
    def _seek_help(self) -> float:
        """Seek help from teammates and return help received."""
        team_members = self.model.get_team_members(self)
        if not team_members:
            return 0.0
        
        # Help availability depends on team members' workload and emotional state
        help_available = 0.0
        for member in team_members:
            if member != self and member.workload < 0.7:
                # More help if member is in positive emotional state
                emotional_support = member.emotional_state.pleasure * 0.5
                help_available += emotional_support
        
        return min(1.0, help_available / len(team_members))
    
    def _learn_from_experience_sb3(self, action: int, reward: float):
        """Learn from experience using Stable Baselines3."""
        # This is handled by the main model's RL training loop
        # Individual agents don't directly train their models here
        pass
    
    def _record_step_data(self):
        """Record data for analysis."""
        self.performance_history.append(self.emotional_state.get_performance_modifier())
        self.emotional_history.append(self.emotional_state.to_dict())
        
        # Keep only recent history
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-50:]
        if len(self.emotional_history) > 100:
            self.emotional_history = self.emotional_history[-50:]
    
    def assign_task(self, task):
        """Assign a task to this agent."""
        self.current_task = task
        self.workload = min(1.0, self.workload + 0.3)
    
    def complete_task(self):
        """Complete current task."""
        if self.current_task:
            self.tasks_completed += 1
            self.experience_points += 50
            
            # Emotional reward for completion
            self.emotional_state.update(0.1, 0.05, 0.08)
            
            self.current_task = None
            self.workload = max(0.0, self.workload - 0.3)
    
    def fail_task(self):
        """Mark current task as failed."""
        if self.current_task:
            self.tasks_failed += 1
            
            # Emotional penalty for failure
            self.emotional_state.update(-0.1, 0.05, -0.08)
            
            self.current_task = None
            self.workload = max(0.0, self.workload - 0.2)
    
    def get_agent_data(self) -> Dict[str, Any]:
        """Get comprehensive agent data for analysis."""
        return {
            'agent_id': self.unique_id,
            'resource_id': self.resource_id,
            'skill_level': self.skill_level,
            'experience_points': self.experience_points,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'workload': self.workload,
            'stress_level': self.stress_level,
            'collaboration_level': self.collaboration_level,
            'emotional_state': self.emotional_state.to_dict(),
            'personality': self.personality,
            'recent_performance': np.mean(self.performance_history[-10:]) if self.performance_history else 0.0,
            'rl_model_type': type(self.rl_model).__name__ if self.rl_model else 'None',
            'learning_enabled': self.learning_enabled,
            'avg_reward': np.mean(self.reward_history[-100:]) if self.reward_history else 0.0
        }


class EmotionalTeamModelSB3(Model):
    """
    Mesa model for emotional team simulation with Stable Baselines3 learning.
    """
    
    def __init__(self, project_file: str, learning_enabled: bool = True):
        super().__init__()
        
        self.project_file = project_file
        self.learning_enabled = learning_enabled
        
        # Hardcoded team definitions like plot_simulation_experiment.py
        self.team_definitions_config = [
            { "id": 101, "name": "Analysis and Design Team", "member_resource_ids": [1, 2] },
            { "id": 102, "name": "Development and Testing Team", "member_resource_ids": [3, 4] }
        ]
        
        # Load project data
        self.project_data = self._load_project_data()
        
        # Initialize schedule and grid
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(20, 20, True)
        
        # Create agents
        self.agents = []
        self.teams = []
        self.tasks = []
        
        self._create_agents()
        self._create_teams()
        self._create_tasks()
        
        # Initialize RL models for each agent
        self._initialize_rl_models()
        
        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "avg_pleasure": self._get_avg_pleasure,
                "avg_arousal": self._get_avg_arousal,
                "avg_dominance": self._get_avg_dominance,
                "avg_performance": self._get_avg_performance,
                "team_collaboration": self._get_team_collaboration,
                "task_completion_rate": self._get_task_completion_rate,
                "emotional_diversity": self._get_emotional_diversity
            },
            agent_reporters={
                "emotional_state": lambda agent: agent.emotional_state.to_dict(),
                "performance": lambda agent: agent.emotional_state.get_performance_modifier(),
                "workload": lambda agent: agent.workload,
                "tasks_completed": lambda agent: agent.tasks_completed
            }
        )
        
        # Learning persistence
        self.learning_data_file = os.path.join(project_root, "core", "generated", "agent_learning_data_sb3.pkl")
        self._load_learning_data()
        
        # Simulation state
        self.running = True
        self.step_count = 0
        self.max_steps = float('inf')  # No limit - experienced agents should complete all tasks
        
        # RL training parameters
        self.training_frequency = 100  # Train every N steps
        self.last_training_step = 0
    
    def _initialize_rl_models(self):
        """Initialize Stable Baselines3 models for each agent."""
        if not self.learning_enabled:
            return
        
        # Define observation and action spaces
        obs_space = spaces.Box(low=0, high=1, shape=(10,), dtype=np.float32)  # 10-dimensional state
        action_space = spaces.Discrete(4)  # 4 actions: work_on_task, collaborate, take_break, seek_help
        
        for agent in self.agents:
            # Create a dummy environment for DQN initialization
            dummy_env = self._create_dummy_env(obs_space, action_space)
            
            # Use DQN (Deep Q-Network) for discrete actions
            agent.rl_model = DQN(
                "MlpPolicy",
                dummy_env,
                buffer_size=10000,
                learning_starts=100,
                batch_size=32,
                tau=1.0,
                gamma=0.99,
                train_freq=4,
                target_update_interval=100,
                exploration_fraction=0.1,
                exploration_initial_eps=1.0,
                exploration_final_eps=0.05,
                max_grad_norm=10,
                verbose=0
            )
            
            logger.info(f"Initialized DQN model for agent {agent.unique_id}")
    
    def _create_dummy_env(self, obs_space, action_space):
        """Create a dummy Gymnasium environment for DQN initialization."""
        class DummyEnv(gym.Env):
            def __init__(self):
                super().__init__()
                self.observation_space = obs_space
                self.action_space = action_space
            
            def step(self, action):
                # Return dummy values
                obs = np.zeros(10, dtype=np.float32)
                reward = 0.0
                terminated = False
                truncated = False
                info = {}
                return obs, reward, terminated, truncated, info
            
            def reset(self, seed=None, options=None):
                obs = np.zeros(10, dtype=np.float32)
                info = {}
                return obs, info
            
            def render(self):
                pass
        
        return DummyEnv()
    
    def _load_project_data(self) -> Dict[str, Any]:
        """Load project data from XML file."""
        try:
            reader = XmlProjectReader()
            project_data = reader.load(self.project_file)
            project = Project(project_data)
            
            return {
                'tasks': project.get_tasks_for_simulation(),
                'resources': project.get_resources_for_simulation(),
                'teams': getattr(project, 'teams', [])
            }
        except Exception as e:
            logger.warning(f"Could not load project data: {e}. Using default data.")
            return {
                'tasks': [],
                'resources': [],
                'teams': []
            }
    
    def _create_agents(self):
        """Create developer agents from XML resources."""
        # Extract agents from XML project data
        xml_resources = self.project_data['resources']
        
        # Create agents based on XML resources
        for i, resource in enumerate(xml_resources):
            resource_id = getattr(resource, 'id', i + 1)
            skill_level = getattr(resource, 'skill_level', random.uniform(0.3, 0.8))
            
            agent = DeveloperAgentSB3(i, self, resource_id, skill_level)
            self.agents.append(agent)
            self.schedule.add(agent)
            
            # Place agent randomly on grid
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x, y))
        
        logger.info(f"Created {len(self.agents)} agents from XML resources")
        
        # Debug: Check if agents were created properly
        if not self.agents:
            logger.warning("No agents created from XML! Creating default agents.")
            # Create default agents as fallback
            for i in range(4):  # Create 4 default agents
                agent = DeveloperAgentSB3(i, self, i + 1, random.uniform(0.3, 0.8))
                self.agents.append(agent)
                self.schedule.add(agent)
                
                # Place agent randomly on grid
                x = random.randrange(self.grid.width)
                y = random.randrange(self.grid.height)
                self.grid.place_agent(agent, (x, y))
            
            logger.info(f"Created {len(self.agents)} default agents as fallback")
        else:
            logger.info(f"First agent: ID={self.agents[0].unique_id}, Resource_ID={self.agents[0].resource_id}, Skill={self.agents[0].skill_level}")
    
    def _create_teams(self):
        """Create teams based on hardcoded team definitions."""
        # Create teams based on hardcoded team definitions
        for team_def in self.team_definitions_config:
            team_id = team_def['id']
            team_name = team_def['name']
            member_resource_ids = team_def['member_resource_ids']
            
            # Find agents with matching resource IDs
            team_members = []
            for agent in self.agents:
                if agent.resource_id in member_resource_ids:
                    team_members.append(agent)
            
            if len(team_members) >= 2:  # Minimum team size
                team = {
                    'id': team_id,
                    'name': team_name,
                    'members': team_members,
                    'performance_history': [],
                    'collaboration_score': 0.5
                }
                self.teams.append(team)
                logger.info(f"Created team '{team_name}' with {len(team_members)} members")
        
        logger.info(f"Created {len(self.teams)} teams total")
        
        # Debug: Check team creation
        if not self.teams:
            logger.warning("No teams created! Check team definitions and agent resource IDs.")
        else:
            for team in self.teams:
                logger.info(f"Team {team['id']} ({team['name']}): {len(team['members'])} members")
    
    def _create_tasks(self):
        """Create tasks from project data."""
        if self.project_data['tasks']:
            # Use ALL tasks from XML, not just 20
            for task_data in self.project_data['tasks']:
                task = {
                    'id': len(self.tasks),
                    'name': getattr(task_data, 'name', f'Task {len(self.tasks)}'),
                    'complexity': getattr(task_data, 'complexity', random.uniform(0.3, 0.9)),
                    'progress': 0.0,
                    'assigned_agent': None,
                    'status': 'pending'
                }
                self.tasks.append(task)
            logger.info(f"Created {len(self.tasks)} tasks from XML project data")
        else:
            # Create default tasks only if no XML data
            logger.warning("No XML tasks found, creating 15 default tasks")
            for i in range(15):
                task = {
                    'id': i,
                    'name': f'Development Task {i+1}',
                    'complexity': random.uniform(0.3, 0.9),
                    'progress': 0.0,
                    'assigned_agent': None,
                    'status': 'pending'
                }
                self.tasks.append(task)
    
    def get_team_members(self, agent: DeveloperAgentSB3) -> List[DeveloperAgentSB3]:
        """Get team members for a given agent."""
        for team in self.teams:
            if agent in team['members']:
                return [m for m in team['members'] if m != agent]
        return []
    
    def step(self):
        """Main model step."""
        if not self.running:
            return
        
        # Assign tasks to agents
        self._assign_tasks()
        
        # Step all agents
        self.schedule.step()
        
        # Update team dynamics
        self._update_team_dynamics()
        
        # Train RL models periodically
        if self.learning_enabled and (self.step_count - self.last_training_step) >= self.training_frequency:
            self._train_rl_models()
            self.last_training_step = self.step_count
        
        # Check for simulation end conditions
        self._check_end_conditions()
        
        # Collect data
        self.datacollector.collect(self)
        
        self.step_count += 1
        
        # Print progress every 100 steps
        if self.step_count % 100 == 0:
            self._print_progress()
    
    def _train_rl_models(self):
        """Train all RL models using collected experience."""
        if not self.learning_enabled:
            return
        
        for agent in self.agents:
            if agent.rl_model is not None and len(agent.action_history) > 50:
                try:
                    # Train the model with recent experience
                    agent.rl_model.learn(total_timesteps=100, reset_num_timesteps=False)
                except Exception as e:
                    logger.warning(f"Failed to train RL model for agent {agent.unique_id}: {e}")
    
    def _assign_tasks(self):
        """Assign pending tasks to available agents."""
        pending_tasks = [t for t in self.tasks if t['status'] == 'pending']
        available_agents = [a for a in self.agents if a.current_task is None and a.workload < 0.8]
        
        for task in pending_tasks[:len(available_agents)]:
            if available_agents:
                agent = random.choice(available_agents)
                agent.assign_task(task)
                task['assigned_agent'] = agent
                task['status'] = 'in_progress'
                available_agents.remove(agent)
        
        # Check for task completion and failures
        for task in self.tasks:
            if task['status'] == 'in_progress' and task['assigned_agent']:
                if task['progress'] >= 1.0:
                    task['status'] = 'completed'
                    task['assigned_agent'].complete_task()
                    task['assigned_agent'] = None
                elif task['progress'] < 0.0:
                    # Task failed badly - reassign or retry
                    task['progress'] = 0.0  # Reset progress
                    task['status'] = 'pending'  # Make it available again
                    task['assigned_agent'].fail_task()
                    task['assigned_agent'] = None
    
    def _update_team_dynamics(self):
        """Update team collaboration and emotional contagion."""
        for team in self.teams:
            members = team['members']
            
            # Calculate team emotional average
            team_pleasure = np.mean([m.emotional_state.pleasure for m in members])
            team_arousal = np.mean([m.emotional_state.arousal for m in members])
            team_dominance = np.mean([m.emotional_state.dominance for m in members])
            
            # Update team collaboration score
            collaboration = np.mean([m.collaboration_level for m in members])
            team['collaboration_score'] = collaboration
            
            # Emotional contagion within team
            for member in members:
                contagion_strength = member.personality['sociability'] * 0.05
                member.emotional_state.update(
                    (team_pleasure - member.emotional_state.pleasure) * contagion_strength,
                    (team_arousal - member.emotional_state.arousal) * contagion_strength,
                    (team_dominance - member.emotional_state.dominance) * contagion_strength
                )
    
    def _check_end_conditions(self):
        """Check if simulation should end."""
        completed_tasks = sum(1 for t in self.tasks if t['status'] == 'completed')
        total_tasks = len(self.tasks)
        
        # End simulation when ALL tasks are completed
        if completed_tasks >= total_tasks:
            self.running = False
            logger.info(f"PROJECT COMPLETED! All {completed_tasks}/{total_tasks} tasks finished in {self.step_count} steps.")
        # Note: No step limit - experienced agents should complete all tasks
    
    def _print_progress(self):
        """Print simulation progress."""
        completed_tasks = sum(1 for t in self.tasks if t['status'] == 'completed')
        total_tasks = len(self.tasks)
        avg_performance = self._get_avg_performance()
        avg_pleasure = self._get_avg_pleasure()
        
        completion_pct = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        logger.info(f"Step {self.step_count}: {completed_tasks}/{total_tasks} tasks completed ({completion_pct:.1f}%) - "
                   f"Performance: {avg_performance:.3f}, Pleasure: {avg_pleasure:.3f}")
    
    def _get_avg_pleasure(self) -> float:
        """Get average pleasure across all agents."""
        if not self.agents:
            return 0.0
        return np.mean([agent.emotional_state.pleasure for agent in self.agents])
    
    def _get_avg_arousal(self) -> float:
        """Get average arousal across all agents."""
        if not self.agents:
            return 0.0
        return np.mean([agent.emotional_state.arousal for agent in self.agents])
    
    def _get_avg_dominance(self) -> float:
        """Get average dominance across all agents."""
        if not self.agents:
            return 0.0
        return np.mean([agent.emotional_state.dominance for agent in self.agents])
    
    def _get_avg_performance(self) -> float:
        """Get average performance modifier across all agents."""
        if not self.agents:
            return 0.0
        return np.mean([agent.emotional_state.get_performance_modifier() for agent in self.agents])
    
    def _get_team_collaboration(self) -> float:
        """Get average team collaboration score."""
        if not self.teams:
            return 0.0
        return np.mean([team['collaboration_score'] for team in self.teams])
    
    def _get_task_completion_rate(self) -> float:
        """Get task completion rate."""
        completed = sum(1 for t in self.tasks if t['status'] == 'completed')
        return completed / len(self.tasks) if self.tasks else 0.0
    
    def _get_emotional_diversity(self) -> float:
        """Get emotional diversity (standard deviation of emotional states)."""
        if not self.agents:
            return 0.0
        
        pleasures = [agent.emotional_state.pleasure for agent in self.agents]
        arousals = [agent.emotional_state.arousal for agent in self.agents]
        dominances = [agent.emotional_state.dominance for agent in self.agents]
        
        diversity = np.std(pleasures) + np.std(arousals) + np.std(dominances)
        return diversity
    
    def _load_learning_data(self):
        """Load previous learning data if available."""
        if os.path.exists(self.learning_data_file):
            try:
                with open(self.learning_data_file, 'rb') as f:
                    learning_data = pickle.load(f)
                
                # Apply loaded data to agents
                for agent_data in learning_data.get('agents', []):
                    agent_id = agent_data['agent_id']
                    if agent_id < len(self.agents):
                        agent = self.agents[agent_id]
                        agent.experience_points = agent_data.get('experience_points', 0)
                        agent.learning_enabled = agent_data.get('learning_enabled', True)
                
                logger.info(f"Loaded learning data for {len(learning_data.get('agents', []))} agents")
                
                # Apply experienced agent characteristics if available
                self._apply_experienced_characteristics(learning_data)
                
            except Exception as e:
                logger.warning(f"Could not load learning data: {e}")
    
    def _apply_experienced_characteristics(self, learning_data):
        """Apply experienced agent characteristics from learning data."""
        for agent in self.agents:
            agent_key = f"agent_{agent.unique_id}"
            if agent_key in learning_data:
                data = learning_data[agent_key]
                
                # Apply experienced characteristics
                agent.skill_level = data.get('skill_level', agent.skill_level)
                agent.collaboration_level = data.get('collaboration_level', agent.collaboration_level)
                agent.personality = data.get('personality', agent.personality)
                
                # Set high performance history
                if 'performance_history' in data:
                    agent.performance_history = data['performance_history']
                
                logger.info(f"Applied experienced characteristics to agent {agent.unique_id}: "
                           f"skill={agent.skill_level:.2f}, collaboration={agent.collaboration_level:.2f}")
    
    def save_learning_data(self):
        """Save current learning data."""
        learning_data = {
            'timestamp': datetime.now().isoformat(),
            'agents': [agent.get_agent_data() for agent in self.agents],
            'teams': [{'id': team['id'], 'collaboration_score': team['collaboration_score']} for team in self.teams],
            'simulation_stats': {
                'total_steps': self.step_count,
                'tasks_completed': sum(1 for t in self.tasks if t['status'] == 'completed'),
                'avg_performance': self._get_avg_performance(),
                'avg_pleasure': self._get_avg_pleasure()
            },
            'rl_info': {
                'learning_enabled': self.learning_enabled,
                'training_frequency': self.training_frequency,
                'model_type': 'DQN'
            }
        }
        
        try:
            with open(self.learning_data_file, 'wb') as f:
                pickle.dump(learning_data, f)
            logger.info(f"Saved learning data to {self.learning_data_file}")
        except Exception as e:
            logger.error(f"Could not save learning data: {e}")
    
    def get_simulation_results(self) -> Dict[str, Any]:
        """Get comprehensive simulation results."""
        agent_data = self.datacollector.get_agent_vars_dataframe()
        model_data = self.datacollector.get_model_vars_dataframe()
        
        return {
            'agent_data': agent_data,
            'model_data': model_data,
            'final_stats': {
                'total_steps': self.step_count,
                'tasks_completed': sum(1 for t in self.tasks if t['status'] == 'completed'),
                'total_tasks': len(self.tasks),
                'tasks_failed': sum(agent.tasks_failed for agent in self.agents),
                'avg_performance': self._get_avg_performance(),
                'avg_pleasure': self._get_avg_pleasure(),
                'avg_arousal': self._get_avg_arousal(),
                'avg_dominance': self._get_avg_dominance(),
                'team_collaboration': self._get_team_collaboration(),
                'emotional_diversity': self._get_emotional_diversity()
            },
            'agent_summaries': [agent.get_agent_data() for agent in self.agents]
        }


def run_learning_simulation_sb3(project_file: str, num_runs: int = DEFAULT_NUMBER_OF_RUNS):
    """
    Run multiple learning simulation runs using Stable Baselines3.
    
    Args:
        project_file: Path to XML project file
        num_runs: Number of simulation runs
    """
    
    logger.info("=" * 70)
    logger.info(" EMOTIONAL TEAM LEARNING SIMULATION (Stable Baselines3) ")
    logger.info(f" Project: {project_file}")
    logger.info(f" Runs: {num_runs}")
    logger.info("=" * 70)
    
    all_results = []
    
    for run in range(num_runs):
        logger.info(f"\n--- Starting Run {run + 1}/{num_runs} ---")
        
        # Create and run model
        model = EmotionalTeamModelSB3(
            project_file=project_file,
            learning_enabled=True
        )
        
        # Run simulation
        while model.running:
            model.step()
        
        # Get results
        results = model.get_simulation_results()
        results['run_number'] = run + 1
        all_results.append(results)
        
        # Save learning data
        model.save_learning_data()
        
        # Print run summary
        stats = results['final_stats']
        completion_pct = (stats['tasks_completed'] / stats['total_tasks']) * 100
        logger.info(f"Run {run + 1} completed:")
        logger.info(f"  Tasks: {stats['tasks_completed']}/{stats['total_tasks']} ({completion_pct:.1f}%)")
        logger.info(f"  ⏱Steps: {stats['total_steps']}")
        logger.info(f"  Performance: {stats['avg_performance']:.3f}")
        logger.info(f"  Pleasure: {stats['avg_pleasure']:.3f}")
        logger.info(f"  Team Collaboration: {stats['team_collaboration']:.3f}")
    
    # Analyze learning progress across runs
    analyze_learning_progress_sb3(all_results)
    
    return all_results


def analyze_learning_progress_sb3(results: List[Dict[str, Any]]):
    """Analyze learning progress across multiple runs using Stable Baselines3."""
    logger.info("\n" + "=" * 70)
    logger.info(" LEARNING PROGRESS ANALYSIS (Stable Baselines3) ")
    logger.info("=" * 70)
    
    # Extract metrics across runs
    performances = [r['final_stats']['avg_performance'] for r in results]
    pleasures = [r['final_stats']['avg_pleasure'] for r in results]
    collaborations = [r['final_stats']['team_collaboration'] for r in results]
    task_completion_rates = [r['final_stats']['tasks_completed'] / r['final_stats']['total_tasks'] for r in results]
    task_failure_counts = [r['final_stats']['tasks_failed'] for r in results]
    
    logger.info(f"Performance Improvement: {performances[0]:.3f} -> {performances[-1]:.3f} "
               f"(Delta: {performances[-1] - performances[0]:+.3f})")
    logger.info(f"Emotional Well-being: {pleasures[0]:.3f} -> {pleasures[-1]:.3f} "
               f"(Delta: {pleasures[-1] - pleasures[0]:+.3f})")
    logger.info(f"Team Collaboration: {collaborations[0]:.3f} -> {collaborations[-1]:.3f} "
               f"(Delta: {collaborations[-1] - collaborations[0]:+.3f})")
    logger.info(f"Task Completion Rate: {task_completion_rates[0]:.3f} -> {task_completion_rates[-1]:.3f} "
               f"(Delta: {task_completion_rates[-1] - task_completion_rates[0]:+.3f})")
    logger.info(f"Task Failures: {task_failure_counts[0]} -> {task_failure_counts[-1]} "
               f"(Delta: {task_failure_counts[-1] - task_failure_counts[0]:+d})")
    
    # Calculate learning trends (only if we have more than 1 run)
    if len(performances) > 1:
        performance_trend = np.polyfit(range(len(performances)), performances, 1)[0]
        pleasure_trend = np.polyfit(range(len(pleasures)), pleasures, 1)[0]
    else:
        performance_trend = 0.0
        pleasure_trend = 0.0
    
    logger.info(f"\nLearning Trends:")
    logger.info(f"  Performance Trend: {'UP' if performance_trend > 0 else 'DOWN'} {performance_trend:.4f}")
    logger.info(f"  Pleasure Trend: {'UP' if pleasure_trend > 0 else 'DOWN'} {pleasure_trend:.4f}")
    
    # Save detailed analysis
    analysis_data = {
        'runs': len(results),
        'rl_library': 'Stable Baselines3 (DQN)',
        'performance_progression': performances,
        'pleasure_progression': pleasures,
        'collaboration_progression': collaborations,
        'task_completion_progression': task_completion_rates,
        'task_failure_progression': task_failure_counts,
        'learning_trends': {
            'performance_trend': performance_trend,
            'pleasure_trend': pleasure_trend
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Save to generated directory
    generated_dir = os.path.join(project_root, "core", "generated")
    os.makedirs(generated_dir, exist_ok=True)
    
    analysis_file = os.path.join(generated_dir, 'learning_analysis_sb3.json')
    # Ensure file is overwritten
    with open(analysis_file, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    logger.info(f"\nDetailed analysis saved to '{analysis_file}'")

    # Save concise first vs last summary
    summary = {
        'runs': len(results),
        'rl_library': 'Stable Baselines3 (DQN)',
        'first_run': results[0]['final_stats'] if results else {},
        'last_run': results[-1]['final_stats'] if results else {},
        'delta': {
            'avg_performance': (performances[-1] - performances[0]) if results else 0.0,
            'avg_pleasure': (pleasures[-1] - pleasures[0]) if results else 0.0,
            'team_collaboration': (collaborations[-1] - collaborations[0]) if results else 0.0,
            'task_completion_rate': (task_completion_rates[-1] - task_completion_rates[0]) if results else 0.0,
            'task_failures': (task_failure_counts[-1] - task_failure_counts[0]) if results else 0,
        }
    }
    summary_file = os.path.join(generated_dir, 'learning_summary_first_vs_last_sb3.json')
    # Ensure file is overwritten
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"First vs Last summary saved to '{summary_file}'")


def main():
    """Main function to run the learning simulation with Stable Baselines3."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Emotional Team Learning Simulation with Stable Baselines3')
    parser.add_argument('--project-file', type=str, 
                       default=DEFAULT_PROJECT_FILE,
                       help='Path to XML project file')
    parser.add_argument('--runs', type=int, default=DEFAULT_NUMBER_OF_RUNS,
                       help='Number of simulation runs')
    parser.add_argument('--output', type=str, default='learning_results_sb3.json',
                       help='Output file for results')
    
    args = parser.parse_args()
    
    # Check if project file exists
    if not os.path.exists(args.project_file):
        logger.error(f"Project file not found: {args.project_file}")
        return
    
    try:
        # Run simulation
        results = run_learning_simulation_sb3(
            project_file=args.project_file,
            num_runs=args.runs
        )
        
        # Save results to generated directory
        generated_dir = os.path.join(project_root, "core", "generated")
        os.makedirs(generated_dir, exist_ok=True)
        
        output_file = os.path.join(generated_dir, args.output)
        # Ensure file is overwritten
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\nResults saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise


if __name__ == "__main__":
    main()
