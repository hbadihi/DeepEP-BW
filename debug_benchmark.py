#!/usr/bin/env python3
"""
Debug version of benchmark runner to see what's happening
"""

import subprocess
import sys
import os
import time

def test_command_directly():
    """Test the command directly to see if it works"""
    
    command = "python3 tests/test_low_latency.py --disable-nvlink"
    
    print(f"Testing command: {command}")
    print("="*60)
    
    # First, check if the script exists
    if not os.path.exists("tests/test_low_latency.py"):
        print("✗ Error: tests/test_low_latency.py does not exist!")
        print("  Current directory:", os.getcwd())
        print("  Directory contents:")
        for item in os.listdir("."):
            print(f"    - {item}")
        return
    
    print("✓ Script file exists")
    
    # Try running with immediate output
    print("\nRunning command with real-time output...")
    print("-"*40)
    
    start_time = time.time()
    
    try:
        # Run with real-time output
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output as it comes
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{time.time()-start_time:.1f}s] {line.rstrip()}")
                sys.stdout.flush()
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\n✓ Command completed successfully in {time.time()-start_time:.1f} seconds")
        else:
            print(f"\n✗ Command failed with return code: {process.returncode}")
            
    except subprocess.TimeoutExpired:
        print(f"\n✗ Command timed out after {time.time()-start_time:.1f} seconds")
        process.kill()
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        
    print("="*60)

if __name__ == "__main__":
    test_command_directly()
