import subprocess
import re
import os
import numpy as np
import pandas as pd
from datetime import datetime
import argparse
import uuid
from collections import defaultdict


def parse_output(output: str):
    """
    Parses the benchmark output to extract all performance metrics.
    
    Returns a dictionary with event types as keys and rank data as values.
    """
    results = defaultdict(lambda: defaultdict(list))
    
    # Pattern for combined dispatch + combine
    combined_pattern = re.compile(
        r"\[rank (\d+)\] Dispatch \+ combine bandwidth: ([\d.]+) GB/s, avg_t=([\d.]+) us"
    )
    for rank, bw, avg_t in combined_pattern.findall(output):
        results['dispatch + combine'][int(rank)] = {
            'bandwidth': float(bw),
            'avg_t': float(avg_t)
        }
    
    # Pattern for separate dispatch and combine
    separate_pattern = re.compile(
        r"\[rank (\d+)\] Dispatch bandwidth: ([\d.]+) GB/s, avg_t=([\d.]+) us \| "
        r"Combine bandwidth: ([\d.]+) GB/s, avg_t=([\d.]+) us"
    )
    for rank, d_bw, d_t, c_bw, c_t in separate_pattern.findall(output):
        results['dispatch'][int(rank)] = {
            'bandwidth': float(d_bw),
            'avg_t': float(d_t)
        }
        results['combine'][int(rank)] = {
            'bandwidth': float(c_bw),
            'avg_t': float(c_t)
        }
    
    # Pattern for send/recv times - split into separate events
    send_recv_pattern = re.compile(
        r"\[rank (\d+)\] Dispatch send/recv time: ([\d.]+) \+ ([\d.]+) us \| "
        r"Combine send/recv time: ([\d.]+) \+ ([\d.]+) us"
    )
    for rank, d_send, d_recv, c_send, c_recv in send_recv_pattern.findall(output):
        # Split dispatch send/recv into separate send and recv events
        results['dispatch send'][int(rank)] = {
            'send_time': float(d_send),
            'avg_t_send': float(d_send)
        }
        results['dispatch recv'][int(rank)] = {
            'recv_time': float(d_recv),
            'avg_t_recv': float(d_recv)
        }
        
        # Split combine send/recv into separate send and recv events
        results['combine send'][int(rank)] = {
            'send_time': float(c_send),
            'avg_t_send': float(c_send)
        }
        results['combine recv'][int(rank)] = {
            'recv_time': float(c_recv),
            'avg_t_recv': float(c_recv)
        }

    return results


def extract_gpu_config(command: str):
    """Extract GPU configuration from command."""
    cuda_visible_match = re.search(r'CUDA_VISIBLE_DEVICES=([0-9,]+)', command)
    if cuda_visible_match:
        return cuda_visible_match.group(1)
    return "all"


def extract_imbalance_test(command: str):
    """Check if imbalance test is enabled in command."""
    return '--imbalance-test' in command


def calculate_bandwidth_from_time(avg_time_us, event_type):
    """
    Note: Send/recv events don't have bandwidth - they are timing breakdowns only.
    This function returns None to indicate bandwidth is not applicable.
    """
    # Send/recv times are components of dispatch/combine operations
    # They don't have independent bandwidth measurements
    return None


def process_runs(command, num_runs, log_dir):
    """Execute command multiple times and collect results."""
    all_results = []
    successful_runs = 0
    
    for run_num in range(1, num_runs + 1):
        print(f"    Starting run {run_num}/{num_runs}...", end='', flush=True)
        start_time = datetime.now()
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )
            
            # Save log
            log_file = os.path.join(log_dir, f"run_{run_num}.log")
            with open(log_file, 'w') as f:
                f.write(f"Command: {command}\n")
                f.write(f"Run: {run_num}/{num_runs}\n")
                f.write("="*80 + "\n")
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\n" + "="*80 + "\n")
                f.write("STDERR:\n")
                f.write(result.stderr)
            
            # Parse results
            parsed = parse_output(result.stdout)
            if parsed:
                all_results.append(parsed)
                successful_runs += 1
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f" ✓ complete ({elapsed:.1f}s)")
            else:
                print(f" ⚠ no data parsed")
                
        except subprocess.TimeoutExpired:
            print(f" ✗ timeout (>300s)")
        except subprocess.CalledProcessError as e:
            print(f" ✗ error (code {e.returncode})")
            # Still save the error log
            log_file = os.path.join(log_dir, f"run_{run_num}_error.log")
            with open(log_file, 'w') as f:
                f.write(f"Command: {command}\n")
                f.write(f"Error Code: {e.returncode}\n")
                f.write("STDOUT:\n" + e.stdout)
                f.write("\nSTDERR:\n" + e.stderr)
        except Exception as e:
            print(f" ✗ unexpected error: {e}")
    
    return all_results, successful_runs


