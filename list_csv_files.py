#!/usr/bin/env python3
"""
Simple script to list all CSV files and their locations
"""

import os
import glob
from datetime import datetime

print("=" * 60)
print("CSV FILE FINDER")
print("=" * 60)

# Current directory
print(f"\nCurrent working directory: {os.getcwd()}")

# List all CSV files in current directory
csv_files = glob.glob("*.csv")
if csv_files:
    print(f"\n{len(csv_files)} CSV files in current directory:")
    for f in sorted(csv_files):
        size = os.path.getsize(f) / 1024
        mod_time = datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {f:<50} {size:>8.1f} KB  {mod_time}")
else:
    print("\nNo CSV files in current directory")

# Look specifically for results files
results_files = glob.glob("results_*.csv")
if results_files:
    print(f"\n{len(results_files)} result files found:")
    for f in sorted(results_files):
        print(f"  {f}")

# Check subdirectories
print("\nChecking subdirectories...")
found_in_subdirs = False
for root, dirs, files in os.walk(".", topdown=True):
    # Skip hidden directories and limit depth
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    
    csv_in_dir = [f for f in files if f.endswith('.csv')]
    if csv_in_dir and root != ".":
        if not found_in_subdirs:
            print("CSV files in subdirectories:")
            found_in_subdirs = True
        print(f"\n  {root}/")
        for f in csv_in_dir[:5]:  # Show first 5
            print(f"    - {f}")
        if len(csv_in_dir) > 5:
            print(f"    ... and {len(csv_in_dir) - 5} more")

if not found_in_subdirs:
    print("  No CSV files found in subdirectories")

# Show absolute paths for any results files
if results_files:
    print("\n" + "=" * 60)
    print("ABSOLUTE PATHS OF RESULT FILES:")
    print("=" * 60)
    for f in results_files[:5]:  # Show first 5
        print(f"  {os.path.abspath(f)}")

print("\n" + "=" * 60)
