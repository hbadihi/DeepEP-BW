#!/usr/bin/env python3
"""
Debug script to find where the CSV files are being created
"""

import os
import glob
import subprocess
from datetime import datetime

def find_csv_files():
    """Find all CSV files in current directory and subdirectories"""
    print("=" * 60)
    print("SEARCHING FOR CSV FILES")
    print("=" * 60)
    
    # Current directory
    print(f"\nCurrent directory: {os.getcwd()}")
    
    # Look for results files in current directory
    print("\nCSV files in current directory:")
    current_dir_csvs = glob.glob("*.csv")
    if current_dir_csvs:
        for f in current_dir_csvs:
            size = os.path.getsize(f) / 1024
            mod_time = datetime.fromtimestamp(os.path.getmtime(f))
            print(f"  - {f} ({size:.1f} KB, modified: {mod_time})")
    else:
        print("  No CSV files found")
    
    # Look for results files pattern
    print("\nResults files matching 'results_*.csv':")
    results_files = glob.glob("results_*.csv")
    if results_files:
        for f in results_files:
            print(f"  - {f}")
    else:
        print("  No results files found")
    
    # Check subdirectories
    print("\nChecking subdirectories:")
    for root, dirs, files in os.walk(".", topdown=True):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        csv_files = [f for f in files if f.endswith('.csv')]
        if csv_files and root != ".":
            print(f"\n  In {root}:")
            for f in csv_files:
                full_path = os.path.join(root, f)
                size = os.path.getsize(full_path) / 1024
                print(f"    - {f} ({size:.1f} KB)")
    
    # Check /tmp for benchmark logs
    print("\n\nChecking /tmp for benchmark logs:")
    tmp_dirs = glob.glob("/tmp/benchmark_logs_*")
    if tmp_dirs:
        print(f"Found {len(tmp_dirs)} benchmark log directories:")
        for d in sorted(tmp_dirs)[-5:]:  # Show last 5
            print(f"  - {d}")
    else:
        print("  No benchmark log directories found")
    
    # Try running a simple echo test to see where files go
    print("\n\nTesting file creation with benchmark_runner:")
    test_cmd = 'echo "test"'
    test_output = f"test_location_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    cmd = [
        "python3", "benchmark_runner.py",
        "-c", test_cmd,
        "-n", "1",
        "-o", test_output
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if os.path.exists(test_output):
            print(f"✓ Test file created at: {os.path.abspath(test_output)}")
            os.remove(test_output)
        else:
            print(f"✗ Test file {test_output} not found in current directory")
            
            # Check if it's somewhere else
            found_files = glob.glob(f"**/{test_output}", recursive=True)
            if found_files:
                print(f"  Found at: {found_files}")
    except Exception as e:
        print(f"Error running test: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    find_csv_files()
