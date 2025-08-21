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

def run_experiment(name, gpu_config, imbalance_test, output_dir, num_runs=5):
    """
    Run a single experiment with the specified configuration
    
    Args:
        name: Descriptive name for the experiment
        gpu_config: GPU configuration string (e.g., "0,2,4,6" or "all")
        imbalance_test: Boolean, whether to include --imbalance-test flag
        output_dir: Directory where output files will be saved
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
    
    # Create output filename with timestamp in the output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"results_{name}_{timestamp}.csv"
    output_file_abs = os.path.join(os.path.abspath(output_dir), output_file)
    
    # Build the benchmark runner command
    benchmark_cmd = [
        "python3", "benchmark_runner.py",
        "-c", cmd,
        "-n", str(num_runs),
        "-o", output_file_abs
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
            
            # Extract and show log directory from benchmark_runner output
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if "Log directory:" in line:
                        log_dir = line.split("Log directory:")[-1].strip()
                        print(f"  Experiment logs saved to: {log_dir}")
                    if "Results saved to:" in line:
                        print(f"  Benchmark runner reported: {line.strip()}")
            
            # Verify the file actually exists
            if os.path.exists(output_file_abs):
                print(f"  Results CSV saved to: {os.path.basename(output_file_abs)}")
            else:
                print(f"  ⚠ Warning: Output file not found after completion")
                print(f"    Expected at: {output_file_abs}")
            
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
            # Return None on failure
            return None
                
    except subprocess.TimeoutExpired:
        print(f"✗ Experiment '{name}' timed out (>30 minutes)")
        return None
    except Exception as e:
        print(f"✗ Unexpected error in experiment '{name}': {e}")
        return None
    
    # Small delay between experiments
    time.sleep(2)
    
    # Return the absolute path if we get here
    return output_file_abs if 'output_file_abs' in locals() else None


def main():
    """
    Main function to run all AI NIC sharing experiments
    """
    print("=" * 80)
    print("AI NIC SHARING EXPERIMENTS")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create output directory for all results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"nic_experiments_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    output_dir_abs = os.path.abspath(output_dir)
    
    print(f"\nOutput Directory: {output_dir_abs}")
    print("All results will be saved here")
    print("-" * 40)
    
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
                output_dir=output_dir,
                num_runs=5
            )
            # Only add to results if file actually exists
            if output_file and os.path.exists(output_file):
                results_files.append((exp_name, output_file))
                successful_experiments += 1
            else:
                print(f"⚠ Warning: Output file for {exp_name} not found")
                failed_experiments.append(exp_name)
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
            # Show relative path within output directory
            rel_path = os.path.basename(filename)
            print(f"  {exp_name:30} -> {rel_path} ({size:.1f} KB)")
        else:
            print(f"  {exp_name:30} -> {os.path.basename(filename)} (not found)")
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create a master summary file in the output directory
    summary_file = os.path.join(output_dir, f"experiment_summary_{timestamp}.txt")
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
    
    # Create combined CSV tables
    print("\n" + "=" * 80)
    print("CREATING COMBINED CSV TABLES")
    print("=" * 80)
    
    if results_files:
        create_combined_tables(results_files, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ All experiments completed!")
    print("=" * 80)
    print(f"\n📁 All results saved in: {output_dir_abs}")
    print(f"   View results with: cd {output_dir} && ls -la")
    print(f"   Combined tables: combined_*.csv")
    print(f"   Individual results: results_*.csv")
    print(f"   Summary report: experiment_summary_{timestamp}.txt")


def create_combined_tables(results_files, output_dir):
    """
    Create 5 combined CSV tables from all experiment results
    
    Args:
        results_files: List of tuples (experiment_name, file_path)
        output_dir: Directory where combined tables will be saved
    """
    import pandas as pd
    
    print(f"\nAttempting to combine {len(results_files)} result files...")
    
    # Read all result files
    all_data = []
    
    for exp_name, filename in results_files:
        print(f"  Checking {exp_name}: {os.path.basename(filename)}")
        if os.path.exists(filename):
            try:
                df = pd.read_csv(filename)
                print(f"    ✓ Read {len(df)} rows")
                # Add experiment name as a column
                df['Experiment'] = exp_name
                all_data.append(df)
            except Exception as e:
                print(f"    ✗ Error reading: {e}")
        else:
            print(f"    ✗ File not found")
    
    if not all_data:
        print("\n⚠ No data to combine - no CSV files could be read")
        print("  Please check that the experiments generated output files")
        return
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Create timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define the 5 tables to create
    tables = [
        ("dispatch_combine", "dispatch + combine"),
        ("combine_only", "combine"),
        ("dispatch_only", "dispatch"),
        ("combine_send_recv", ["combine send", "combine recv"]),
        ("dispatch_send_recv", ["dispatch send", "dispatch recv"])
    ]
    
    # Common columns to keep for the summary
    summary_columns = ['Experiment', 'Event', 'GPU Configuration', 'Imbalance test',
                       'avg bandwidth [GB/s]', 'avg_t [us]', 'avg_t_send [us]', 
                       'avg_t_recv [us]', 'Std deviation [GB/s]']
    
    # Add rank columns
    for i in range(8):
        summary_columns.append(f'Avg. rank{i} BW [GB/s]')
    
    created_files = []
    
    for table_name, event_filter in tables:
        # Filter data for specific events
        if isinstance(event_filter, list):
            # Multiple events (for send/recv tables)
            filtered_df = combined_df[combined_df['Event'].isin(event_filter)]
        else:
            # Single event
            filtered_df = combined_df[combined_df['Event'] == event_filter]
        
        if not filtered_df.empty:
            # Select only available columns
            available_cols = [col for col in summary_columns if col in filtered_df.columns]
            filtered_df = filtered_df[available_cols]
            
            # Sort by experiment name and event (for send/recv tables)
            if isinstance(event_filter, list):
                filtered_df = filtered_df.sort_values(['Experiment', 'Event'])
            else:
                filtered_df = filtered_df.sort_values('Experiment')
            
            # Save to CSV in output directory
            output_file = os.path.join(output_dir, f"combined_{table_name}_{timestamp}.csv")
            filtered_df.to_csv(output_file, index=False, float_format='%.2f')
            created_files.append(output_file)
            
            print(f"✓ Created: {os.path.basename(output_file)} ({len(filtered_df)} rows)")
            
            # Also create a pivot table for better readability
            if not isinstance(event_filter, list):
                # For single event tables, create a pivot showing bandwidth across experiments
                pivot_file = os.path.join(output_dir, f"pivot_{table_name}_{timestamp}.csv")
                
                # Select key columns for pivot
                pivot_data = filtered_df[['Experiment', 'GPU Configuration', 
                                         'Imbalance test', 'avg bandwidth [GB/s]', 
                                         'avg_t [us]', 'Std deviation [GB/s]']]
                
                # Sort by imbalance test and experiment name
                pivot_data = pivot_data.sort_values(['Imbalance test', 'Experiment'])
                
                pivot_data.to_csv(pivot_file, index=False, float_format='%.2f')
                created_files.append(pivot_file)
                print(f"✓ Created pivot table: {os.path.basename(pivot_file)}")
        else:
            print(f"⚠ No data found for {table_name}")
    
    # Create a master combined file with all events
    master_file = os.path.join(output_dir, f"combined_all_events_{timestamp}.csv")
    combined_df.to_csv(master_file, index=False, float_format='%.2f')
    created_files.append(master_file)
    print(f"✓ Created master file: {os.path.basename(master_file)} ({len(combined_df)} rows)")
    
    # Create a summary statistics file
    create_summary_statistics(combined_df, timestamp, output_dir)
    
    return created_files


def create_summary_statistics(df, timestamp, output_dir):
    """
    Create summary statistics across all experiments
    
    Args:
        df: Combined dataframe with all results
        timestamp: Timestamp string for file naming
        output_dir: Directory where output file will be saved
    """
    import pandas as pd
    
    summary_file = os.path.join(output_dir, f"summary_statistics_{timestamp}.csv")
    
    # Calculate statistics for dispatch + combine events
    dispatch_combine = df[df['Event'] == 'dispatch + combine']
    
    if not dispatch_combine.empty:
        # Group by imbalance test
        stats = []
        
        for imbalance in [False, True]:
            imb_data = dispatch_combine[dispatch_combine['Imbalance test'] == imbalance]
            if not imb_data.empty:
                stats.append({
                    'Imbalance Test': 'Yes' if imbalance else 'No',
                    'Mean Bandwidth [GB/s]': imb_data['avg bandwidth [GB/s]'].mean(),
                    'Std Bandwidth [GB/s]': imb_data['avg bandwidth [GB/s]'].std(),
                    'Min Bandwidth [GB/s]': imb_data['avg bandwidth [GB/s]'].min(),
                    'Max Bandwidth [GB/s]': imb_data['avg bandwidth [GB/s]'].max(),
                    'Mean Time [us]': imb_data['avg_t [us]'].mean(),
                    'Std Time [us]': imb_data['avg_t [us]'].std(),
                })
        
        if stats:
            stats_df = pd.DataFrame(stats)
            stats_df.to_csv(summary_file, index=False, float_format='%.2f')
            print(f"✓ Created summary statistics: {os.path.basename(summary_file)}")
            
            # Print summary to console
            print("\nSummary Statistics (Dispatch + Combine):")
            print("-" * 40)
            print(stats_df.to_string(index=False))


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
