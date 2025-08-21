# Final Benchmark Runner Modifications

## Summary of All Changes

The `benchmark_runner.py` script has been completely redesigned with the following major improvements:

### 1. CSV Output with Split Events
- **Event Splitting**: Dispatch send/recv and combine send/recv are now split into separate rows:
  - `dispatch send` - separate row with avg_t_send populated
  - `dispatch recv` - separate row with avg_t_recv populated  
  - `combine send` - separate row with avg_t_send populated
  - `combine recv` - separate row with avg_t_recv populated
  
- **Complete CSV columns**:
  1. `Event` - The event type (7 different types total)
  2. `GPU Configuration` - Extracted from CUDA_VISIBLE_DEVICES
  3. `Imbalance test` - Boolean, checks for --imbalance-test flag
  4. `avg bandwidth [GB/s]` - Average bandwidth across all ranks
  5. `avg_t [us]` - Average time in microseconds
  6. `avg_t_send [us]` - Send time (only for send events, 0 otherwise)
  7. `avg_t_recv [us]` - Receive time (only for recv events, 0 otherwise)
  8. `Std deviation [GB/s]` - Standard deviation of bandwidth
  9. `Avg. rank0 BW [GB/s]` through `Avg. rank7 BW [GB/s]` - Per-rank averages

### 2. Log Management
- Logs saved to `/tmp/benchmark_logs_TIMESTAMP/`
- Each experiment in its own subdirectory
- Each run saved as separate log file
- Error runs captured with full stdout/stderr

### 3. Clean Console Output
- Uses progress indicators: ✓ (success), ⚠ (warning), ✗ (error)
- Shows only summary statistics, not raw output
- Informative progress messages
- Final summary with key metrics

### 4. Event Types Parsed
The script now correctly parses and splits these event types:
1. `dispatch + combine` - Combined metrics
2. `dispatch` - Dispatch only metrics
3. `combine` - Combine only metrics
4. `dispatch send` - Send portion of dispatch (from split)
5. `dispatch recv` - Receive portion of dispatch (from split)
6. `combine send` - Send portion of combine (from split)
7. `combine recv` - Receive portion of combine (from split)

### 5. Key Implementation Details

#### Parsing Logic
```python
# Send/recv events are split into separate entries
results['dispatch send'][rank] = {
    'send_time': float(d_send),
    'avg_t_send': float(d_send)
}
results['dispatch recv'][rank] = {
    'recv_time': float(d_recv),
    'avg_t_recv': float(d_recv)
}
```

#### Time Column Population
- For `dispatch send` and `combine send`: `avg_t_send` is populated, `avg_t_recv` is 0
- For `dispatch recv` and `combine recv`: `avg_t_recv` is populated, `avg_t_send` is 0
- For all other events: both `avg_t_send` and `avg_t_recv` are 0

### 6. Usage Examples

#### Basic usage:
```bash
python3 benchmark_runner.py
```

#### With custom output and multiple runs:
```bash
python3 benchmark_runner.py \
  -c "python3 tests/test_low_latency.py --disable-nvlink" \
  -n 10 \
  -o my_results.csv
```

#### Multiple experiments:
```bash
python3 benchmark_runner.py \
  -c "python3 tests/test_low_latency.py" \
     "CUDA_VISIBLE_DEVICES=0,1,2,3 python3 tests/test_low_latency.py --num-processes 4" \
     "python3 tests/test_low_latency.py --imbalance-test" \
  -n 5 \
  -o comparison.csv
```

### 7. Example CSV Output

```csv
Event,GPU Configuration,Imbalance test,avg bandwidth [GB/s],avg_t [us],avg_t_send [us],avg_t_recv [us],Std deviation [GB/s],Avg. rank0 BW [GB/s],Avg. rank1 BW [GB/s],...
dispatch + combine,all,False,24.38,904.30,0.00,0.00,0.05,24.40,24.36,...
dispatch,all,False,23.85,312.50,0.00,0.00,0.30,23.49,24.02,...
combine,all,False,24.90,585.00,0.00,0.00,0.20,25.14,24.83,...
dispatch send,all,False,0.30,190.23,190.23,0.00,0.02,0.31,0.29,...
dispatch recv,all,False,0.03,73509.90,0.00,73509.90,0.01,0.03,0.03,...
combine send,all,False,0.16,201.45,201.45,0.00,0.01,0.17,0.15,...
combine recv,all,False,0.01,135822.10,0.00,135822.10,0.00,0.01,0.01,...
```

### 8. Testing

Two test scripts are provided:
1. `test_benchmark_runner.py` - Basic functionality test
2. `test_split_events.py` - Verifies send/recv event splitting

Run tests:
```bash
python3 test_split_events.py
```

### 9. Dependencies
- pandas (for CSV handling)
- numpy (for statistics)
- Standard Python libraries (subprocess, re, os, datetime, argparse, collections)

### 10. Error Handling
- 5-minute timeout per run
- Graceful handling of failed runs
- Continues processing even if some runs fail
- Error logs saved separately

## Verification

The modifications ensure that:
1. ✅ Send/recv times are split into separate CSV rows
2. ✅ Each event type has appropriate timing columns populated
3. ✅ Original verbose output is saved to log files
4. ✅ Console shows only summary information
5. ✅ CSV includes all requested columns in the correct order
6. ✅ GPU configuration and imbalance test flags are extracted from commands
