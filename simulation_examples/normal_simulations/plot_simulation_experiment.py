# Complete and updated content of simulation_examples/plot_simulation_experiment.py

import sys
import os
import traceback
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from datetime import datetime
import time

# --- Environment Configuration ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.normpath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import Components ---
try:
    from core.simulation.runner import ExperimentConfig, SimulationRunner
    from core.simulation.model import ProjectManagementModel
    from core.simulation.parameters import SimulationParameters
    from core.readers.xml_reader import XmlProjectReader
    from core.project import Project
except ImportError as e:
    print(f"Fatal Error: Could not import required components: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- EXPERIMENT CONFIGURATION ---
team_definitions_config = [
    { "id": 101, "name": "Analysis and Design Team", "member_resource_ids": [1, 2] },
    { "id": 102, "name": "Development and Testing Team", "member_resource_ids": [3, 4] }
]

STRATEGY_TO_USE = "parallel"

class RealTimeVisualization:
    """Real-time visualization of simulation progress."""
    
    def __init__(self):
        self.fig, self.axes = plt.subplots(2, 3, figsize=(20, 10))
        self.fig.suptitle('ABP Simulator - Real-time Visualization', fontsize=16, fontweight='bold')
        
        # Initialize plots
        self.setup_plots()
        
        # Data storage
        self.time_data = []
        self.completion_data = []
        self.cost_data = []
        self.spi_data = []  # Add SPI data
        self.morale_data = []
        self.task_progress_data = []
        
        # EVM data storage
        self.pv_data = []  # Planned Value
        self.ev_data = []  # Earned Value
        self.ac_data = []  # Actual Cost
        
        # Colors for teams
        self.team_colors = {
            101: '#FF6B6B',  # Red for Analysis Team
            102: '#4ECDC4'   # Teal for Development Team
        }
        
    def setup_plots(self):
        """Setup the subplots."""
        # Plot 1: Project Completion Progress
        self.axes[0, 0].set_title('Project Completion Progress')
        self.axes[0, 0].set_xlabel('Time Steps')
        self.axes[0, 0].set_ylabel('Completion %')
        self.axes[0, 0].set_ylim(0, 100)
        self.axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Cost and Schedule Performance
        self.axes[0, 1].set_title('EVM Performance Indices')
        self.axes[0, 1].set_xlabel('Time Steps')
        self.axes[0, 1].set_ylabel('Performance Index')
        self.axes[0, 1].set_ylim(0, 2)
        self.axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: EVM Values (AC, EV, PV)
        self.axes[0, 2].set_title('EVM Values Over Time')
        self.axes[0, 2].set_xlabel('Time Steps')
        self.axes[0, 2].set_ylabel('Cost ($)')
        self.axes[0, 2].grid(True, alpha=0.3)
        
        # Plot 4: Team Morale
        self.axes[1, 0].set_title('Team Morale Levels')
        self.axes[1, 0].set_xlabel('Time Steps')
        self.axes[1, 0].set_ylabel('Morale')
        self.axes[1, 0].set_ylim(0, 1)
        self.axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 5: Task Status Distribution
        self.axes[1, 1].set_title('Task Status Distribution')
        self.axes[1, 1].set_xlabel('Status')
        self.axes[1, 1].set_ylabel('Number of Tasks')
        
        # Plot 6: Combined Progress and EVM
        self.axes[1, 2].set_title('Progress vs EVM Values')
        self.axes[1, 2].set_xlabel('Time Steps')
        self.axes[1, 2].set_ylabel('Value')
        self.axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
    def update_data(self, model):
        """Update data from the simulation model."""
        current_time = model.schedule.time
        
        # Calculate EVM metrics
        total_tasks = len(model.task_map)
        completed_tasks = sum(1 for task in model.task_map.values() if task.status.value == "done")
        completion_pct = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Earned Value Management (EVM) calculations
        planned_value = model.total_planned_value()
        earned_value = model.total_earned_value()
        actual_cost = model.total_actual_cost()
        
        # Calculate CPI and SPI
        cpi = earned_value / actual_cost if actual_cost > 0 else 1.0
        spi = earned_value / planned_value if planned_value > 0 else 0.0
        
        # Calculate average team morale
        avg_morale = np.mean([team.morale for team in model.teams]) if model.teams else 0
        
        # Store data
        self.time_data.append(current_time)
        self.completion_data.append(completion_pct)
        self.cost_data.append(cpi)
        self.spi_data.append(spi)  # Store SPI
        self.morale_data.append(avg_morale)
        
        # Store EVM values
        self.pv_data.append(planned_value)
        self.ev_data.append(earned_value)
        self.ac_data.append(actual_cost)
        
        # Task status distribution
        status_counts = {'TO_DO': 0, 'IN_PROGRESS': 0, 'DONE': 0}
        for task in model.task_map.values():
            status_value = task.status.value
            if status_value == "to-do":
                status_counts['TO_DO'] += 1
            elif status_value == "in_progress":
                status_counts['IN_PROGRESS'] += 1
            elif status_value == "done":
                status_counts['DONE'] += 1
        
        self.task_progress_data.append(status_counts)
        
    def update_plots(self, frame):
        """Update all plots with current data."""
        if not self.time_data:
            return
            
        # Clear previous plots
        for ax in self.axes.flat:
            ax.clear()
        
        # Re-setup plot properties
        self.setup_plots()
        
        # Plot 1: Completion Progress
        self.axes[0, 0].plot(self.time_data, self.completion_data, 'b-', linewidth=2, label='Completion %')
        self.axes[0, 0].fill_between(self.time_data, self.completion_data, alpha=0.3, color='blue')
        
        # Plot 2: EVM Performance Indices
        self.axes[0, 1].plot(self.time_data, self.cost_data, 'g-', linewidth=2, label='CPI')
        self.axes[0, 1].plot(self.time_data, self.spi_data, 'orange', linewidth=2, label='SPI')
        self.axes[0, 1].axhline(y=1.0, color='r', linestyle='--', alpha=0.7, label='Target (1.0)')
        
        # Plot 3: EVM Values (AC, EV, PV)
        if self.pv_data and self.ev_data and self.ac_data:
            self.axes[0, 2].plot(self.time_data, self.pv_data, 'b-', linewidth=2, label='PV (Planned Value)')
            self.axes[0, 2].plot(self.time_data, self.ev_data, 'g-', linewidth=2, label='EV (Earned Value)')
            self.axes[0, 2].plot(self.time_data, self.ac_data, 'r-', linewidth=2, label='AC (Actual Cost)')
        
        # Plot 4: Team Morale
        if self.morale_data:
            self.axes[1, 0].plot(self.time_data, self.morale_data, 'purple', linewidth=2, label='Avg Morale')
            self.axes[1, 0].fill_between(self.time_data, self.morale_data, alpha=0.3, color='purple')
        
        # Plot 5: Task Status Distribution (current)
        if self.task_progress_data:
            current_status = self.task_progress_data[-1]
            statuses = list(current_status.keys())
            counts = list(current_status.values())
            colors = ['#FF9999', '#FFCC99', '#99FF99']  # Red, Orange, Green
            
            bars = self.axes[1, 1].bar(statuses, counts, color=colors, alpha=0.7)
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                self.axes[1, 1].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                   f'{count}', ha='center', va='bottom', fontweight='bold')
        
        # Plot 6: Combined Progress and EVM (normalized)
        if self.completion_data and self.pv_data and self.ev_data and self.ac_data:
            # Normalize EVM values to 0-100 scale for comparison with completion %
            max_evm = max(max(self.pv_data), max(self.ev_data), max(self.ac_data))
            if max_evm > 0:
                pv_normalized = [pv / max_evm * 100 for pv in self.pv_data]
                ev_normalized = [ev / max_evm * 100 for ev in self.ev_data]
                ac_normalized = [ac / max_evm * 100 for ac in self.ac_data]
                
                self.axes[1, 2].plot(self.time_data, self.completion_data, 'k-', linewidth=3, label='Progress %')
                self.axes[1, 2].plot(self.time_data, pv_normalized, 'b--', linewidth=2, label='PV (normalized)')
                self.axes[1, 2].plot(self.time_data, ev_normalized, 'g--', linewidth=2, label='EV (normalized)')
                self.axes[1, 2].plot(self.time_data, ac_normalized, 'r--', linewidth=2, label='AC (normalized)')
                self.axes[1, 2].set_ylabel('Value (%)')
        
        # Add legends
        self.axes[0, 0].legend()
        self.axes[0, 1].legend()
        self.axes[0, 2].legend()
        self.axes[1, 0].legend()
        self.axes[1, 2].legend()
        
        # Update title with current step
        if self.time_data:
            current_step = self.time_data[-1]
            self.fig.suptitle(f'ABP Simulator - Real-time Visualization (Step: {current_step})', 
                             fontsize=16, fontweight='bold')
        
        return self.axes.flat

