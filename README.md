# ABP Simulator

**Agent-Based Project Management Simulator** - A simulation framework for project management using agent-based modeling.

## Features

✨ **Core Functionality**
- Agent-based project simulation
- Multiple assignment strategies
- Real-time metrics calculation
- XML/MPP project file support

🔧 **Configuration**
- Flexible simulation parameters
- Multiple assignment strategies
- Customizable team dynamics

📊 **Metrics**
- Cost Performance Index (CPI)
- Schedule Performance Index (SPI)
- Earned Value Management (EVM)
- Team dynamics tracking

## Installation

### From source
```bash
git clone <repository-url>
cd abp-simulator
pip install -r requirements.txt
```

## Quick Start

### Run a simulation
```bash
python simulation_examples/simulation_experiment_01.py
```

### Run the demo
```bash
python simulation_examples/integral_demo_final.py
```

## Project Structure

```
abp_simulator/
├── core/                    # Core simulation framework
│   ├── entities.py         # Task, Resource, Team classes
│   ├── entities_extended.py # Extended entity classes
│   ├── exceptions.py       # Custom exceptions
│   ├── interfaces.py       # Base interfaces
│   ├── project.py          # Project management classes
│   ├── config/             # Configuration system
│   ├── readers/            # Project file readers
│   └── simulation/         # Simulation engine
├── data/                   # Sample project files
├── simulation_examples/    # Example simulations
└── analysis/              # Result analysis tools
```

## Usage

### Basic Simulation
```python
from core.simulation.runner import ExperimentConfig, SimulationRunner

config = ExperimentConfig(
    mpp_file_name="Software Development Plan.xml",
    data_folder_relative_path="data",
    reader_type="xml",
    assignment_strategy="greedy",
    num_simulations=10
)

runner = SimulationRunner(config=config)
runner.run()
```

## Requirements

- Python 3.8+
- pandas
- mesa
- numpy
- aspose-tasks
- JPype1
- lxml

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes
5. Submit a pull request

## License

This project is licensed under the MIT License.