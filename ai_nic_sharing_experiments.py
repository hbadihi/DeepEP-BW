#!/usr/bin/env python3
"""
AI NIC Sharing Experiments Script
Runs various GPU configurations with and without imbalance testing
"""

import subprocess
import os
import sys
from datetime import datetime
import time

def run_experiment(name, gpu_config, imbalance_test, num_runs=5):
    """
    Run a single experiment with the specified configuration
    
    Args:
        name: Descriptive name for the experiment
        gpu_config: GPU configuration string (e.g., "0,2,4,6" or "all")
        imbalance_test: Boolean, whether to include --imbalance-test flag
        num_runs: Number of runs per experiment (default 5)
    """
    print(f"\n{'='*80}")
    print(f"Starting Experiment: {name}")
    print(f"{'='*80}")
    print(f"GPU Configuration: {gpu_config}")
    print(f"Imbalance Test: {imbalance_test}")
    print(f"Number of Runs: {num_runs}")
    
    # Build the command
    base_cmd = "python3 tests/test_low_latency.py --disable-nvlink"
    
    # Add GPU configuration if not "all"
    if gpu_config.lower() != "all":
        # Determine number of processes based on GPU count
        num_gpus = len(gpu_config.split(','))
        cmd = f"CUDA_VISIBLE_DEVICES={gpu_config} {base_cmd} --num-processes {num_gpus}"
    else:
        # Use all available GPUs (assuming 8)
        cmd = base_cmd
    
    # Add imbalance test flag if needed
    if imbalance_test:
        cmd += " --imbalance-test"
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"results_{name}_{timestamp}.csv"
    
    # Build the benchmark runner command
    benchmark_cmd = [
        "python3", "benchmark_runner.py",
        "-c", cmd,
        "-n", str(num_runs),
        "-o", output_file
    ]
    
    print(f"Command: {' '.join(benchmark_cmd)}")
    print(f"Output CSV: {output_file}")
    print("-" * 40)
    
    try:
        # Run the benchmark
        result = subprocess.run(
            benchmark_cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout for entire experiment
        )
        
        # Check if successful
        if result.returncode == 0:
            print(f"✓ Experiment '{name}' completed successfully")
            print(f"  Output saved to: {output_file}")
            
            # Extract summary from output
            if "✓ Results saved to:" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "Summary by Event Type:" in line:
                        # Print summary section
                        idx = lines.index(line)
                        for summary_line in lines[idx:idx+10]:
                            if summary_line.strip():
                                print(f"  {summary_line}")
                            if "=" in summary_line and idx != lines.index(line):
                                break
        else:
            print(f"✗ Experiment '{name}' failed")
            print(f"  Return code: {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr[:500]}")  # First 500 chars of error
                
    except subprocess.TimeoutExpired:
        print(f"✗ Experiment '{name}' timed out (>30 minutes)")
    except Exception as e:
        print(f"✗ Unexpected error in experiment '{name}': {e}")
    
    # Small delay between experiments
    time.sleep(2)
    
    return output_file


def main():
    """
    Main function to run all AI NIC sharing experiments
    """
    print("=" * 80)
    print("AI NIC SHARING EXPERIMENTS")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define all experiments based on the table
    experiments = [
        # Name, GPU Configuration, Imbalance Test
        ("1-to-1", "0,2,4,6", False),
        ("2-to-1-1x", "0,1,2,4", False),
        ("2-to-1-2x", "0,1,4,5", False),
        ("all-to-all", "all", False),
        ("1-to-1-imbalanced", "0,2,4,6", True),
        ("2-to-1-1x-imbalanced", "0,1,2,4", True),
        ("2-to-1-2x-imbalanced", "0,1,4,5", True),
        ("all-to-all-imbalanced", "all", True),
    ]
    
    # Track results
    results_files = []
    successful_experiments = 0
    failed_experiments = []
    
    # Run each experiment
    for exp_name, gpu_config, imbalance in experiments:
        try:
            output_file = run_experiment(
                name=exp_name,
                gpu_config=gpu_config,
                imbalance_test=imbalance,
                num_runs=5
            )
            results_files.append((exp_name, output_file))
            successful_experiments += 1
        except Exception as e:
            print(f"Failed to run experiment {exp_name}: {e}")
            failed_experiments.append(exp_name)
    
    # Final summary
    print("\n" + "=" * 80)
    print("EXPERIMENT SUMMARY")
    print("=" * 80)
    print(f"Total Experiments: {len(experiments)}")
    print(f"Successful: {successful_experiments}")
    print(f"Failed: {len(failed_experiments)}")
    
    if failed_experiments:
        print("\nFailed Experiments:")
        for exp in failed_experiments:
            print(f"  - {exp}")
    
    print("\nOutput Files:")
    for exp_name, filename in results_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename) / 1024  # Size in KB
            print(f"  {exp_name:30} -> {filename} ({size:.1f} KB)")
        else:
            print(f"  {exp_name:30} -> {filename} (not found)")
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create a master summary file
    summary_file = f"experiment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(summary_file, 'w') as f:
        f.write("AI NIC SHARING EXPERIMENTS SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Experiments Configuration:\n")
        f.write("-" * 40 + "\n")
        f.write(f"{'Experiment':<30} {'GPU Config':<20} {'Imbalance':<10}\n")
        f.write("-" * 40 + "\n")
        for exp_name, gpu_config, imbalance in experiments:
            f.write(f"{exp_name:<30} {gpu_config:<20} {'Yes' if imbalance else 'No':<10}\n")
        
        f.write("\n\nResults Files:\n")
        f.write("-" * 40 + "\n")
        for exp_name, filename in results_files:
            f.write(f"{exp_name}: {filename}\n")
        
        f.write(f"\n\nSummary:\n")
        f.write(f"Total Experiments: {len(experiments)}\n")
        f.write(f"Successful: {successful_experiments}\n")
        f.write(f"Failed: {len(failed_experiments)}\n")
        
        if failed_experiments:
            f.write("\nFailed Experiments:\n")
            for exp in failed_experiments:
                f.write(f"  - {exp}\n")
    
    print(f"\nSummary saved to: {summary_file}")
    print("\n✅ All experiments completed!")


if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists("tests/test_low_latency.py"):
        print("Error: tests/test_low_latency.py not found!")
        print("Please run this script from the DeepEP root directory")
        sys.exit(1)
    
    if not os.path.exists("benchmark_runner.py"):
        print("Error: benchmark_runner.py not found!")
        print("Please ensure benchmark_runner.py is in the current directory")
        sys.exit(1)
    
    # Run all experiments
    main()