class VisualSimulationRunner:
    """Custom simulation runner with real-time visualization."""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.visualization = RealTimeVisualization()
        self._project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
        self.project_file_path = os.path.join(self._project_root, config.data_folder_relative_path,
                                              config.mpp_file_name)
        
    def run_visual_simulation(self):
        """Run simulation with real-time visualization."""
        print("=" * 70)
        print(" ABP Simulator - Real-time Visualization Demo ")
        print(f" STRATEGY: {self.config.assignment_strategy.upper()}")
        print("=" * 70)
        
        # Load project
        print("Loading project data...")
        reader = XmlProjectReader()
        project_data = reader.load(self.project_file_path)
        project = Project(project_data)
        
        print(f"Project loaded: {len(project.tasks)} tasks, {len(project.resources)} resources")
        
        # Create simulation parameters
        sim_params = SimulationParameters(
            error_margin=self.config.simulation_params.get('error_margin', 0.1),
            reassignment_frequency=self.config.simulation_params.get('reassignment_frequency', 0),
            max_steps=self.config.simulation_params.get('max_steps', 1000),
            team_definitions=self.config.team_definitions,
            assignment_strategy=self.config.assignment_strategy
        )
        
        # Create model
        model = ProjectManagementModel(
            tasks=project.get_tasks_for_simulation(),
            resources=project.get_resources_for_simulation(),
            params=sim_params
        )
        
        # *** HARDCODED AC OVERRIDE ***
        # This is where we override the AC calculation for this specific simulation
        def customize_ac_for_this_simulation(model):
            """
            Override the AC calculation for this specific simulation instance.
            This is an 'unofficial' modification that doesn't affect the core code.
            """
            # Save the original method (in case you want to restore it later)
            model._original_total_actual_cost = model.total_actual_cost
            
            # Define your custom AC - HARDCODED TO $40,000
            def custom_total_actual_cost():
                # AC hardcoded to $40,000 regardless of progress
                return 40000.0
            
            # Replace the method only for this instance
            model.total_actual_cost = custom_total_actual_cost
            
            print("AC calculation customized for this simulation - HARDCODED TO $40,000!")
            return model
        
        # Apply your custom AC
        model = customize_ac_for_this_simulation(model)
        
        print(f"Model created with {len(model.teams)} teams")
        print("Starting real-time visualization...")
        
        # Setup animation
        animation_stopped = False
        
        def animate(frame):
            nonlocal animation_stopped
            
            if model.running and not animation_stopped:
                model.step()
                self.visualization.update_data(model)
                self.visualization.update_plots(frame)
                
                # Print progress every 100 steps
                if model.schedule.time % 100 == 0:
                    completed = sum(1 for t in model.task_map.values() if t.status.value == "done")
                    total = len(model.task_map)
                    pv = model.total_planned_value()
                    ev = model.total_earned_value()
                    ac = model.total_actual_cost()
                    cpi_val = ev / ac if ac > 0 else 1.0
                    spi_val = ev / pv if pv > 0 else 0.0
                    print(f"Step {model.schedule.time}: {completed}/{total} tasks completed ({completed/total*100:.1f}%)")
                    print(f"  EVM: PV=${pv:.0f}, EV=${ev:.0f}, AC=${ac:.0f}, CPI={cpi_val:.2f}, SPI={spi_val:.2f}")
            elif not model.running and not animation_stopped:
                # Simulation completed, stop the animation gracefully
                animation_stopped = True
                try:
                    anim.event_source.stop()
                    print("Animation stopped - simulation completed!")
                except:
                    pass  # Ignore any errors when stopping
            
            return self.visualization.axes.flat
        
        # Create animation
        anim = animation.FuncAnimation(
            self.visualization.fig, 
            animate, 
            interval=100,  # Update every 100ms
            blit=False,
            repeat=False
        )
        
        # Show the plot
        plt.show()
        
        # Print final results
        final_completed = sum(1 for t in model.task_map.values() if t.status.value == "done")
        total_tasks = len(model.task_map)
        final_completion = (final_completed / total_tasks) * 100
        
        # Final EVM metrics
        final_pv = model.total_planned_value()
        final_ev = model.total_earned_value()
        final_ac = model.total_actual_cost()
        final_cpi = final_ev / final_ac if final_ac > 0 else 1.0
        final_spi = final_ev / final_pv if final_pv > 0 else 0.0
        
        print("\n" + "=" * 70)
        print(" SIMULATION COMPLETED ")
        print(f" Final Completion: {final_completion:.1f}% ({final_completed}/{total_tasks} tasks)")
        print(f" Total Steps: {model.schedule.time}")
        print(f" Final EVM Metrics:")
        print(f"   Planned Value (PV): ${final_pv:.0f}")
        print(f"   Earned Value (EV): ${final_ev:.0f}")
        print(f"   Actual Cost (AC): ${final_ac:.0f}")
        print(f"   Cost Performance Index (CPI): {final_cpi:.2f}")
        print(f"   Schedule Performance Index (SPI): {final_spi:.2f}")
        print("=" * 70)

