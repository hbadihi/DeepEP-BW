# Benchmark Runner Modifications Summary

## Key Changes Made

### 1. CSV Output
- **Added CSV export functionality** using pandas
- **Filename options**: Can specify with `-o/--output` flag or auto-generates with timestamp
- **Column structure**:
  - Event (dispatch, combine, dispatch + combine, dispatch send, dispatch recv, combine send, combine recv)
  - GPU Configuration (extracted from CUDA_VISIBLE_DEVICES)
  - Imbalance test (boolean, checks for --imbalance-test flag)
  - avg bandwidth [GB/s]
  - avg_t [us]
  - avg_t_send [us] (only populated for send events)
  - avg_t_recv [us] (only populated for recv events)
  - Std deviation [GB/s]
  - Avg. rank0 BW [GB/s] through Avg. rank7 BW [GB/s]

### 2. Log Management
- **Automatic log saving** to `/tmp/benchmark_logs_TIMESTAMP/`
- **Organized structure**:
  - Each experiment gets its own subdirectory
  - Each run saved as `run_N.log`
  - Error runs saved as `run_N_error.log`
  - Command saved in `command.txt`

### 3. Improved Console Output
- **Cleaner, more informative display**:
  - Progress indicators (✓, ⚠, ✗) for run status
  - Summary statistics per experiment
  - Overall summary at the end
  - No verbose raw output displayed

### 4. Enhanced Parsing
- **Comprehensive event parsing**:
  - Dispatch + combine bandwidth
  - Separate dispatch and combine bandwidth
  - Dispatch send times (split from send/recv)
  - Dispatch recv times (split from send/recv)
  - Combine send times (split from send/recv)
  - Combine recv times (split from send/recv)
- **Automatic aggregation** across multiple runs
- **Per-rank statistics** calculation

### 5. New Features
- **Timeout protection**: 5-minute timeout per run
- **Error handling**: Graceful handling of failed runs
- **pandas dependency**: Added for better CSV handling

## Usage Examples

### Basic usage with default settings:
```bash
python3 benchmark_runner.py
```

### Specify custom commands and output:
```bash
python3 benchmark_runner.py \
  -c "python3 tests/test_low_latency.py --disable-nvlink" \
     "CUDA_VISIBLE_DEVICES=0,1,2,3 python3 tests/test_low_latency.py --num-processes 4" \
  -n 10 \
  -o results.csv
```

### With imbalance testing:
```bash
python3 benchmark_runner.py \
  -c "python3 tests/test_low_latency.py --disable-nvlink --imbalance-test" \
  -n 5 \
  -o imbalance_results.csv
```

## Output Files

### CSV Format Example:
```csv
Event,GPU Configuration,Imbalance test,avg bandwidth [GB/s],avg_t [us],avg_t_send [us],avg_t_recv [us],Std deviation [GB/s],Avg. rank0 BW [GB/s],...
dispatch + combine,all,False,24.38,904.30,0.00,0.00,0.05,24.40,...
dispatch,all,False,23.85,312.50,0.00,0.00,0.30,23.49,...
combine,all,False,24.90,585.00,0.00,0.00,0.20,25.14,...
dispatch send,all,False,0.30,190.23,190.23,0.00,0.02,0.31,...
dispatch recv,all,False,0.30,73509.90,0.00,73509.90,0.05,0.29,...
combine send,all,False,0.16,201.45,201.45,0.00,0.01,0.17,...
combine recv,all,False,0.16,135822.10,0.00,135822.10,0.03,0.15,...
```

### Log Structure:
```
/tmp/benchmark_logs_20241121_143025/
├── experiment_1/
│   ├── command.txt
│   ├── run_1.log
│   ├── run_2.log
│   └── run_3.log
└── experiment_2/
    ├── command.txt
    ├── run_1.log
    └── run_2_error.log
```

## Dependencies
- pandas (new requirement)
- numpy
- subprocess
- re
- os
- datetime
- argparse
- uuid
- collections

## Testing
Run the test script to verify functionality:
```bash
python3 test_benchmark_runner.py
```
