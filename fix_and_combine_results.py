#!/usr/bin/env python3
"""
Fix script to find and combine existing result CSV files
Use this if the main script couldn't find the files
"""

import glob
import os
import sys
import pandas as pd
from datetime import datetime

def find_and_combine_results():
    """
    Find all result CSV files and create combined tables
    """
    print("=" * 80)
    print("FINDING AND COMBINING RESULT FILES")
    print("=" * 80)
    
    # Look for result files in current directory
    pattern = "results_*.csv"
    result_files = glob.glob(pattern)
    
    if not result_files:
        print(f"\nNo files found matching '{pattern}' in current directory")
        print("Searching in subdirectories...")
        
        # Search recursively
        result_files = glob.glob(f"**/{pattern}", recursive=True)
    
    if not result_files:
        print("No result files found anywhere")
        return []
    
    print(f"\nFound {len(result_files)} result files:")
    
    # Organize files by experiment name
    experiment_files = {}
    
    for filepath in sorted(result_files):
        filename = os.path.basename(filepath)
        # Extract experiment name from filename
        # Format: results_EXPNAME_TIMESTAMP.csv
        parts = filename.replace("results_", "").replace(".csv", "")
        
        # Try to extract experiment name (everything before the timestamp)
        import re
        match = re.match(r'(.+?)_\d{8}_\d{6}', parts)
        if match:
            exp_name = match.group(1)
        else:
            exp_name = parts.split('_')[0] if '_' in parts else parts
        
        # Get file info
        size = os.path.getsize(filepath) / 1024
        mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        print(f"  {filename}")
        print(f"    Experiment: {exp_name}")
        print(f"    Size: {size:.1f} KB")
        print(f"    Modified: {mod_time}")
        
        # Store for combining (keep latest if multiple)
        if exp_name not in experiment_files or os.path.getmtime(filepath) > os.path.getmtime(experiment_files[exp_name][1]):
            experiment_files[exp_name] = (exp_name, filepath)
    
    if not experiment_files:
        print("\nCould not parse experiment names from files")
        return []
    
    # Convert to list of tuples
    results_files = list(experiment_files.values())
    
    print(f"\nWill combine {len(results_files)} experiments")
    
    # Now create combined tables
    from ai_nic_sharing_experiments import create_combined_tables
    
    print("\n" + "=" * 80)
    print("CREATING COMBINED TABLES")
    print("=" * 80)
    
    created_files = create_combined_tables(results_files)
    
    print("\n✅ Done!")
    
    return created_files

def check_csv_contents(filepath):
    """
    Check if a CSV file has valid content
    """
    try:
        df = pd.read_csv(filepath)
        print(f"\n  File: {filepath}")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)[:5]}...")  # Show first 5 columns
        
        if 'Event' in df.columns:
            events = df['Event'].unique()
            print(f"  Events: {list(events)}")
        
        return True
    except Exception as e:
        print(f"\n  Error reading {filepath}: {e}")
        return False

def main():
    """
    Main function
    """
    # First, check if there are any CSV files
    all_csvs = glob.glob("*.csv")
    
    if all_csvs:
        print("\nFound CSV files in current directory:")
        for csv in all_csvs[:10]:  # Show first 10
            print(f"  - {csv}")
        
        # Check a sample file
        if 'results_' in all_csvs[0]:
            print("\nChecking sample file contents:")
            check_csv_contents(all_csvs[0])
    
    # Try to find and combine
    find_and_combine_results()

if __name__ == "__main__":
    main()
