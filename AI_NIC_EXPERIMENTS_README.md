# AI NIC Sharing Experiments

This suite of scripts runs comprehensive NIC (Network Interface Card) sharing experiments on multi-GPU systems to evaluate different GPU communication patterns.

## Experiment Configurations

The experiments test the following configurations:

| Experiment | GPU Configuration | Imbalance Test | Description |
|------------|------------------|----------------|-------------|
| 1-to-1 | 0,2,4,6 | No | Each GPU communicates with one other GPU |
| 2-to-1-(1x) | 0,1,2,4 | No | Two GPUs share communication with one |
| 2-to-1-(2x) | 0,1,4,5 | No | Alternative 2-to-1 configuration |
| all-to-all | All GPUs | No | All GPUs communicate with each other |
| 1-to-1-imbalanced | 0,2,4,6 | Yes | 1-to-1 with workload imbalance |
| 2-to-1-(1x)-imbalanced | 0,1,2,4 | Yes | 2-to-1 with workload imbalance |
| 2-to-1-(2x)-imbalanced | 0,1,4,5 | Yes | Alternative 2-to-1 with imbalance |
| all-to-all-imbalanced | All GPUs | Yes | All-to-all with workload imbalance |

## Scripts Overview

### 1. `ai_nic_sharing_experiments.py`
Main script that runs all experiments with 5 runs each.

**Usage:**
```bash
python3 ai_nic_sharing_experiments.py
```

**Features:**
- Runs all 8 experiment configurations automatically
- Each experiment runs 5 times for statistical reliability
- Generates individual CSV files for each experiment
- Creates a summary file with all experiment details
- Shows progress and results in real-time

**Output Files:**
- `results_<experiment_name>_<timestamp>.csv` - Individual experiment results
- `experiment_summary_<timestamp>.txt` - Overall summary of all experiments

### 2. `test_ai_nic_experiments.py`
Quick test script to verify setup before running full experiments.

**Usage:**
```bash
python3 test_ai_nic_experiments.py
```

**Features:**
- Runs minimal tests with reduced parameters
- Uses only 32 tokens for speed
- Single run per configuration
- Helps identify setup issues quickly

### 3. `combine_experiment_results.py`
Combines all experiment CSV files into a single summary.

**Usage:**
```bash
# Combine all results_*.csv files
python3 combine_experiment_results.py

# Combine specific pattern
python3 combine_experiment_results.py "results_*imbalanced*.csv"

# Generate LaTeX table
python3 combine_experiment_results.py --latex
```

**Output Files:**
- `combined_results_<timestamp>.csv` - All results in one file
- `comparison_table_<timestamp>.csv` - Simplified comparison table
- `results_table.tex` - LaTeX formatted table (if --latex flag used)

## Prerequisites

1. **Environment Setup:**
   ```bash
   # Ensure you're in the DeepEP root directory
   cd /path/to/DeepEP
   
   # Install DeepEP if not already installed
   python setup.py install
   ```

2. **Check Environment:**
   ```bash
   python3 check_environment.py
   ```

3. **Verify GPU Access:**
   ```bash
   nvidia-smi
   ```

## Running the Experiments

### Step 1: Test the Setup
```bash
# Run quick test to ensure everything works
python3 test_ai_nic_experiments.py
```

### Step 2: Run Full Experiments
```bash
# This will take approximately 30-60 minutes depending on your system
python3 ai_nic_sharing_experiments.py
```

### Step 3: Analyze Results
```bash
# Combine all results into summary tables
python3 combine_experiment_results.py

# Generate LaTeX table for paper/report
python3 combine_experiment_results.py --latex
```

## Expected Runtime

- **Quick Test**: ~2-5 minutes
- **Full Experiments**: ~30-60 minutes
  - Each configuration: ~3-8 minutes
  - 8 configurations × 5 runs each = 40 runs total

## Output Structure

```
DeepEP/
├── results_1-to-1_20241121_140000.csv
├── results_2-to-1-1x_20241121_140500.csv
├── results_2-to-1-2x_20241121_141000.csv
├── results_all-to-all_20241121_141500.csv
├── results_1-to-1-imbalanced_20241121_142000.csv
├── results_2-to-1-1x-imbalanced_20241121_142500.csv
├── results_2-to-1-2x-imbalanced_20241121_143000.csv
├── results_all-to-all-imbalanced_20241121_143500.csv
├── experiment_summary_20241121_144000.txt
├── combined_results_20241121_144500.csv
└── comparison_table_20241121_144500.csv
```

## Troubleshooting

### If experiments hang:
1. Check GPU availability: `nvidia-smi`
2. Check for port conflicts: Try changing port with `--port 8362`
3. Reduce number of processes or tokens for testing
4. Check system logs: `dmesg | tail -20`

### If CSV files are empty:
1. Check that test_low_latency.py runs manually
2. Verify DeepEP is properly installed
3. Check log files in `/tmp/benchmark_logs_*`

### Common Issues:
- **CUDA out of memory**: Reduce `--num-tokens` parameter
- **Port in use**: Change port with `--port` flag
- **Module not found**: Run `python setup.py install`
- **Timeout errors**: Increase timeout in scripts or reduce workload

## Interpreting Results

The CSV files contain the following metrics:
- **Event Type**: dispatch, combine, dispatch+combine, send/recv operations
- **Average Bandwidth [GB/s]**: Communication throughput
- **Average Time [us]**: Operation latency
- **Standard Deviation**: Consistency of performance
- **Per-rank Bandwidth**: Individual GPU performance

Key metrics to compare:
1. **Bandwidth differences** between configurations
2. **Impact of imbalance** on performance
3. **Scaling efficiency** from 1-to-1 to all-to-all
4. **Send/recv time asymmetry** in different topologies

## Contact

For issues or questions about these experiments, please refer to the DeepEP documentation or create an issue in the repository.