def aggregate_results(all_results, event_type, metric='bandwidth'):
    """Aggregate results across multiple runs for a specific event type."""
    if not all_results:
        return {}
    
    # Collect all rank data
    rank_data = defaultdict(list)
    for run_results in all_results:
        if event_type in run_results:
            for rank, data in run_results[event_type].items():
                if metric in data:
                    rank_data[rank].append(data[metric])
                elif metric == 'bandwidth' and ('send_time' in data or 'recv_time' in data):
                    # Send/recv events don't have bandwidth - skip
                    pass
    
    return rank_data


def create_csv_row(command, event_type, all_results, num_ranks=8):
    """Create a CSV row for a specific event type."""
    row = {
        'Event': event_type,
        'GPU Configuration': extract_gpu_config(command),
        'Imbalance test': extract_imbalance_test(command),
    }
    
    # Check if this is a send/recv event (these don't have bandwidth)
    is_send_recv_event = 'send' in event_type or 'recv' in event_type
    
    if not is_send_recv_event:
        # Get bandwidth data for non-send/recv events
        bw_data = aggregate_results(all_results, event_type, 'bandwidth')
        
        if bw_data:
            # Calculate overall statistics
            all_values = [v for rank_values in bw_data.values() for v in rank_values]
            row['avg bandwidth [GB/s]'] = np.mean(all_values) if all_values else 0
            row['Std deviation [GB/s]'] = np.std(all_values) if all_values else 0
            
            # Per-rank averages
            for rank in range(num_ranks):
                if rank in bw_data and bw_data[rank]:
                    row[f'Avg. rank{rank} BW [GB/s]'] = np.mean(bw_data[rank])
                else:
                    row[f'Avg. rank{rank} BW [GB/s]'] = 0
        else:
            row['avg bandwidth [GB/s]'] = 0
            row['Std deviation [GB/s]'] = 0
            for rank in range(num_ranks):
                row[f'Avg. rank{rank} BW [GB/s]'] = 0
    else:
        # Send/recv events don't have bandwidth
        row['avg bandwidth [GB/s]'] = 'N/A'
        row['Std deviation [GB/s]'] = 'N/A'
        for rank in range(num_ranks):
            row[f'Avg. rank{rank} BW [GB/s]'] = 'N/A'
    
    # Get timing data - handle send/recv events specially
    if 'send' in event_type:
        # For send events, use avg_t_send
        time_data = aggregate_results(all_results, event_type, 'avg_t_send')
        if time_data:
            all_times = [v for rank_values in time_data.values() for v in rank_values]
            row['avg_t [us]'] = np.mean(all_times) if all_times else 0
            row['avg_t_send [us]'] = np.mean(all_times) if all_times else 0
        else:
            row['avg_t [us]'] = 0
            row['avg_t_send [us]'] = 0
        row['avg_t_recv [us]'] = 0  # Not applicable for send events
        
    elif 'recv' in event_type:
        # For recv events, use avg_t_recv
        time_data = aggregate_results(all_results, event_type, 'avg_t_recv')
        if time_data:
            all_times = [v for rank_values in time_data.values() for v in rank_values]
            row['avg_t [us]'] = np.mean(all_times) if all_times else 0
            row['avg_t_recv [us]'] = np.mean(all_times) if all_times else 0
        else:
            row['avg_t [us]'] = 0
            row['avg_t_recv [us]'] = 0
        row['avg_t_send [us]'] = 0  # Not applicable for recv events
        
    else:
        # For non-send/recv events, use regular avg_t
        time_data = aggregate_results(all_results, event_type, 'avg_t')
        if time_data:
            all_times = [v for rank_values in time_data.values() for v in rank_values]
            row['avg_t [us]'] = np.mean(all_times) if all_times else 0
        else:
            row['avg_t [us]'] = 0
        row['avg_t_send [us]'] = 0  # Not applicable
        row['avg_t_recv [us]'] = 0  # Not applicable
    
    return row