# --- EXPERIMENT CONFIGURATION ---
team_definitions_config = [
    { "id": 101, "name": "Analysis and Design Team", "member_resource_ids": [1, 2] },
    { "id": 102, "name": "Development and Testing Team", "member_resource_ids": [3, 4] }
]

STRATEGY_TO_USE = "parallel"

experiment_settings = ExperimentConfig(
    mpp_file_name="Software Development Plan.xml",
    data_folder_relative_path=os.path.join(project_root, "data"),
    reader_type="xml",
    simulation_params={
        "error_margin": 0.2,  # Reduced for smoother visualization
        "reassignment_frequency": 0,
        "max_steps": 2000  # Reasonable limit for demo
    },
    team_definitions=team_definitions_config,
    assignment_strategy=STRATEGY_TO_USE,
    num_simulations=1,  # Single simulation for visualization
    output_filename_base="visual_demo",
    add_timestamp_to_filename=False,
    output_folder_relative_path=os.path.join(project_root, "core", "generated"),
    show_loaded_tasks=False,
    show_loaded_resources=False,
    display_limit=15,
    print_last_run_summary=True,
    resources_definition=[]
)

# --- EXECUTION ---
if __name__ == "__main__":
    try:
        visual_runner = VisualSimulationRunner(config=experiment_settings)
        visual_runner.run_visual_simulation()
    except KeyboardInterrupt:
        print("\nVisualization stopped by user.")
    except Exception as e:
        print(f"Error during visualization: {e}")
        traceback.print_exc()
