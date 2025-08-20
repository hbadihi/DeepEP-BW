import subprocess
import re
import os
import numpy as np
from datetime import datetime
import argparse


def parse_output(output: str):
    """
    Parses the benchmark output to find various performance metrics for each rank.

    Args:
        output: The stdout string from the test script.

    Returns:
        A dictionary containing lists of (rank, value) tuples for each metric.
    """
    results = {
        'total_bw': [],
        'dispatch_bw': [],
        'combine_bw': [],
        'dispatch_latency': [],
        'combine_latency': [],
    }

    # Pattern for combined bandwidth from bench()
    # e.g., [rank 3] Dispatch + combine bandwidth: 23.18 GB/s...
    total_bw_pattern = re.compile(r"\[rank (\d+)\] Dispatch \+ combine bandwidth: ([\d.]+) GB/s")
    for rank, bw in total_bw_pattern.findall(output):
        results['total_bw'].append((int(rank), float(bw)))

    # Pattern for separate bandwidths from bench_kineto(hook=False)
    # e.g., [rank 0] Dispatch bandwidth: 88.01 GB/s, ... | Combine bandwidth: 68.61 GB/s, ...
    separate_bw_pattern = re.compile(r"\[rank (\d+)\] Dispatch bandwidth: ([\d.]+) GB/s.*?Combine bandwidth: ([\d.]+) GB/s")
    for rank, dbw, cbw in separate_bw_pattern.findall(output):
        results['dispatch_bw'].append((int(rank), float(dbw)))
        results['combine_bw'].append((int(rank), float(cbw)))

    # Pattern for separate latencies from bench_kineto(hook=True)
    # e.g., [rank 0] Dispatch send/recv time: 5.23 + 37.15 us | Combine send/recv time: 1.63 + 32.59 us
    latency_pattern = re.compile(r"\[rank (\d+)\] Dispatch send/recv time: ([\d.]+) \+ ([\d.]+) us.*?Combine send/recv time: ([\d.]+) \+ ([\d.]+) us")
    for rank, d_send, d_recv, c_send, c_recv in latency_pattern.findall(output):
        dispatch_latency = float(d_send) + float(d_recv)
        combine_latency = float(c_send) + float(c_recv)
        results['dispatch_latency'].append((int(rank), dispatch_latency))
        results['combine_latency'].append((int(rank), combine_latency))

    return results


def main(args):
    """
    Main function to run the benchmark experiments.
    """
    print("Starting benchmark suite...")

    metric_titles = {
        'total_bw': "Aggregated Bandwidth (GB/s)",
        'dispatch_bw': "Dispatch Bandwidth (GB/s)",
        'combine_bw': "Combine Bandwidth (GB/s)",
        'dispatch_latency': "Dispatch Latency (us)",
        'combine_latency': "Combine Latency (us)",
    }
    
    # Dictionaries to store all results for the final summary.
    all_results = {key: {cmd: [] for cmd in args.commands} for key in metric_titles}
    num_ranks_per_command = {cmd: 0 for cmd in args.commands}
    
    for command in args.commands:
        print(f"\n{'='*80}")
        print(f"Running Experiment: {command}")
        print(f"{'='*80}")

        for run_num in range(1, args.num_runs + 1):
            print(f"  > Starting run {run_num}/{args.num_runs}...")
            
            try:
                # Execute the command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Parse the output to get all metric data
                parsed_data = parse_output(result.stdout)

                if not any(parsed_data.values()):
                    print("    ! Warning: Could not parse any performance information from output.")
                    continue

                # Store number of ranks for this command if we haven't already
                if num_ranks_per_command[command] == 0 and parsed_data['total_bw']:
                    num_ranks_per_command[command] = len(parsed_data['total_bw'])

                # Store results for the final summary
                for metric, values in parsed_data.items():
                    all_results[metric][command].extend(values)
                
                # Print a detailed summary for the completed run
                print(f"    - Run {run_num} complete. Per-rank results:")
                for metric, title in metric_titles.items():
                    if parsed_data[metric]:
                        avg_val = np.mean([v for _, v in parsed_data[metric]])
                        unit = "GB/s" if "Bandwidth" in title else "us"
                        rank_vals_str = ", ".join([f"R{r}: {v:.2f}" for r, v in sorted(parsed_data[metric])])
                        print(f"      - {title:<30} | Avg: {avg_val:>6.2f} {unit} | Ranks: [{rank_vals_str}]")


            except subprocess.CalledProcessError as e:
                print(f"    ! Error running command on run {run_num}!")
                print(f"    ! Return Code: {e.returncode}")
                print(f"    ! Stdout:\n{e.stdout}")
                print(f"    ! Stderr:\n{e.stderr}")
            except Exception as e:
                print(f"    ! An unexpected error occurred on run {run_num}: {e}")

    # --- Final Summary ---
    print(f"\n\n{'='*80}")
    print("Benchmark Complete: Overall Summary")
    print(f"{'='*80}")
    
    for metric, title in metric_titles.items():
        header_char = ['#', '*', '+', '-', '~'][list(metric_titles.keys()).index(metric)]
        print(f"\n\n{header_char*80}")
        print(f"{header_char*3} Summary for: {title}")
        print(f"{header_char*80}")

        results_for_metric = all_results[metric]

        for command, values in results_for_metric.items():
            if values:
                num_ranks = num_ranks_per_command[command]
                # values is now a list of (rank, value) tuples
                numeric_values = [v for _, v in values]
                num_runs = len(numeric_values) // num_ranks if num_ranks > 0 else 0
                overall_avg = np.mean(numeric_values)
                std_dev = np.std(numeric_values)
                min_val = np.min(numeric_values)
                max_val = np.max(numeric_values)
                unit = "GB/s" if "Bandwidth" in title else "us"

                print(f"\nExperiment: {command}")
                print(f"  - Total Runs: {num_runs}, Ranks per run: {num_ranks}")
                print(f"  - Average: {overall_avg:.2f} {unit}")
                print(f"  - Std Dev: {std_dev:.2f} {unit}")
                print(f"  - Min (across all ranks & runs): {min_val:.2f} {unit}")
                print(f"  - Max (across all ranks & runs): {max_val:.2f} {unit}")

                # Calculate and print per-rank averages
                if num_ranks > 0:
                    rank_averages = []
                    for r in range(num_ranks):
                        rank_values = [v for rank, v in values if rank == r]
                        if rank_values:
                            rank_avg = np.mean(rank_values)
                            rank_averages.append(f"Rank {r}: {rank_avg:.2f}")
                    print(f"  - Per-Rank Avg ({unit}): {', '.join(rank_averages)}")
            else:
                print(f"\nExperiment: {command}")
                print("  - No data collected for this experiment.")


if __name__ == "__main__":
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Run benchmark experiments for test_low_latency.py and print results to the console.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '-c', '--commands',
        nargs='+',  # This allows specifying one or more commands
        help='One or more command strings to execute for the benchmark.\n'
             'Example: -c "python3 script.py" "python3 script.py --arg2"',
        default=[
            "CUDA_VISIBLE_DEVICES=0,2,4,6 python3 tests/test_low_latency.py --disable-nvlink --num-processes 4",
            "CUDA_VISIBLE_DEVICES=0,1,2,4 python3 tests/test_low_latency.py --disable-nvlink --num-processes 4",
            "python3 tests/test_low_latency.py --disable-nvlink"
        ]
    )
    
    parser.add_argument(
        '-n', '--num-runs',
        type=int,
        default=10,
        help='Number of times to run each command (default: 10).'
    )
    
    parsed_args = parser.parse_args()
    main(parsed_args)
