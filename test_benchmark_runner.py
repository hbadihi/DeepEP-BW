#!/usr/bin/env python3
"""
Test script to verify the benchmark_runner.py modifications
"""

import os
import subprocess
import sys

def test_benchmark_runner():
    """Test the modified benchmark runner with a simple command"""
    
    print("Testing modified benchmark_runner.py")
    print("="*60)
    
    # Test with a simple echo command that mimics the output format
    test_command = """echo '[rank 0] Dispatch + combine bandwidth: 24.38 GB/s, avg_t=904.30 us, min_t=890.59 us, max_t=925.28 us
[rank 1] Dispatch + combine bandwidth: 24.38 GB/s, avg_t=904.32 us, min_t=889.57 us, max_t=927.23 us
[rank 0] Dispatch bandwidth: 23.49 GB/s, avg_t=319.75 us | Combine bandwidth: 25.14 GB/s, avg_t=578.22 us
[rank 1] Dispatch bandwidth: 24.02 GB/s, avg_t=312.71 us | Combine bandwidth: 24.83 GB/s, avg_t=585.38 us
[rank 0] Dispatch send/recv time: 190.23 + 73509.90 us | Combine send/recv time: 201.45 + 135822.10 us
[rank 1] Dispatch send/recv time: 208.55 + 87379.60 us | Combine send/recv time: 180.49 + 121608.89 us'"""
    
    # Run the benchmark runner with test command
    cmd = f'python3 benchmark_runner.py -c "{test_command}" -n 2 -o test_output.csv'
    
    print(f"Running: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    print("Output:")
    print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    # Check if CSV was created
    if os.path.exists('test_output.csv'):
        print("\n✓ CSV file created successfully")
        print("\nCSV Contents:")
        with open('test_output.csv', 'r') as f:
            print(f.read())
        
        # Clean up
        os.remove('test_output.csv')
    else:
        print("\n✗ CSV file was not created")
    
    # Check if logs were created
    import glob
    log_dirs = glob.glob('/tmp/benchmark_logs_*')
    if log_dirs:
        print(f"\n✓ Log directory created: {log_dirs[-1]}")
    else:
        print("\n✗ Log directory was not created")

if __name__ == "__main__":
    test_benchmark_runner()
