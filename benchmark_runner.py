import subprocess
import re
import os
import numpy as np
from datetime import datetime
import argparse


def parse_bandwidth(output: str):
    """
    Parses the benchmark output to find the bandwidth of each rank.

    Args:
        output: The stdout string from the test script.

    Returns:
        A list of tuples, where each tuple is (rank, bandwidth).
    """
    # Regex to find lines like:
    # [rank 3] Dispatch + combine bandwidth: 23.18 GB/s...
    pattern = re.compile(r"\[rank (\d+)\] Dispatch \+ combine bandwidth: ([\d.]+) GB/s")
    matches = pattern.findall(output)
    
    # Convert found strings to correct types (int for rank, float for bandwidth)
    return [(int(rank), float(bandwidth)) for rank, bandwidth in matches]


def main(args):
    """
    Main function to run the benchmark experiments.
    """
    print("Starting benchmark...")
    
    # Dictionary to store all bandwidth results for final summary.
    all_results = {cmd: [] for cmd in args.commands}
    num_ranks_per_command = {cmd: 0 for cmd in args.commands}
    
    for command in args.commands:
        print(f"\n{'='*80}")
        print(f"Running Experiment: {command}")
        print(f"{'='*80}")

        for run_num in range(1, args.num_runs + 1):
            print(f"  > Starting run {run_num}/{args.num_runs}...")
            
            try:
                # Execute the command. Using shell=True to handle env vars easily.
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True  # This will raise an exception for non-zero exit codes
                )

                # Parse the output to get bandwidth data
                bandwidth_data = parse_bandwidth(result.stdout)

                if not bandwidth_data:
                    print("    ! Warning: Could not parse bandwidth information from output.")
                    continue

                # Store number of ranks for this command if we haven't already
                if num_ranks_per_command[command] == 0:
                    num_ranks_per_command[command] = len(bandwidth_data)

                # Get current timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Calculate run average and store individual rank data for the final summary
                run_avg = np.mean([bw for _, bw in bandwidth_data])
                for _, bandwidth in bandwidth_data:
                    all_results[command].append(bandwidth)
                
                # Format individual rank data for appealing stdout, sorted by rank
                rank_bw_str = ", ".join([f"Rank {r}: {bw:.2f}" for r, bw in sorted(bandwidth_data)])
                print(f"    - Run {run_num} complete. Average: {run_avg:.2f} GB/s | Ranks: [{rank_bw_str}]")


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
    
    for command, bandwidths in all_results.items():
        if bandwidths:
            num_ranks = num_ranks_per_command[command]
            num_runs = len(bandwidths) // num_ranks if num_ranks > 0 else 0
            overall_avg = np.mean(bandwidths)
            std_dev = np.std(bandwidths)
            min_bw = np.min(bandwidths)
            max_bw = np.max(bandwidths)
            print(f"\nExperiment: {command}")
            print(f"  - Runs: {num_runs}, Ranks per run: {num_ranks}")
            print(f"  - Average Bandwidth: {overall_avg:.2f} GB/s")
            print(f"  - Standard Deviation: {std_dev:.2f} GB/s")
            print(f"  - Min Bandwidth (single rank): {min_bw:.2f} GB/s")
            print(f"  - Max Bandwidth (single rank): {max_bw:.2f} GB/s")
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
