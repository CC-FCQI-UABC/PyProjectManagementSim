# Simulation Examples

This directory contains usage examples for the ABP simulator.

## Available Files

### `simulation_experiment_01.py`
Original simulator experiment that demonstrates:
- Reading XML project files
- Experiment configuration
- Simulation execution
- CSV results generation

### `integral_demo_final.py`
Comprehensive demo that demonstrates:
- Data file verification
- XML file analysis
- Sample data generation
- Experiment simulation
- Results analysis
- Report generation

## How to Run

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run Original Experiment
```bash
python simulation_examples/simulation_experiment_01.py
```

### Run Comprehensive Demo
```bash
python simulation_examples/integral_demo_final.py
```

## Data Files

The examples use project files in `data/`:
- `Software Development Plan.xml` - XML project file
- `Software Development Plan.mpp` - MPP project file

## Results

Results are generated in:
- `core/generated/` - CSV and JSON result files
- Console - Detailed execution logs