#!/usr/bin/env python3
"""
Test script to verify the split send/recv events functionality
"""

import os
import sys
import pandas as pd
import subprocess

def test_split_events():
    """Test that send/recv events are properly split into separate rows"""
    
    print("Testing split send/recv events functionality")
    print("="*60)
    
    # Create a test command that outputs send/recv times
    test_command = """echo '[rank 0] Dispatch + combine bandwidth: 24.38 GB/s, avg_t=904.30 us, min_t=890.59 us, max_t=925.28 us
[rank 1] Dispatch + combine bandwidth: 24.38 GB/s, avg_t=904.32 us, min_t=889.57 us, max_t=927.23 us
[rank 2] Dispatch + combine bandwidth: 24.39 GB/s, avg_t=904.16 us, min_t=887.36 us, max_t=931.52 us
[rank 0] Dispatch bandwidth: 23.49 GB/s, avg_t=319.75 us | Combine bandwidth: 25.14 GB/s, avg_t=578.22 us
[rank 1] Dispatch bandwidth: 24.02 GB/s, avg_t=312.71 us | Combine bandwidth: 24.83 GB/s, avg_t=585.38 us
[rank 2] Dispatch bandwidth: 24.03 GB/s, avg_t=312.60 us | Combine bandwidth: 24.83 GB/s, avg_t=585.33 us
[rank 0] Dispatch send/recv time: 190.23 + 73509.90 us | Combine send/recv time: 201.45 + 135822.10 us
[rank 1] Dispatch send/recv time: 208.55 + 87379.60 us | Combine send/recv time: 180.49 + 121608.89 us
[rank 2] Dispatch send/recv time: 220.71 + 78025.26 us | Combine send/recv time: 217.64 + 137580.66 us'"""
    
    # Run the benchmark runner
    cmd = f'python3 benchmark_runner.py -c "{test_command}" -n 1 -o test_split.csv'
    
    print(f"Running command to generate CSV...\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        return False
    
    # Read and analyze the CSV
    if not os.path.exists('test_split.csv'):
        print("✗ CSV file was not created")
        return False
    
    df = pd.read_csv('test_split.csv')
    
    print("Generated CSV contents:")
    print(df.to_string())
    print()
    
    # Verify the expected events are present
    expected_events = [
        'dispatch + combine',
        'dispatch',
        'combine',
        'dispatch send',  # Split from dispatch send/recv
        'dispatch recv',  # Split from dispatch send/recv
        'combine send',   # Split from combine send/recv
        'combine recv'    # Split from combine send/recv
    ]
    
    actual_events = df['Event'].unique().tolist()
    
    print("Verification:")
    print(f"Expected events: {expected_events}")
    print(f"Actual events: {actual_events}")
    print()
    
    # Check each expected event
    all_good = True
    for event in expected_events:
        if event in actual_events:
            print(f"✓ Event '{event}' found")
            
            # Check specific columns for send/recv events
            event_row = df[df['Event'] == event].iloc[0]
            
            if 'send' in event:
                send_time = event_row['avg_t_send [us]']
                recv_time = event_row['avg_t_recv [us]']
                if send_time > 0 and recv_time == 0:
                    print(f"  ✓ avg_t_send = {send_time:.2f} us (populated)")
                    print(f"  ✓ avg_t_recv = {recv_time:.2f} us (zero as expected)")
                else:
                    print(f"  ✗ Unexpected values: send={send_time}, recv={recv_time}")
                    all_good = False
                    
            elif 'recv' in event:
                send_time = event_row['avg_t_send [us]']
                recv_time = event_row['avg_t_recv [us]']
                if recv_time > 0 and send_time == 0:
                    print(f"  ✓ avg_t_send = {send_time:.2f} us (zero as expected)")
                    print(f"  ✓ avg_t_recv = {recv_time:.2f} us (populated)")
                else:
                    print(f"  ✗ Unexpected values: send={send_time}, recv={recv_time}")
                    all_good = False
                    
            else:
                # Non send/recv events should have both as 0
                send_time = event_row['avg_t_send [us]']
                recv_time = event_row['avg_t_recv [us]']
                if send_time == 0 and recv_time == 0:
                    print(f"  ✓ Both avg_t_send and avg_t_recv are 0 (as expected)")
                else:
                    print(f"  ✗ Expected both to be 0: send={send_time}, recv={recv_time}")
                    all_good = False
        else:
            print(f"✗ Event '{event}' NOT found")
            all_good = False
    
    # Clean up
    if os.path.exists('test_split.csv'):
        os.remove('test_split.csv')
    
    print()
    if all_good:
        print("✅ All tests passed! Send/recv events are properly split.")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    return all_good

if __name__ == "__main__":
    success = test_split_events()
    sys.exit(0 if success else 1)
