#!/usr/bin/env python3
"""
Debug script to test benchmark_runner.py directly
"""

import subprocess
import os
from datetime import datetime

def test_benchmark_runner():
    """
    Test benchmark_runner with a simple command
    """
    print("Testing benchmark_runner.py directly...")
    print("-" * 60)
    
    # Test with a simple echo command that produces expected output
    test_cmd = """
import time
print("[rank 0] Dispatch + combine bandwidth: 20.5 GB/s, avg_t=1000.5 us, min_t=900 us, max_t=1100 us")
print("[rank 1] Dispatch + combine bandwidth: 21.0 GB/s, avg_t=990.5 us, min_t=890 us, max_t=1090 us")
time.sleep(0.1)
    """
    
    # Create a temporary test script
    test_script = "temp_test_output.py"
    with open(test_script, 'w') as f:
        f.write(test_cmd)
    
    # Run benchmark_runner with this test script
    output_file = f"debug_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    cmd = [
        "python3", "benchmark_runner.py",
        "-c", f"python3 {test_script}",
        "-n", "2",
        "-o", output_file
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Return code:", result.returncode)
        print("\nSTDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        # Check if CSV was created
        if os.path.exists(output_file):
            print(f"\n✓ CSV file created: {output_file}")
            with open(output_file, 'r') as f:
                print("\nCSV Contents:")
                print(f.read())
            os.remove(output_file)
        else:
            print(f"\n✗ CSV file not created: {output_file}")
            
    finally:
        # Clean up
        if os.path.exists(test_script):
            os.remove(test_script)
    
    print("\n" + "-" * 60)
    print("Now testing with actual test_low_latency.py...")
    print("-" * 60)
    
    # Test with actual command
    real_cmd = [
        "python3", "benchmark_runner.py",
        "-c", "python3 tests/test_low_latency.py --disable-nvlink --num-tokens 128",
        "-n", "1",
        "-o", f"real_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    ]
    
    print(f"Command: {' '.join(real_cmd)}")
    print("\nRunning (this may take a minute)...")
    
    result = subprocess.run(
        real_cmd,
        capture_output=True,
        text=True,
        timeout=180
    )
    
    print("Return code:", result.returncode)
    
    # Look for key information
    if result.stdout:
        for line in result.stdout.split('\n'):
            if any(keyword in line for keyword in ["Results saved", "Log directory", "Successful runs", "No data", "Error", "⚠"]):
                print(f"  > {line.strip()}")
    
    if result.stderr:
        print("\nSTDERR (first 10 lines):")
        for line in result.stderr.split('\n')[:10]:
            if line.strip():
                print(f"  {line}")

if __name__ == "__main__":
    if not os.path.exists("benchmark_runner.py"):
        print("Error: benchmark_runner.py not found!")
        exit(1)
    
    test_benchmark_runner()
