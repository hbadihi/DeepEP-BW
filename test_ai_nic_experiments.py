#!/usr/bin/env python3
"""
Quick test version of AI NIC experiments with reduced parameters
Use this for testing before running the full experiments
"""

import subprocess
import os
import sys
from datetime import datetime

def run_quick_test():
    """
    Run a quick test with minimal parameters to verify setup
    """
    print("=" * 60)
    print("QUICK TEST - AI NIC Sharing Experiments")
    print("=" * 60)
    print("Running with reduced parameters for testing...")
    print()
    
    # Test configurations - using smaller token counts for speed
    test_experiments = [
        ("1-to-1-test", "0,2,4,6", False),
        ("all-to-all-test", "all", False),
    ]
    
    for exp_name, gpu_config, imbalance in test_experiments:
        print(f"\nTesting: {exp_name}")
        print("-" * 40)
        
        # Build test command with minimal parameters
        base_cmd = "python3 tests/test_low_latency.py --disable-nvlink --num-tokens 32"
        
        if gpu_config.lower() != "all":
            num_gpus = len(gpu_config.split(','))
            cmd = f"CUDA_VISIBLE_DEVICES={gpu_config} {base_cmd} --num-processes {num_gpus}"
        else:
            cmd = base_cmd
        
        if imbalance:
            cmd += " --imbalance-test"
        
        output_file = f"test_{exp_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Run with only 1 run for testing
        benchmark_cmd = [
            "python3", "benchmark_runner.py",
            "-c", cmd,
            "-n", "1",  # Just 1 run for testing
            "-o", output_file
        ]
        
        print(f"Command: {' '.join(benchmark_cmd)}")
        
        try:
            result = subprocess.run(
                benchmark_cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes timeout for test
            )
            
            if result.returncode == 0:
                print(f"✓ Test '{exp_name}' completed successfully")
                
                # Check if CSV was created and has data
                if os.path.exists(output_file):
                    size = os.path.getsize(output_file)
                    if size > 100:  # Should be more than 100 bytes if it has data
                        print(f"  CSV created: {output_file} ({size} bytes)")
                    else:
                        print(f"  ⚠ CSV created but seems empty: {output_file}")
                else:
                    print(f"  ⚠ CSV file not created")
                
                # Clean up test file
                if os.path.exists(output_file):
                    os.remove(output_file)
                    print(f"  Cleaned up test file")
                    
            else:
                print(f"✗ Test '{exp_name}' failed with code {result.returncode}")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
                    
        except subprocess.TimeoutExpired:
            print(f"✗ Test '{exp_name}' timed out")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("If tests passed, you can run the full experiments with:")
    print("  python3 ai_nic_sharing_experiments.py")
    print("=" * 60)


if __name__ == "__main__":
    # Check environment
    if not os.path.exists("tests/test_low_latency.py"):
        print("Error: tests/test_low_latency.py not found!")
        print("Please run from the DeepEP root directory")
        sys.exit(1)
    
    if not os.path.exists("benchmark_runner.py"):
        print("Error: benchmark_runner.py not found!")
        sys.exit(1)
    
    run_quick_test()
