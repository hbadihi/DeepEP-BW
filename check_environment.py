#!/usr/bin/env python3
"""
Check if the environment is properly set up for running test_low_latency.py
"""

import os
import sys
import subprocess
import importlib.util

def check_environment():
    """Check various aspects of the environment"""
    
    print("Environment Check for test_low_latency.py")
    print("="*60)
    
    # 1. Check Python version
    print(f"1. Python version: {sys.version}")
    if sys.version_info < (3, 6):
        print("   ⚠ Warning: Python 3.6+ recommended")
    else:
        print("   ✓ Python version OK")
    
    # 2. Check if test file exists
    print("\n2. Checking test file:")
    if os.path.exists("tests/test_low_latency.py"):
        print("   ✓ tests/test_low_latency.py exists")
    else:
        print("   ✗ tests/test_low_latency.py NOT FOUND")
        print(f"   Current directory: {os.getcwd()}")
        return False
    
    # 3. Check PyTorch
    print("\n3. Checking PyTorch:")
    try:
        import torch
        print(f"   ✓ PyTorch version: {torch.__version__}")
        
        # Check CUDA
        if torch.cuda.is_available():
            print(f"   ✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"   ✓ Number of GPUs: {torch.cuda.device_count()}")
        else:
            print("   ✗ CUDA not available")
            return False
    except ImportError:
        print("   ✗ PyTorch not installed")
        return False
    
    # 4. Check distributed package
    print("\n4. Checking torch.distributed:")
    try:
        import torch.distributed as dist
        print("   ✓ torch.distributed available")
    except ImportError:
        print("   ✗ torch.distributed not available")
        return False
    
    # 5. Check deep_ep module
    print("\n5. Checking deep_ep module:")
    try:
        import deep_ep
        print("   ✓ deep_ep module found")
    except ImportError:
        print("   ✗ deep_ep module not found")
        print("   Run: python setup.py install")
        return False
    
    # 6. Check for utils module
    print("\n6. Checking test utils:")
    spec = importlib.util.spec_from_file_location("utils", "tests/utils.py")
    if spec and spec.loader:
        print("   ✓ tests/utils.py found")
    else:
        print("   ✗ tests/utils.py not found")
        return False
    
    # 7. Check multiprocessing
    print("\n7. Checking multiprocessing:")
    try:
        import torch.multiprocessing as mp
        mp.set_start_method('spawn', force=True)
        print("   ✓ torch.multiprocessing available")
    except Exception as e:
        print(f"   ✗ multiprocessing issue: {e}")
        return False
    
    # 8. Check environment variables
    print("\n8. Environment variables:")
    important_vars = ['CUDA_VISIBLE_DEVICES', 'MASTER_PORT', 'MASTER_ADDR']
    for var in important_vars:
        value = os.environ.get(var, "Not set")
        print(f"   {var}: {value}")
    
    # 9. Try a simple distributed test
    print("\n9. Quick distributed test:")
    try:
        # Try to get device count via nvidia-smi
        result = subprocess.run(
            "nvidia-smi -L",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            gpu_lines = [l for l in result.stdout.split('\n') if l.strip()]
            print(f"   ✓ Found {len(gpu_lines)} GPUs via nvidia-smi")
            for line in gpu_lines[:4]:  # Show first 4
                print(f"     {line}")
        else:
            print("   ⚠ Could not query GPUs via nvidia-smi")
    except:
        print("   ⚠ nvidia-smi not available")
    
    print("\n" + "="*60)
    print("Environment check complete!")
    return True

def test_simple_run():
    """Try to run the test with minimal parameters"""
    print("\n10. Attempting minimal test run:")
    print("    Command: python3 tests/test_low_latency.py --num-processes 2 --num-tokens 32")
    
    try:
        result = subprocess.run(
            "python3 tests/test_low_latency.py --num-processes 2 --num-tokens 32",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("   ✓ Test completed successfully!")
            # Show first few lines of output
            lines = result.stdout.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"     {line}")
        else:
            print(f"   ✗ Test failed with return code: {result.returncode}")
            if result.stderr:
                print("   Error output:")
                for line in result.stderr.split('\n')[:5]:
                    if line.strip():
                        print(f"     {line}")
    except subprocess.TimeoutExpired:
        print("   ✗ Test timed out (>30s)")
    except Exception as e:
        print(f"   ✗ Error: {e}")

if __name__ == "__main__":
    if check_environment():
        test_simple_run()
    else:
        print("\n⚠ Please fix the environment issues above before running benchmarks.")
