import subprocess
import re
import csv
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
    # Format: { "command_string": [bw1, bw2, ...] }
    all_results = {cmd: [] for cmd in args.commands}
    
    # Handle file existence: if output file exists, create a new one with a suffix.
    output_filename = args.output_file
    if os.path.exists(output_filename):
        base, ext = os.path.splitext(output_filename)
        counter = 1
        new_filename = f"{base}_{counter}{ext}"
        while os.path.exists(new_filename):
            counter += 1
            new_filename = f"{base}_{counter}{ext}"
        print(f"File '{output_filename}' already exists. Saving new results to '{new_filename}'.")
        output_filename = new_filename

    # Always create a new file, so use 'w' mode and always write the header.
    with open(output_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        csv_writer.writerow(["timestamp", "command", "run", "rank", "bandwidth_gb_s"])

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

                    # Get current timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Write each rank's data to the CSV and store for averaging
                    for rank, bandwidth in bandwidth_data:
                        csv_writer.writerow([timestamp, command, run_num, rank, bandwidth])
                        all_results[command].append(bandwidth)
                    
                    # Calculate and print the average for this specific run
                    run_avg = np.mean([bw for _, bw in bandwidth_data])
                    print(f"    - Run {run_num} complete. Average bandwidth for this run: {run_avg:.2f} GB/s")


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
            overall_avg = np.mean(bandwidths)
            print(f"\nExperiment: {command}")
            print(f"  - Total Average Bandwidth across all runs: {overall_avg:.2f} GB/s")
            min_bw = np.min(bandwidths)
            max_bw = np.max(bandwidths)
            print(f"  - Min Bandwidth (single rank): {min_bw:.2f} GB/s")
            print(f"  - Max Bandwidth (single rank): {max_bw:.2f} GB/s")
        else:
            print(f"\nExperiment: {command}")
            print("  - No data collected for this experiment.")

    print(f"\nDetailed results saved to '{output_filename}'")


if __name__ == "__main__":
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Run benchmark experiments for test_low_latency.py and save results to a CSV file.",
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
    
    parser.add_argument(
        '-o', '--output-file',
        type=str,
        default="benchmark_results.csv",
        help='Name of the output CSV file (default: benchmark_results.csv).'
    )
    
    parsed_args = parser.parse_args()
    main(parsed_args)