def main(args):
    """Main function to run benchmark experiments."""
    # Setup output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.output:
        csv_filename = args.output if args.output.endswith('.csv') else f"{args.output}.csv"
    else:
        csv_filename = f"benchmark_results_{timestamp}.csv"
    
    # Create log directory
    log_base_dir = f"/tmp/benchmark_logs_{timestamp}"
    os.makedirs(log_base_dir, exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"Benchmark Suite Started")
    print(f"{'='*80}")
    print(f"Output CSV: {csv_filename}")
    print(f"Log directory: {log_base_dir}")
    print(f"Number of runs per command: {args.num_runs}")
    print(f"Number of experiments: {len(args.commands)}")
    print(f"{'='*80}\n")
    
    # Prepare CSV data
    csv_rows = []
    
    # Process each command
    for cmd_idx, command in enumerate(args.commands, 1):
        print(f"\n[Experiment {cmd_idx}/{len(args.commands)}]")
        print(f"Command: {command[:80]}{'...' if len(command) > 80 else ''}")
        
        # Create command-specific log directory
        cmd_log_dir = os.path.join(log_base_dir, f"experiment_{cmd_idx}")
        os.makedirs(cmd_log_dir, exist_ok=True)
        
        # Save command info
        with open(os.path.join(cmd_log_dir, "command.txt"), 'w') as f:
            f.write(command)
        
        # Run the command multiple times
        all_results, successful_runs = process_runs(command, args.num_runs, cmd_log_dir)
        
        print(f"  Successful runs: {successful_runs}/{args.num_runs}")
        
        if all_results:
            # Determine which event types are present
            event_types = set()
            for run_results in all_results:
                event_types.update(run_results.keys())
            
            # Create rows for each event type
            for event_type in sorted(event_types):
                row = create_csv_row(command, event_type, all_results)
                csv_rows.append(row)
                
                # Print summary
                print(f"  {event_type}:")
                if row['avg bandwidth [GB/s]'] != 'N/A':
                    print(f"    - Avg BW: {row['avg bandwidth [GB/s]']:.2f} GB/s")
                    print(f"    - Std dev: {row['Std deviation [GB/s]']:.2f} GB/s")
                print(f"    - Avg time: {row['avg_t [us]']:.2f} us")
        else:
            print("  ⚠ No data collected for this experiment")
    
    # Save CSV
    if csv_rows:
        df = pd.DataFrame(csv_rows)
        
        # Ensure all columns are present in the correct order
        columns_order = [
            'Event', 'GPU Configuration', 'Imbalance test',
            'avg bandwidth [GB/s]', 'avg_t [us]', 'avg_t_send [us]', 'avg_t_recv [us]',
            'Std deviation [GB/s]'
        ]
        for rank in range(8):
            columns_order.append(f'Avg. rank{rank} BW [GB/s]')
        
        # Reorder columns
        df = df.reindex(columns=columns_order, fill_value=0)
        
        # Save to CSV (don't use float_format since we have 'N/A' values)
        df.to_csv(csv_filename, index=False)
        
        print(f"\n{'='*80}")
        print(f"Benchmark Complete")
        print(f"{'='*80}")
        print(f"✓ Results saved to: {csv_filename}")
        print(f"✓ Logs saved to: {log_base_dir}")
        print(f"✓ Total experiments: {len(args.commands)}")
        print(f"✓ Total rows in CSV: {len(csv_rows)}")
        
        # Print summary statistics
        print(f"\nSummary by Event Type:")
        for event in df['Event'].unique():
            event_df = df[df['Event'] == event]
            # Check if bandwidth data is available (not 'N/A')
            if event_df['avg bandwidth [GB/s]'].iloc[0] != 'N/A':
                avg_bw = event_df['avg bandwidth [GB/s]'].mean()
                print(f"  {event}: {avg_bw:.2f} GB/s average")
            else:
                avg_time = event_df['avg_t [us]'].mean()
                print(f"  {event}: {avg_time:.2f} us average (timing only)")
    else:
        print(f"\n{'='*80}")
        print("⚠ No data collected across all experiments")
        print(f"{'='*80}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run benchmark experiments and output results to CSV",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '-c', '--commands',
        nargs='+',
        help='Commands to execute for benchmarking',
        default=[
            "python3 tests/test_low_latency.py --disable-nvlink",
            "CUDA_VISIBLE_DEVICES=0,2,4,6 python3 tests/test_low_latency.py --disable-nvlink --num-processes 4",
        ]
    )
    
    parser.add_argument(
        '-n', '--num-runs',
        type=int,
        default=3,
        help='Number of times to run each command (default: 3)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output CSV filename (default: benchmark_results_TIMESTAMP.csv)'
    )
    
    args = parser.parse_args()
    main(args)